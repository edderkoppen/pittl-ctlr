from enum import Enum

import cli
import gpio
import lcd
import inet


class Service(Enum):
    CLI = 1
    GPIO = 2
    LCD = 3
    INET = 4


def start():
    cli.service.start()
    gpio.service.start()
    lcd.service.start()
    inet.service.start()
