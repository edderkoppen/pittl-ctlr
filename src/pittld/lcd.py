from collections import namedtuple
from enum import Enum
import time
import queue

import pigpio
from RPLCD.pigpio import CharLCD

from pittld import logger
from pittld.svc import BaseService


# Constants
DELAY = 5


# Initialize lcd
pi = pigpio.pi()


# Service
class Service(BaseService):

    def __init__(self):
        super().__init__()
        self.name = 'lcd'

        self._lcd = CharLCD(pi,
                           pin_rs=15,
                           pin_rw=18,
                           pin_e=16,
                           pins_data=[21, 22, 23, 24],
                           pin_contrast=17,
                           cols=16, rows=2)

        self._row = [queue.Queue(), queue.Queue()]
        self._buffer = [[''], ['']]
        self._idx = [0, 0]

        self.reset()

    def run(self):
        logger.info('Starting lcd driver service')

        t0 = time.time()
        while True:
            for i in 0, 1:
                try:
                    buffer = self._row[i].get_nowait()
                    logger.debug('Retrieved new buffer {} in row {}'.format(buffer, i))
                    self._buffer[i] = buffer
                    self._idx[i] = 0
                except queue.Empty:
                    pass

            t1 = time.time()
            if t1 - t0 > DELAY:
                t0 = t1
                self.reset()
                time.sleep(0.2)
                self._update_display()

    def _update_display(self):
        line1 = self._buffer[0][self._idx[0]].ljust(16)
        line2 = self._buffer[1][self._idx[1]].ljust(16)

        self.reset()
        time.sleep(0.5)
        self._lcd.write_string(line1)
        time.sleep(0.5)
        self._lcd.crlf()
        time.sleep(0.5)
        self._lcd.write_string(line2)

        self._idx[0] = (self._idx[0] + 1) % len(self._buffer[0])
        self._idx[1] = (self._idx[1] + 1) % len(self._buffer[1])

    def put(self, row, buffer):
        try:
            self._row[row].get_nowait()
        except queue.Empty:
            pass
        self._row[row].put_nowait(buffer)

    def reset(self):
        self._lcd.cursor_mode = 'hide'
        self._lcd.clear()
        self._lcd.home()
