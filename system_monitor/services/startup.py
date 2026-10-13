"""Per-user Windows startup registration, without elevation."""
import os
from pathlib import Path
import subprocess
import sys

NAME = 'SystemMonitorWidget'
RUN_KEY = r'Software\Microsoft\Windows\CurrentVersion\Run'


def command():
    if getattr(sys, 'frozen', False):
        args = [sys.executable]
    else:
        executable = Path(sys.executable)
        windowed = executable.with_name('pythonw.exe')
        args = [str(windowed if windowed.exists() else executable),
                str(Path(__file__).resolve().parents[2] / 'main.py')]
    return subprocess.list2cmdline(args)


def enabled():
    if os.name != 'nt':
        return False
    import winreg
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as key:
            value, _ = winreg.QueryValueEx(key, NAME)
            # A registration from the source build or a moved executable still
            # needs to be visible so the user can remove or update it.
            return isinstance(value, str) and bool(value)
    except FileNotFoundError:
        return False


def set_enabled(value):
    if os.name != 'nt':
        if value:
            raise OSError('Startup is only supported on Windows.')
        return
    import winreg
    with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE) as key:
        if value:
            winreg.SetValueEx(key, NAME, 0, winreg.REG_SZ, command())
        else:
            try:
                winreg.DeleteValue(key, NAME)
            except FileNotFoundError:
                pass
