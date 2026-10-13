import ctypes
import os
import re


def default_disk():
    return os.environ.get('SystemDrive', 'C:').upper() + '\\' if os.name == 'nt' else '/'


def normalize_disk(value):
    if isinstance(value, str) and re.fullmatch(r'[A-Za-z]:[\\/]?', value):
        return value[0].upper() + ':\\'
    if os.name != 'nt' and value == '/':
        return value
    return default_disk()


def available_disks():
    """Enumerate local/removable drives without probing capacity on the UI thread."""
    if os.name != 'nt':
        return ['/']
    library = ctypes.WinDLL('kernel32.dll')
    library.GetLogicalDrives.argtypes = []
    library.GetLogicalDrives.restype = ctypes.c_uint32
    library.GetDriveTypeW.argtypes = [ctypes.c_wchar_p]
    library.GetDriveTypeW.restype = ctypes.c_uint32
    mask = library.GetLogicalDrives()
    return [root for index in range(26)
            if mask & (1 << index)
            for root in [chr(65 + index) + ':\\']
            if library.GetDriveTypeW(root) in (2, 3, 6)]
