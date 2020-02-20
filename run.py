import sys
import time
import threading
from PyQt5 import QtWidgets, QtCore

import server.server as srv
from ui.closed_loop_ui import ClosedLoopUI

def stop_server():
    server.shutdown_signal.set()

if __name__=="__main__":
    server = srv.Server()
    app = QtWidgets.QApplication(sys.argv)
    window = ClosedLoopUI(server)
    window.set_callbacks()
    window.kill_server.connect(stop_server)
    window.show()
    sys.exit(app.exec_())
