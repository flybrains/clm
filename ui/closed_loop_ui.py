import os
import sys
import threading

from PyQt5 import QtCore, QtGui, QtWidgets, uic
from PyQt5.QtWidgets import QLabel, QMainWindow, QTextEdit, QAction, QFileDialog, QApplication, QMessageBox

import server.server as server


cwd = os.getcwd()
qtCreatorFile = cwd+"/ui/closedloop.ui"
Ui_MainWindow, QtBaseClass = uic.loadUiType(qtCreatorFile)

class ErrorMsg(QMessageBox):
	def __init__(self, msg, parent=None):
		super(ErrorMsg, self).__init__(parent)
		self.setIcon(QMessageBox.Critical)
		self.setText(msg)
		self.setWindowTitle('Error')

class WarningMsg(QMessageBox):
	def __init__(self, msg, parent=None):
		super(WarningMsg, self).__init__(parent)
		self.setText(msg)
		self.setWindowTitle('Warning')

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
		self.sourceID = None

	def set_callbacks(self):
		self.runServerPB.clicked.connect(self.run_server)
		self.stopServerPB.clicked.connect(self.stop_server)

	def pre_run_config_check(self):
		n_clients = 3
		if self.ReplayRadioButton.isChecked():
			self.sourceID = 'REPLAYER'
		elif self.FTRadioButton.isChecked():
			self.sourceID = 'FICTRAC'

		self.server_instance.set_n_clients(n_clients)
		self.server_instance.set_source(self.sourceID)


	def run_server(self):
		self.pre_run_config_check()
		if self.sourceID is None:
			msg = 'Select a data-generating source'
			self.error = ErrorMsg(msg)
			self.error.show()
		else:
			thread = threading.Thread(target=self.server_instance.run)
			thread.start()


	def stop_server(self):
		self.kill_server.emit()
