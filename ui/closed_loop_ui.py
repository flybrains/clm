import os
import cv2
import sys
import pickle
import threading
import numpy as np
import time


from PyQt5 import QtCore, QtGui, QtWidgets, uic
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import QLabel, QMainWindow, QTextEdit, QAction, QFileDialog, QApplication, QMessageBox

import ui.utils as utils
import server.server as server
import server.fictraccer_temp as ft
from server.clients.lightClient import LightClient
from server.clients.motorClient import MotorClient
from server.clients.mfcClient import MFCClient

from odorscape.OdorscapeMainWindow import Odorscape
from odorscape.odorscape import Canvas, OOBOption

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
		self.UIClientInstance = utils.UIClient()
		self.FrameGrabInstance = utils.FicTracFrameGrabber()
		self.FTConfig = None

		self.FicTracInstance = ft.FicTraccer()


	def load_in_experiment(self, odorscape_window):
		self.canvasImg = Canvas(self.experiment_data.w, self.experiment_data.h)
		self.canvasImg.airchannel = self.experiment_data.airchannel
		self.canvasImg.channel1 = self.experiment_data.channel1
		self.canvasImg.channel2 = self.experiment_data.channel2
		self.displayImg = self.canvasImg.build_canvas()
		self.setCanvasImg(self.displayImg)
		self.window_w = self.displayImg.shape[1]
		self.window_h = self.displayImg.shape[0]

		if odorscape_window:
			self.odorscape_window.close()

		try:
			self.lightDictionary = self.experiment_data.lightDictionary
		except AttributeError:
			self.lightDictionary = None

	@QtCore.pyqtSlot(str)
	def recieve_from_odorscape(self, experiment_pickle_name):
		pickle_in = open(experiment_pickle_name, "rb")
		self.experiment_data = pickle.load(pickle_in)
		self.load_in_experiment(True)
	def launch_odorscape(self):
		self.odorscape_window = Odorscape(self)
		self.odorscape_window.send_to_closedloop.connect(self.recieve_from_odorscape)
		self.odorscape_window.show()

	@QtCore.pyqtSlot(list)
	def use_server_data(self, server_info):
		self.update_viewing_window_track(server_info[7], server_info[8])
		self.populate_labels(server_info)

	def update_viewing_window_track(self, x, y):
		x = x + self.window_w/2
		y = self.window_h-(y + self.window_h/2)
		self.displayed_with_track = self.displayImg.copy()
		self.displayed_with_track = cv2.circle(self.displayed_with_track, (int(x), int(y)), 6, (0,0,0),-1)
		self.setCanvasImg(self.displayed_with_track)

	@QtCore.pyqtSlot()
	def update_FT_window_track(self):
		aimage = self.FrameGrabInstance.ft_mat
		bimage = aimage.copy()
		self.cimage = QImage(bimage, bimage.shape[1], bimage.shape[0], QImage.Format_RGB888)
		self.dimage = self.cimage.scaled(640,480)
		e_pixmap = QPixmap(self.dimage)
		f_pixmap = e_pixmap.scaled(640, 480)
		self.FTLabel.setPixmap(f_pixmap)
		self.FTLabel.show()

	def pick_ft_config(self):
		self.FTConfig = QFileDialog.getOpenFileName(self, 'Select FT Config to Use', os.getcwd(), "(*.txt)")[0]
		self.FicTracInstance.add_config_address(self.FTConfig)

	def set_callbacks(self):
		self.runServerPB.clicked.connect(self.run_server)
		self.stopServerPB.clicked.connect(self.stop_server)
		self.selectLogPB.clicked.connect(self.open_log_file)
		self.UIClientInstance.new_data.connect(self.use_server_data)
		self.editFTConfigPB.clicked.connect(self.FicTracInstance.edit_config)
		self.pickFTConfigPB.clicked.connect(self.pick_ft_config)

	def populate_labels(self, server_info):
		self.xLabel.setText(str(round(server_info[7],2)))
		self.yLabel.setText(str(round(server_info[8],2)))
		self.headingLabel.setText(str(round(server_info[9],2)))
		self.motorLabel.setText(str(round(server_info[1])))
		self.mfc1Label.setText(str(round(server_info[2],2)))
		self.mfc2Label.setText(str(round(server_info[3],2)))
		self.mfc3Label.setText(str(round(server_info[4],2)))
		self.led1Label.setText(str(round(server_info[5],2)))
		self.led2Label.setText(str(round(server_info[6],2)))

		if server_info[5]>0.0:
			self.redLEDIndicatorLabel.setStyleSheet('background-color: red')
		else:
			self.redLEDIndicatorLabel.setStyleSheet("")

		if server_info[6]>0.0:
			self.greenLEDIndicatorLabel.setStyleSheet('background-color: red')
		else:
			self.greenLEDIndicatorLabel.setStyleSheet("")

	def setCanvasImg(self, image):
		image = cv2.cvtColor(image,cv2.COLOR_BGR2RGB)
		image = image.copy()
		self.qimage = QImage(image, image.shape[0], image.shape[1], QImage.Format_RGB888)
		self.qimage = self.qimage.scaled(500,500)
		pixmap = QPixmap(self.qimage)
		pixmap = pixmap.scaled(500,500)
		self.gradientViewerLabel.setPixmap(pixmap)
		self.gradientViewerLabel.show()

	def load_experiment(self):
		experiment_name = QFileDialog.getOpenFileName(self, 'Select Experiment to Open', os.getcwd(), "(*.pkl)")[0]
		if experiment_name == '':
			return None
		pickle_in = open(experiment_name, "rb")
		self.experiment_data = pickle.load(pickle_in)
		self.load_in_experiment(False)

	def open_log_file(self):
		if not self.ReplayRadioButton.isChecked():
			self.ReplayRadioButton.setChecked(True)
		self.replay_log_name = QFileDialog.getOpenFileName(self, 'Select Log to Open', os.getcwd(), "(*.log)")[0]
		if self.replay_log_name != '':
			self.replay_log_selected_indicator_label.setStyleSheet('background-color: green')

	def pre_run_config_check(self):
		self.clients = None
		lookup_table = None

		if self.ReplayRadioButton.isChecked():
			self.replay = True
			self.server_instance.set_replayer_log_file(self.replay_log_name)
			#lookup_table = [self.canvasImg.airchannel, self.canvasImg.channel1,self.canvasImg.channel2]
			self.UIClientInstance.set_replay_status(True)
			self.clients = [LightClient(replay=self.replay), MFCClient(lookup_table=lookup_table,oob_option=None,replay=self.replay), MotorClient(replay=self.replay), self.UIClientInstance]

		elif self.FTRadioButton.isChecked():
			self.replay = False
			self.FrameGrabInstance.new_data.connect(self.update_FT_window_track)
			self.UIClientInstance.set_replay_status(False)

			#self.server_instance.add_experiment_config([self.canvasImg.airchannel, self.canvasImg.channel1,self.canvasImg.channel2], self.lightDictionary)
			self.clients = [LightClient(replay=self.replay), MFCClient(lookup_table=lookup_table,oob_option=None,replay=self.replay), MotorClient(replay=self.replay), self.UIClientInstance]

		self.server_instance.set_clients(self.clients)

	@QtCore.pyqtSlot()
	def set_ft_window_blank(self):
		frame = np.zeros((480,640,3), dtype=np.uint8)
		self.update_FT_window_track(mat=frame)

	def server_waiter(self, server_done):
		self.server_done.wait()
		self.stop_server()

	def run_server(self):
		self.pre_run_config_check()

		if self.sourceID is None:
			msg = 'Select a data-generating source'
			self.error = utils.ErrorMsg(msg)
			self.error.show()

		elif self.replay:
			self.FicTracInstance = None
			self.server_done = threading.Event()
			thread = threading.Thread(target=self.server_instance.run, args=(self.server_done, self.FicTracInstance))
			waiter = threading.Thread(target=self.server_waiter, args=(self.server_done,))
			thread.start()
			waiter.start()

		else:
			self.server_done = threading.Event()
			thread = threading.Thread(target=self.server_instance.run, args=(self.server_done, self.FicTracInstance))
			waiter = threading.Thread(target=self.server_waiter, args=(self.server_done,))
			frame_grab = threading.Thread(target=self.FrameGrabInstance.run)
			#frame_grab.start()
			thread.start()
			waiter.start()

		self.runServerPB.setEnabled(False)
		self.stopServerPB.setEnabled(True)
		self.runningLabel.setText("Running")
		self.stoppedLabel.setText("")

	def stop_server(self):
		self.kill_server.emit()
		self.server_done.set()
