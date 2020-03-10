import time
import socket
from PIL import Image
import io
import cv2
import sys
import os
import base64
import errno
import numpy as np
import server.hardware_parameters as hw
from PyQt5 import QtCore
from PyQt5.QtWidgets import QMessageBox, QAction, QMainWindow, QFileDialog

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


def populate_taskbar(ui):
	newAct = QAction('Create New Experiment', ui)
	loadAct = QAction('Load Existing Experiment', ui)
	newAct.triggered.connect(ui.launch_odorscape)
	loadAct.triggered.connect(ui.load_experiment)
	menubar = QMainWindow.menuBar(ui)
	ui.fileMenu = menubar.addMenu('File')
	ui.fileMenu.addAction(newAct)
	ui.fileMenu.addAction(loadAct)

class UIClient(QtCore.QObject):

	new_data = QtCore.pyqtSignal(list)
	def __init__(self, parent=None):
		super(UIClient, self).__init__(parent)

		self.host = hw.params['local_host']
		self.port = hw.params['local_port']
		self.most_recent_data = [0,0]

	def set_replay_status(self, replay):
		self.replay = replay

	def connect(self):
		self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.client.connect((self.host, self.port))
		self.client.sendall(bytes("UI Connected",'UTF-8'))

	def read_from_server(self):
		data = self.client.recv(1024).decode()
		if not data=='<>':
			data = [float(e) for e in data[1:-1].split(',')]
			self.most_recent_data = [data[7], data[8]]
			self.new_data.emit(data)
		return data

	def send_to_server(self, send_val):
		self.client.sendall(bytes('ui_{}'.format(send_val),'UTF-8'))

	def run(self):
		while True:
			data = self.read_from_server()
			self.most_recent_data = data
			if data=='<>':
				self.client.sendall(bytes('<>'.format(data),'UTF-8'))
				self.client.close()
				break
			self.send_to_server([])


class FicTracFrameGrabber(QtCore.QObject):
	new_data = QtCore.pyqtSignal()
	ft_done = QtCore.pyqtSignal()
	def __init__(self, parent=None):
		super(FicTracFrameGrabber, self).__init__(parent)

	def pipe_cleaner(self):
		if 'framefifo' in os.listdir('/tmp'):
			os.remove('/tmp/framefifo')
		os.mkfifo('/tmp/framefifo')

	def run(self):
		self.pipe_cleaner()
		while True:
			with open("/tmp/framefifo") as fifo:
				while True:
					data = fifo.read()
					data = str(data)

					if len(data) == 0:
						break

					if data[:-1]=='kill':
						self.ft_done.emit()
						sys.exit()
						break

					bytes = base64.b64decode(data)
					try:
						self.ft_mat = np.array(Image.open(io.BytesIO(bytes)))
						self.new_data.emit()

					except OSError:
						pass
