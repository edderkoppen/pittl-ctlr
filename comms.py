from enum import Enum


HOST = '0.0.0.0'
PORT = 5000


class Msg(Enum):
    QUERY = 1
    START = 2
    STOP = 3
    GEN = 4
    SET = 5
    DEBUG = 6
