import os
import sys
import threading

from PyQt5 import QtCore, QtGui, QtWidgets, uic
from PyQt5.QtWidgets import QLabel, QMainWindow, QTextEdit, QAction, QFileDialog, QApplication, QMessageBox

import server.server as server


cwd = os.getcwd()
qtCreatorFile = cwd+"/ui/closedloop.ui"
Ui_MainWindow, QtBaseClass = uic.loadUiType(qtCreatorFile)

class ClosedLoopUI(QMainWindow, Ui_MainWindow):
    kill_server = QtCore.pyqtSignal()
    def __init__(self, server_instance):
        # General Initialization
        QtWidgets.QMainWindow.__init__(self)
        Ui_MainWindow.__init__(self)
        self.setupUi(self)
        self.title = 'Closed Loop Controller'
        self.setWindowTitle(self.title)
        self.setFixedSize(self.size())
        self.server_instance = server_instance

    def set_callbacks(self):
        self.runServerPB.clicked.connect(self.run_server)
        self.stopServerPB.clicked.connect(self.stop_server)

    def run_server(self):
        thread = threading.Thread(target=self.server_instance.run)
        thread.start()

    def stop_server(self):
        self.kill_server.emit()
