import signal
import sys

from PyQt5.QtWidgets import QApplication

from gui.ctrl_panel_logic import MainWindow
from utils.logger import log


def grace_exit(signum, frame):
    log('[EXIT] User exit')
    sys.exit()


if __name__ == '__main__':
    signal.signal(signal.SIGINT, grace_exit)
    signal.signal(signal.SIGTERM, grace_exit)

    app = QApplication(sys.argv)

    mainWindow = MainWindow()
    mainWindow.show()

    sys.exit(app.exec_())
