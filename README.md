# pittl-ctlr
Raspberry Pi TTL Controller, 0.2.0  
nGelwan | 2019

## Introduction
PiTTL is a collection of schematics and code which can be used to cheaply build a remotely-controllable random TTL sequence generator using a Raspberry Pi 4 (https://www.raspberrypi.org/products/raspberry-pi-4-model-b/) and a couple of additional hardware components. It consists of two parts, the PiTTL controller, contained in this repository, and the PiTTL client (https://github.com/edderkoppen/pittl-client). When pushed to the extreme, PiTTL supports generating sequences which run for at least a month consisting of pulses of less than 10ms duration. 

## Overview
### Usage
PiTTL can be used to stage and then generate individual sequences of TTL pulses, called **programs**. Generating-- also known as **staging**-- a program is a two-step process: first, the **timing** of the program is staged, and then the program's **sequence** is staged. If a sequence has been successfully staged, a program can be **started** and **stopped** at will.

**Timing** is specified with 3 parameters: the **total time**, **exposure fraction**, and **resolution**. Total time is the desired length of the program, exposure fraction is the desired fraction of the program during which TTL-on logic will occur, and resolution is the minimum width of a TTL-on pulse. The resolution parameter is *very* important. It drastically simplifies the algorithm for generating random sequences of pulses satisfying the desired exposure fraction. It is important to note that when these three parameters are supplied to PiTTL, that total time and exposure fraction will be adjusted so that the time spent in TTL-on and TTL-off are both integer multiples of the resolution, and so that they are as close to the values specified as possible. Thus, after staging, timing is converted into the **specified**, **adjusted**, and **digital** domains. The specified timing consists of those floating point values requested, adjusted are those values after adjustment for resolution, and digital are those values in integral units of resolution.

A **sequence** is literally a binary sequence representing the TTL-logic time-series of the program. PiTTL can be induced to randomly generate a sequence based on any valid staged timing. If a sequence has been staged and new timing is then staged, the two are then unrelated, and the staged sequence is purged.

Once a program has been **started**, the timing and the sequence are considered **committed**. New sequences and timing can be staged without interrupting the running program.

PiTTL is capable of evaluating the **progress** and **ETA** of a currently running program, and also **stopping** a program, clearing any committed timings and sequences.

This functionality is implemented via PiTTL controller's python API and publicly via the combination of the PiTTL controller's manager service and the PiTTL client (https://github.com/edderkoppen/pittl-client).

#### Troubleshooting
If the PiTTL controller is not behaving as expected (usually indicated by oddities displayed on the HAT's LCD), or has encountered an error, the most robust way to fix the problem is to cycle the power on the Raspberry Pi. There has not yet been implemented a robust software means of resetting the pittld service.

If problems persist, the software repository should be updated and the service reinstalled. If further problems persist, a fresh Raspbian should be installed. 

### Details
The PiTTL controller is organised into several related hardware components and software services. These are the:
1. Manager
2. TTL Driver
3. LCD
4. Connectivity monitor

The software services are packaged under the name **pittld**, for PiTTL Daemon.
### The Manager
The manager provides a public endpoint for communicating with a PiTTL controller. It is the means by which a PiTTL client can command a PiTTL controller to stage timing and sequences and to start and stop programs, and also the means by which a PiTTL client can query a PiTTL controller for any staged or committed timing or sequences, or the progress of any running program.
### The TTL Driver
This software service leverages the use of the python library PiGPIO (http://abyz.me.uk/rpi/pigpio/) and a MOSFET to generate the ~4.4V square wave pulses consituting a TTL pulse train.

This software includes the routines to approximately sample from the collection of all subsets of the unit interval with fixed measure without measure-zero components. A resolution parameter (defining the minimum width of a sampled pulse) specifies the accuracy (and memory burden) of the sampling routine, with asymptotic convergence to the ideal sampler upon decreasing the parameter. Once sampled, such a subset defines a pulse train via a mapping of the unit interval onto some interval (probably larger) interval of the time axis. Non-exhaustive testing has determined that *time \* resolution* reaches a practical minimum at ~10^-3 s^2 due to GPIO consdierations and that *time / resolution* reaches a practical maximum at ~0.2 \* 10\^9 due to memory considerations.

This software also contains routines to generate TTL-pulse trains of (ideally) arbitrary frequencey and duty-cycle, but as of 0.2.0 these have not been extensively tested.
### The LCD
The PiTTL HAT was designed with a HD44780 16colx2row LCD which can convey information about connectivity and program progress without having to use the python API, pittld logs, or PiTTL client.
### The Connectivity Monitor
The connectivity monitor supplies pittld with information regarding internet connectivity.

## Installation
### HAT Construction
If you don't have an already constructed PiTTL, one can be constructed relatively cheaply. The hardware for PiTTL has been designed like a Raspberry Pi HAT (https://www.raspberrypi.org/blog/introducing-raspberry-pi-hats/), to live on an auxiliary baord which talks to the Raspberry Pi via its GPIO headers. The schematics for the HAT are detailed in the **board** sub-repo (https://github.com/edderkoppen/pittl-ctlr/board), and can be viewed with EDA software. I used Eagle (https://www.autodesk.com/products/eagle/overview). The gerber files packaged in the **board** sub-repo can be supplied to a custom PCB-vendor in order to custom print the PCB for the HAT.

### Software Installation
One may install the PiTTL controller software on any Raspberry Pi, although the software has only been tested with the Raspberry Pi 4, and the practical limitation of the TTL driver listed above are given in the context of the hardware on a Raspberry Pi 4. Presumably, the software will function on a variety of operating systems, but certain features have been designed with Raspbian in mind (e.g. automatic start using systemd).

The only software prerequisites for the installation of pittld are python >=3.4, python setuptools, and a C-compiler for the compilation of pigpio. To setup and install the software, a very rudimentary shell script *setup/setup.sh* is provided, which should be run as root. Be warned, the setup script is non-transactional and doesn't try very hard to catch errors, so one should pay attention closely to stdout during the installation. If setup completes successfully, pittld may be started by entering

>*pittld*

at the command-line or-- assuming the installation of the systemd units succeeded-- automatically upon restart of the Raspberry Pi. The logs for pittld can be followed with  

>*journalctl -f -u pittld*

on Raspbian. Confirmation that pittld is running successfully can be found in journalctl or by observing the updates on the HAT's LCD.
