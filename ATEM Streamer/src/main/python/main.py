import sys, traceback
import time
import calendar
from argparse import ArgumentParser
from datetime import datetime, date
from fbs_runtime.application_context.PyQt5 import ApplicationContext
from PyQt5.QtWidgets import QWidget, QPushButton, QLabel, QVBoxLayout, QHBoxLayout, QComboBox, QLineEdit
from PyQt5.QtGui import QIcon, QPixmap, QMovie, QPainter
from PyQt5.QtCore import QObject, pyqtSignal, QRunnable, QThreadPool, pyqtSlot
from streamAutomation import StreamAutomation


class Thumbnail(QWidget):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent=parent)
        self.p = QPixmap()

    def setPixmap(self, p):
        self.p = p
        self.update()

    def paintEvent(self, event):
        if not self.p.isNull():
            painter = QPainter(self)
            painter.setRenderHint(QPainter.SmoothPixmapTransform)
            painter.drawPixmap(self.rect(), self.p)

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

class WorkerSignals(QObject):
    finished = pyqtSignal()
    error = pyqtSignal(tuple)
    result = pyqtSignal(str)
    progress = pyqtSignal(str)

class Worker(QRunnable):
    '''
    Worker Thread
    '''
    def __init__(self, fn, *args, **kwargs):
        super(Worker, self).__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

        self.kwargs['progress_callback'] = self.signals.progress

    @pyqtSlot()
    def run(self):
        try:
            result = self.fn(*self.args, **self.kwargs)
        except:
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit((exctype, value, traceback.format_exc()))
        else:
            self.signals.result.emit(result)
        finally:
            self.signals.finished.emit()
        
def start_stream_process(streamAutomation, title_text, visibility, thumbnail_path, progress_callback):
    progress_callback.emit("Turning on PowerSwitch")
    streamAutomation.turnOnPowerSwitch()
    progress_callback.emit("Creating Broadcast")
    broadcast_id = streamAutomation.createBroadcast(title_text, visibility == "Public")
    streamAutomation.setThumbnail(broadcast_id, thumbnail_path)
    streamAutomation.bindBroadcast(broadcast_id)
    progress_callback.emit("Starting ATEM Stream")
    streamAutomation.startATEMStream()
    return broadcast_id

def stop_stream_process(streamAutomation, broadcast_id, progress_callback):
    progress_callback.emit("Ending Broadcast")
    streamAutomation.endBroadcast(broadcast_id)
    progress_callback.emit("Stoping ATEM Stream")
    streamAutomation.stopATEMStream()
    progress_callback.emit("Turing off PowerSwitch")
    streamAutomation.turnOffPowerSwitch()


class Window(QWidget):
    def __init__(self, ctx):
        super().__init__()
        #TODO: Parse arguments from automation parameters
        self.parser = ArgumentParser()
        self.parser.add_argument('--title', help='Title and Thumbnail')
        self.parser.add_argument('--duration', help='Time in hours')
        self.args = self.parser.parse_args()
        self.ctx = ctx
        self.threadpool = QThreadPool()
        self.streamAutomation = StreamAutomation(self.ctx.get_resource("keys"))
        self.thumbnail_path = None
        self.broadcast_id = None
        self.styleSheetBlack = (
            'background-color:black'
        )
        self.styleSheetWhite = ('background-color:white')
        #maps title to image
        self.titlesDict = {
            'Divine Liturgy':'Divine_Liturgy.jpg',
            'Vespers & Midnight Praises': "Midnight_Praises.jpg",
            'Bible Study': "Bible_Study.jpg",
            'Palm Sunday': "Palm_Sunday.jpg",
            'Holy Week': "Holy_Week.jpg",
            'Coptic New Year': "Coptic_New_Year.jpg",
            'Feast of Nativity': "Feast_of_Nativity.jpg",
            'Feast of Resurrection': "Feast_of_Resurrection.jpg",
            'Feast of the Cross': "Feast_of_the_Cross.jpg",
            'Feast of Theophany': "Feast_of_Theophany.jpg",
            'Virgin Mary Revival (Nahda)' : "Saint_Mary.jpg"
        }
        self.streaming = False
        self.resize(1100,800)
        self.setMinimumSize(550,400)
        self.create_widgets()
        self.create_layout()
        self.setLayout(self.mainVbox)
 
    def create_layout(self):
        self.mainVbox = QVBoxLayout()
        header = QHBoxLayout()
        header.addWidget(self.titleSelector)
        titleLayout = QHBoxLayout()
        titleLayout.addWidget(QLabel("Video Title:"))
        titleLayout.addWidget(self.title)
        footer = QHBoxLayout()
        footer.addWidget(self.visibilitySelector)
        footer.addWidget(self.startStreamBtn)
        self.mainVbox.addLayout(header)
        self.mainVbox.addWidget(self.thumbnail)
        self.mainVbox.addLayout(titleLayout)
        self.mainVbox.addLayout(footer)

    def create_widgets(self):
        self.titleSelector = QComboBox()
        self.titleSelector.addItems([*self.titlesDict])
        self.titleSelector.setCurrentIndex(1)
        if self.args.title in self.titlesDict:
            index = self.titleSelector.findText(self.args.title)
            self.titleSelector.setCurrentIndex(index)
        self.titleSelector.currentIndexChanged.connect(self.title_selector_changed)
        self.title = QLineEdit(self.create_title(self.titleSelector.currentText()))
        self.visibilitySelector = QComboBox()
        self.visibilitySelector.addItems(["Public", "Unlisted"])
        self.startStreamBtn = LoadingButton("Start Stream")
        self.startStreamBtn.setGif(self.ctx.get_resource('images/loading.gif'))
        self.startStreamBtn.setStyleSheet(self.styleSheetWhite)
        self.startStreamBtn.clicked.connect(lambda: self.stop_stream() if self.streaming else self.start_stream())
        self.thumbnail = Thumbnail(self)
        self.thumbnail_path = self.set_thumbnail(self.titlesDict[self.titleSelector.currentText()])

    def create_title(self, selection):
        title = selection
        if selection == "Holy Week":
            if int(datetime.now().strftime("%H")) < 12:
                # Day of current day
                day = calendar.day_name[date.today().weekday()]
                title = f"Day of {day} Pascha"
            else:
                # Eve of next day
                day = calendar.day_name[date.today().weekday() + 1]
                title = f"Eve of {day} Pascha"
            # TODO: Add custom names for Thrusday Friday Saturday and Resrrection
        return f'{title} - {date.strftime(date.today(), "%m/%d/%Y")}'

    def set_thumbnail(self, image_name):
        resource = self.ctx.get_resource(f'images/{image_name}')
        self.thumbnail.setPixmap(QPixmap(resource))
        return resource 
    
    def title_selector_changed(self):
        self.thumbnail_path = self.set_thumbnail(self.titlesDict[self.titleSelector.currentText()])
        self.title.setText(self.create_title(self.titleSelector.currentText()))

    def stream_process_progress(self, n):
        self.startStreamBtn.setText(n)
    
    def save_result(self, s):
        self.broadcast_id = s

    def thread_complete(self):
        self.startStreamBtn.stop()
        self.startStreamBtn.setText("Stop Stream" if self.streaming else "Start Stream")
        self.startStreamBtn.setDisabled(False)
    
    def start_stream(self):
        self.streaming = True
        self.startStreamBtn.setDisabled(True)
        self.startStreamBtn.start()
        worker = Worker(start_stream_process, self.streamAutomation, self.title.text(), self.visibilitySelector.currentText(), self.thumbnail_path)
        worker.signals.result.connect(self.save_result)
        worker.signals.finished.connect(self.thread_complete)
        worker.signals.progress.connect(self.stream_process_progress)
        self.threadpool.start(worker)

    def stop_stream(self):
        self.streaming = False
        self.startStreamBtn.setDisabled(True)
        self.startStreamBtn.start()
        worker = Worker(stop_stream_process, self.streamAutomation, self.broadcast_id)
        worker.signals.finished.connect(self.thread_complete)
        worker.signals.progress.connect(self.stream_process_progress)
        self.threadpool.start(worker)
        


if __name__ == '__main__':
    appctxt = ApplicationContext()       # 1. Instantiate ApplicationContext
    window = Window(appctxt)
    window.show()
    exit_code = appctxt.app.exec_()      # 2. Invoke appctxt.app.exec_()
    sys.exit(exit_code)