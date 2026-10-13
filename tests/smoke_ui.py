import os
import sys
from pathlib import Path

os.environ['QT_QPA_PLATFORM'] = 'offscreen'
if os.name == 'nt':
    os.environ['QT_QPA_FONTDIR'] = str(Path(os.environ.get('WINDIR', r'C:\Windows')) / 'Fonts')
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication
from system_monitor.services.monitor import Monitor
from system_monitor.ui.widget import Widget

app = QApplication([])
widget = Widget()
monitor = Monitor()
samples = []
monitor.sampled.connect(samples.append)
monitor.sampled.connect(widget.display)
app.aboutToQuit.connect(monitor.stop)
widget.show()
app.processEvents()
widget.set_background_opacity(100)
opaque = widget.grab().toImage()
widget.set_background_opacity(0)
transparent = widget.grab().toImage()
assert opaque.pixelColor(20, 80).alpha() == 255
assert transparent.pixelColor(20, 80).alpha() == 0
assert max(transparent.pixelColor(x, y).alpha() for x in range(31, 150) for y in range(30, 50)) > 220, 'Title must remain readable'
widget.set_background_opacity(65)
monitor.start()
def preview():
    directory = Path(__file__).resolve().parents[1] / 'build'
    directory.mkdir(exist_ok=True)
    assert widget.grab().save(str(directory / 'ui-preview.png'))
QTimer.singleShot(8000, preview)
QTimer.singleShot(9000, widget.close)
app.exec()
assert len(samples) >= 2, f'Expected live updates, got {len(samples)}'
assert all(samples[-1][key] is not None for key in ('cpu', 'ram', 'disk', 'network'))
assert not monitor.thread.isRunning()
assert widget.metrics['cpu'].value.text() != 'N/A'
print(f'PASS: {len(samples)} real samples; widget updated; worker stopped.')
