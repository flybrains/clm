import os
import cv2
import sys
import pickle
import threading


from PyQt5 import QtCore, QtGui, QtWidgets, uic
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import QLabel, QMainWindow, QTextEdit, QAction, QFileDialog, QApplication, QMessageBox

import ui.utils as utils
import server.server as server
from server.clients.lightClient import LightClient
from server.clients.motorClient import MotorClient
from server.clients.mfcClient import MFCClient

from odorscape.OdorscapeMainWindow import Odorscape
from odorscape.odorscape import Canvas

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
		self.sourceID = None
		self.stopServerPB.setEnabled(False)
		utils.populate_taskbar(self)

	@QtCore.pyqtSlot(str)
	def recieve_from_odorscape(self, experiment_pickle_name):
		pickle_in = open(experiment_pickle_name, "rb")
		self.experiment_data = pickle.load(pickle_in)
		self.lightDictionary = self.experiment_data.lightDictionary
		self.canvasImg = Canvas(self.experiment_data.w, self.experiment_data.h)
		self.canvasImg.airchannel = self.experiment_data.airchannel
		self.canvasImg.channel1 = self.experiment_data.channel1
		self.canvasImg.channel2 = self.experiment_data.channel2
		self.canvasImg = self.canvasImg.build_canvas()
		self.setCanvasImg(self.canvasImg)
		self.odorscape_window.close()

	def launch_odorscape(self):
		self.odorscape_window = Odorscape(self)
		self.odorscape_window.send_to_closedloop.connect(self.recieve_from_odorscape)
		self.odorscape_window.show()

	def set_callbacks(self):
		self.runServerPB.clicked.connect(self.run_server)
		self.stopServerPB.clicked.connect(self.stop_server)
		self.selectLogPB.clicked.connect(self.open_log_file)

	def setCanvasImg(self, image):
		image = cv2.cvtColor(image,cv2.COLOR_BGR2RGB)
		image = image.copy()
		self.qimage = QImage(image, image.shape[0], image.shape[1], QImage.Format_RGB888)
		self.qimage = self.qimage.scaled(500,500)
		pixmap = QPixmap(self.qimage)
		pixmap = pixmap.scaled(500,500)
		self.gradientViewerLabel.setPixmap(pixmap)
		self.gradientViewerLabel.show()

	def open_log_file(self):
		if not self.ReplayRadioButton.isChecked():
			self.ReplayRadioButton.setChecked(True)
		self.replay_log_name = QFileDialog.getOpenFileName(self, 'Select Log to Open', os.getcwd())[0]
		if self.replay_log_name != '':
			self.replay_log_selected_indicator_label.setStyleSheet('background-color: green')

	def pre_run_config_check(self):

		self.clients = [LightClient(), MotorClient(), MFCClient()]
		self.server_instance.set_clients(self.clients)
		self.server_instance.add_experiment_config([self.canvasImg.airchannel, self.canvasImg.channel1,self.canvasImg.channel2], self.lightDictionary)

		if self.ReplayRadioButton.isChecked():
			self.sourceID = 'REPLAYER'
			self.server_instance.set_replayer_log_file(self.replay_log_name)
		elif self.FTRadioButton.isChecked():
			self.sourceID = 'FICTRAC'

		self.server_instance.set_source(self.sourceID)


	def run_server(self):
		self.pre_run_config_check()
		if self.sourceID is None:
			msg = 'Select a data-generating source'
			self.error = utils.ErrorMsg(msg)
			self.error.show()
		else:
			thread = threading.Thread(target=self.server_instance.run)
			thread.start()
			self.runServerPB.setEnabled(False)
			self.stopServerPB.setEnabled(True)
			self.runningLabel.setText("Running")
			self.stoppedLabel.setText("")


	def stop_server(self):
		self.kill_server.emit()
		self.runServerPB.setEnabled(True)
		self.stopServerPB.setEnabled(False)
		self.stoppedLabel.setText("Safe Exit")
		self.runningLabel.setText("")
