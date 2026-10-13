"""Generate a Windows icon from the same Qt drawing used by the tray."""
import os
from pathlib import Path
import struct
import sys

os.environ['QT_QPA_PLATFORM'] = 'offscreen'
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from PySide6.QtCore import QBuffer, QIODevice
from PySide6.QtWidgets import QApplication
from system_monitor.services.controller import icon

app = QApplication([])
buffer = QBuffer()
buffer.open(QIODevice.OpenModeFlag.WriteOnly)
assert icon().pixmap(64, 64).save(buffer, 'PNG')
png = bytes(buffer.data())
header = struct.pack('<HHH', 0, 1, 1)
entry = struct.pack('<BBBBHHII', 64, 64, 0, 0, 1, 32, len(png), 22)
path = Path(__file__).resolve().parents[1] / 'system_monitor' / 'assets' / 'monitor.ico'
path.write_bytes(header + entry + png)
print(path)
