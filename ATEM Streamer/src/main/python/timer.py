from PyQt5.QtWidgets import (QWidget,
                             QPushButton,
                             QLabel,
                             QHBoxLayout,
                             QSizePolicy,
                             QLineEdit)
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QIntValidator

class TimeSpinner(QWidget):
    def __init__(self, title, min, max, connected_function=None, step=1, value=0, *args, **kwargs):
        super(TimeSpinner, self).__init__(*args, **kwargs)
        self.min = min
        self.max = max
        self.step = step
        
        minusButton = QPushButton("-")
        minusButton.setFixedWidth(75)
        minusButton.clicked.connect(self.__decrement)
        
        self.lineEdit = QLineEdit(str(value))
        self.lineEdit.setValidator(QIntValidator(min, max))
        self.lineEdit.setPlaceholderText("0")
        self.lineEdit.setFixedWidth(40)
        self.lineEdit.setAlignment(Qt.AlignHCenter)
        
        self.title = QLabel(title + ": ")
        self.title.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)
        self.title.adjustSize()
        if connected_function:
            self.lineEdit.textChanged.connect(connected_function)
            
        plusButton = QPushButton("+")
        plusButton.setFixedWidth(75)
        plusButton.clicked.connect(self.__increment)
        
        layout = QHBoxLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(0,0,0,0)
        layout.addWidget(self.title)
        layout.addWidget(minusButton)
        layout.addWidget(self.lineEdit)
        layout.addWidget(plusButton)
        layout.addStretch(1)
        self.setLayout(layout)
        
    def __increment(self):
        value = self.getValue() + self.step
        if value > self.max:
            value = self.max
        self.lineEdit.setText(str(value))
        
    def __decrement(self):
        value = self.getValue() - self.step
        if value < self.min:
            value = self.min
        self.lineEdit.setText(str(value))
    
    def getValue(self):
        text = self.lineEdit.text()
        if text:
            return int(text)
        else:
            return 0
        
    def clear(self):
        self.lineEdit.setText("0")
    

NO_TIMER = "No Timer Set"
START_TIMER  = "Start Timer"

class Timer(QWidget):
    def __init__(self, stop_stream_callback, showTimerButton, *args, **kwargs):
        super(Timer, self).__init__(*args, **kwargs)
        # self.setFixedHeight(50)
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Maximum)
        self.stop_stream = stop_stream_callback
        self.timer = QTimer()
        self.timer.timeout.connect(self.__timer_interval)
        self.remaining_time = 0
        self.running = False
        self.timer_button = QPushButton(START_TIMER)
        self.timer_button.clicked.connect(lambda: self.stop() if self.running else self.start())
        self.timer_button.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Maximum)
        if not showTimerButton:
            self.timer_button.hide()
        
        self.timer_label = QLabel(NO_TIMER)
        self.timer_label.setAlignment(Qt.AlignCenter)
        self.timer_label.setFixedWidth(150)
        self.timer_label.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.timer_label.adjustSize()
        
        self.hourSelector = TimeSpinner("Hours", 0, 23, connected_function=self.__timer_hours_minutes_changed)
        self.minuteSelector = TimeSpinner("Minutes", 0, 59, connected_function=self.__timer_hours_minutes_changed)
            
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.hourSelector)
        layout.addStretch(1)
        layout.addWidget(self.minuteSelector)
        layout.addStretch(2)
        layout.addWidget(self.timer_label)
        layout.addStretch(2)
        layout.addWidget(self.timer_button)
        layout.addStretch(1)
        
        self.setLayout(layout)
    
    def getTime(self):
        return self.remaining_time
        
    
    def setTime(self, time):
        self.remaining_time = time
        self._update_timer()

    def start(self):
        if self.remaining_time > 0:
            self.timer_button.show()
            self.running = True
            self.timer.start(1000)
            self.hourSelector.hide()
            self.minuteSelector.hide()
            self.timer_button.setText('Cancel Timer')
        
    def stop(self):
        if self.timer.isActive():
            self.running = False
            self.timer.stop()
        self.timer_button.setText(START_TIMER)
        self.__timer_hours_minutes_changed()
        self.hourSelector.show()
        self.minuteSelector.show()
    
    def __timer_hours_minutes_changed(self):
        self.remaining_time = self.hourSelector.getValue() * 3600 + self.minuteSelector.getValue() * 60
        self.__update_timer()
   
    def __timer_interval(self):
        if self.remaining_time == 0:
            self.stop()
            self.timer_button.hide()
            self.stop_stream()
            return
        
        self.remaining_time -= 1
        self.__update_timer()
    
    def __update_timer(self):
        if self.remaining_time == 0:
            self.timer_label.setText(NO_TIMER)
            return
        hours = self.remaining_time // 3600
        remaining = self.remaining_time % 3600
        minutes = remaining // 60
        seconds = remaining % 60
        self.timer_label.setText("Timer: " + str(int(hours)) + ":" + str(int(minutes)).zfill(2) + ":" + str(int(seconds)).zfill(2))
        self.timer_label.adjustSize()