#!/usr/bin/env python
# -*- coding: utf-8 -*-
#

# Copyright (c) 2021, Stephen Goadhouse <sgoadhouse@virginia.edu>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
 
#-----------------------------------------------------------------------------
#  Control a HP/Agilent/Keysight E364xA series DC Power Supplies with PyVISA
#  Assuming that a KISS-488 or equivalent Ethernet to GPIB interface is used
#-----------------------------------------------------------------------------

# For future Python3 compatibility:
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

try:
    from . import SCPI
except:
    from SCPI import SCPI
    
from time import sleep
import pyvisa as visa

class KeysightE364xA(SCPI):
    """Basic class for controlling and accessing a HP/Agilent/Keysight E364xA DC Power Supply.

       It is assumed that the power supply is being accessed using a KISS-488 Ethernet to GPIB 
       adapter (https://www.ebay.com/itm/114514724752) that is properly configured to access 
       the power supply at its GPIB address (default is 5).
  
       It should be possible to use this directly over GPIB by modifying the resource string 
       but some minor code edits may be needed. For now, this code has only been tested with 
       a KISS-488 Ethernet to GPIB interface.
    """

    ## Dictionary to translate SCPI commands for this device
    _xlateCmdTbl = {
        'isOutput':                  'OUTPut?',
        'outputOn':                  'OUTPut ON',
        'outputOff':                 'OUTPut OFF',
        'setVoltage':                'VOLTage {}',
        'setCurrent':                'CURRent {}',
        'queryVoltage':              'VOLTage?',
        'queryCurrent':              'CURRent?',
        'measureVoltage':            'MEASure:VOLTage?',
        'measureCurrent':            'MEASure:CURRent?',
        'setVoltageProtection':      'VOLTage:PROTection:LEVel {}',
        'queryVoltageProtection':    'VOLTage:PROTection:LEVel?',
        'voltageProtectionOn':       'VOLTage:PROTection:STATe ON',
        'voltageProtectionOff':      'VOLTage:PROTection:STATe OFF',
    }

    def __init__(self, resource, wait=0.1, verbosity=0):
        """Init the class with the instruments resource string

        resource - resource string or VISA descriptor, like TCPIP0::172.16.2.13::INSTR
        wait     - float that gives the default number of seconds to wait after sending each command
        """
        super(KeysightE364xA, self).__init__(resource, max_chan=1, wait=wait, cmd_prefix='',
                                             verbosity = verbosity,
                                             read_termination = '\n', write_termination = '\n',
                                             timeout=3, query_delay=2) # for open_resource()
    
    def _instQuery(self, queryStr):
        """ KISS-488 requires queries to end in '\r' so it knows a response is expected """
        # Overload _instQuery from SCPI.py so can append the \r
        # Need to also strip out any leading or trailing white space from the response
        return super(KeysightE364xA, self)._instQuery(queryStr+'\r').strip()
        
    def open(self):
        """ Overloaded open() so can read out the extra two lines after opening the connection """

        super(KeysightE364xA, self).open()

        sleep(0.5)

        ## Can clear strings instead of reading and printing them out
        #@@@#self._inst.clear()

        # The initial header from KISS-488 should be 2 lines - just read them and print to screen
        try:
            while True:
                bytes = self._inst.read_raw()
                # If the expected header from KISS-488, print it out, otherwise ignore.
                # Need to do this because Keysight E3642A prints out a garbage string after connecting to it
                if ('KISS-488'.encode() in bytes):
                    print(bytes.decode('utf-8').strip())
        except visa.errors.VisaIOError as err:
            if (err.error_code != visa.constants.StatusCode.error_timeout):
                # Ignore timeouts here since just reading strings until they stop.
                # Output any other errors
                print(f"ERROR: {err}, {type(err)}")

            #@@@#self.printAllErrors()
            self.cls()
            

    def beeperOn(self):
        """Enable the system beeper for the instrument"""
        # NOTE: Unsupported command by this power supply. However,
        # instead of raising an exception and breaking any scripts,
        # simply return quietly.
        pass
        
    def beeperOff(self):
        """Disable the system beeper for the instrument"""
        # NOTE: Unsupported command by this power supply. However,
        # instead of raising an exception and breaking any scripts,
        # simply return quietly.
        pass
        
    def setLocal(self):
        """Disable the system local command for the instrument"""
        # NOTE: Unsupported command by this power supply. However,
        # instead of raising an exception and breaking any scripts,
        # simply return quietly.
        pass
    
    def setRemote(self):
        """Disable the system remote command for the instrument"""
        # NOTE: Unsupported command by this power supply. However,
        # instead of raising an exception and breaking any scripts,
        # simply return quietly.
        pass
    
    def setRemoteLock(self):
        """Disable the system remote lock command for the instrument"""
        # NOTE: Unsupported command by this power supply. However,
        # instead of raising an exception and breaking any scripts,
        # simply return quietly.
        pass

        
if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Access and control a HP/Agilent/Keysight E364xA DC Power Supply')
    parser.add_argument('chan', nargs='?', type=int, help=f'Channel to access/control (max channel: 1)', default=1)
    args = parser.parse_args()

    from time import sleep
    from os import environ
    import sys

    resource = environ.get('E364XA_VISA', 'TCPIP0::192.168.1.20::23::SOCKET')
    dcpwr = KeysightE364xA(resource)
    dcpwr.open()

    # Reset to power on default
    dcpwr.rst()        
    
    print(dcpwr.idn())
    print()
    
    dcpwr.beeperOff()
    
    if not dcpwr.isOutputOn(args.chan):
        dcpwr.outputOn()
        
    print('Ch. {} Settings: {:6.4f} V  {:6.4f} A'.
              format(args.chan, dcpwr.queryVoltage(),
                         dcpwr.queryCurrent()))

    voltageSave = dcpwr.queryVoltage()
    
    print('{:6.4f}V / {:6.4f}A (limit: {:6.4f}A)\n'.format(dcpwr.measureVoltage(), dcpwr.measureCurrent(), dcpwr.queryCurrent()))

    print("Changing Output Voltage to 2.7V")
    dcpwr.setVoltage(2.7)
    print('{:6.4f}V / {:6.4f}A (limit: {:6.4f}A)\n'.format(dcpwr.measureVoltage(), dcpwr.measureCurrent(), dcpwr.queryCurrent()))
    
    print("Changing Output Voltage to 2.3V and current to 1.3A")
    dcpwr.setVoltage(2.3)
    dcpwr.setCurrent(1.3)
    print('{:6.4f}V / {:6.4f}A (limit: {:6.4f}A)\n'.format(dcpwr.measureVoltage(), dcpwr.measureCurrent(), dcpwr.queryCurrent()))

    print("Set Over-Voltage Protection to 3.6V")
    dcpwr.setVoltageProtection(3.6)
    print('OVP: {:6.4f}V\n'.format(dcpwr.queryVoltageProtection()))

    dcpwr.voltageProtectionOff()
    
    print("Changing Output Voltage to 3.7V with OVP off")
    dcpwr.setVoltage(3.7)
    print('{:6.4f}V / {:6.4f}A (limit: {:6.4f}A)\n'.format(dcpwr.measureVoltage(), dcpwr.measureCurrent(), dcpwr.queryCurrent()))

    if (dcpwr.isVoltageProtectionTripped()):
        print("OVP is TRIPPED but should NOT be - FAILURE\n")
    else:
        print("OVP is not TRIPPED as expected\n")
        
    print("Enable OVP")
    dcpwr.voltageProtectionOn()
    
    if (dcpwr.isVoltageProtectionTripped()):
        print("OVP is TRIPPED as expected.\n")
    else:
        print("OVP is not TRIPPED but is SHOULD be - FAILURE\n")

    print("Changing Output Voltage to 3.58V and clearing OVP Trip")
    dcpwr.setVoltage(3.58)
    dcpwr.voltageProtectionClear()
    print('{:6.4f}V / {:6.4f}A (limit: {:6.4f}A)\n'.format(dcpwr.measureVoltage(), dcpwr.measureCurrent(), dcpwr.queryCurrent()))
        
    print("Restoring original Output Voltage setting")
    dcpwr.setVoltage(voltageSave)
    print('{:6.4f}V / {:6.4f}A (limit: {:6.4f}A)\n'.format(dcpwr.measureVoltage(), dcpwr.measureCurrent(), dcpwr.queryCurrent()))

    ## turn off the channel
    dcpwr.outputOff()

    dcpwr.beeperOn()

    ## return to LOCAL mode
    dcpwr.setLocal()
    
    dcpwr.close()
