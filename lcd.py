from collections import namedtuple
from enum import Enum
from threading import Thread
import time
import queue

import pigpio
from RPLCD.pigpio import CharLCD


# Constants
DELAY = 0.1
CLEAR = ' ' * 16


# Initialize lcd
pi = pigpio.pi()
lcd = CharLCD(pi,
              pin_rs=15, pin_rw=18, pin_e=16, pins_data=[21, 22, 23, 24],
              pin_contrast=17,
              cols=16, rows=2)
lcd.cursor_mode = 'hide'
lcd.home()


# Service
# State
db = {'buffer': [[''], ['']],
      'buffer_idx': [0, 0],
      'cycle_idx':[0, 0],
      'delay_cycles': [1, 1]}


# Interface
WriteData = namedtuple('WriteData', ['row', 'buffer', 'delay'])
ResetData = namedtuple('ResetData', ['row'])


class Msg(Enum):
    WRITE = 1
    RESET = 2


interface = queue.Queue()


# Routines
def run():
    t0 = time.time()
    while True:
        try:
            event = interface.get_nowait()
            dispatch(*event)
        except queue.Empty:
            pass

        t1 = time.time()
        if t1 - t0 > DELAY:
            t0 = t1
            update_display()


def dispatch(msg, data):
    if msg == Msg.WRITE:
        row = data.row
        buff = data.buffer
        delay_cycles = round(data.delay / DELAY)
        db['buffer'][row] = buff
        db['buffer_idx'][row] = 0
        db['cycle_idx'][row] = 0
        db['delay_cycles'][row] = delay_cycles
    elif msg == Msg.RESET:
        row = data.row
        overwrite(row, '')
        db['buffer'][row] = ['']
        db['buffer_idx'][row] = 0
        db['cycle_idx'][row] = 0
        db['delay_cycles'][row] = 1



def update_display():
    for row in (0, 1):
        buffer_idx = db['buffer_idx'][row]
        cycle_idx = db['cycle_idx'][row]
        delay_cycles = db['delay_cycles'][row]
        buff = db['buffer'][row]

        cycle_idx = (cycle_idx + 1) % delay_cycles
        if (cycle_idx == 0) and (delay_cycles != 1):
            buffer_idx = (buffer_idx + 1) % len(buff)
            overwrite(row, buff[buffer_idx])

        # Some hacky stuff don't worry about it it's n
        time.sleep(DELAY)

        db['buffer_idx'][row] = buffer_idx
        db['cycle_idx'][row] = cycle_idx


def overwrite(row, string):
    lcd.cursor_pos = (row, 0)
    lcd.write_string(CLEAR)
    lcd.cursor_pos = (row, 0)
    lcd.write_string(string)


service = Thread(target=run)
