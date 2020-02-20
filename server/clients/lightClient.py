import time
import socket
import server.hardware_parameters as hw

class LightClient(object):
    def __init__(self):#, params):

        # For now, only one light condition permitted
        # Spin more out as solo clients if needed

        self.host = hw.params['local_host']
        self.port = hw.params['local_port']
        #
        # self.color = params['color']
        # self.intensity = params['intensity']
        # self.initial_delay = params['initial_delay']
        #
        # self.condition_type = params['condition_type']
        # self.condition_region = params['condition_region']
        #
        # self.repeat_condition = params['repeat_condition']
        # self.pulse_duration = params['pulse_duration']
        # self.post_pulse_lockout_duration = params['post_pulse_lockout_duration']
        # self.condition_threshold = params['condition_threshold']
        #
        # self.last_trigger_time = None
        # self.sliding_window = []

    #     if float(initial_delay) > 0:
    #         self.lockout = True
    #         self.on = False
    #         self.initial_delay_passed = False
    #     else:
    #         self.lockout = False
    #         self.initial_delay_passed = True
    #
    #
    # def switch_off(self):
    #     self.on = False
    #
    # def switch_on(self):
    #     self.on = True
    #     self.last_trigger_time = time.time()
    #
    # def check_lockout_condition(self):
    #     if time.time() - self.last_trigger_time >= self.post_pulse_lockout_duration:
    #         self.lockout = False
    #
    # def preserve_through_duration(self):
    #     if time.time() - self.last_trigger_time() >= self.pulse_duration:
    #         self.switch_off()
    #
    # def check_timed_condition(self):
    #     if (not self.initial_delay_passed) or (self.lockout):
    #         pass
    #     else:
    #         if time.time() - self.last_trigger_time:
    #             self.switch_on()

    # def check_positional_condition(self, posx, posy):
    #     if lockout:
    #         pass
    #     else:
    #
    # def check_kinematic_condition(self):
    #     if lockout:
    #         pass
    #     else:

    def connect(self):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client.connect((self.host, self.port))
        self.client.sendall(bytes("Lights Connected",'UTF-8'))

    def read_from_server(self):
        data = self.client.recv(1024).decode()

        # RETURN PARSED DATA OR <>

        return data

    def send_to_server(self, send_val):
        self.client.sendall(bytes('<mt_{}>'.format(send_val),'UTF-8'))

    # def shut_down(self):
    #     self.client.sendall(bytes('<>'.format(data),'UTF-8'))
    #     self.client.close()

    def run(self):
        while True:
            #data = self.read_from_server()
            data = self.client.recv(1024).decode()
            if data=='<>':
                self.client.sendall(bytes('<>'.format(data),'UTF-8'))
                self.client.close()
                break






            # Conditional stuff to get send_val
            send_val = 2
            self.send_to_server(send_val)






















#
