import sys, traceback
from os.path import basename
import time
import calendar
from argparse import ArgumentParser
from datetime import datetime, date
from fbs_runtime.application_context.PyQt5 import ApplicationContext
from timer import Timer
from PyQt5.QtWidgets import (QWidget,
                             QPushButton,
                             QLabel,
                             QVBoxLayout,
                             QHBoxLayout,
                             QComboBox,
                             QLineEdit,
                             QFileDialog,
                             QSizePolicy)
from PyQt5.QtGui import QIcon, QPixmap, QMovie, QFont, QPalette
from PyQt5.QtCore import QObject, pyqtSignal, QRunnable, QThreadPool, pyqtSlot, Qt
from streamAutomation import StreamAutomation

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
    broadcastStatus = streamAutomation.checkBroadcastStatus(broadcast_id)
    while "live" not in broadcastStatus:
        progress_callback.emit(f"Broadcast is: {broadcastStatus}")
        streamAutomation.stopATEMStream()
        time.sleep(1)
        streamAutomation.startATEMStream()
        time.sleep(5)
        broadcastStatus = streamAutomation.checkBroadcastStatus(broadcast_id)
    progress_callback.emit(f"Broadcast is: {broadcastStatus}")
    print("Stream is active")
    time.sleep(3)
    return broadcast_id

def stop_stream_process(streamAutomation, broadcast_id, progress_callback):
    print(f"This is the broadcast_id to end the stream: {broadcast_id}")
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
        self.parser.add_argument('-t', '--title', type=str, help='''Title and Thumbnail options:
                                                        Divine Liturgy
                                                        Vespers & Midnight Praises
                                                        Bible Study
                                                        Palm Sunday
                                                        Holy Week
                                                        Coptic New Year
                                                        Feast of Nativity
                                                        Feast of Resurrection
                                                        Feast of the Cross
                                                        Feast of Theophany
                                                        Virgin Mary Revival''')
        self.parser.add_argument('-i', '--image', type=str, help='''Thumbnail options:
                                                        Divine Liturgy
                                                        Vespers & Midnight Praises
                                                        Bible Study
                                                        Palm Sunday
                                                        Holy Week
                                                        Coptic New Year
                                                        Feast of Nativity
                                                        Feast of Resurrection
                                                        Feast of the Cross
                                                        Feast of Theophany
                                                        Virgin Mary Revival''')
        self.parser.add_argument('-d', '--duration', type=float, help='Time in hours')
        self.parser.add_argument('-u', '--unlisted', help='Use to make stream unlisted', action='store_true')
        self.parser.add_argument('-a', '--autostart', help='Use to autostart stream', action='store_true')
        self.args = self.parser.parse_args()
        self.ctx = ctx
        self.threadpool = QThreadPool()
        self.streamAutomation = StreamAutomation(self.ctx.get_resource("keys"))
        self.thumbnail_path = None
        self.broadcast_id = self.streamAutomation.checkForCurrentLiveStream()
        self.fornt = QFont("Arial", 16)
        self.setFont(QFont("Arial", 16))
        self.styleSheetRefresh = ('background-color:white; padding:8px')
        self.styleSheetWhite = ('font-family: Arial; font-size: 16pt; background-color:white; padding-top: 3px; padding-bottom: 3px; padding-left: auto; padding-right: auto;')
        self.styleSheetGreen = ('font-family: Arial; font-size: 16pt; background-color:green; padding-top: 3px; padding-bottom: 3px; padding-left: auto; padding-right: auto;')
        self.styleSheetRed = ('font-family: Arial; font-size: 16pt; background-color:red; padding-top: 3px; padding-bottom: 3px; padding-left: auto; padding-right: auto;')
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
        self.streaming = True if self.broadcast_id is not None else False
        print(self.broadcast_id)
        self.timer = Timer(self.stop_stream, self.streaming)
        height = 800
        width = 1100
        scale_factor = 0.65
        self.resize(width,height)
        self.setMinimumSize(width * scale_factor, height * scale_factor)
        self.create_widgets()
        self.create_layout()
        self.setLayout(self.mainVbox)

    def closeEvent(self, event):
        self.streamAutomation.closeATEMConnection()
        event.accept()
 
    def create_layout(self):
        self.mainVbox = QVBoxLayout()
        header = QHBoxLayout()
        header.addWidget(self.titleSelector)
        header.addWidget(self.openFile)
        titleLayout = QHBoxLayout()
        video_title = QLabel("Video Title:")
        
        titleLayout.addWidget(video_title)
        titleLayout.addWidget(self.title)
        
        footer = QHBoxLayout()
        footer.addWidget(self.visibilitySelector)
        footer.addWidget(self.startStreamBtn)
        footer.addWidget(self.refreshStatusBtn)
        
  
        self.mainVbox.addLayout(header)
        
        self.mainVbox.addWidget(self.thumbnail)
        # self.mainVbox.addStretch(1)
        self.mainVbox.addLayout(titleLayout)
        self.mainVbox.addWidget(self.timer)
        self.mainVbox.addLayout(footer)

    def create_widgets(self):
        self.titleSelector = QComboBox()
        self.titleSelector.addItems([*self.titlesDict])
        self.titleSelector.setCurrentIndex(0)
        self.titleSelector.currentIndexChanged.connect(self.title_selector_changed)
        
        self.openFile = QPushButton("Open Image")
        self.openFile.clicked.connect(self.openFileClicked)
        
        # Set Title Selector if argument given
        self.title = QLineEdit()
        if self.args.image in self.titlesDict:
            index = self.titleSelector.findText(self.args.title)
            self.titleSelector.setCurrentIndex(index)
        elif self.args.title in self.titlesDict:
            index = self.titleSelector.findText(self.args.title)
            self.titleSelector.setCurrentIndex(index)
            self.title.setText(self.create_title(self.titleSelector.currentText()))
        elif self.args.title:
            self.title.setText(self.args.title)
        else:
            self.title.setText(self.create_title(self.titleSelector.currentText()))
            
        
        # Set duration
        if self.args.duration and self.args.duration > 0:
            self.timer.setTime(self.args.duration * 3600)
            self.timer.start()
    
        self.visibilitySelector = QComboBox()
        self.visibilitySelector.addItems(["Public", "Unlisted"])
        self.visibilitySelector.setFixedWidth(150)
        if self.args.unlisted:
            self.visibilitySelector.setCurrentIndex(1) 
        self.startStreamBtn = LoadingButton("Stop Stream") if self.streaming else LoadingButton("Start Stream")
        self.startStreamBtn.setGif(self.ctx.get_resource('images/loading.gif'))
        self.startStreamBtn.setStyleSheet(self.styleSheetRed if self.streaming else self.styleSheetGreen)
        self.startStreamBtn.clicked.connect(lambda: self.stop_stream() if self.streaming else self.start_stream())
        self.refreshStatusBtn = LoadingButton()
        self.refreshStatusBtn.setIcon(QIcon(self.ctx.get_resource('images/refresh.png')))
        self.refreshStatusBtn.clicked.connect(self.refresh_status)
        self.refreshStatusBtn.setStyleSheet(self.styleSheetRefresh)
        self.refreshStatusBtn.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)
        # self.thumbnail = Thumbnail(self)
        self.thumbnail = QLabel()
        self.thumbnail.setBackgroundRole(QPalette.Base)
        self.thumbnail.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.thumbnail.setScaledContents(True)
        self.thumbnail_path = self.set_thumbnail(self.titlesDict[self.titleSelector.currentText()])

        # self.webview=QtWebEngineWidgets.QWebEngineView()
        # self.webview.settings().setAttribute(QtWebEngineWidgets.QWebEngineSettings.LocalContentCanAccessRemoteUrls, True)
        # self.webview.settings().setAttribute(QtWebEngineWidgets.QWebEngineSettings.AllowRunningInsecureContent, True)
        # self.webview.setUrl(QUrl("https://www.youtube.com/embed/c2VD8q5hYIE?autoplay=1&livemonitor=1"))
        # self.webview.setUrl(QUrl("https://youtu.be/c2VD8q5hYIE"))
        
        if self.args.autostart:
            self.start_stream()

    def openFileClicked(self):
        filename = QFileDialog.getOpenFileName(self, "Open File", "C:\\Users\\strea\\Pictures\\Thumbnails", "Image Files (*.png *jpg *jpeg)")
        print(filename)
        if filename[0]:
            self.thumbnail_path = filename[0]
            self.thumbnail.setPixmap(QPixmap(self.thumbnail_path))
            self.title.setText(self.create_title(basename(self.thumbnail_path.split('.')[0])))
        
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
        if self.streaming and self.timer.getTime() > 0:
            self.timer.start()
        else:
            self.broadcast_id = None
        self.startStreamBtn.stop()
        self.update_stream_button_status()
        self.startStreamBtn.setDisabled(False)
        
    def refresh_status(self):
        self.broadcast_id = self.streamAutomation.checkForCurrentLiveStream()
        if self.broadcast_id is not None:
            self.streaming = True
            self.update_stream_button_status()
            
    def update_stream_button_status(self):
        self.startStreamBtn.setText("Stop Stream" if self.streaming else "Start Stream")
        self.startStreamBtn.setStyleSheet(self.styleSheetRed if self.streaming else self.styleSheetGreen)
    
    def is_straming(self):
        return self.streaming
    
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
        self.timer.stop()
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