"""One process per user, with a local wake-up channel for subsequent launches."""
import hashlib
import logging

from PySide6.QtCore import QLockFile, QObject, Signal
from PySide6.QtNetwork import QLocalServer, QLocalSocket


class Instance(QObject):
    show_requested = Signal()

    def __init__(self, directory, parent=None):
        super().__init__(parent)
        self.lock = QLockFile(str(directory / 'instance.lock'))
        self.lock.setStaleLockTime(0)
        digest = hashlib.sha256(str(directory.resolve()).casefold().encode()).hexdigest()[:24]
        self.name = 'SystemMonitorWidget-' + digest
        self.server = QLocalServer(self)
        self.server.setSocketOptions(QLocalServer.SocketOption.UserAccessOption)
        self.server.newConnection.connect(self.receive)

    def acquire(self):
        if not self.lock.tryLock(0):
            socket = QLocalSocket()
            socket.connectToServer(self.name)
            socket.waitForConnected(500)
            socket.disconnectFromServer()
            return False
        QLocalServer.removeServer(self.name)
        if not self.server.listen(self.name):
            logging.warning('Instance notification unavailable: %s', self.server.errorString())
        return True

    def receive(self):
        while self.server.hasPendingConnections():
            socket = self.server.nextPendingConnection()
            socket.disconnectFromServer()
            socket.deleteLater()
            self.show_requested.emit()

    def close(self):
        self.server.close()
        self.lock.unlock()
