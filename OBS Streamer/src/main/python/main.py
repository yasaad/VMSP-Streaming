import sys
from datetime import date
from fbs_runtime.application_context.PyQt5 import ApplicationContext
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QLabel, QVBoxLayout, QHBoxLayout, QComboBox
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtCore import QObject, QThread, pyqtSignal
from streamAutomation import StreamAutomation

class Window(QWidget):
    def __init__(self, ctx):
        super().__init__()
        self.ctx = ctx
        self.streamAutomation = StreamAutomation()
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
        }
        self.streaming = False
        self.setGeometry(500, 300, 400, 300)
        self.setFixedSize(500,400)
        # self.setStyleSheet(self.styleSheetBlack)
        self.create_widgets()
        self.create_layout()
        self.setLayout(self.mainVbox)
 
    def create_layout(self):
        self.mainVbox = QVBoxLayout()
        self.header = QHBoxLayout()
        self.header.addWidget(self.titleSelector)
        self.footer = QHBoxLayout()
        self.footer.addWidget(self.visibilitySelector)
        self.footer.addWidget(self.startStreamBtn)
        self.mainVbox.addLayout(self.header)
        self.mainVbox.addWidget(self.thumbnail)
        self.mainVbox.addLayout(self.footer)

    def create_widgets(self):
        self.titleSelector = QComboBox()
        self.titleSelector.addItems([*self.titlesDict])
        self.titleSelector.currentIndexChanged.connect(self.new_title)
        self.visibilitySelector = QComboBox()
        self.visibilitySelector.addItems(["Public", "Unlisted"])
        self.startStreamBtn = QPushButton("Start Stream", self)
        self.startStreamBtn.setStyleSheet(self.styleSheetWhite)
        self.startStreamBtn.clicked.connect(lambda: self.stop_stream() if self.streaming else self.start_stream())
        self.thumbnail = QLabel(self)
        self.thumbnail_path = self.set_thumbnail(self.titlesDict[self.titleSelector.currentText()])
    def set_thumbnail(self, image_name):
        resource = self.ctx.get_resource(f'images/{image_name}')
        self.thumbnail.setPixmap(QPixmap(resource).scaledToWidth(self.width()))
        return resource
    def new_title(self):
        self.thumbnail_path = self.set_thumbnail(self.titlesDict[self.titleSelector.currentText()])
 
    
    def start_stream(self):
        self.streaming = True
        self.startStreamBtn.setDisabled(True)
        self.streamAutomation.turnOnPowerSwitch()
        service_date = date.strftime(date.today(),"%m/%d/%Y")
        video_title = f"{self.titleSelector.currentText()} - {service_date}"
        self.broadcast_id = self.streamAutomation.createBroadcast(video_title, self.visibilitySelector.currentText() == "Public")
        self.streamAutomation.setThumbnail(self.broadcast_id, self.thumbnail_path)
        self.streamAutomation.bindBroadcast(self.broadcast_id)
        self.streamAutomation.startOBS()
        self.startStreamBtn.setText("Stop Stream")
        self.startStreamBtn.setDisabled(False)

    def stop_stream(self):
        self.streaming = False
        self.startStreamBtn.setDisabled(True)
        self.streamAutomation.endBroadcast(self.broadcast_id)
        self.streamAutomation.stopOBS()
        self.streamAutomation.turnOffPowerSwitch()
        self.startStreamBtn.setDisabled(False)
        self.startStreamBtn.setText("Start Stream")
if __name__ == '__main__':
    appctxt = ApplicationContext()       # 1. Instantiate ApplicationContext
    window = Window(appctxt)
    window.show()
    exit_code = appctxt.app.exec_()      # 2. Invoke appctxt.app.exec_()
    sys.exit(exit_code)