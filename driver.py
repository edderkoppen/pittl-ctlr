from collections import namedtuple
from enum import Enum
import queue
import random
from threading import Thread
import time

import pigpio

from pittl import logger
import pittl.lcd as lcd


# Constants
ON = 0
OFF = 1
PIN = 14
MICROSECONDS = 1e6


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
            p = pigpio.pulse(1 << PIN, 0, int(res * MICROSECONDS))
        else:
            p = pigpio.pulse(0, 1 << PIN, int(res * MICROSECONDS))
        wf.append(p)
    return wf


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


# Initialize the pigpio client
pi = pigpio.pi()
pi.set_mode(PIN, pigpio.OUTPUT)
pi.write(PIN, OFF)


# Interface
class Msg(Enum):
    pass


# Service
class Service(Thread):

    def __init__(self):
        super().__init__()
        self.name = "driver"

        self.interface = queue.Queue()

        # PIN
        self.commited_timing = None
        self.commited_seq = None

        self.commit_wid = None
        self.commit_time = None

        self.staged_timing = None
        self.staged_seq = None

    def run(self):
        logger.info('Starting gpio management service')

        # Interface
        while True:
            try:
                event = self.interface.get_nowait()
                logger.debug('Reveived even {}'.format(event))
                self.dispatch(*event)
            except queue.Empty:
                pass

        # Sync
        self.sync_to_pigpio()

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
        pi.write(PIN, OFF)
        pi.wave_delete(self.commit_wid)

        self.commited_timing = None
        self.commited_seq = None
        self.commit_start = None
        self.commit_wid = None

        self.send('Sequence stopped')

    def query_progress(self):
        if self.commit_start:
            t = time.time() - self.commit_start
            return max(t / self.commit_timing.adjusted.total, 1.0)
        else:
            return 0.0

    def sync_to_pigpio(self):
        if self.query_progress() == 1:
            self.stop_seq()
        elif pi.wave_tx_busy():
            self.stop_seq()
