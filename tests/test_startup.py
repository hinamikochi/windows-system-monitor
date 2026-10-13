import os
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch, MagicMock

from system_monitor.services import startup


@unittest.skipUnless(os.name == 'nt', 'Windows integration')
class StartupTests(unittest.TestCase):
    def test_old_executable_registration_can_be_disabled(self):
        registry = MagicMock()
        registry.QueryValueEx.return_value = ('"C:\\Old Folder\\SystemMonitor.exe"', 1)
        with patch.dict(sys.modules, {'winreg': registry}):
            self.assertTrue(startup.enabled())

    def test_frozen_path_is_quoted(self):
        with patch.object(sys, 'frozen', True, create=True), patch.object(sys, 'executable', r'C:\App Folder\SystemMonitor.exe'):
            self.assertEqual(startup.command(), '"C:\\App Folder\\SystemMonitor.exe"')

    def test_registry_enable_and_disable_use_current_user(self):
        registry = MagicMock()
        handle = registry.CreateKeyEx.return_value.__enter__.return_value
        with patch.dict(sys.modules, {'winreg': registry}):
            startup.set_enabled(True)
            registry.CreateKeyEx.assert_called_with(registry.HKEY_CURRENT_USER, startup.RUN_KEY, 0, registry.KEY_SET_VALUE)
            registry.SetValueEx.assert_called_once_with(handle, startup.NAME, 0, registry.REG_SZ, startup.command())
            startup.set_enabled(False)
            registry.DeleteValue.assert_called_once_with(handle, startup.NAME)
