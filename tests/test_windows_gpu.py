import unittest
from unittest.mock import Mock

from system_monitor.monitoring.windows_gpu import busiest_engine, memory_usage
from system_monitor.monitoring.gpu import GPU


class WindowsGPUTests(unittest.TestCase):
    def test_sum_processes_then_busiest_physical_engine(self):
        def instance(pid, engine, kind='3D', adapter='0x00000000_0x12345678'):
            return f'pid_{pid}_luid_{adapter}_phys_0_eng_{engine}_engtype_{kind}'
        values = [(instance(1, 0), 25), (instance(2, 0), 35),
                  (instance(1, 1, 'Copy'), 45),
                  (instance(1, 0, adapter='0x00000000_0x87654321'), 10)]
        self.assertEqual(busiest_engine(values), 60)

    def test_invalid_and_missing_samples_are_not_zero(self):
        self.assertIsNone(busiest_engine([]))
        self.assertIsNone(busiest_engine([('invalid', 99)]))
        self.assertIsNone(memory_usage([('gpu', float('nan')), ('gpu2', -1)]))
        self.assertEqual(memory_usage([('gpu', 0)]), 0)

    def test_engine_clamped_after_aggregation(self):
        name = 'pid_1_luid_0x0_0x1_phys_0_eng_0_engtype_3D'
        self.assertEqual(busiest_engine([(name, 70), (name, 50)]), 100)

    def test_shared_memory_is_not_fabricated_vram_capacity(self):
        gpu = GPU.__new__(GPU)
        gpu.name = 'Intel Iris Xe Graphics'
        gpu.nvml = gpu.handle = None
        gpu.windows = Mock()
        gpu.windows.sample.return_value = dict(percent=12, shared=1024, dedicated=256)
        sample = gpu.sample()
        self.assertEqual(sample['percent'], 12)
        self.assertEqual(sample['memory_kind'], 'shared')
        self.assertEqual(sample['used'], 1024)
        self.assertIsNone(sample['total'])
        gpu.close()
        self.assertIsNone(gpu.windows)

    def test_counter_error_degrades_to_na(self):
        gpu = GPU.__new__(GPU)
        gpu.name = 'Intel'
        gpu.nvml = gpu.handle = None
        gpu.windows = Mock()
        gpu.windows.sample.side_effect = OSError('counter unavailable')
        self.assertIsNone(gpu.sample()['percent'])
