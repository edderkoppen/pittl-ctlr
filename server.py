from collections import namedtuple
from datetime import datetime
from multiprocessing import Process, Queue
from pathlib import Path
import pickle
import queue
import random
import socket
from threading import Thread
import time

import yaml

from comms import Msg, HOST, PORT
import worker


# Constants
SESSION_PATH = Path.home() / 'sessions'


# Timing data structures
Timing = namedtuple('Timing',
                    ['specified', 'adjusted', 'digital', 'resolution'])
Domain = namedtuple('Domain', ['total', 'exposure'])


# Formatting
def dictify_timing(timing):
    specd = timing.specified
    ajstd = timing.adjusted
    digit = timing.digital
    res = timing.resolution
    return {'timing': {'specified': dict(specd._asdict()),
                       'adjusted': dict(ajstd._asdict()),
                       'digital': dict(digit._asdict()),
                       'resolution': res}}


def format_datetime(dt):
    return dt.strftime('%Y%m%d-%H%M%S')


def dictify_datetime(dt):
    return {'datetime': format_datetime(dt)}


def dictify_sequence(seq):
    return {'sequence': pickle.dumps(seq)}


# Init server db
db = {}


# Server routines
def send(msg):
    if msg[-1] != '\n':
        append = '\n'
    else:
        append = ''
    print('[server->client] {}'.format(msg))
    data = (msg + append).encode()
    try:
        db['client'].send(data)
    except KeyError:
        pass


def server():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((HOST, PORT))
            s.listen(0)

            print('[server] CLI listening on {}:{}'.format(*s.getsockname()))

            await_client(s)
    except Exception as e:
        stop_experiment()
        raise(e)


def await_client(s):
    while True:
        client, addr = s.accept()

        print('[server] Accepted connection from {}:{}'.format(*addr))
        db['client'] = client

        handle_client(client, addr)

        del db['client']
        print('[server] {}:{} disconnected'.format(*addr))


def handle_client(client, addr):
    with client:
        while True:
            # Get a msg please
            try:
                data = client.recv(1024)
            except ConnectionResetError:
                return
            if not data:
                return
            try:
                event = pickle.loads(data)
                print('[client->server] {}'.format(event))

                dispatch(event)
            except pickle.UnpicklingError:
                send('I couldn\'t read that. '
                     'Don\'t try and play any nasty tricks.')

def progress():
    return (db['last_idx'] + 1) / db['timing'].digital.total


def query():
    try:
        last_idx = db['last_idx']
    except KeyError:
        send('Worker hasn\'t provided any updates yet. ' +
             'Try again soon.')
    except KeyError:
        last_idx = None

    if last_idx is None:
        send('There is no worker running! Aborting.')
    else:
        try:
            pct = progress() * 100
            send('Experiment running - {}%'.format(pct))
        except KeyError:
            send('Something has gone very wrong. Aborting.')


def timing(total, exposure, resolution):
    total, exposure = float(total), float(exposure)
    specd = Domain(total, exposure)
    digit = Domain(round(total / resolution),
                         round(exposure / resolution))
    ajstd = Domain(digit.total * resolution,
                         digit.exposure * resolution)
    return Timing(specd, ajstd, digit, resolution)


def set_timing(data):
    db['timing'] = timing(*data)
    try:
        del db['sequence']
    except KeyError:
        pass
    send('Timing successfully set.')


def sequence(timing):
    n = timing.digital.total
    m = timing.digital.exposure

    head = [True] * m
    tail = [False] * (n - m)
    seq = head + tail

    # Knuth shuffle
    for i in range(n - 1):
        j = random.randint(i, n - 1)
        a = seq[i]
        seq[i] = seq[j]
        seq[j] = a

    return tuple(seq)


def gen_sequence():
    try:
        db['sequence'] = sequence(db['timing'])
    except KeyError:
        send('No timing set! Aborted.')
    send('Sequence successfully generated.')


def create_session_file():
    dt = datetime.now()
    file_name = 'session_{}.yaml'.format(format_datetime(dt))
    file_path = SESSION_PATH / file_name

    with open(file_path, 'w') as f:
        data = {**dictify_timing(db['timing']),
                **dictify_sequence(db['sequence']),
                **dictify_datetime(dt)}

        yaml.dump(data, f)

    return file_path


def start_worker(sess_fp):
    proc_conn = Queue()
    proc = Process(target=worker.run,
                   args=(sess_fp, proc_conn))
    proc.start()

    return proc, proc_conn


def monitor():
    while True:
        try:
            last_idx = db['proc_conn'].get_nowait()
            db['last_idx'] = last_idx
        except queue.Empty:
            pass
        try:
            if progress() == 1:
                stop_experiment()
                return
            print('[server-monitor] curr progress {}'.format(progress()))
        except KeyError:
            pass
        try:
            if not db['proc'].is_alive:
                stop_experiment()
                return
        except KeyError:
            stop_experiment()
            return
        time.sleep(1)


def start_monitor():
    t = Thread(target=monitor)
    t.start()
    print('[server] Monitor started')
    return t


def start_experiment():
    try:
        if db['proc'].is_alive:
            send('An experiment is already running. Aborting.')
            return
    except KeyError:
        pass
    try:
        timing = db['timing']
    except KeyError:
        send('No timing set! Aborting.')
        return
    try:
        sequence = db['sequence']
    except KeyError:
        send('No sequence set! Aborting.')
        return
    try:
        sess_fp = create_session_file()
        send('Created session file at {}'.format(sess_fp))
    except:
        send('Woah! Unexpected error creating session file.')
        return
    try:
        proc, proc_conn = start_worker(sess_fp)
        db['proc'] = proc
        db['proc_conn'] = proc_conn
    except:
        send('Woah! Unexpected error starting worker.')
        return
    db['last_idx'] = -1
    db['proc_monitor'] = start_monitor()


def stop_experiment():
    try:
        db['proc'].terminate()
        del db['proc']
        print('[server] Proc deleted')
    except KeyError:
        pass
    proc = Process(target=worker.reset)
    proc.start()
    try:
        del db['proc_conn']
        print('[server] Proc conn deleted')
    except KeyError:
        pass
    try:
        del db['proc_monitor']
        print('[server] Proc monitor deleted')
    except KeyError:
        pass
    send('Experiment terminated.')


def dispatch(event):
    msg, data = event
    if msg == Msg.QUERY:
        query()
    elif msg == Msg.SET:
        set_timing(data)
    elif msg == Msg.GEN:
        gen_sequence()
    elif msg == Msg.START:
        start_experiment()
    elif msg == Msg.STOP:
        stop_experiment()
    elif msg == Msg.DEBUG:
        import pdb; pdb.set_trace()
