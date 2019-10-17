import socket
from threading import Queue

import netifaces


class InetError(Exception):
    pass


class IFDown(Exception):
    pass


ETH_IF = 'eth0'
WLAN_IF = 'wlan0'


using = Queue()


def adress(interface):
    addrs = netifaces.ifaddresses(interface)
    try:
        return addrs[socket.AF_INET.value][0]['addr']
    except KeyError:
        return None


def run():
    while True:
        # Check that there aren't any low-level network config problems
        interfaces = netifaces.interfaces()
        if not (ETH_IF in interfaces and WLAN_IF in interfaces):
            raise InetException('Raspberry Pi is not recognizing both ethernet and '
                                'wlan interfaces.')

        eth_addr = address(ETH_IF)
        wlan_addr = address(WLAN_IF)
        primary_addr = eth_addr or wlan_addr


