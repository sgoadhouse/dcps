#!/usr/bin/env python

# Use to make power cycling easier

# For future Python3 compatibility:
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import sys

from time import sleep
import os
import binascii
import argparse
import random
import sys
#import tty, termios

# Print out command line for recording
print('Executed with:',' '.join(sys.argv))

# Parse command line arguments
parser = argparse.ArgumentParser()
parser.add_argument('--off', '-0', action='store_true', help='instead of power cycle, just turn off power')
parser.add_argument('--on', '-1', action='store_true', help='instead of power cycle, just turn on power')
parser.add_argument('--random_time', '-r', action='store_true', help='have power supply remain off for a random number of seconds (< 10s)')
locgroup = parser.add_mutually_exclusive_group(required=True)
locgroup.add_argument('--psa', '-a', action='store_true', help='use Power Supply A')
locgroup.add_argument('--psb', '-b', action='store_true', help='use Power Supply B')
locgroup.add_argument('--psc', '-c', action='store_true', help='use Power Supply C')

args = parser.parse_args()


if (args.psa):
    # For control of the Rigol Power Supply, channel 1
    from dcps import RigolDP800

    # open connection to power supply
    #@@@#pwr = RigolDP800('USB0::0x1AB1::0x0E11::DP8B153600499::INSTR', open_timeout=5.0, verbosity=1)
    pwr = RigolDP800('USB0::6833::3601::DP8B153600499::0::INSTR', open_timeout=5.0, verbosity=1)    
    pwrChan = 1
elif (args.psb):
    # For control of the Rigol Power Supply, channel 2
    from dcps import RigolDP800

    # open connection to power supply
    pwr = RigolDP800('USB0::0x1AB1::0x0E11::DP8B153600499::INSTR')
    pwrChan = 2
elif (args.psc):
    # For control of the Rigol Power Supply, channel 2
    from dcps import RigolDP800

    # open connection to power supply
    pwr = RigolDP800('USB0::0x1AB1::0x0E11::DP8B153600499::INSTR')
    pwrChan = 3
else:
    # Error - must pick a power supply
    print('ERROR, must choose a power supply!')
    sys.exit()
    
pwr.open()

print(pwr.idn())

#if not pwr.isOutputOn(pwrChan):
#    # Enable channel 
#    pwr.outputOn(pwrChan)

print('\n\nBefore any change ...')
print('Power Supply, channel {}, is {}: {:6.4f} V {:6.4f} A\n'.
      format(pwrChan,
             pwr.isOutputOn(pwrChan) and "ON" or "OFF",
             pwr.measureVoltage(pwrChan),
             pwr.measureCurrent(pwrChan)))

def dotSleep(seconds):
    """ Sleep for desired seconds and output a '.' for each full second that has expired """

    #fd = sys.stdin.fileno()
    #old_settings = termios.tcgetattr(fd)

    ctrlc = False
    try:
        while(seconds > 0):
            if (seconds > 1):
                per = 1
            else:
                per = seconds

            sleep(per)

            if (per == 1):
                print('.', end='')
                sys.stdout.flush()

            seconds -= per

        #try:
        #    tty.setcbreak(sys.stdin.fileno())
        #    ch = sys.stdin.read(1)
        #finally:
        #    termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        #
        #if (ch):
        #    print('ch=',ch,end='')
        #    sys.stdout.flush()

    except KeyboardInterrupt:
        #print('Got Ctrl-C')
        ctrlc = True

    return ctrlc


def powerCycle():
    if (args.random_time):
        time_off = random.uniform(1.5, 10.0)
    else:
        time_off = 1.5

    print('     Power Cycling with off time={:.2f}s  '.format(time_off), end='')
    sys.stdout.flush()

    # Disable channel
    pwr.outputOff(pwrChan)

    # give some time for power supply to enable its output
    if (dotSleep(time_off)):
        # If asked to Quit, then Quit
        print(' Quitting GBT Test as requested.\n')
        return 1

    # Enable channel 
    pwr.outputOn(pwrChan)

    print('P', end='')
    sys.stdout.flush()
    # give a second for power supply to enable its output
    if (dotSleep(1.0)):
        # If asked to Quit, then Quit
        print(' Quitting GBT Test as requested.\n')
        return 1

    # continue as normal
    return 0

if (args.on):
    print("Turning on channel {}".format(pwrChan))
    pwr.outputOn(pwrChan)
elif (args.off):
    print("Turning off channel {}".format(pwrChan))
    pwr.outputOff(pwrChan)
else:
    powerCycle()
    print()                         # add line feed

# return to LOCAL mode
pwr.setLocal()    

pwr.close()

