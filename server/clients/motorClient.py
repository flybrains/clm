import time
import socket
import server.hardware_parameters as hw

class MotorClient(object):
    def __init__(self, replay=False):
        self.host = hw.params['local_host']
        self.port = hw.params['local_port']
        self.replay = replay

    @staticmethod
    def convert_angle_for_arduino(inputVal, previousAngle, mult):
    	inputVal = inputVal*(256/800)
    	spr = 800
    	conv1 = spr*(1000/256)
    	newAngle1 = (inputVal*conv1)/1000

    	highLimit = 500
    	lowLimit = 300
    	midPoint = 400
    	offset = mult*spr

    	if (newAngle1 < highLimit) and (newAngle1 > lowLimit):
    		if(newAngle1 > midPoint):
    			newAngle1 = highLimit
    		else:
    			newAngle1 = lowLimit

    	newAngle1 = newAngle1 + offset

    	if np.abs(newAngle1-previousAngle) > 400:
    		if(newAngle1 > previousAngle):
    			mult = mult-1
    			offset = mult*spr
    			newAngle1 = newAngle1 - spr
    		else:
    			mult = mult + 1
    			offset = mult*spr
    			newAngle1 = newAngle1 + spr
    	previousAngle = newAngle1
    	return int(newAngle1), mult

    def connect(self):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client.connect((self.host, self.port))
        self.client.sendall(bytes("Motor Connected",'UTF-8'))

    def read_from_server(self):
        data = self.client.recv(1024).decode()
        if not data=='<>':
            data = [float(e) for e in data[1:-1].split(',')]
        return data

    def send_to_server(self, send_val):
        self.client.sendall(bytes('mt_{}'.format(send_val),'UTF-8'))

    def run(self):
        while True:
            data = self.read_from_server()

            if data=='<>':
                self.client.sendall(bytes('<>'.format(data),'UTF-8'))
                self.client.close()
                break

            if self.replay:
                send_val = [0.0]
            else:
                s

            self.send_to_server(send_val)
