from PySide6.QtCore import QObject, QThread, QTimer, Signal, Slot

from system_monitor.monitoring.collector import Collector


class Worker(QObject):
    sampled = Signal(dict)

    def __init__(self, settings):
        super().__init__()
        self.settings = settings

    @Slot()
    def start(self):
        self.collector = Collector()
        self.collector.configure(self.settings['modules'], self.settings.get('disk_path'))
        self.timer = QTimer(self)
        self.timer.setInterval(self.settings['interval'] * 1000)
        self.timer.timeout.connect(self.sample)
        self.sample()
        self.timer.start()

    @Slot()
    def sample(self):
        self.sampled.emit(self.collector.sample())

    @Slot(dict)
    def configure(self, settings):
        self.settings = settings
        if hasattr(self, 'timer'):
            self.timer.setInterval(settings['interval'] * 1000)
            self.collector.configure(settings['modules'], settings.get('disk_path'))

    @Slot()
    def stop(self):
        if hasattr(self, 'timer'):
            self.timer.stop()
            self.collector.close()
        QThread.currentThread().quit()


class Monitor(QObject):
    sampled = Signal(dict)
    configure_requested = Signal(dict)
    stop_requested = Signal()

    def __init__(self, parent=None, settings=None):
        super().__init__(parent)
        self.thread = QThread(self)
        if settings is None:
            from system_monitor.config.store import defaults
            settings = defaults()
        self.worker = Worker(settings)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.start)
        self.worker.sampled.connect(self.sampled)
        self.thread.finished.connect(self.worker.deleteLater)
        self.configure_requested.connect(self.worker.configure)
        self.stop_requested.connect(self.worker.stop)

    def start(self):
        self.thread.start()

    def stop(self):
        if self.thread.isRunning():
            self.stop_requested.emit()
            self.thread.wait()
