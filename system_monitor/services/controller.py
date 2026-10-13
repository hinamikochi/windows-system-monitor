import logging

from PySide6.QtCore import QObject, QTimer
from PySide6.QtGui import QAction, QIcon, QPixmap, QPainter, QColor, QPen
from PySide6.QtWidgets import QMenu, QSystemTrayIcon, QDialog, QMessageBox

from system_monitor.services import startup
from system_monitor.ui.settings import SettingsDialog


def icon():
    pixmap = QPixmap(64, 64)
    pixmap.fill(QColor('transparent'))
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setBrush(QColor('#192538'))
    painter.setPen(QPen(QColor('#7c9cff'), 3))
    painter.drawRoundedRect(4, 4, 56, 56, 12, 12)
    painter.setPen(QPen(QColor('#73c9ec'), 5))
    painter.drawLine(16, 42, 16, 31)
    painter.drawLine(32, 42, 32, 18)
    painter.drawLine(48, 42, 48, 25)
    painter.end()
    return QIcon(pixmap)


class Controller(QObject):
    def __init__(self, app, widget, monitor, store, settings):
        super().__init__(app)
        self.app, self.widget, self.monitor, self.store = app, widget, monitor, store
        self.settings = settings
        self.dialog = None
        self.shutting_down = False
        self.tray = QSystemTrayIcon(icon(), self)
        widget.setWindowIcon(self.tray.icon())
        app.setWindowIcon(self.tray.icon())
        self.menu = QMenu()
        self.menu.addAction('Show / Hide', self.toggle_visible)
        self.pin_action = QAction('Always on Top', self.menu)
        self.pin_action.setCheckable(True)
        self.pin_action.setChecked(settings['always_on_top'])
        self.pin_action.toggled.connect(widget.pin.setChecked)
        self.menu.addAction(self.pin_action)
        self.menu.addAction('Settings', self.open_settings)
        self.menu.addSeparator()
        self.menu.addAction('Exit', self.exit)
        self.tray.setContextMenu(self.menu)
        self.tray.setToolTip('System Monitor')
        self.tray.activated.connect(self.tray_activated)
        self.tray.show()
        self.check_tray()
        self.tray_timer = QTimer(self)
        self.tray_timer.setInterval(5000)
        self.tray_timer.timeout.connect(self.check_tray)
        self.tray_timer.start()
        widget.settings_requested.connect(self.open_settings)
        widget.pin_changed.connect(self.pin_changed)
        widget.closing.connect(self.save)
        app.aboutToQuit.connect(self.shutdown)
        app.screenAdded.connect(self.attach_screen)
        app.screenRemoved.connect(lambda *_: widget.ensure_on_screen())
        for screen in app.screens():
            self.attach_screen(screen)

    def attach_screen(self, screen):
        screen.availableGeometryChanged.connect(lambda *_: self.widget.ensure_on_screen())
        screen.geometryChanged.connect(lambda *_: self.widget.ensure_on_screen())

    def check_tray(self):
        available = QSystemTrayIcon.isSystemTrayAvailable()
        self.widget.tray_available = available
        self.app.setQuitOnLastWindowClosed(not available)
        if not available and not self.widget.isVisible():
            self.widget.show()

    def toggle_visible(self):
        if self.widget.isVisible() and not self.widget.isMinimized():
            self.save()
            self.widget.hide()
        else:
            self.widget.restore()

    def tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.toggle_visible()

    def pin_changed(self, enabled):
        self.settings['always_on_top'] = enabled
        self.pin_action.blockSignals(True)
        self.pin_action.setChecked(enabled)
        self.pin_action.blockSignals(False)
        self.save()

    def save(self):
        if self.widget.isMinimized():
            geometry = self.widget.normalGeometry()
            if geometry.isValid():
                self.settings['position'] = [geometry.x(), geometry.y()]
        else:
            self.settings['position'] = [self.widget.x(), self.widget.y()]
        try:
            self.store.save(self.settings)
        except OSError:
            logging.exception('Unable to save configuration')

    def open_settings(self):
        if self.dialog is not None:
            self.dialog.raise_()
            self.dialog.activateWindow()
            return
        self.dialog = SettingsDialog(self.settings, self.widget)
        try:
            if self.dialog.exec() != QDialog.DialogCode.Accepted:
                return
            candidate = self.dialog.values()
            try:
                if candidate['startup'] or candidate['startup'] != self.settings['startup']:
                    startup.set_enabled(candidate['startup'])
                self.store.save(candidate)
            except OSError as error:
                try:
                    self.settings['startup'] = startup.enabled()
                except OSError:
                    pass
                QMessageBox.warning(self.widget, 'Settings', f'Unable to save settings: {error}')
                return
            self.settings = candidate
            self.widget.apply_settings(candidate)
            self.monitor.configure_requested.emit(candidate)
            self.save()
        finally:
            self.dialog.deleteLater()
            self.dialog = None

    def exit(self):
        self.widget.exiting = True
        self.app.quit()

    def shutdown(self):
        if self.shutting_down:
            return
        self.shutting_down = True
        self.save()
        self.tray_timer.stop()
        self.tray.hide()
        self.monitor.stop()
