from enum import auto, IntEnum


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


class Response(IntEnum):
    SUCCESS = 1
    FAILURE = 2
