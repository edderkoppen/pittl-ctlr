from enum import auto, IntEnum


PORT = 5000


class Request(IntEnum):
    STAGE_TIMING = 1
    STG_TIME = 1
    STAGE_SEQUENCE_RANDOM = 2
    STG_SEQ_RAND = 2
    STAGE_SEQUENCE_REGULAR = 3
    STG_SEQ_REG = 3
    START_SEQUENCE = 4
    START = 4
    STOP_SEQUENCE = 5
    STOP = 5
    QUERY_TIMING = 6
    Q_TIME = 6
    QUERY_SEQUENCE = 7
    Q_SEQ = 7
    QUERY_PROGRESS = 8
    Q_PROG = 8
    QUERY_EXPERIMENT = 9
    Q_EXP = 9


class Response(IntEnum):
    SUCCESS = 1
    FAILURE = 2
