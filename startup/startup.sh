#!/bin/sh
echo $PYTHONPATH
pip3 freeze
export PYTHONPATH=/home/pi/bind/pittl/code
echo $PYTHONPATH
python3 /home/pi/bind/pittl/startup/startup.py
