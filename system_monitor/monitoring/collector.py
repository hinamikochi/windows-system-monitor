import logging
import os
import time

import psutil
from system_monitor.monitoring.disks import default_disk, normalize_disk

log = logging.getLogger(__name__)


class Collector:
    def __init__(self):
        self.disk_path = default_disk()
        self.previous_network = None
        self.previous_time = None
        self.cpu_primed = False
        self.gpu_reader = None
        self.enabled = {'cpu', 'ram', 'disk', 'network', 'gpu', 'battery'}

    def sample(self):
        result = {}
        for name in ('cpu', 'ram', 'disk', 'network', 'gpu', 'battery'):
            if name not in self.enabled:
                continue
            try:
                result[name] = getattr(self, name)()
            except Exception:
                log.exception('Unable to read %s', name)
                result[name] = None
        return result

    def gpu(self):
        if self.gpu_reader is None:
            from system_monitor.monitoring.gpu import GPU
            self.gpu_reader = GPU()
        return self.gpu_reader.sample()

    def battery(self):
        battery = psutil.sensors_battery()
        if battery is None:
            return None
        return dict(percent=battery.percent, plugged=battery.power_plugged)

    def configure(self, modules, disk_path=None):
        if disk_path is not None:
            self.disk_path = normalize_disk(disk_path)
        self.enabled = {key for key, enabled in modules.items() if enabled}
        # A re-enabled metric needs a fresh baseline, not an average over time hidden.
        self.cpu_primed = False
        self.previous_network = self.previous_time = None
        if 'gpu' not in self.enabled and self.gpu_reader is not None:
            self.gpu_reader.close()
            self.gpu_reader = None

    def close(self):
        if self.gpu_reader is not None:
            self.gpu_reader.close()

    def cpu(self):
        percent = psutil.cpu_percent(interval=None)
        ready = self.cpu_primed
        self.cpu_primed = True
        try:
            frequency = psutil.cpu_freq()
        except (OSError, NotImplementedError, psutil.Error):
            frequency = None
        return dict(percent=percent if ready else None,
                    count=psutil.cpu_count(logical=True),
                    mhz=frequency.current if frequency else None)

    def ram(self):
        memory = psutil.virtual_memory()
        return dict(percent=memory.percent, used=memory.total - memory.available,
                    total=memory.total)

    def disk(self):
        disk = psutil.disk_usage(self.disk_path)
        return dict(percent=disk.percent, used=disk.used, total=disk.total,
                    path=self.disk_path)

    def network(self):
        counters = psutil.net_io_counters()
        now = time.monotonic()
        if counters is None:
            self.previous_network = self.previous_time = None
            return None
        rates = dict(download=None, upload=None)
        if self.previous_network is not None:
            elapsed = now - self.previous_time
            if elapsed > 0:
                rates = dict(
                    download=max(0, counters.bytes_recv - self.previous_network.bytes_recv) / elapsed,
                    upload=max(0, counters.bytes_sent - self.previous_network.bytes_sent) / elapsed)
        self.previous_network, self.previous_time = counters, now
        return rates
