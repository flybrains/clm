import time
import socket
import server.hardware_parameters as hw

class LightClient(object):
    def __init__(self, replay=False):

        self.host = hw.params['local_host']
        self.port = hw.params['local_port']
        self.replay = replay

    def connect(self):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client.connect((self.host, self.port))
        self.client.sendall(bytes("Lights Connected",'UTF-8'))

    def read_from_server(self):
        data = self.client.recv(1024).decode()
        if not data=='<>':
            data = [float(e) for e in data[1:-1].split(',')]
        return data

    def send_to_server(self, send_val):
        self.client.sendall(bytes('lt_{}'.format(send_val),'UTF-8'))

    def run(self):
        while True:
            data = self.read_from_server()

            if data=='<>':
                self.client.sendall(bytes('<>'.format(data),'UTF-8'))
                self.client.close()
                break

            if self.replay:
                send_val = [float(data[5]), float(data[6])]
            else:
                send_val = self.check_conditions(data)

            self.send_to_server(send_val)






















#
