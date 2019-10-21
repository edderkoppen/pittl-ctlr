from collections import namedtuple
from enum import Enum
import pickle
import random
import socket
from threading import Thread

import pigpio

from pittl import logger


# Exceptions
class GPIOError(Exception):
    pass


# Data structures
Domain = namedtuple('Domain', ['total', 'exposure'])


class Timing:

    def __init__(self, total, exposure, resolution):
        total = float(total)
        exposure = float(exposure)
        self.resolution = resolution
        self.specified = Domain(total, exposure)
        digit = Domain(round(total / resolution),
                       round(exposure / resolution))
        self.digital = digit
        ajstd = Domain(digit.total * resolution,
                       digit.exposure * resolution)
        self.adjusted = ajstd

    def __repr__(self):
        fstr = 'Timing(resolution={}, specified={}, ' + \
               'adjusted={}, digital={})'
        return fstr.format(self.resolution,
                           self.specified,
                           self.adjusted,
                           self.digital)


# Constants
ON = 0
OFF = 1
GPIO = 14
MICROSECONDS = 1e6

HOST = '0.0.0.0'
PORT = 5000


# Initialize the pigpio client
pi = pigpio.pi()


# Initialize the gpio pin
pi.set_mode(GPIO, pigpio.OUTPUT)
pi.write(GPIO, OFF)


# Low-level routines
def regular_sequence(n, m):
    f = round(n / m - 0.5)
    a = round(n / f - 0.5)
    unit_head = str(ON) * m
    unit_tail = str(OFF) * (f - m)
    unit = unit_head + unit_tail
    seq = unit * a

    return seq


def random_sequence(n, m):
    head = [ON] * m
    tail = [OFF] * (n - m)
    seq = head + tail

    # Knuth shuffle
    for i in range(n - 1):
        j = random.randint(i, n - 1)
        a = seq[i]
        seq[i] = seq[j]
        seq[j] = a

    return seq


def waveform(seq, res):
    wf = []
    for i in seq:
        if i == ON:
            p = pigpio.pulse(1 << GPIO, 0, int(res * MICROSECONDS))
        else:
            p = pigpio.pulse(0, 1 << GPIO, int(res * MICROSECONDS))
        wf.append(p)
    return wf


# Interface
class Msg(Enum):
    SET_TIME = 1
    GEN_SEQ_RAND = 2
    GEN_SEQ_REG = 3
    START_SEQ = 4
    STOP_SEQ = 5
    GET_TIME = 6
    GET_SEQ = 7
    GET_PROG = 8


# Service
class Service(Thread):

    def __init__(self):
        super().__init__()
        self.name = 'main'

        # CLI
        self.client = None

        # GPIO
        self.commited_timing = None
        self.commited_seq = None

        self.commit_wid
        self.commit_time = None
        
        self.staged_timing = None
        self.staged_seq = None

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
        if msg == Msg.STAGE_TIMING:
            self.stage_timing(data)
        elif msg == Msg.STAGE_SEQ_RAND:
            self.stage_seq_rand()
        elif msg == Msg.STAGE_SEQ_REG:
            self.stage_seq_reg()
        elif msg == Msg.START_SEQ:
            self.start_seq()
        elif msg == Msg.STOP_SEQ:
            self.stop_seq()
        elif msg == Msg.QUERY_STAGED_TIME:
            pass
        elif msg == Msg.QUERY_STAGED_SEQ:
            pass
        elif msg == Msg.QUERY_COMMIT_TIME:
            pass
        elif msg == Msg.QUERY_COMMIT_SEQ:
            pass
        elif msg == Msg.QUERY_PROG:
            pass

    def stage_timing(self, data):
        self.staged_timing = data
        self.staged_seq = None
        self.send('Timing staged')

    def stage_seq_rand(self):
        self.staged_seq = random_sequence(self.timing.digital.total,
                                          self.timing.digital.exposure)
        self.send('Random sequence staged')

    def stage_seq_reg(self):
        self.staged_seq = regular_sequence(self.timing.digital.total,
                                           self.timing.digital.exposure)
        self.send('Regular sequence staged')

    def start_seq(self):
        if self.commit_wid is not None:
            self.send('Sequence currently in progress')

        self.commited_timing = self.staged_timing
        self.commited_seq = self.staged_seq

        wf = waveform(self.commited_seq,
                      self.commited_timing.resolution)

        pi.wave_add_generic(wf)
        self.commit_wid = pi.wave_create()

        self.commit_start = time.time()
        pi.wave_send_once(self.wid)

        self.send('Sequence started')

    def stop_seq(self):
        pi.wave_tx_stop()
        pi.write(GPIO, OFF)
        pi.wave_delete(self.commit_wid)

        self.commited_timing = None
        self.commited_seq = None
        self.commit_start = None
        self.commit_wid = None

        self.send('Sequence stopped')
