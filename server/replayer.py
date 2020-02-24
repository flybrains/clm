import sys
import os
import socket
import time
import threading
import numpy as np
from datetime import datetime
import server.hardware_parameters as hw

class Replayer(object):
    def __init__(self, shutdown, address):
        self.address = address
        self.connected = False
        self.host = hw.params['source_host']
        self.port = hw.params['source_port']
        self.shutdown = shutdown

    def parse_log(self):
        self.playback = []
        self.times = []
        with open(self.address) as f:
            for idx, row in enumerate(f.read().split("\n")):
                if idx==0:
                    pass
                else:
                    try:
                        time, toks = row.split(",")[0], row.split(",")[1]
                        time = time.split("-")[1]
                        dt = datetime.strptime(time, '%H:%M:%S.%f')
                        self.times.append(dt)
                        # mfc1, mfc2, mfc3
                        self.playback.append(float(toks))
                    except IndexError:
                        pass

    def run(self):
        self.parse_log()

        with self.conn:
            self.conn.send(str.encode('{}'.format(self.playback[0])))
            time.sleep(0.015)
            index = 0
            while True:
                try:
                    if self.shutdown.is_set():
                        break
                    st = str(self.times[index+1] - self.times[index]).split('.')
                    if len(st)==1:
                        delta=float(0.0)
                    else:
                        delta = float('0.{}'.format(st[-1]))
                    time.sleep(delta)
                    self.conn.send(str.encode('{}'.format(self.playback[index])))
                    index += 1

                except (KeyboardInterrupt, BrokenPipeError, ConnectionResetError) as e:
                    self.sock.close()
                    sys.exit()

    def bind(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((self.host, self.port))
        self.sock.listen()
        self.conn, self.addr = self.sock.accept()
