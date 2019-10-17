"""
"""
import os
import pickle
import time
import queue
import subprocess
import sys

import gpiozero
import yaml


# GPIO pin to control the MOSFET
PIN = 14
# The worker will report back to the manager every 5s
REPORT_TIME = 1


def run(sess_fp, conn):
    # Set cpu affinity
    # NOTE: Alpine linux doesn't have `taskset` so this
    # doesn't work in docker
    subprocess.run(['taskset', '-p', '-c', '0', str(os.getpid())])

    # Load the experiment info
    with open(sess_fp, 'r') as f:
        data = yaml.load(f)

    sequence = pickle.loads(data['sequence'])
    n = int(data['timing']['digital']['total'])
    resolution = float(data['timing']['resolution'])

    # Set up the gpio if
    device = gpiozero.DigitalOutputDevice(PIN, active_high=False)

    # Run the experiment
    p = round((REPORT_TIME / resolution) + 0.5)
    t0 = time.time()
    for i in range(n):
        # Try to get close to exact timing
        while True:
            t1 = time.time()
            if (t1 - t0) > resolution:
                break

        # Inform the boss of progress
        if i % p == 0:
            # Empty the queue first
            try:
                conn.get_nowait()
            except queue.Empty:
                pass
            conn.put_nowait(i)

        # Switch
        t0 = t1
        if sequence[i]:
            device.on()
        else:
            device.off()

    # Finish by dropping the pin
    device.off()

    # Report back to the governor that all is well in
    # workertown
    try:
        conn.get_nowait()
    except queue.Empty:
        pass
    conn.put_nowait(i)

    sys.exit()


def reset():
    device = gpiozero.DigitalOutputDevice(PIN, active_high=False)
    device.off()
