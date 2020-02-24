from PyQt5.QtWidgets import QMessageBox, QAction, QMainWindow

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
	newAct.triggered.connect(ui.launch_odorscape)
	menubar = QMainWindow.menuBar(ui)
	ui.fileMenu = menubar.addMenu('File')
	ui.fileMenu.addAction(newAct)
