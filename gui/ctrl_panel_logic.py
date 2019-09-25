import cgitb
import signal
import sys

from PyQt5.QtGui import QCursor

cgitb.enable()  # Enable hidden errors and warnings, especially important for windows PYQT
import setproctitle

setproctitle.setproctitle('polyplayer')
from PyQt5.QtWidgets import QMainWindow, QApplication, QFileDialog, QStyle, QStyleFactory
from PyQt5.QtCore import QThread, Qt
from PyQt5 import QtGui, QtCore

from gui.ctrl_panel import Ui_MainWindow


class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.setupUi(self)

        # frameless
        self.setWindowFlags(Qt.FramelessWindowHint)
        # transparent
        # self.setAttribute(QtCore.Qt.WA_TranslucentBackground, True)

        # set window style
        QApplication.setStyle('Fusion')

        # set icon
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("ico.ico"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.setWindowIcon(icon)

        # global search thread
        self.global_search_thread = TextEditThread(self.global_search, self.search_online)
        self.global_search_thread.start()
        self.global_search_last_text = ''

    def search_online(self):
        print(self.global_search.text())

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.m_flag = True
            self.m_Position = event.globalPos() - self.pos()
            event.accept()
            self.setCursor(QCursor(Qt.OpenHandCursor))

    def mouseMoveEvent(self, QMouseEvent):
        if Qt.LeftButton and self.m_flag:
            self.move(QMouseEvent.globalPos() - self.m_Position)
            QMouseEvent.accept()

    def mouseReleaseEvent(self, QMouseEvent):
        self.m_flag = False
        self.setCursor(QCursor(Qt.ArrowCursor))


class TextEditThread(QThread):
    def __init__(self, text_edit_widget, target_func):
        super(QThread, self).__init__()
        self.text_edit_widget = text_edit_widget
        self.target_func = target_func

    def run(self):
        self.text_edit_widget.textChanged.connect(self.target_func)
