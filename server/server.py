import sys
import time
import queue
import socket
import threading
import numpy as np
import subprocess
from PyQt5 import QtCore

import json
import server.fictraccer_temp as ft
from .clients.motorClient import MotorClient
from .clients.lightClient import LightClient
from .clients.mfcClient import MFCClient
from server.replayer import Replayer


class ClientManagerThread(threading.Thread):
    def __init__(self,clientAddress, clientsocket, data_queue, new_source_data, read_and_wrote, shutdown, client_shutdown):
        threading.Thread.__init__(self)
        self.csocket = clientsocket
        self.clientAddress = clientAddress
        self.source_data_queue = data_queue[0]
        self.destination_data_queue = data_queue[1]
        self.new_source_data = new_source_data
        self.read_and_wrote = read_and_wrote
        self.shutdown = shutdown
        self.client_shutdown = client_shutdown

    def _get_new_data(self):
        return self.source_data_queue.get()

    def _put_new_data(self, val):
        self.destination_data_queue.put(val)

    def run(self):
        while not self.shutdown.is_set():
            self.new_source_data.wait()
            new_source_data = self._get_new_data()
            if self.client_shutdown.is_set():
                new_source_data = '<>'
            self.csocket.send(bytes('{}'.format(new_source_data),'UTF-8'))
            data = self.csocket.recv(2048).decode()
            if data=='<>':
                self._put_new_data(data)
                self.read_and_wrote.set()
                break
            self._put_new_data(data)
            self.read_and_wrote.set()
            self.new_source_data.clear()
        print('Client Thread = Safe Exit')


class Server(object):
    def __init__(self):
        self.load_json()
        self.local_host = self.config_data['local_host']
        self.local_port = self.config_data['local_port']

        self.queue_pairs = []
        self.read_and_wrote_events = []
        self.shutdown = threading.Event()
        self.source_is_shutdown = threading.Event()
        self.client_shutdown = threading.Event()
        self.new_source_data = threading.Event()
        self.read_next_from_source = threading.Event()
        self.read_next_from_source.set()
        self.kill_switch = False

    def reinitialize(self):
        self.queue_pairs = []
        self.read_and_wrote_events = []
        self.shutdown = threading.Event()
        self.source_is_shutdown = threading.Event()
        self.client_shutdown = threading.Event()
        self.new_source_data = threading.Event()
        self.read_next_from_source = threading.Event()
        self.read_next_from_source.set()
        self.kill_switch = False

    def load_json(self):
        with open('/home/patrick/Desktop/clm/config.json', 'r+') as j:
            self.config_data = json.load(j)

    def connect_source(self, mode=None):
        self.load_json()
        if mode=='FT':
            self.source_host = self.config_data['ft_reciever_host']
            self.source_port = self.config_data['ft_reciever_port']
        if mode=='RP':
            self.source_host = self.config_data['replay_host']
            self.source_port = self.config_data['replay_port']

        self.source_reader = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.source_reader.connect((self.source_host, self.source_port))

    def bind(self):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind((self.local_host, self.local_port))

    def activate_shutdown(self, mode):
        if mode=='soft':
            self.client_shutdown.set()

        if mode=='hard':
            self.shutdown.set()
            self.read_next_from_source.set()

    def read_from_source(self):
        while not self.shutdown.is_set():
            self.read_next_from_source.wait()
            self.from_source = self.source_reader.recv(1024)
            data = self.from_source.decode('UTF-8')


            if data=='<>':
                [q[0].put('<>') for q in self.queue_pairs]
                self.shutdown.set()
                self.new_source_data.set()
                self.read_next_from_source.clear()
                break

            try:
                data = [float(e) for e in data[1:-1].split(',')]

                client_data = data[:-5]
                client_data.insert(0,time.time())

                # Send information to hardware clients
                [q[0].put(client_data) for q in self.queue_pairs]

                self.new_source_data.set()
                self.read_next_from_source.clear()
            except ValueError:
                pass
        print('Server Read Thread = Safe Exit')

    def write_to_destination(self):
        while not self.shutdown.is_set():
            [rwe.wait() for rwe in self.read_and_wrote_events]
            from_clients = [q[1].get() for q in self.queue_pairs]
            if from_clients[0]=="<>":
                break
            print(from_clients)
            #########################
            # Write to Pi here
            #########################
            # Join and log here
            #########################
            self.read_next_from_source.set()
            [rwe.clear() for rwe in self.read_and_wrote_events]


        print('Server Write Thread = Safe Exit')

    def set_clients(self, list_of_clients):
        self.clients = list_of_clients

    def set_replayer_log_file(self, address):
        self.replayer_log_file = address

    def bind_clients(self):

        for i in range(len(self.clients)):
            self.server.listen(1)
            clientsock, clientAddress = self.server.accept()

            queue_pair = [queue.Queue(), queue.Queue()]
            self.queue_pairs.append(queue_pair)

            read_and_wrote = threading.Event()
            self.read_and_wrote_events.append(read_and_wrote)

            newthread = ClientManagerThread(clientAddress, clientsock, queue_pair, self.new_source_data, read_and_wrote, self.shutdown, self.client_shutdown)
            newthread.start()

    def run(self, server_done, FicTracInstance):
        self.reinitialize()


        if FicTracInstance is not None:
            self.sourceID = 'FICTRAC'
        else:
            self.sourceID = 'REPLAYER'

        if self.sourceID == 'REPLAYER':
            self.replayer_log_file = '/home/patrick/Desktop/clm/logs/short.log'
            self.source = Replayer(self.shutdown, self.source_is_shutdown, self.replayer_log_file)
            self.source_binder = threading.Thread(target=self.source.bind)
            self.source_binder.start()
            try:
                self.connect_source(mode='RP')
            except ConnectionRefusedError:
                time.sleep(2)
                self.connect_source(mode='RP')
            self.source_binder.join()

            self.bind()
            self.clients_binder = threading.Thread(target=self.bind_clients)
            self.clients_binder.start()
            [client.connect() for client in self.clients]
            self.clients_binder.join()
            self.client_threads = [threading.Thread(target=client.run) for client in self.clients]
            [thread.start() for thread in self.client_threads]

            self.source_thread = threading.Thread(target=self.source.run)
            self.source_thread.start()
            self.reader_thread = threading.Thread(target=self.read_from_source)
            self.reader_thread.start()

            self.writer_thread = threading.Thread(target=self.write_to_destination)
            self.writer_thread.start()
            self.source_is_shutdown.wait()
            self.activate_shutdown('soft')
            [thread.join() for thread in self.client_threads]
            self.activate_shutdown('hard')
            self.reader_thread.join()
            self.writer_thread.join()
            self.source_thread.join()
            print('Done... Shutting Down')


        if self.sourceID == 'FICTRAC':

            self.source_binder = threading.Thread(target=FicTracInstance.bind)
            self.source_binder.start()

            try:
                time.sleep(1)
                self.connect_source(mode='FT')
            except ConnectionRefusedError:
                time.sleep(2)
                self.connect_source(mode='FT')
            self.source_binder.join()

            signal_from_ft_that_hes_done = threading.Event()

            self.ft_thread_done = threading.Event()
            self.source_thread = threading.Thread(target=FicTracInstance.run, args=(self.shutdown,self.source_is_shutdown,))
            self.source_thread.start()


            self.bind()
            self.clients_binder = threading.Thread(target=self.bind_clients)
            self.clients_binder.start()
            [client.connect() for client in self.clients]
            self.clients_binder.join()
            self.client_threads = [threading.Thread(target=client.run) for client in self.clients]
            [thread.start() for thread in self.client_threads]


            self.reader_thread = threading.Thread(target=self.read_from_source)
            self.reader_thread.start()
            self.writer_thread = threading.Thread(target=self.write_to_destination)
            self.writer_thread.start()

            time.sleep(3)
            self.shutdown.set()

            #self.source_is_shutdown.wait()

            self.activate_shutdown('soft')
            [thread.join() for thread in self.client_threads]
            self.activate_shutdown('hard')
            self.reader_thread.join()
            self.writer_thread.join()
            self.source_thread.join()
            print('Done... Shutting Down')












if __name__=='__main__':
    server = Server()
    print(server)
