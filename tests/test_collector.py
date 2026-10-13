import unittest
from types import SimpleNamespace
from unittest.mock import patch

from system_monitor.monitoring.collector import Collector


class CollectorTests(unittest.TestCase):
    def test_network_elapsed_time_and_counter_reset(self):
        collector = Collector()
        values = [SimpleNamespace(bytes_recv=100, bytes_sent=100),
                  SimpleNamespace(bytes_recv=2148, bytes_sent=1124),
                  SimpleNamespace(bytes_recv=1, bytes_sent=1)]
        with patch('system_monitor.monitoring.collector.psutil.net_io_counters', side_effect=values), patch('system_monitor.monitoring.collector.time.monotonic', side_effect=[10, 12, 13]):
            self.assertIsNone(collector.network()['download'])
            self.assertEqual(collector.network(), dict(download=1024, upload=512))
            self.assertEqual(collector.network(), dict(download=0, upload=0))

    def test_failure_isolated_to_one_metric(self):
        collector = Collector()
        with patch.object(collector, 'disk', side_effect=PermissionError), patch.object(collector, 'cpu', return_value={'percent': 10}), patch.object(collector, 'ram', return_value={'percent': 20}), patch.object(collector, 'network', return_value={}):
            with self.assertLogs('system_monitor.monitoring.collector', level='ERROR'):
                result = collector.sample()
            self.assertIsNone(result['disk'])
            self.assertEqual(result['cpu']['percent'], 10)
            self.assertEqual(result['ram']['percent'], 20)

    def test_cpu_initial_sample_is_not_reported(self):
        collector = Collector()
        with patch('system_monitor.monitoring.collector.psutil.cpu_percent', return_value=42), patch('system_monitor.monitoring.collector.psutil.cpu_freq', return_value=None):
            self.assertIsNone(collector.cpu()['percent'])
            self.assertEqual(collector.cpu()['percent'], 42)


if __name__ == '__main__':
    unittest.main()
