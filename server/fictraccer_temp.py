import subprocess
import time
import threading
import queue
import os
import signal
import socket
import sys
import json
import numpy as np

mypid = 0
new_sock = 0

class FicTraccer(object):
    def __init__(self):
        self.load_json()
        self.host = self.config_data['ft_reciever_host']
        self.port = self.config_data['ft_reciever_port']
        self.readwrite_queue = queue.Queue()

    def add_config_address(self, config_address):
        self.config_address = config_address

    def edit_config(selsf):
        if self.config_address is not None:
            p = subprocess.Popen("gedit {}".format(self.config_address), shell=True)
        else:
            p = subprocess.Popen("gedit ft/sample/config.txt", shell=True)

    def ft_process(self):
        global mypid
        global new_sock
        p = subprocess.Popen("ft/bin/fictrac ft/sample/config.txt",stdout=subprocess.PIPE,shell=True, preexec_fn=os.setsid)
        mypid = os.getpgid(p.pid)

        for line in iter(p.stdout.readline,''):
            l = line.rstrip().decode("utf-8")
            if "Unable to open output data socket" in l:
                sockID = l.split('(')[-1]
                sockID = int(sockID[:-2])
                newSockID = sockID + 1
                break
        self.auto_update_ft_sock(newSockID)
        os.killpg(mypid, signal.SIGTERM)

        p = subprocess.Popen("ft/bin/fictrac ft/sample/config.txt",stdout=subprocess.PIPE,shell=True, preexec_fn=os.setsid)
        mypid = os.getpgid(p.pid)
        new_sock = newSockID

    def bind(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((self.host, self.port))
        self.sock.listen()
        self.conn, self.addr = self.sock.accept()

    def auto_update_ft_sock(self, new_sock):
        lines = []
        with open('ft/sample/config.txt') as file:
            for line in file.readlines():
                if 'sock_port' in line:
                    l = line[:-5]+'{}'.format(new_sock)
                    lines.append(l.rstrip())
                else:
                    lines.append(line.rstrip())
        with open('ft/sample/config.txt', mode='w') as file:
            for line in lines:
                file.write(line)
                file.write('\n')

    def get_current_ft_sock(self):
        with open('ft/sample/config.txt') as file:
            for line in file.readlines():
                if 'sock_port' in line:
                    port = line.split(':')[-1].rstrip()
                    port = int(port)
                    self.ft_port = port
                    with open('/home/patrick/Desktop/clm/config.json', 'r+') as j:
                        data = json.load(j)
                        data['fictrac_port'] = self.ft_port
                        j.seek(0)
                        json.dump(data, j, indent=4)
                        j.truncate()
                    break


    def sock_check(self):
        self.get_current_ft_sock()
        self.load_json()
        if self.ft_port != self.config_data['fictrac_port']:
            self.config_data['fictrac_port'] = self.ft_port

    def load_json(self):
        with open('/home/patrick/Desktop/clm/config.json', 'r+') as j:
            self.config_data = json.load(j)

    def update_json(self,set_port):
        with open('/home/patrick/Desktop/clm/config.json', 'r+') as j:
            data = json.load(j)
            data['fictrac_port'] = set_port
            j.seek(0)
            json.dump(data, j, indent=4)
            j.truncate()



    def send_to_server(self, wrote, read):
        with self.conn:
            while True:
                val = self.readwrite_queue.get()
                self.conn.send(str.encode('{}'.format(val)))

    def recieve_from_ft(self, reciever_kill_signal, done_receiving_event, connected_event, wrote, read):
        global new_sock

        self.sock_check()

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:

            if new_sock == 0:
                sock.connect(('127.0.0.1', self.ft_port))
            else:
                self.ft_port = new_sock
                self.update_json(self.ft_port)
                self.load_json()
                sock.connect(('127.0.0.1', self.ft_port))
            connected_event.set()
            data = ""
            i = 0
            while not reciever_kill_signal.isSet():
                # Receive one data frame
                new_data = sock.recv(1024)
                if not new_data:
                    break
                data += new_data.decode('UTF-8')
                endline = data.find("\n")
                line = data[:endline]       # copy first frame
                data = data[endline+1:]     # delete first frame
                toks = line.split(", ")

                if ((len(toks) < 24) | (toks[0] != "FT")):
                    print('Bad read')
                    continue
                cnt = int(toks[1])
                dr_cam = [float(toks[2]), float(toks[3]), float(toks[4])]
                err = float(toks[5])
                dr_lab = [float(toks[6]), float(toks[7]), float(toks[8])]
                r_cam = [float(toks[9]), float(toks[10]), float(toks[11])]
                r_lab = [float(toks[12]), float(toks[13]), float(toks[14])]
                posx = float(toks[15])
                posy = float(toks[16])
                heading = float(toks[17])
                step_dir = float(toks[18])
                step_mag = float(toks[19])
                intx = float(toks[20])
                inty = float(toks[21])
                ts = float(toks[22])
                seq = int(toks[23])

                send_string = '{}'.format(toks[1:])
                self.readwrite_queue.put(send_string)
            print('here')
        done_receiving_event.set()


    def poll_and_stop(self, stop_ft_event, done_polling_event, connected_event):
        global mypid
        connected_event.wait()
        while True:
            if not stop_ft_event.isSet():
                time.sleep(0.01)
            else:
                os.killpg(mypid, signal.SIGTERM)
                break
        done_polling_event.set()

    def run(self, shutdown, signal_to_server_that_im_done):

        self.stop_ft_event = threading.Event()
        self.done_polling_event = threading.Event()
        self.kill_reciever = threading.Event()
        self.done_receiving_event = threading.Event()
        self.reciever_connected = threading.Event()

        self.wrote = threading.Event()
        self.read = threading.Event()
        self.read.set()

        ft_thread = threading.Thread(target=self.ft_process)
        reciever_thread = threading.Thread(target=self.recieve_from_ft, args=(self.kill_reciever,self.done_receiving_event,self.reciever_connected,self.wrote, self.read,))
        sender_thread = threading.Thread(target=self.send_to_server, args=(self.wrote, self.read,))
        polling_thread = threading.Thread(target=self.poll_and_stop, args=(self.stop_ft_event, self.done_polling_event, self.reciever_connected,))

        ft_thread.start()
        time.sleep(0.4)
        reciever_thread.start()
        sender_thread.start()
        polling_thread.start()

        shutdown.wait()
        self.stop_ft_event.set()

        self.done_polling_event.wait()
        self.kill_reciever.set()
        self.done_receiving_event.wait()
        signal_to_server_that_im_done.set()

if __name__=="__main__":
    ft = FicTraccer()
    thread = threading.Thread(target=ft.run)
    thread.start()
    time.sleep(8)
    ft.stop_ft_event.set()
