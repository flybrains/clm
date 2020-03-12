import sys
import time
import threading
from PyQt5 import QtWidgets, QtCore

import server.server as srv
from server.replayer import Replayer
import server.fictraccer_temp as ft
from server.clients.motorClient import MotorClient
from server.clients.lightClient import LightClient
from server.clients.mfcClient import MFCClient

#from ui.closed_loop_ui import ClosedLoopUI

def stop_server():
    server.shutdown_signal.set()

if __name__=="__main__":
    myFicTracInstance = ft.FicTraccer()

    sig1 = threading.Event()
    sig2 = threading.Event()


    myReplayInstance = Replayer(sig1, sig2, '/home/patrick/Desktop/clm/logs/short.log')

    myServerInstance = srv.Server()
    myServerInstance.set_clients([MotorClient(), LightClient(), MFCClient()])
    #myFicTracInstance = None
    thread = threading.Thread(target=myServerInstance.run, args=(sig1, myFicTracInstance))
    thread.start()
    thread.join()

    for thread in threading.enumerate():
        print(thread.name)


    # app = QtWidgets.QApplication(sys.argv)
    # window = ClosedLoopUI(server)
    # window.set_callbacks()
    # window.kill_server.connect(stop_server)
    # window.show()
    # sys.exit(app.exec_())
