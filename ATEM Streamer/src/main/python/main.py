import sys, traceback
import time
import calendar
from argparse import ArgumentParser
from datetime import datetime, date
from fbs_runtime.application_context.PyQt5 import ApplicationContext
from PyQt5.QtWidgets import QWidget, QPushButton, QLabel, QVBoxLayout, QHBoxLayout, QComboBox, QLineEdit, QSizePolicy
from PyQt5.QtGui import QIcon, QPixmap, QMovie, QPainter, QFont
from PyQt5.QtCore import QObject, pyqtSignal, QRunnable, QThreadPool, pyqtSlot, QTimer, Qt
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
        self.parser.add_argument('-d', '--duration', type=float, help='Time in hours')
        self.parser.add_argument('-u', '--unlisted', help='Use to make stream unlisted', action='store_true')
        self.parser.add_argument('-a', '--autostart', help='Use to autostart stream', action='store_true')
        self.args = self.parser.parse_args()
        self.ctx = ctx
        self.threadpool = QThreadPool()
        self.streamAutomation = StreamAutomation(self.ctx.get_resource("keys"))
        self.thumbnail_path = None
        self.broadcast_id = None
        self.font= QFont("Arial", 16)
        self.styleSheetWhite = ('background-color:white; padding-top: 3px; padding-bottom: 3px; padding-left: auto; padding-right: auto;')
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

    def closeEvent(self, event):
        self.streamAutomation.closeATEMConnection()
        event.accept()
 
    def create_layout(self):
        self.mainVbox = QVBoxLayout()
        header = QHBoxLayout()
        header.addWidget(self.titleSelector)
        titleLayout = QHBoxLayout()
        video_title = QLabel("Video Title:")
        video_title.setFont(self.font)
        titleLayout.addWidget(video_title)
        titleLayout.addWidget(self.title)
        footer = QHBoxLayout()
        footer.addWidget(self.visibilitySelector)
        footer.addWidget(self.startStreamBtn)
        timerLayout = QHBoxLayout()
        timerLayout.addWidget(self.resetBtn)
        timerLayout.addWidget(self.timer_label)
        self.mainVbox.addLayout(header)
        self.mainVbox.addWidget(self.thumbnail)
        self.mainVbox.addLayout(titleLayout)
        self.mainVbox.addLayout(footer)
        self.mainVbox.addLayout(timerLayout)

    def create_widgets(self):
        self.titleSelector = QComboBox()
        self.titleSelector.setFont(self.font)
        self.titleSelector.addItems([*self.titlesDict])
        self.titleSelector.setCurrentIndex(0)
        # Set Title Selector if argument given
        if self.args.title in self.titlesDict:
            index = self.titleSelector.findText(self.args.title)
            self.titleSelector.setCurrentIndex(index)
            
            
        self.titleSelector.currentIndexChanged.connect(self.title_selector_changed)
        self.title = QLineEdit(self.create_title(self.titleSelector.currentText()))
        self.title.setFont(self.font)
        
        # Set duration
        self.remaining_time = -1
        self.timer_label = QLabel()
        if self.args.duration and self.args.duration > 0:
            self.remaining_time = self.args.duration * 3600
            self.update_timer()
        else:
            self.timer_label.setText("No timer set")
        self.timer_label.setFont(self.font)
        # self.timer_label.setAlignment(Qt.AlignCenter)
        self.timer_label.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)
        self.timer_label.adjustSize()
        self.visibilitySelector = QComboBox()
        self.visibilitySelector.addItems(["Public", "Unlisted"])
        self.visibilitySelector.setFont(self.font)
        if self.args.unlisted:
            self.visibilitySelector.setCurrentIndex(1)
        self.startStreamBtn = LoadingButton("Start Stream")
        self.startStreamBtn.setFont(self.font)
        self.startStreamBtn.setGif(self.ctx.get_resource('images/loading.gif'))
        self.startStreamBtn.setStyleSheet(self.styleSheetWhite)
        self.startStreamBtn.clicked.connect(lambda: self.stop_stream() if self.streaming else self.start_stream())
        self.resetBtn = QPushButton("Reset Timer")
        self.resetBtn.setFont(self.font)
        self.resetBtn.clicked.connect(self.reset_clicked)
        self.resetBtn.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)
        self.resetBtn.setStyleSheet(self.styleSheetWhite)
        self.thumbnail = Thumbnail(self)
        self.thumbnail_path = self.set_thumbnail(self.titlesDict[self.titleSelector.currentText()])
        self.timer = QTimer()
        self.timer.timeout.connect(self.timer_interval)
        
        if self.args.autostart:
            self.start_stream()
  

            

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
    
    def reset_clicked(self):
        if self.timer.isActive():
            self.timer.stop()
            self.timer_label.setText("Timer Canceled")
            self.resetBtn.setText("Reset Timer")
            return
        self.remaining_time = 2 * 3600
        self.update_timer()
        
        
    def timer_interval(self):
        if self.remaining_time == 0:
            self.timer.stop()
            self.stop_stream()
            self.timer_label.setText("AutoStop Timer: Stream Completed")
            return
        self.remaining_time -= 1
        self.update_timer()
        
    def update_timer(self):
        
        hours = self.remaining_time // 3600
        remaining = self.remaining_time % 3600
        minutes = remaining // 60
        seconds = remaining % 60
        self.timer_label.setText("Time Remaining: " + str(int(hours)) + ":" + str(int(minutes)).zfill(2) + ":" + str(int(seconds)).zfill(2))
        self.timer_label.adjustSize()
    
    def start_stream(self):
        self.streaming = True
        if self.remaining_time > 0:
            self.timer.start(1000)
            self.resetBtn.setText('Cancel Timer')
        self.startStreamBtn.setDisabled(True)
        self.startStreamBtn.start()
        worker = Worker(start_stream_process, self.streamAutomation, self.title.text(), self.visibilitySelector.currentText(), self.thumbnail_path)
        worker.signals.result.connect(self.save_result)
        worker.signals.finished.connect(self.thread_complete)
        worker.signals.progress.connect(self.stream_process_progress)
        self.threadpool.start(worker)

    def stop_stream(self):
        self.streaming = False
        if self.timer.isActive():
            self.timer.stop()
            self.resetBtn.setText('Reset Timer')
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