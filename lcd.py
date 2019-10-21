from collections import namedtuple
from enum import Enum
import logging
from threading import Thread
import time
import queue

import pigpio
from RPLCD.pigpio import CharLCD

from pittl import logger


# Constants
DELAY = 0.6
CLEAR = ' ' * 16


# Initialize lcd
pi = pigpio.pi()


# Interface
WriteData = namedtuple('WriteData', ['row', 'buffer', 'delay'])
ResetData = namedtuple('ResetData', ['row'])


class Msg(Enum):
    WRITE = 1
    RESET = 2


# Service
class Service(Thread):

    def __init__(self):
        super().__init__()
        self.name = 'lcd'

        self.lcd = CharLCD(pi,
                           pin_rs=15,
                           pin_rw=18,
                           pin_e=16,
                           pins_data=[21, 22, 23, 24],
                           pin_contrast=17,
                           cols=16, rows=2)
        self.lcd.cursor_mode = 'hide'
        self.lcd.clear()
        self.lcd.home()

        self.buffer = [[''], ['']]
        self.buffer_idx = [0, 0]
        self.cycle_idx = [0, 0]
        self.delay_cycles = [1, 1]

        self.interface = queue.Queue()

    def run(self):
        logger.info('Starting lcd driver service')

        t0 = time.time()
        while True:
            try:
                event = self.interface.get_nowait()
                logger.debug('Received event {}'.format(event))
                self.dispatch(*event)
            except queue.Empty:
                pass

            t1 = time.time()
            if t1 - t0 > DELAY:
                t0 = t1
                self.update_display()

    def dispatch(self, msg, data):
        if msg == Msg.WRITE:
            row = data.row
            buff = data.buffer
            delay_cycles = max(round(data.delay / DELAY), 1)
            self.buffer[row] = buff
            self.buffer_idx[row] = 0
            self.cycle_idx[row] = 0
            self.delay_cycles[row] = delay_cycles
        elif msg == Msg.RESET:
            row = data.row
            self.overwrite(row, '')
            self.buffer[row] = ['']
            self.buffer_idx[row] = 0
            self.cycle_idx[row] = 0
            self.delay_cycles[row] = 1

    def update_display(self):
        for row in (0, 1):
            buffer_idx = self.buffer_idx[row]
            cycle_idx = self.cycle_idx[row]
            delay_cycles = self.delay_cycles[row]
            buff = self.buffer[row]

            cycle_idx = (cycle_idx + 1) % delay_cycles
            if (cycle_idx == 0) and (delay_cycles != 1):
                buffer_idx = (buffer_idx + 1) % len(buff)
                self.overwrite(row, buff[buffer_idx])

            self.buffer_idx[row] = buffer_idx
            self.cycle_idx[row] = cycle_idx

            # THIS IS SUPER IMPORTANT
            # The screen really can't write to two rows in
            # sequence that quickly
            time.sleep(0.3)

    def overwrite(self, row, string):
        # The sleeps are hacky cuz the lcd is cheap
        # Precision is not important here
        self.lcd.cursor_pos = (row, 0)
        self.lcd.write_string(CLEAR)
        time.sleep(0.2)
        self.lcd.cursor_pos = (row, 0)
        self.lcd.write_string(string)
