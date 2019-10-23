from collections import namedtuple
from enum import Enum
import random
from threading import Thread
import time

import pigpio

from pittl import logger
import pittl.lcd as lcd


# Exceptions
class DriverException(Exception):
    pass


# Constants
ON = 0
OFF = 1
PIN = 14
MICROSECONDS = 1e6
DISP_DELAY = 10


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
            p = pigpio.pulse(0, 1 << PIN, int(res * MICROSECONDS))
        else:
            p = pigpio.pulse(1 << PIN, 0, int(res * MICROSECONDS))
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

    def __init__(self, lcd_svc):
        super().__init__()
        self.name = "driver"

        self.lcd_svc = lcd_svc
        self.last_disp = 0

        self.last_busy = 0

        self.committed_timing = None
        self.committed_seq = None

        self.commit_wid = None
        self.commit_time = None

        self.staged_timing = None
        self.staged_seq = None

    def run(self):
        logger.info('Starting pigpio sync service')

        while True:
            # Sync
            self.sync_to_pigpio()

    def stage_timing(self, data):
        if type(data) != Timing:
            raise DriverException('Object to be staged was not timing')
        self.staged_timing = data
        self.staged_seq = None

    def stage_seq_rand(self):
        if self.staged_timing is None:
            raise DriverException('No timing staged')
        self.staged_seq = random_sequence(self.staged_timing.digital.total,
                                          self.staged_timing.digital.exposure)

    def stage_seq_reg(self):
        if self.staged_timing is None:
            raise DriverException('No timing staged')
        self.staged_seq = regular_sequence(self.staged_timing.digital.total,
                                           self.staged_timing.digital.exposure)

    def start_seq(self):
        if self.staged_timing is None:
            raise DriverException('No timing staged')
        if self.staged_seq is None:
            raise DriverException('No sequence staged')
        if self.commit_wid is not None:
            raise DriverException('Sequence already in progress')

        self.committed_timing = self.staged_timing
        self.committed_seq = self.staged_seq

        wf = waveform(self.committed_seq,
                      self.committed_timing.resolution)

        pi.wave_add_generic(wf)
        self.commit_wid = pi.wave_create()

        self.commit_time = time.time()
        pi.wave_send_once(self.commit_wid)

    def stop_seq(self):
        pi.wave_tx_stop()
        pi.write(PIN, OFF)
        if self.commit_wid is not None:
            pi.wave_delete(self.commit_wid)
            self.commit_wid = None

        self.committed_timing = None
        self.committed_seq = None
        self.commit_time = None

    def query_progress(self):
        if self.commit_time is not None:
            t = time.time() - self.commit_time
            return min(t / self.committed_timing.adjusted.total, 1.0)
        else:
            return 0.0

    def sync_to_pigpio(self):
        prog = self.query_progress()

        t = time.time()
        if t - self.last_disp > DISP_DELAY:
            self.last_disp = t
            prog_str = str(prog * 100)[1:8] + '%'
            buffer = [prog_str]
            self.lcd_svc.put(1, [prog_str])

        curr_busy = pi.wave_tx_busy()
        if curr_busy != self.last_busy:
            logger.info('Detected pigpio change {}->{}'.format(self.last_busy,
                                                               curr_busy))
            self.last_busy = curr_busy
            if not curr_busy:
                self.stop_seq()
        elif prog == 1:
            self.stop_seq()
