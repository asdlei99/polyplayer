import types
import cgitb
import signal
import sys
import os
import time
import traceback
from concurrent import futures

from PyQt5.QtGui import QCursor

cgitb.enable()  # Enable hidden errors and warnings, especially important for windows PYQT
import setproctitle

setproctitle.setproctitle('polyplayer')

if 'nt' in os.name:
    import ctypes

    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("polyplayer")

from PyQt5.QtWidgets import QMainWindow, QApplication, QFileDialog, QStyle, QStyleFactory, QLineEdit, QListView, \
    QWidget, QTableWidgetItem, QCheckBox
from PyQt5.QtCore import QThread, Qt
from PyQt5 import QtGui, QtCore

from gui.ctrl_panel import Ui_MainWindow
from api.pymusicdl_parser import MusicDL
from log import log

header_list = [
    'added',
    'downloaded',
    'title',
    'artist',
    'album',
    'duration',
    'filesize',
    'source',
]


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

        # set playlist unit width

        # setup pools for logics
        self.search_thread = SearchThread(self)
        self.search_thread.start()

        # global search thread
        self.global_search_thread = TextEditThread(self.global_search, self.search_thread.run)
        self.global_search_thread.start()

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

        self.text_edit_delay = DelayedExecutionTimer(max_delay=2000, min_delay=500)

    def run(self):
        self.text_edit_widget.textChanged.connect(self.text_edit_delay.trigger)
        self.text_edit_delay.triggered.connect(self.target_func)

        # setup key press trigger too
        self.text_edit_widget.returnPressed.connect(self.target_func)


class SearchThread(QThread):
    def __init__(self, main_window):
        super(QThread, self).__init__()
        self.main_window = main_window
        self.pool = futures.ThreadPoolExecutor(16)

        # ready music download engine
        self.mdl = MusicDL()

    def run(self):
        self.pool.submit(self.proc)

    def proc(self):
        keyword = self.main_window.global_search.text()
        sources = self.main_window.dl_source.currentText()

        if not keyword:
            return

        log.info('searching {} from {}'.format(keyword, sources))

        try:
            song_list = self.mdl.search(keyword, sources)
        except Exception as e:
            tb = traceback.format_exc()
            log.error(e)
            log.error(tb)
            return

        self.main_window.playlist.setRowCount(len(song_list))

        # fill cells
        for i, song in enumerate(song_list):
            data = {'title': song.title,
                    'artist': song.singer,
                    'album': song.album,
                    'duration': song.duration,
                    'filesize': str(song.size) + 'MB',
                    'source': song.source}

            for header in data:
                self.main_window.playlist.setItem(i, header_list.index(header),
                                                  QTableWidgetItem(str(data[header])))


class DelayedExecutionTimer(QtCore.QObject):
    triggered = QtCore.pyqtSignal(str)

    def __init__(self, max_delay=2000, min_delay=500, parent=None):
        super(DelayedExecutionTimer, self).__init__(parent)
        # The min delay is the time the class will wait after being triggered before emitting the triggered() signal
        # (if there is no key press for this time: trigger)
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.minTimer = QtCore.QTimer(self)
        self.maxTimer = QtCore.QTimer(self)
        self.minTimer.timeout.connect(self.timeout)
        self.maxTimer.timeout.connect(self.timeout)

    def timeout(self):
        self.minTimer.stop()
        self.maxTimer.stop()
        self.triggered.emit(self.string)

    def trigger(self, string):
        self.string = string
        if not self.maxTimer.isActive():
            self.maxTimer.start(self.max_delay)
        self.minTimer.stop()
        self.minTimer.start(self.min_delay)
