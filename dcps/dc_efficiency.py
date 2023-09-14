#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright (c) 2017, Emmanuel Blot <emmanuel.blot@free.fr>
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#     * Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#     * Neither the name of the Neotion nor the names of its contributors may
#       be used to endorse or promote products derived from this software
#       without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL NEOTION BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA,
# OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE,
# EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

from binascii import hexlify
import argparse
#@@@#from doctest import testmod
from os import environ
import PowerTestBoard
import BK9115

#@@@#from i2cflash.serialeeprom import SerialEepromManager
from sys import modules, stdout
#@@@#from math import floor
import logging
#@@@#import unittest
from time import sleep

#@@@#ftdi_url = 'ftdi://ftdi:4232h/1'
ftdi_url_const = 'ftdi://ftdi:4232:FTK1RRYC/1'


def poweron():
    """Set the BK 9115 DC power supply to 12.000V with a reasonable current limit and enable the power.
    """

    resource = environ.get('BK9115_USB', 'USB0::INSTR')
    bkps = BK9115.BK9115(resource)
    bkps.open()

    print(bkps.idn())

    # IMPORTANT: 9115 requires Remote to be set or else commands are ignored
    bkps.setRemote()
    
    ## set Remote Lock On
    #bkps.setRemoteLock()
    
    bkps.beeperOff()

    # BK Precision 9115 has a single channel, so force chan to be 1
    chan = 1

    bkps.outputOff()
        
    bkps.setCurrent(5)
    bkps.setVoltage(12.0)
    bkps.setVoltageProtection(16.0)
    
    print('BK9115 Settings: {:6.4f} V  {:6.4f} A'.
              format(bkps.queryVoltage(),
                     bkps.queryCurrent()))

    bkps.outputOn()
    sleep(1)
    print('BK9115 Values:   {:6.4f} V  {:6.4f} A'.
              format(bkps.measureVoltage(),
                     bkps.measureCurrent()))
    
    ## return to LOCAL mode
    bkps.setLocal()
    
    bkps.close()
    
def poweroff():
    """Disable the BK 9115 DC power supply output.
    """

    resource = environ.get('BK9115_USB', 'USB0::INSTR')
    bkps = BK9115.BK9115(resource)
    bkps.open()

    # IMPORTANT: 9115 requires Remote to be set or else commands are ignored
    bkps.setRemote()
    
    # BK Precision 9115 has a single channel, so force chan to be 1
    chan = 1

    bkps.outputOff()
        
    ## return to LOCAL mode
    bkps.setLocal()
    
    bkps.close()

def powerValues():
    """Get the Voltage and Current values from the BK 9115 DC power supply output.
    """

    resource = environ.get('BK9115_USB', 'USB0::INSTR')
    bkps = BK9115.BK9115(resource)
    bkps.open()

    # IMPORTANT: 9115 requires Remote to be set or else commands are ignored
    bkps.setRemote()
    
    # BK Precision 9115 has a single channel, so force chan to be 1
    chan = 1

    voltage = bkps.measureVoltage()
    current = bkps.measureCurrent()
    
    #@@@#print('BK9115 Values:   {:6.4f} V  {:6.4f} A'.format(voltage,current))
            
    ## return to LOCAL mode
    bkps.setLocal()
    
    bkps.close()

    return (voltage, current)

def DCEfficiency(PTB,circuit):

    PTB.powerEnable(circuit,True)
    sleep(1)
    
    print('BK9115 Values:   {:6.4f} V  {:6.4f} A'.format(*powerValues()))

    sleep(1)
    PTB.powerEnable(circuit,False)
    
    
if __name__ == '__main__':
    #@@@#testmod(modules[__name__])

    ptb = PowerTestBoard.PowerTestBoard(environ.get('FTDI_DEVICE', ftdi_url_const))
            
    parser = argparse.ArgumentParser(description='Measure the DC Efficiency of the selected DC Circuits on the Power Test Board')

    # Choose EITHER ON or OFF and the circuits on the command line
    # will be enabled or disable. If neither of these is selected,
    # then get status of all circuits.
    #@@@#mutex_grp = parser.add_mutually_exclusive_group(required=False)        
    #@@@#mutex_grp.add_argument('-1', '--on',  action='store_true', help='enable/turn ON the circuits')
    #@@@#mutex_grp.add_argument('-0', '--off', action='store_true', help='disable/turn OFF the circuits')


    parser.add_argument('list_of_circuits', metavar='circuits', type=ptb.validate_circuits, nargs='*', help='a list of circuits - or all if omitted')
    
    args = parser.parse_args()

    try:
        poweron()
        
        circuit_list = args.list_of_circuits

        # If no list given, then use all circuits
        if len(circuit_list) <= 0:
            circuit_list = ptb.circuits.keys()
        
        for circ in circuit_list:
            DCEfficiency(ptb, ptb.circuits[circ])

        poweroff()
                
        #@@@#test_i2c_gpio()

        #powerEnable(0,0)
        #powerEnable(1,0)
        #powerEnable(2,0)
        #powerEnable(3,0)
    
        #powerEnable(4,0)
        #powerEnable(5,0)
        #powerEnable(6,0)
        #powerEnable(7,0)
        
        #powerEnable(8,0)
        #powerEnable(9,0)
        #powerEnable(10,0)
        #powerEnable(11,0)

    except KeyboardInterrupt:
        exit(2)
