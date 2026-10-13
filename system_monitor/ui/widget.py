from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, Slot, Signal
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (QWidget, QFrame, QVBoxLayout, QHBoxLayout,
                              QLabel, QPushButton, QProgressBar,
                              QGraphicsDropShadowEffect, QApplication)


def size(value):
    return f'{value / 1024 ** 3:.1f} GB'


def rate(value):
    if value is None:
        return 'N/A'
    if value >= 1024 ** 2:
        return f'{value / 1024 ** 2:.1f} MB/s'
    return f'{value / 1024:.1f} KB/s'


class Metric(QFrame):
    def __init__(self, title, color):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 9, 0, 9)
        row = QHBoxLayout()
        name = QLabel(title)
        name.setStyleSheet('color: #a8b2c3; font-weight: 600;')
        self.value = QLabel('N/A')
        self.value.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.value.setStyleSheet('font-size: 19px; font-weight: 600;')
        row.addWidget(name)
        row.addWidget(self.value)
        layout.addLayout(row)
        self.bar = QProgressBar()
        self.bar.setRange(0, 1000)
        self.bar.setTextVisible(False)
        self.bar.setFixedHeight(5)
        self.bar.setStyleSheet(f'QProgressBar {{background: #293141; border: none; border-radius: 2px;}} QProgressBar::chunk {{background: {color}; border-radius: 2px;}}')
        layout.addWidget(self.bar)
        self.detail = QLabel('Waiting for sample…')
        self.detail.setStyleSheet('color: #8995a8; font-size: 11px;')
        layout.addWidget(self.detail)
        self.animation = QPropertyAnimation(self.bar, b'value', self)
        self.animation.setDuration(350)
        self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)

    def update_metric(self, percent, detail):
        self.value.setText('N/A' if percent is None else f'{percent:.0f}%')
        self.detail.setText(detail)
        self.animation.stop()
        self.animation.setStartValue(self.bar.value())
        self.animation.setEndValue(round((percent or 0) * 10))
        self.animation.start()


class Widget(QWidget):
    settings_requested = Signal()
    closing = Signal()
    pin_changed = Signal(bool)

    def __init__(self):
        super().__init__()
        self.setWindowTitle('System Monitor')
        self.setFont(QFont('Segoe UI', 9))
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window | Qt.WindowType.WindowMinimizeButtonHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedWidth(320)
        self.drag_offset = None
        self.settings = None
        self.tray_available = False
        self.exiting = False
        outer = QVBoxLayout(self)
        outer.setContentsMargins(12, 12, 12, 12)
        panel = QFrame()
        self.panel = panel
        panel.setObjectName('panel')
        panel.setStyleSheet('QFrame#panel {background: rgba(20, 26, 37, 235); border: 1px solid #354052; border-radius: 16px;} QLabel {color: #ecf1fa; font-family: "Segoe UI"; font-size: 12px;} QPushButton {color: #b9c6d9; background: #293345; border: none; border-radius: 6px; padding: 5px;} QPushButton:checked {background: #365b77;} QPushButton:hover {background: #405069;}')
        shadow = QGraphicsDropShadowEffect(panel)
        shadow.setBlurRadius(20)
        shadow.setOffset(0, 3)
        shadow.setColor(QColor(0, 0, 0, 100))
        panel.setGraphicsEffect(shadow)
        self.shadow = shadow
        self.set_background_opacity(65)
        outer.addWidget(panel)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(18, 16, 18, 16)
        header = QHBoxLayout()
        title = QLabel('SYSTEM MONITOR')
        title.setStyleSheet('font-size: 11px; font-weight: 700; color: #cbd6e6;')
        header.addWidget(title)
        header.addStretch()
        settings_button = QPushButton('⋯')
        settings_button.setToolTip('Settings')
        settings_button.clicked.connect(self.settings_requested.emit)
        header.addWidget(settings_button)
        self.pin = QPushButton('Pin')
        self.pin.setMinimumWidth(30)
        self.pin.setStyleSheet('font-family: "Segoe UI"; font-size: 12px;')
        self.pin.setCheckable(True)
        self.pin.setToolTip('Always on Top')
        self.pin.toggled.connect(self.set_on_top)
        header.addWidget(self.pin)
        self.minimize = QPushButton('−')
        self.minimize.setStyleSheet('font-family: "Segoe UI"; font-size: 12px;')
        self.minimize.setToolTip('Minimize to taskbar')
        self.minimize.clicked.connect(self.showMinimized)
        header.addWidget(self.minimize)
        close = QPushButton('×')
        close.setToolTip('Hide to tray (or exit if tray is unavailable)')
        close.clicked.connect(self.close)
        header.addWidget(close)
        layout.addLayout(header)
        self.metrics = {}
        for key, title, color in [('cpu', 'CPU', '#7c9cff'), ('ram', 'RAM', '#aa91ef'), ('gpu', 'GPU', '#e5b66c'), ('disk', 'DISK', '#57c4b0'), ('battery', 'BATTERY', '#8ac989')]:
            metric = Metric(title, color)
            self.metrics[key] = metric
            if key == 'battery':
                metric.hide()
            layout.addWidget(metric)
        self.network_frame = QFrame()
        network_layout = QVBoxLayout(self.network_frame)
        network_layout.setContentsMargins(0, 0, 0, 0)
        network_layout.addWidget(QLabel('NETWORK'))
        self.network = QLabel('↓ N/A     ↑ N/A')
        self.network.setStyleSheet('font-size: 15px; color: #73c9ec;')
        network_layout.addWidget(self.network)
        layout.addWidget(self.network_frame)
        self.status = QLabel('LIVE  ·  1 second refresh')
        self.status.setStyleSheet('font-size: 10px; color: #8995a8;')
        layout.addWidget(self.status)
        self.adjustSize()
        screen = QApplication.primaryScreen().availableGeometry()
        self.move(screen.right() - self.width() - 24, screen.top() + 24)

    @Slot(bool)
    def set_on_top(self, enabled):
        minimized = self.isMinimized()
        position = self.normalGeometry().topLeft() if minimized and self.normalGeometry().isValid() else self.pos()
        visible = self.isVisible()
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, enabled)
        self.move(position)
        if visible:
            self.showMinimized() if minimized else self.show()
        self.pin_changed.emit(enabled)

    def apply_settings(self, settings):
        self.settings = settings
        self.setWindowOpacity(1.0)
        self.set_background_opacity(settings['background_opacity'])
        self.pin.setChecked(settings['always_on_top'])
        for key, metric in self.metrics.items():
            metric.setVisible(settings['modules'][key] and key != 'battery')
        self.network_frame.setVisible(settings['modules']['network'])
        self.adjustSize()
        self.ensure_on_screen()

    def set_background_opacity(self, percent):
        alpha = round(max(0, min(100, percent)) * 255 / 100)
        border = '#354052' if alpha else 'transparent'
        self.panel.setStyleSheet(
            f'QFrame#panel {{background: rgba(20, 26, 37, {alpha}); border: 1px solid {border}; border-radius: 16px;}} '
            'QLabel {color: #ecf1fa; font-family: "Segoe UI"; font-size: 12px; background: transparent;} '
            'QPushButton {color: #b9c6d9; background: #293345; border: none; border-radius: 6px; padding: 5px;} '
            'QPushButton:checked {background: #365b77;} QPushButton:hover {background: #405069;}')
        self.shadow.setEnabled(alpha > 0)

    def restore(self):
        self.showNormal() if self.isMinimized() else self.show()
        self.ensure_on_screen()
        self.raise_()
        self.activateWindow()

    def ensure_on_screen(self):
        if self.isMinimized():
            return
        screens = QApplication.screens()
        if not screens:
            return
        screen = QApplication.screenAt(self.frameGeometry().center()) or QApplication.primaryScreen()
        area = screen.availableGeometry()
        self.move(max(area.left(), min(self.x(), area.right() - self.width() + 1)),
                  max(area.top(), min(self.y(), area.bottom() - self.height() + 1)))

    def closeEvent(self, event):
        self.closing.emit()
        if self.tray_available and not self.exiting:
            event.ignore()
            self.hide()
        else:
            event.accept()

    @Slot(dict)
    def display(self, data):
        for key, metric in self.metrics.items():
            if self.settings and not self.settings['modules'][key]:
                continue
            value = data.get(key)
            if key == 'battery':
                metric.setVisible(value is not None)
                if value is not None:
                    metric.update_metric(value['percent'], 'Plugged in' if value['plugged'] else 'On battery')
                continue
            if value is None:
                metric.update_metric(None, 'Unavailable')
            elif key == 'cpu':
                frequency = f'{value["mhz"] / 1000:.2f} GHz' if value['mhz'] else 'Frequency N/A'
                metric.update_metric(value['percent'], f'{value["count"] or "N/A"} logical processors · {frequency}')
            elif key == 'gpu':
                if value.get('memory_kind') == 'shared':
                    shared = size(value['used']) if value['used'] is not None else 'N/A'
                    dedicated = size(value['dedicated']) if value.get('dedicated') is not None else 'N/A'
                    memory = f'Shared: {shared} · Dedicated: {dedicated}'
                else:
                    memory = f'{size(value["used"])} / {size(value["total"])} VRAM' if value['total'] is not None else 'VRAM N/A'
                metric.detail.setWordWrap(True)
                metric.update_metric(value['percent'], f'{value["name"]}\n{memory}')
            else:
                detail = f'{size(value["used"])} / {size(value["total"])}'
                if key == 'disk':
                    detail = f'{value["path"]}  ·  {detail}'
                metric.update_metric(value['percent'], detail)
        network = data.get('network') or dict(download=None, upload=None)
        self.network.setText(f'↓ {rate(network["download"])}    ↑ {rate(network["upload"])}')
        failed = [key.upper() for key, value in data.items() if value is None and key != 'battery']
        interval = self.settings['interval'] if self.settings else 1
        self.status.setText('Unavailable: ' + ', '.join(failed) if failed else f'LIVE  ·  {interval} second refresh')
        previous_size = self.size()
        self.adjustSize()
        if self.size() != previous_size:
            self.ensure_on_screen()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            handle = self.windowHandle()
            if handle and handle.startSystemMove():
                return
            self.drag_offset = event.globalPosition().toPoint() - self.pos()
            event.accept()

    def mouseMoveEvent(self, event):
        if self.drag_offset is not None and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_offset)
            event.accept()

    def mouseReleaseEvent(self, event):
        self.drag_offset = None
        super().mouseReleaseEvent(event)
