from collections import namedtuple
from enum import Enum
import pickle
import random
import socket
from threading import Thread

import pigpio

from pittl import logger
from pittl.public import Request


# Constants
HOST = '0.0.0.0'
PORT = 5000


# Service
class Service(Thread):

    def __init__(self, driver_svc):
        super().__init__()
        self.name = 'cli_server'

        # CLI
        self.client = None

        # Driver mirror
        self.driver_svc = driver_svc

    def send(self, msg):
        if msg[-1] != '\n':
            append = '\n'
        else:
            append = ''
        data = (msg + append).encode()

        try:
            self.client.send(data)
            logger.debug('Sent {}'.format(msg))
        except socket.error:
            pass

    def run(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((HOST, PORT))
            s.listen(0)
            addr = s.getsockname()
            logger.info('Awaiting connection on {}:{}'.format(*addr))

            self.await_client(s)

    def await_client(self, s):
        while True:
            client, addr = s.accept()
            self.client = client

            logger.info('Accepted connection from {}:{}'.format(*addr))
            self.handle_client(client, addr)
            logger.info('{}:{} disconnected'.format(*addr))

    def handle_client(self, client, addr):
        with client:
            while True:
                # Get a msg please
                try:
                    data = client.recv(1024)
                except ConnectionResetError:
                    return
                if not data:
                    return
                try:
                    event = pickle.loads(data)
                    logger.debug('Received {}'.format(event))

                    self.dispatch(*event)

                except pickle.UnpicklingError:
                    self.send('I couldn\'t read that. '
                              'Don\'t try and play any nasty tricks.')

    def dispatch(self, msg, data):
        if msg == Request.STAGE_TIMING:
            pass
        elif msg == Request.STAGE_SEQUENCE_RANDOM:
            pass
        elif msg == Request.STAGE_SEQUENCE_REGULAR:
            pass
        elif msg == Request.START_SEQUENCE:
            pass
        elif msg == Request.STOP_SEQUENCE:
            pass
