import os
from pathlib import Path
import sys
import tempfile
from unittest.mock import patch

os.environ['QT_QPA_PLATFORM'] = 'offscreen'
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PySide6.QtCore import QTimer, Qt, QEventLoop
from PySide6.QtWidgets import QApplication
from system_monitor.config.store import defaults, Store
from system_monitor.services.controller import Controller
from system_monitor.services.monitor import Monitor
from system_monitor.services.instance import Instance
from system_monitor.ui.widget import Widget

app = QApplication([])
errors = []


def checked(function):
    def run():
        try:
            function()
        except Exception as error:
            errors.append(error)
            app.quit()
    return run


with tempfile.TemporaryDirectory() as directory:
    store = Store(Path(directory) / 'config.json')
    first = Instance(Path(directory))
    second = Instance(Path(directory))
    notified = []
    first.show_requested.connect(lambda: notified.append(True))
    assert first.acquire()
    assert not second.acquire(), 'Duplicate instance must be refused'
    event_loop = QEventLoop()
    QTimer.singleShot(100, event_loop.quit)
    event_loop.exec()
    assert notified, 'Second launch must notify the existing instance'
    first.close()
    assert second.acquire()
    second.close()
    settings = defaults()
    widget = Widget()
    widget.apply_settings(settings)
    widget.move(-50000, -50000)
    widget.ensure_on_screen()
    assert app.primaryScreen().availableGeometry().intersects(widget.frameGeometry())
    monitor = Monitor(settings=settings)
    controller = Controller(app, widget, monitor, store, settings)
    controller.tray_timer.stop()
    app.setQuitOnLastWindowClosed(False)
    widget.tray_available = True
    samples = []
    monitor.sampled.connect(samples.append)
    monitor.sampled.connect(widget.display)
    widget.show()
    monitor.start()

    def change_settings():
        def accept_dialog():
            dialog = controller.dialog
            for key, checkbox in dialog.modules.items():
                checkbox.setChecked(key == 'cpu')
            dialog.interval.setCurrentIndex(dialog.interval.findData(2))
            dialog.pin.setChecked(True)
            dialog.opacity.setValue(80)
            dialog.disk.addItem('D:\\', 'D:\\')
            dialog.disk.setCurrentIndex(dialog.disk.count() - 1)
            dialog.startup.setChecked(not settings['startup'])
            dialog.accept()
        with patch('system_monitor.services.startup.set_enabled') as startup:
            QTimer.singleShot(0, accept_dialog)
            controller.open_settings()
            startup.assert_called_once_with(True)
        assert controller.settings['interval'] == 2
        assert controller.settings['background_opacity'] == 80
        assert controller.settings['disk_path'] == 'D:\\'
        assert widget.windowFlags() & Qt.WindowType.WindowStaysOnTopHint
        assert controller.pin_action.isChecked()
        assert widget.metrics['ram'].isHidden()
        assert widget.network_frame.isHidden()
        normal_position = widget.pos()
        widget.minimize.click()
        assert widget.isMinimized()
        assert monitor.thread.isRunning(), 'Minimizing must preserve monitoring'
        widget.pin.setChecked(False)
        assert widget.isMinimized(), 'Changing Pin must not restore the minimized window'
        controller.save()
        assert store.load()['position'] == [normal_position.x(), normal_position.y()]
        controller.toggle_visible()
        assert not widget.isMinimized() and widget.isVisible(), 'Tray must restore a minimized window'
        widget.close()
        assert not widget.isVisible(), 'Close should hide with a tray'
        assert monitor.thread.isRunning(), 'Hiding must preserve monitoring'
        controller.toggle_visible()
        assert widget.isVisible()

    def finish():
        assert len(samples) >= 2
        assert set(samples[-1]) == {'cpu'}, 'Disabled modules must not be collected'
        assert store.load()['interval'] == 2
        assert store.load()['disk_path'] == 'D:\\'
        controller.exit()

    QTimer.singleShot(6500, checked(change_settings))
    QTimer.singleShot(12500, checked(finish))
    QTimer.singleShot(20000, app.quit)
    app.exec()
    controller.shutdown()
    assert not errors, errors
    assert not monitor.thread.isRunning()
    assert controller.shutting_down
    print('PASS: settings, polling filter, Pin, tray hide/show, screen recovery, JSON, lock and shutdown.')
