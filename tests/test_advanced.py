import unittest
from types import SimpleNamespace
from unittest.mock import patch

from system_monitor.monitoring.collector import Collector
from system_monitor.monitoring.gpu import GPU


class AdvancedTests(unittest.TestCase):
    def test_absent_battery(self):
        with patch('psutil.sensors_battery', return_value=None):
            self.assertIsNone(Collector().battery())

    def test_battery_charging(self):
        with patch('psutil.sensors_battery', return_value=SimpleNamespace(percent=73, power_plugged=True)):
            self.assertEqual(Collector().battery(), dict(percent=73, plugged=True))

    def test_unsupported_gpu_remains_readable(self):
        gpu = GPU.__new__(GPU)
        gpu.nvml = gpu.handle = None
        gpu.name = 'Intel graphics'
        self.assertEqual(gpu.sample(), dict(name='Intel graphics', percent=None, used=None, total=None))

    def test_gpu_partial_support(self):
        gpu = GPU.__new__(GPU)
        gpu.name = 'NVIDIA'
        gpu.handle = object()
        from unittest.mock import Mock
        gpu.nvml = Mock()
        gpu.nvml.nvmlDeviceGetUtilizationRates.side_effect = RuntimeError('not supported')
        gpu.nvml.nvmlDeviceGetMemoryInfo.return_value = SimpleNamespace(used=10, total=20)
        self.assertEqual(gpu.sample(), dict(name='NVIDIA', percent=None, used=10, total=20))

    def test_disabled_modules_are_not_polled(self):
        collector = Collector()
        collector.configure(dict(cpu=False, gpu=False, battery=False))
        with patch.object(collector, 'gpu', side_effect=AssertionError('must not poll')):
            self.assertEqual(collector.sample(), {})
