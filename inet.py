from enum import Enum
import socket
from threading import Thread
import time

import netifaces

import lcd


class InetError(Exception):
    pass


# Constants
DELAY = 2


class IF(Enum):
    NONE = ''
    ETH = 'eth0'
    WLAN = 'wlan0'


# Service
class Service(Thread):

    def __init__(self, lcd_service):
        super().__init__()
        self.interface = None
        self.addr = ''
        self.lcd_service = lcd_service

    def run(self):
        while True:
            # Check that there aren't any low-level network config problems
            ifs = netifaces.interfaces()
            if not (IF.ETH.value in ifs and IF.WLAN.value in ifs):
                raise InetError('Raspberry Pi is not recognizing both '
                                'ethernet and wlan interfaces.')

            eth_addr = address(IF.ETH.value)
            wlan_addr = address(IF.WLAN.value)
            primary_addr = eth_addr or wlan_addr

            if eth_addr:
                buff = ['using ethernet', eth_addr]
                primary_if = IF.ETH
            elif wlan_addr:
                buff = ['using wifi', wlan_addr]
                primary_if = IF.WLAN
            else:
                buff = ['no internet :(']
                primary_if = IF.NONE

            if self.addr != primary_addr or self.interface != primary_if:
                event = (lcd.Msg.WRITE,
                         lcd.WriteData(row=0, buffer=buff, delay=3))
                self.lcd_service.interface.put(event)

                self.addr = primary_addr
                self.interface = primary_if

            time.sleep(DELAY)


def address(interface):
    addrs = netifaces.ifaddresses(interface)
    try:
        return addrs[socket.AF_INET.value][0]['addr']
    except KeyError:
        return None
