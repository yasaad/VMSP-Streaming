from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtGui import QMovie, QIcon


class LoadingButton(QPushButton):
    @pyqtSlot()
    def start(self):
        if hasattr(self, "_movie"):
            self._movie.start()

    @pyqtSlot()
    def stop(self):
        if hasattr(self, "_movie"):
            self._movie.stop()
            self.setIcon(QIcon())

    def setGif(self, filename):
        if not hasattr(self, "_movie"):
            self._movie = QMovie(self)
            self._movie.setFileName(filename)
            self._movie.frameChanged.connect(self.on_frameChanged)
            if self._movie.loopCount() != -1:
                self._movie.finished.connect(self.start)
        self.stop()

    @pyqtSlot(int)
    def on_frameChanged(self, frameNumber):
        self.setIcon(QIcon(self._movie.currentPixmap()))
