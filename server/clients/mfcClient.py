import time
import socket
import server.hardware_parameters as hw

class MFCClient(object):
    def __init__(self,lookup_table=None, oob_option=None, replay=False):
        self.host = hw.params['local_host']
        self.port = hw.params['local_port']
        self.replay = replay
        if not self.replay and lookup_table is not None:
            self.airchannel = lookup_table[0]
            self.channel1 = lookup_table[1]
            self.channel2 = lookup_table[2]

            self.w = self.airchannel.shape[1]
            self.h = self.airchannel.shape[0]

    def connect(self):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client.connect((self.host, self.port))
        self.client.sendall(bytes("MFCs Connected",'UTF-8'))

    def read_from_server(self):
        data = self.client.recv(1024).decode()
        if not data=='<>':
            data = [float(e) for e in data[1:-1].split(',')]
        return data

    def send_to_server(self, send_val):
        self.client.sendall(bytes('mf_{}'.format(send_val),'UTF-8'))

    def check_conditions(self):
        px = int(data[7])
        py = int(data[8])

        # Out of bounds options
        if (self.oob_option is None) or (self.oob_option.x_choice == 'loop' and self.oob_option.y_choice == 'loop'):
            if px > self.w/2:
                while px > self.w/2:
                    px = px - self.w
            elif px < -self.w/2:
                while px < -self.w/2:
                    px = px + self.w
            if py > self.h/2:
                while py > self.h/2:
                    py = py - self.h
            elif py < -self.h/2:
                while py < -self.h/2:
                    py = py + self.h
            send_val = [float(self.airchannel[px,py]), float(self.channel1[px,py]), float(self.channel2[px,py])]

        elif self.oob_option.x_choice == 'constant' and self.oob_option.y_choice == 'constant':
            pass

        elif self.oob_option.x_choice == 'loop' and self.oob_option.y_choice == 'constant':
            if py > self.h/2:
                send_val = self.oob_option.y_const_hi
            elif py < -self.h/2:
                send_val = self.oob_option.y_const_lo
            else:
                if px > self.w/2:
                    while px > self.w/2:
                        px = px - self.w
                elif px < -self.w/2:
                    while px < -self.w/2:
                        px = px + self.w
                send_val = [float(self.airchannel[px,py]), float(self.channel1[px,py]), float(self.channel2[px,py])]


        elif self.oob_option.x_choice == 'constant' and self.oob_option.y_choice == 'loop':
            if px > self.w/2:
                send_val = self.oob_option.x_const_hi
            elif px < -self.w/2:
                send_val = self.oob_option.x_const_lo
            else:
                if py > self.h/2:
                    while py > self.h/2:
                        py = py - self.h
                elif py < -self.h/2:
                    while py < -self.h/2:
                        py = py + self.h
                send_val = [float(self.airchannel[px,py]), float(self.channel1[px,py]), float(self.channel2[px,py])]

        return send_val



    def run(self):
        while True:
            data = self.read_from_server()

            if data=='<>':
                self.client.sendall(bytes('<>'.format(data),'UTF-8'))
                self.client.close()
                break

            if self.replay:
                send_val = [float(data[2]), float(data[3]), float(data[4])]
            else:
                send_val = self.check_conditions(data)

            self.send_to_server(send_val)
