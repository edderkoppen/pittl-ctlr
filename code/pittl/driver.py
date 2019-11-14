from collections import namedtuple
import random
from threading import Thread
import time

import pigpio

from pittl import logger


# Exceptions
class DriverException(Exception):
    pass


# Some more constants
PIN = 14
ON = 0
OFF = 1
MICROS = 1e6
DISP_DELAY = 4


# Initialize the pigpio client
pi = pigpio.pi()
pi.set_mode(PIN, pigpio.OUTPUT)
pi.write(PIN, OFF)


MAX_MICROS = pi.wave_get_max_micros()
MAX_PULSES = 4000


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


def split(seq, res):
    seq_len = len(seq)
    seq_micros = seq_len * res * MICROS
    # chain_len = round(seq_micros / FCN_MAX_MICROS - 0.5)
    chain_len = round(seq_len / MAX_PULSES - 0.5)
    try:
        wf_len = round(seq_len / chain_len - 0.5)
        extra_len = seq_len % wf_len
    except ZeroDivisionError:
        wf_len = 0
        extra_len = seq_len

    chain = []
    for i in range(chain_len):
        start_idx = wf_len * i
        stop_idx = start_idx + wf_len
        chain.append(seq[start_idx:stop_idx])

    if extra_len:
        start_idx = wf_len * chain_len
        chain.append(seq[start_idx:-1])

    return chain


def waveform(seq, res):
    wf = []
    for i in seq:
        if i == ON:
            p = pigpio.pulse(0, 1 << PIN, int(res * MICROS))
        else:
            p = pigpio.pulse(1 << PIN, 0, int(res * MICROS))
        wf.append(p)
    return wf


# Data structures
# Domain = namedtuple('Domain', ['total', 'exposure'])
class Domain:

    def __init__(self, total, exposure):
        self.total = total
        self.exposure = exposure

    def to_dict(self):
        return vars(self)


    def __repr__(self):
        fstr = 'Domain(total={}, exposure={})'
        return fstr.format(self.total, self.exposure)


class Timing:

    def __init__(self, total, exposure_frac, resolution):
        total = float(total)
        exposure_frac = float(exposure_frac)
        exposure = total * exposure_frac
        self.resolution = resolution
        self.specified = Domain(total, exposure)
        digit = Domain(round(total / resolution),
                       round(exposure / resolution))
        self.digital = digit
        ajstd = Domain(digit.total * resolution,
                       digit.exposure * resolution)
        self.adjusted = ajstd


    def to_dict(self):
        return {'resolution': self.resolution,
                'specified': self.specified.to_dict(),
                'adjusted': self.adjusted.to_dict(),
                'digital': self.digital.to_dict()}


    def __repr__(self):
        fstr = 'Timing(resolution={}, specified={}, ' + \
               'adjusted={}, digital={})'
        return fstr.format(self.resolution,
                           self.specified,
                           self.adjusted,
                           self.digital)


# Service
class Service(Thread):

    def __init__(self, lcd_svc):
        super().__init__()
        self.name = "driver"

        self._lcd_svc = lcd_svc
        self._last_disp = 0

        self.staged_timing = None
        self.staged_seq = None

        self.committed_timing = None
        self.committed_seq = None

        self._chain = None
        self._chain_idx = 0
        self.started = None

        self._wid = None
        self._wf_start = None
        self._staged_wf = None

        # In case service is restarted
        # This shouldn't be happening, by the way
        self.stop_seq()

    def run(self):
        logger.info('Starting pigpio driver service')

        while True:
            self._display()

            if self._chain and self._chain_idx < len(self._chain) - 1:
                if self._staged_wf is None and self.wf_progress() >= 0.5:
                    self._stage_wf(self._chain_idx + 1)
                elif self.wf_progress() >= 1.0:
                    self._stop_wf()
                    self._chain_idx += 1
                    self._start_wf()
            elif self.wf_progress() >= 1.0:
                self.stop_seq()

    def stage_timing(self, data):
        try:
            self.staged_timing = Timing(*data)
        except Exception as e:
            logger.error(e)
            raise DriverException('Object to be staged could '
                                  'not be interpreted as timing')
        self.staged_seq = None
        logger.info('Staged timing {} '
                    '(and reset sequence)'.format(self.staged_timing))

    def stage_seq_rand(self):
        if self.staged_timing is None:
            raise DriverException('No timing staged')
        self.staged_seq = random_sequence(self.staged_timing.digital.total,
                                          self.staged_timing.digital.exposure)
        logger.info('Staged random sequence')

    def stage_seq_reg(self):
        if self.staged_timing is None:
            raise DriverException('No timing staged')
        self.staged_seq = regular_sequence(self.staged_timing.digital.total,
                                           self.staged_timing.digital.exposure)
        logger.info('Staged regular sequence')

    def _stage_wf(self, idx):
        logger.info('Staging waveform {}'.format(idx))

        self._staged_wf = waveform(self._chain[idx],
                                   self.committed_timing.resolution)

    def _stop_wf(self):
        pi.wave_tx_stop()
        if self._wid is not None:
            logger.info('Stopping waveform {}'.format(self._chain_idx))

            pi.wave_delete(self._wid)
            self._wid = None

    def _start_wf(self):
        self._stop_wf()

        logger.info('Starting waveform {}'.format(self._chain_idx))

        if self._staged_wf is not None:
            pi.wave_add_generic(self._staged_wf)
            self._wid = pi.wave_create()
            self._wf_start = time.time()
            pi.wave_send_once(self._wid)
            self._staged_wf = None
        else:
            raise DriverException('No staged waveform found.')

    def stop_seq(self):
        self._stop_wf()
        pi.write(PIN, OFF)
        self.committed_timing = None
        self.committed_seq = None

        self._chain = None
        self._chain_idx = None
        self.started = None
        self._staged_wf = None
        self._wf_start = None

    def start_seq(self):
        if self.staged_timing is None:
            raise DriverException('No timing staged')
        if self.staged_seq is None:
            raise DriverException('No sequence staged')
        if self._chain is not None:
            raise DriverException('Sequence already in progress')
        logger.info('Committing and starting sequence')

        self.committed_timing = self.staged_timing
        self.committed_seq = self.staged_seq

        self._chain = split(self.committed_seq,
                            self.committed_timing.resolution)
        logger.debug('Sequence split into '
                     'chain with {} sub-sequence(s)'.format(len(self._chain)))

        self.started = time.time()
        self._chain_idx = 0
        self._stage_wf(self._chain_idx)
        self._start_wf()


    def eta(self):
        if self.started is not None:
            t = self.committed_timing.adjusted.total
            return (1 - self.chain_progress()) * t
        else:
            return None


    def chain_progress(self):
        if self.started is not None:
            t = time.time() - self.started
            return min(t / self.committed_timing.adjusted.total, 1.0)
        else:
            return 0.0

    def wf_progress(self):
        try:
            if self._wf_start is not None:
                t = time.time() - self._wf_start
                wf_total = len(self._chain[self._chain_idx]) * \
                    self.committed_timing.resolution
                return min(t / wf_total, 1.0)
        except AttributeError:
            pass
        return 0.0

    def _display(self):
        t = time.time()
        if t - self._last_disp > DISP_DELAY:
            self._last_disp = t

            prog = self.chain_progress() * 100
            buffer = ['Prog @ {:.3}%'.format(prog)]
            self._lcd_svc.put(1, buffer)
