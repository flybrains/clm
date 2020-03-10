import subprocess
import time
import threading
import os
import signal
import socket
import sys
import numpy as np

mypid = 0
new_sock = 0

class FicTraccer(object):
    def __init__(self):
        pass

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
        print("Changed {} to {}".format(sockID, newSockID))
        os.killpg(mypid, signal.SIGTERM)

        p = subprocess.Popen("ft/bin/fictrac ft/sample/config.txt",stdout=subprocess.PIPE,shell=True, preexec_fn=os.setsid)
        mypid = os.getpgid(p.pid)
        new_sock = newSockID


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


    def recieve_and_pass(self, reciever_kill_signal, done_receiving_event, connected_event):
        global new_sock
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:

            if new_sock == 0:
                sock.connect(('127.0.0.1', 5000))
            else:
                sock.connect(('127.0.0.1', new_sock))

            connected_event.set()


            data = ""
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
                print(toks)

        done_receiving_event.set()


    def poll_and_stop(self, stop_ft_event, done_polling_event, connected_event):
        global mypid
        connected_event.wait()
        print('POLLING')
        while True:
            if not stop_ft_event.isSet():
                time.sleep(0.5)

            else:
                os.killpg(mypid, signal.SIGTERM)
                break
        done_polling_event.set()

    def run(self):

        self.stop_ft_event = threading.Event()
        self.done_polling_event = threading.Event()
        self.kill_reciever = threading.Event()
        self.done_receiving_event = threading.Event()
        self.reciever_connected = threading.Event()

        ft_thread = threading.Thread(target=self.ft_process)
        reciever_thread = threading.Thread(target=self.recieve_and_pass, args=(self.kill_reciever,self.done_receiving_event,self.reciever_connected,))
        polling_thread = threading.Thread(target=self.poll_and_stop, args=(self.stop_ft_event, self.done_polling_event, self.reciever_connected,))

        ft_thread.start()
        time.sleep(0.5)
        reciever_thread.start()
        polling_thread.start()

        self.done_polling_event.wait()
        print('Done Polling')
        self.kill_reciever.set()
        print('Reciever Kill Sent')
        self.done_receiving_event.wait()
        print('Done Receiving')

if __name__=="__main__":
    ft = FicTraccer()
    thread = threading.Thread(target=ft.run)
    thread.start()
    time.sleep(5)
    ft.stop_ft_event.set()
