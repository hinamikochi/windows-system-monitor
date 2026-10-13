import logging
from logging.handlers import RotatingFileHandler
import sys

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication, QMessageBox

from system_monitor.config.store import Store, data_directory
from system_monitor.services import startup
from system_monitor.services.controller import Controller
from system_monitor.services.instance import Instance
from system_monitor.services.monitor import Monitor
from system_monitor.ui.widget import Widget


def main():
    app = QApplication(sys.argv)
    app.setApplicationName('System Monitor')
    directory = data_directory()
    try:
        directory.mkdir(parents=True, exist_ok=True)
        handler = RotatingFileHandler(directory / 'app.log', maxBytes=512000, backupCount=2, encoding='utf-8')
        logging.basicConfig(level=logging.INFO, handlers=[handler],
                            format='%(asctime)s %(levelname)s %(name)s: %(message)s')
    except OSError as error:
        QMessageBox.critical(None, 'System Monitor', f'Cannot create application data directory: {error}')
        return 1
    def report_exception(kind, value, traceback):
        logging.critical('Unhandled exception', exc_info=(kind, value, traceback))
    sys.excepthook = report_exception
    instance = Instance(directory, app)
    if not instance.acquire():
        return 0
    store = Store()
    settings = store.load()
    try:
        settings['startup'] = startup.enabled()
    except OSError:
        logging.exception('Unable to query startup registration')
        settings['startup'] = False
    widget = Widget()
    widget.apply_settings(settings)
    if settings['position'] is not None:
        widget.move(*settings['position'])
    widget.ensure_on_screen()
    monitor = Monitor(settings=settings)
    controller = Controller(app, widget, monitor, store, settings)
    def show_existing():
        widget.restore()
    instance.show_requested.connect(show_existing)
    monitor.sampled.connect(widget.display)
    widget.show()
    monitor.start()
    if '--smoke-test' in sys.argv:
        samples = []
        monitor.sampled.connect(samples.append)
        QTimer.singleShot(10000, controller.exit)
    try:
        result = app.exec()
        if '--smoke-test' in sys.argv and len(samples) < 2:
            logging.error('Package smoke test did not receive enough samples')
            return 2
        if '--smoke-test' in sys.argv:
            latest = samples[-1]
            if any(latest.get(key) is None for key in ('cpu', 'ram', 'disk', 'network')):
                logging.error('Package smoke test could not read a core metric')
                return 3
            logging.info('SMOKE PASS: %s samples; GPU=%s; battery=%s',
                         len(samples), latest.get('gpu'), latest.get('battery'))
        return result
    finally:
        controller.shutdown()
        instance.close()
