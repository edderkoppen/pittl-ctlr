import argparse
from contextlib import closing
from datetime import datetime, timedelta
import pickle
from pprint import pprint
import socket
import time

from pittl.shared import PORT, Request


# Main parser
parser = argparse.ArgumentParser()
parser.add_argument('ip',
                    help='ip address of pittl pi')
subparsers = parser.add_subparsers()


# Config parser
config_parser = subparsers.add_parser('config', help='config parser')


# Query parser
query_parser = subparsers.add_parser('query', help='query parser')
query_parser.add_argument('query_what',
                          metavar='w',
                          nargs='+',
                          type=str,
                          help='what to query',
                          choices=['timing',
                                   'sequence',
                                   'experiment'],
                          action='append')
query_parser.add_argument('-f', '--format',
                          dest='format',
                          type=str,
                          help='output format',
                          default='text',
                          choices=['text', 'json', 'yaml'])
query_parser.add_argument('-c', '--continuous',
                          dest='continuous',
                          default=False,
                          action='store_true')


# Staging parser
stage_parser = subparsers.add_parser('stage', help='stage parser')
stage_subparsers = stage_parser.add_subparsers()


# Parse stage timing
stage_timing_parser = stage_subparsers.add_parser('timing')
stage_timing_parser.add_argument('exposure',
                                 metavar='X',
                                 type=float,
                                 help='exposure to be given, in fraction '
                                      'of total experimental time')
stage_timing_parser.add_argument('resolution',
                                 metavar='R',
                                 type=float,
                                 help='experimental resolution, in seconds')
stage_timing_parser.add_argument('-D', '--days',
                                 type=float,
                                 default=0.0,
                                 help='add days to experiment time')
stage_timing_parser.add_argument('-H', '--hours',
                                 type=float,
                                 default=0.0,
                                 help='add hours to experiment time')
stage_timing_parser.add_argument('-M', '--minutes',
                                 type=float,
                                 default=0.0,
                                 help='add minutes to experiment time')
stage_timing_parser.add_argument('-S', '--seconds',
                                 type=float,
                                 default=0.0,
                                 help='add seconds to experiment time')
stage_timing_parser.add_argument('-m', '--milliseconds',
                                 type=float,
                                 default=0.0,
                                 help='add milliseconds to experiment time')


# Parse stage sequence
stage_sequence_parser = stage_subparsers.add_parser('sequence')
stage_sequence_parser.add_argument('-g', '--regular',
                                   dest='regular',
                                   action='store_true',
                                   default=False,
                                   help='stage a regular sequence instead of '
                                        'a random sequence')


start_parser = subparsers.add_parser('start', help='start parser')
start_parser.add_argument('-w', '--wait',
                          dest='start_wait',
                          type=float,
                          default=0.0,
                          help='Wait this many seconds before sending the '
                               'start signal')


stop_parser = subparsers.add_parser('stop', help='stop parser')
stop_parser.add_argument('-w', '--wait',
                         dest='stop_wait',
                         type=float,
                         default=0.0,
                         help='Wait this many seconds before sending the '
                              'stop signal')


# Parse args
args = parser.parse_args()

# Constants
HOST = args.ip
TIMEOUT = 30
QUERY_DELAY = 2
QUERY_MAP = {'timing': Request.Q_TIME,
             'sequence': Request.Q_SEQ,
             'experiment': Request.Q_EXP}


# Utils
def remote(host, port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((host, port))
    s.settimeout(TIMEOUT)
    return s


def send(conn, msg, data=None):
    b = pickle.dumps((msg, data))
    conn.send(b)
    event = pickle.loads(conn.recv(4096))
    return event


def connect(fn):
    def wrapper(*args, **kwargs):
        with closing(remote(HOST, PORT)) as conn:
            fn(conn, *args, **kwargs)
    return wrapper


# Client routines
def format_experiment(args, experiment):
    progress = experiment['progress']
    if progress is not None:
        progress = round(progress * 1000) / 1000
        experiment['progress'] = progress

    eta = experiment['eta']
    if eta is not None:
        eta = str(timedelta(seconds=eta))
        experiment['eta'] = eta

    started = experiment['started']
    if started is not None:
        started = str(datetime.fromtimestamp(started))
        experiment['started'] = started

    return experiment


def format_timing(args, timing):
    if timing['staged'] is not None:
        timing['staged'] = timing['staged'].to_dict()
    else:
        timing['staged'] = {}
    if timing['committed'] is not None:
        timing['committed'] = timing['committed'].to_dict()
    else:
        timing['committed'] = {}
    return timing


@connect
def query(conn, args):
    what = set(args.query_what[0])
    if what != {'experiment'}:
        args.continuous = False

    if args.continuous:
        # Continuous experiment query
        try:
            while True:
                rsp, data = send(conn, Request.Q_EXP)
                pprint(format_experiment(args, data['experiment']))
                time.sleep(QUERY_DELAY)
        except KeyboardInterrupt:
            pass
    else:
        info = {}
        for x in what:
            if x == 'experiment':
                rsp, data = send(conn, Request.Q_EXP)
                data['experiment'] = format_experiment(args, data['experiment'])
                info.update(data)
            elif x == 'timing':
                rsp, data = send(conn, Request.Q_TIME)
                data['timing'] = format_timing(args, data['timing'])
                info.update(data)
            elif x == 'sequence':
                # TODO: Sequences get very big there needs to be more here
                pass

        pprint(info)


@connect
def stage_timing(conn, args):
    td = timedelta(days=args.days,
                   hours=args.hours,
                   minutes=args.minutes,
                   seconds=args.seconds,
                   microseconds=args.milliseconds * 1000)
    total = td.total_seconds()
    event = send(conn,
                  Request.STAGE_TIMING,
                  (total, args.exposure, args.resolution))
    pprint(event)


@connect
def stage_sequence(conn, args):
    if args.regular:
        rq = Request.STG_SEQ_REG
    else:
        rq = Request.STG_SEQ_RAND
    event = send(conn, rq)
    pprint(event)


@connect
def start(conn, args):
    time.sleep(args.start_wait)
    event = send(conn, Request.START)
    pprint(event)


@connect
def stop(conn, args):
    time.sleep(args.stop_wait)
    event = send(conn, Request.STOP)
    pprint(event)


def dispatch(args):
    if hasattr(args, 'query_what'):
        query(args)
    elif hasattr(args, 'resolution'):
        stage_timing(args)
    elif hasattr(args, 'regular'):
        stage_sequence(args)
    elif hasattr(args, 'start_wait'):
        start(args)
    elif hasattr(args, 'stop_wait'):
        stop(args)


if __name__ == '__main__':
    dispatch(args)
