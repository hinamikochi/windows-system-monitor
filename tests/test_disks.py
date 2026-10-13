from types import SimpleNamespace
import unittest
from unittest.mock import patch

from system_monitor.config.store import defaults, validate
from system_monitor.monitoring.collector import Collector
from system_monitor.monitoring.disks import normalize_disk


class DiskTests(unittest.TestCase):
    def test_config_accepts_letters_and_rejects_arbitrary_paths(self):
        self.assertEqual(validate({'disk_path': 'd:/'})['disk_path'], 'D:\\')
        self.assertEqual(validate({'disk_path': 'E:'})['disk_path'], 'E:\\')
        self.assertEqual(validate({'disk_path': r'\\server\share'})['disk_path'], defaults()['disk_path'])

    def test_selected_drive_is_used_by_collector(self):
        collector = Collector()
        collector.configure({'disk': True}, 'D:\\')
        with patch('psutil.disk_usage', return_value=SimpleNamespace(percent=25, used=25, total=100)) as usage:
            self.assertEqual(collector.sample()['disk']['path'], 'D:\\')
            usage.assert_called_once_with('D:\\')

    def test_removed_drive_does_not_crash(self):
        collector = Collector()
        collector.configure({'disk': True}, 'E:\\')
        with patch('psutil.disk_usage', side_effect=FileNotFoundError), self.assertLogs('system_monitor.monitoring.collector'):
            self.assertIsNone(collector.sample()['disk'])
