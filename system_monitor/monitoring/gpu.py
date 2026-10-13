"""NVIDIA NVML telemetry with native Windows counters for Intel/AMD."""
import logging
import os

log = logging.getLogger(__name__)


class GPU:
    def __init__(self):
        self.nvml = None
        self.handle = None
        self.windows = None
        self.name = 'N/A'
        try:
            import pynvml
            pynvml.nvmlInit()
            self.nvml = pynvml
            self.handle = pynvml.nvmlDeviceGetHandleByIndex(0)
            name = pynvml.nvmlDeviceGetName(self.handle)
            self.name = name.decode(errors='replace') if isinstance(name, bytes) else name
        except Exception:
            self.close()
            if os.name == 'nt':
                try:
                    from system_monitor.monitoring.windows_gpu import adapter_names, WindowsGPU
                    names = adapter_names()
                    self.name = names[0] if len(names) == 1 else 'Windows GPUs (all adapters)' if names else 'Windows GPU'
                    self.windows = WindowsGPU()
                except Exception:
                    log.debug('Windows GPU telemetry unavailable', exc_info=True)

    def sample(self):
        result = dict(name=self.name, percent=None, used=None, total=None)
        windows = getattr(self, 'windows', None)
        if windows is not None:
            try:
                sample = windows.sample()
                result.update(percent=sample['percent'], used=sample['shared'],
                              memory_kind='shared', dedicated=sample['dedicated'])
            except Exception:
                log.debug('GPU counters unavailable', exc_info=True)
        if self.nvml is not None and self.handle is not None:
            try:
                result['percent'] = self.nvml.nvmlDeviceGetUtilizationRates(self.handle).gpu
            except Exception:
                pass
            try:
                memory = self.nvml.nvmlDeviceGetMemoryInfo(self.handle)
                result.update(used=memory.used, total=memory.total)
            except Exception:
                pass
        return result

    def close(self):
        if getattr(self, 'windows', None) is not None:
            self.windows.close()
            self.windows = None
        if self.nvml is not None:
            try:
                self.nvml.nvmlShutdown()
            except Exception:
                log.debug('NVML shutdown failed', exc_info=True)
        self.nvml = self.handle = None
