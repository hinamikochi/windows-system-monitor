# Build a single Windows executable without a console.
from pathlib import Path

root = Path(SPECPATH)
a = Analysis(
    [str(root / 'main.py')], pathex=[str(root)],
    binaries=[], datas=[], hiddenimports=['pynvml'],
    hookspath=[], hooksconfig={}, runtime_hooks=[],
    excludes=['PySide6.QtWebEngineCore', 'PySide6.QtWebEngineWidgets',
              'PySide6.QtWebEngineQuick', 'PySide6.QtPdf', 'PySide6.QtQml',
              'PySide6.QtQuick'], noarchive=False)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, a.binaries, a.datas, [], name='SystemMonitor',
          debug=False, bootloader_ignore_signals=False, strip=False,
          upx=False, console=False, disable_windowed_traceback=False,
          icon=str(root / 'system_monitor' / 'assets' / 'monitor.ico'))
