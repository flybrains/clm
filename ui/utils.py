from PyQt5.QtWidgets import QMessageBox

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
