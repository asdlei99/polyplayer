import types
import cgitb
import signal
import sys
import os
import time
import traceback
from collections import OrderedDict
from concurrent import futures
from multiprocessing import Pool

from PyQt5.QtGui import QCursor

cgitb.enable()  # Enable hidden errors and warnings, especially important for windows PYQT
import setproctitle

setproctitle.setproctitle('polyplayer')

if 'nt' in os.name:
    import ctypes

    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("polyplayer")

from PyQt5.QtWidgets import QMainWindow, QApplication, QFileDialog, QStyle, QStyleFactory, QLineEdit, QListView, \
    QWidget, QTableWidgetItem, QCheckBox, QComboBox
from PyQt5.QtCore import QThread, Qt, pyqtSignal
from PyQt5 import QtGui, QtCore

from gui.ctrl_panel import Ui_MainWindow
from api.pymusicdl_parser import MusicDL
from api.audio_player import AudioPlayer
from utils.logger import log

header_dict = {
    'added': 36,
    'downloaded': 36,
    'title': 360,
    'artist': 120,
    'album': 120,
    'duration': 80,
    'filesize': 80,
    'source': 80,
}


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

        # ready music download engine
        self.mdl = MusicDL()
        self.song_list = []

        # set table width
        for i, header in enumerate(header_dict):
            self.playlist.setColumnWidth(i, header_dict[header])

        # set table click event
        self.playlist.viewport().installEventFilter(self)

        # setup pools for logics
        self.search_thread = SearchThread(self)
        self.search_thread.trigger.connect(self._set_table_button)
        self.search_thread.start()

        # global search thread
        self.global_search_thread = TextEditThread(self.global_search,
                                                   self.search_thread.run)
        self.global_search_thread.start()

        # download button thread
        self.download_thread = DownloadThread(self)
        self.download_thread.start()
        self.download_button_thread = ButtonThread(self.pushButton_download,
                                                   self.download_thread.run)
        self.download_button_thread.start()

        # set audio player
        self.current_music_file_path = None
        self.last_music_file_path = None
        self.audio_player = None
        self.is_playing = False
        self.pushButton_play.clicked.connect(self.play)

    def play(self, start_at=0):
        if self.current_music_file_path != self.last_music_file_path:
            if isinstance(self.audio_player, AudioPlayer):
                self.audio_player.stop()
                self.audio_player = None
            else:
                self.audio_player = None
        else:
            self.audio_player.pause()
            return

        if self.audio_player is None:
            self.audio_player = AudioPlayer(self.current_music_file_path)
            self.last_music_file_path = self.current_music_file_path

        self.audio_player.play(start_at)

    def eventFilter(self, source, event):
        if (event.type() == QtCore.QEvent.MouseButtonDblClick and
                event.buttons() == QtCore.Qt.LeftButton and
                source is self.playlist.viewport()):
            item = self.playlist.itemAt(event.pos())
            if item is not None:
                print('dblclick:', item.row(), item.column())
        return super(MainWindow, self).eventFilter(source, event)

    def _set_table_button(self, len_song_list):
        add_idx = list(header_dict.keys()).index('added')
        download_idx = list(header_dict.keys()).index('downloaded')
        for i in range(len_song_list):
            checkbox_add = QCheckBox()
            self.playlist.setCellWidget(i, add_idx, checkbox_add)

            checkbox_download = QCheckBox()
            self.playlist.setCellWidget(i, download_idx, checkbox_download)

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


class BaseQThread(QThread):
    def __init__(self, widget, target_func):
        super(QThread, self).__init__()
        self.widget = widget
        self.target_func = target_func

    def run(self):
        pass


class ButtonThread(BaseQThread):
    def __init__(self, widget, target_func):
        super().__init__(widget, target_func)

    def run(self):
        self.widget.clicked.connect(self.target_func)


class TextEditThread(BaseQThread):
    def __init__(self, widget, target_func):
        super().__init__(widget, target_func)
        self.text_edit_delay = DelayedExecutionTimer(max_delay=2000, min_delay=500)

    def run(self):
        self.widget.textChanged.connect(self.text_edit_delay.trigger)
        self.text_edit_delay.triggered.connect(self.target_func)

        # setup key press trigger too
        self.widget.returnPressed.connect(self.target_func)


class SearchThread(QThread):
    trigger = pyqtSignal(int)

    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.pool = futures.ThreadPoolExecutor(1)

    def run(self):
        self.pool.submit(self.proc)
        # self.proc()

    def proc(self):
        keyword = self.main_window.global_search.text()
        sources = self.main_window.dl_source.currentText()

        if not keyword:
            return

        try:
            self.main_window.song_list = self.main_window.mdl.search(keyword, sources)
        except Exception as e:
            tb = traceback.format_exc()
            log.error(e)
            log.error(tb)
            return

        self.main_window.playlist.setRowCount(len(self.main_window.song_list))

        # fill cells
        for i, song in enumerate(self.main_window.song_list):
            # TODO: add widget on table

            # data display
            data = {
                'title': song.title,
                'artist': song.singer,
                'album': song.album,
                'duration': song.duration,
                'filesize': str(song.size) + 'MB',
                'source': song.source
            }

            for header in data:
                self.main_window.playlist.setItem(i, list(header_dict.keys()).index(header),
                                                  QTableWidgetItem(str(data[header])))

        self.trigger.emit(len(self.main_window.song_list))


class DownloadThread(QThread):
    def __init__(self, main_window):
        super(QThread, self).__init__()
        self.main_window = main_window
        self.pool = futures.ThreadPoolExecutor(os.cpu_count())

    def run(self):
        current_row = self.main_window.playlist.currentRow()
        if current_row < 0:
            return

        if current_row < len(self.main_window.song_list):
            self.pool.submit(self.main_window.mdl.download,
                             self.main_window.song_list[current_row])


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
