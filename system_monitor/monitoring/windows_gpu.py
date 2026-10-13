"""Persistent Windows PDH query for WDDM GPU counters (no shell polling)."""
import ctypes as ct
import math
import os
import re

DWORD = ct.c_uint32
HANDLE = ct.c_void_p
MORE_DATA = 0x800007D2
FMT_DOUBLE = 0x200 | 0x800  # Preserve raw byte counts and uncapped per-process values.


class ValueUnion(ct.Union):
    _fields_ = [('doubleValue', ct.c_double), ('largeValue', ct.c_int64),
                ('longValue', ct.c_int32), ('stringValue', ct.c_void_p)]


class Value(ct.Structure):
    _anonymous_ = ('value',)
    _fields_ = [('status', DWORD), ('value', ValueUnion)]


class Item(ct.Structure):
    _fields_ = [('name', ct.c_wchar_p), ('value', Value)]


class DisplayDevice(ct.Structure):
    _fields_ = [('cb', DWORD), ('device', ct.c_wchar * 32),
                ('description', ct.c_wchar * 128), ('flags', DWORD),
                ('id', ct.c_wchar * 128), ('key', ct.c_wchar * 128)]


def adapter_names():
    if os.name != 'nt':
        return []
    dll = ct.WinDLL('user32.dll')
    enum = dll.EnumDisplayDevicesW
    enum.argtypes = [ct.c_wchar_p, DWORD, ct.POINTER(DisplayDevice), DWORD]
    enum.restype = ct.c_int32
    names = []
    for index in range(64):
        device = DisplayDevice()
        device.cb = ct.sizeof(device)
        if not enum(None, index, ct.byref(device), 0):
            break
        if device.description and not device.flags & 8 and device.description not in names:
            names.append(device.description)
    return names


def busiest_engine(values):
    # Sum processes on each physical engine, then take the busiest engine.
    # Summing independent engines would incorrectly exceed 100%.
    engines = {}
    for name, value in values:
        match = re.search(r'(luid_0x[0-9a-f]+_0x[0-9a-f]+_phys_\d+)_eng_(\d+)', name, re.I)
        if match and math.isfinite(value) and value >= 0:
            key = match.group(0).lower()
            engines[key] = engines.get(key, 0.0) + value
    return min(100.0, max(engines.values())) if engines else None


def memory_usage(values):
    samples = [value for _, value in values if math.isfinite(value) and value >= 0]
    return round(sum(samples)) if samples else None


class WindowsGPU:
    def __init__(self):
        self.query = HANDLE()
        self.counters = {}
        self.ready = False
        self.dll = ct.WinDLL('pdh.dll')
        signatures = {
            'PdhOpenQueryW': ([ct.c_wchar_p, ct.c_size_t, ct.POINTER(HANDLE)],),
            'PdhAddEnglishCounterW': ([HANDLE, ct.c_wchar_p, ct.c_size_t, ct.POINTER(HANDLE)],),
            'PdhCollectQueryData': ([HANDLE],),
            'PdhGetFormattedCounterArrayW': ([HANDLE, DWORD, ct.POINTER(DWORD), ct.POINTER(DWORD), ct.c_void_p],),
            'PdhCloseQuery': ([HANDLE],),
        }
        for name, (arguments,) in signatures.items():
            function = getattr(self.dll, name)
            function.argtypes = arguments
            function.restype = DWORD
        if self.dll.PdhOpenQueryW(None, 0, ct.byref(self.query)) != 0:
            raise OSError('Unable to open GPU performance query')
        try:
            for key, path in {
                'percent': r'\GPU Engine(*)\Utilization Percentage',
                'shared': r'\GPU Adapter Memory(*)\Shared Usage',
                'dedicated': r'\GPU Adapter Memory(*)\Dedicated Usage',
            }.items():
                counter = HANDLE()
                if self.dll.PdhAddEnglishCounterW(self.query, path, 0, ct.byref(counter)) == 0:
                    self.counters[key] = counter
            self.dll.PdhCollectQueryData(self.query)
        except Exception:
            self.close()
            raise

    def read(self, key):
        counter = self.counters.get(key)
        if counter is None:
            return []
        # Instance counts can change between sizing and reading the array.
        size, count = DWORD(), DWORD()
        for _ in range(3):
            size.value = 0
            status = self.dll.PdhGetFormattedCounterArrayW(counter, FMT_DOUBLE, ct.byref(size), ct.byref(count), None)
            if status != MORE_DATA or not size.value or size.value > 32 * 1024 * 1024:
                return []
            buffer = ct.create_string_buffer(size.value)
            status = self.dll.PdhGetFormattedCounterArrayW(counter, FMT_DOUBLE, ct.byref(size), ct.byref(count), buffer)
            if status == MORE_DATA:
                continue
            if status != 0 or count.value * ct.sizeof(Item) > len(buffer):
                return []
            items = ct.cast(buffer, ct.POINTER(Item))
            return [(items[i].name or '', items[i].value.doubleValue)
                    for i in range(count.value) if items[i].value.status in (0, 1)]
        return []

    def sample(self):
        if self.dll.PdhCollectQueryData(self.query) != 0:
            self.ready = False
            return dict(percent=None, shared=None, dedicated=None)
        percent = busiest_engine(self.read('percent')) if self.ready else None
        self.ready = True
        return dict(percent=percent,
                    shared=memory_usage(self.read('shared')),
                    dedicated=memory_usage(self.read('dedicated')))

    def close(self):
        if self.query.value:
            self.dll.PdhCloseQuery(self.query)
            self.query = HANDLE()
