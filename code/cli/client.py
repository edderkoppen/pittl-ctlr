import pickle
import socket

from pittl.cli import HOST, PORT


def mac():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((HOST, PORT))
    return s


def demac(s):
    try:
        s.close()
    except:
        pass


def send(s, msg, data):
    b = pickle.dumps((msg, data))
    s.send(b)
