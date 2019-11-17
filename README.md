# pittl-ctlr
Raspberry Pi TTL Controller, 0.2.0
nGelwan | 2019

## Introduction
PiTTL is a collection of schematics and code which can be used to cheaply build a remotely-controllable random TTL sequence generator using a Raspberry Pi 4 (https://www.raspberrypi.org/products/raspberry-pi-4-model-b/) and a couple of additional hardware components. It consists of two parts, the PiTTL controller, contained in this repository, and the PiTTL client (https://github.com/edderkoppen/pittl-client). When pushed to the extreme, PiTTL supports generating sequences which run for at least a month consisting of pulses of less than 10ms duration. 

## Overview
The PiTTL controller is organised into several related hardware components and software services. These are the:
1. Manager
2. TTL Driver
3. LCD
4. Connectivity monitor

### The Manager
The manager provides the software API for commanding and interrogating the PiTTL controller. It is the mean by which a PiTTL client can command and interrogate a PiTTL controller.
### The TTL Driver
This software service leverages the use of the python library PiGPIO (http://abyz.me.uk/rpi/pigpio/) and a MOSFET to generate the ~4.4V square wave pulses consituting a TTL pulse train.

This software includes the routines to approximately sample from the collection of all subsets of the unit interval with fixed measure without measure-zero components. A resolution parameter specifies the accuracy (and memory burden) of the sampling routine, with asymptotic convergence to the ideal sampler. Once sampled, such a subset defines a pulse train via a mapping of the unit interval onto some interval (probably larger) interval of the time axis. Non-exhaustive texting has determined that *time \* resolution* reaches a practical minimum at ~1ms due to GPIO consdierations and that *time / resolution* reaches a practical maximum at ~0.2 \* 10\^9 due to memory considerations.

This software also contains routines to generate TTL-pulse trains of (ideally) arbitrary frequencey and duty-cycle, but as of 0.2.0 these have not been extensively tested.
### The LCD
The PiTTL HAT was designed with a HD44780 16colx2row LCD which can display information about connectivity and program progress without having to ssh into the Raspberry Pi or use the PiTTL client for interrogation.
### The Connectivity Monitor
The PiTTL controller was designed for ease of control in mind, and in that vein there is a service which supplies the primary ip address and interface that the Raspberry Pi controller is using to the LCD.

## Installation
### Components
If you don't have an already constructed PiTTL, one can be constructed relatively cheaply. The hardware for PiTTL has been designed like a Raspberry Pi HAT (https://www.raspberrypi.org/blog/introducing-raspberry-pi-hats/), to live on an auxiliary baord which talks to the Raspberry Pi via its GPIO headers. The schematics for the HAT are detailed in the **board** sub-repo (https://github.com/edderkoppen/pittl-ctlr/board), and can be viewed with EDA software. I used Eagle (https://www.autodesk.com/products/eagle/overview). The gerber files packaged in the **board** sub-repo can be supplied to a custom PCB-vendor in order to custom print the PCB for the HAT.
