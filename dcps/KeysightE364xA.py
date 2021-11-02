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
#-----------------------------------------------------------------------------

# For future Python3 compatibility:
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

try:
    from . import SCPI
except:
    from SCPI import SCPI
    
import re
from time import sleep
import pyvisa as visa

class KeysightE364xA(SCPI):
    """Basic class for controlling and accessing a HP/Agilent/Keysight E364xA DC Power Supply.

       If the VISA resource string is of the form TCPIP[n]::*::23::SOCKET,
       it is assumed that the power supply is being accessed using a
       KISS-488 Ethernet to GPIB adapter
       (https://www.ebay.com/itm/114514724752) that is properly
       configured to access the power supply at its GPIB address
       (default is 5).
  
       If the VISA resource string is of the form TCPIP[n]::*::1234::SOCKET, 
       it is assumed that the power supply is being accessed using a
       Prologix Ethernet to GPIB adapter
       (http://prologix.biz/gpib-ethernet-controller.html). The
       Prologix has commands to set GPIB address and such.
  
       It should be possible to use this directly over GPIB or with a
       USB to GPIB interface by modifying the resource string but some
       minor code edits may be needed. For now, this code has only
       been tested with a KISS-488 or Prologix Ethernet to GPIB interface.

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

    def __init__(self, resource, gaddr=5, wait=0.25, verbosity=0, query_delay=0.75, **kwargs):
        """Init the class with the instruments resource string

        resource  - resource string or VISA descriptor, like TCPIP0::172.16.2.13::23::SOCKET
        gaddr     - GPIB bus address of instrument - this is only useful if using Prologix interface
        wait      - float that gives the default number of seconds to wait after sending each command
        verbosity - verbosity output - set to 0 for no debug output
        kwargs    - other named options to pass when PyVISA open() like open_timeout=2.0
        """

        # Set defaults
        self._enetgpib = False  # True if an Ethernet to GPIB interface is being used
        self._kiss488  = False  # True if the Ethernet to GPIB interface is a KISS-488
        self._prologix = False  # True if the Ethernet to GPIB interface is a Prologix
        
        ## regexp for resource string that indicates it is being used with KISS-488 or Prologix
        reskiss488  = re.compile("^TCPIP[0-9]*::.*::23::SOCKET$")
        resprologix = re.compile("^TCPIP[0-9]*::.*::1234::SOCKET$")
        if (reskiss488.match(resource)):
            self._enetgpib = True
            self._kiss488  = True
            if (query_delay < 1.5):
                ## Found that for KISS-488 Interface, query_delay must be at least 1.5
                query_delay = 1.5
        elif (resprologix.match(resource)):
            self._enetgpib = True
            self._prologix = True

        # save some parameters in case need it
        self._gaddr = gaddr
        self._query_delay = query_delay

        super(KeysightE364xA, self).__init__(resource, max_chan=1, wait=wait, cmd_prefix='',
                                             verbosity = verbosity,
                                             read_termination = '\n', write_termination = '\n',
                                             timeout=2, # found that needed longer timeout
                                             query_delay=query_delay,  # for open_resource()
                                             **kwargs)
    
    def open(self):
        """ Overloaded open() so can handle GPIB interfaces after opening the connection """

        super(KeysightE364xA, self).open()

        if (self._kiss488):
            # Give the instrument time to output whatever initial output it may send
            sleep(1.5)

            ## Can clear strings instead of reading and printing them out
            #@@@#self._inst.clear()

            # Read out any strings that are sent after connecting (happens
            # for KISS-488 and may happen with other interfaces)
            try:
                while True:
                    bytes = self._inst.read_raw()
                    if (self._kiss488):
                        # If the expected header from KISS-488, print it out, otherwise ignore.
                        if ('KISS-488'.encode() in bytes):
                            print(bytes.decode('utf-8').strip())
            except visa.errors.VisaIOError as err:
                if (err.error_code != visa.constants.StatusCode.error_timeout):
                    # Ignore timeouts here since just reading strings until they stop.
                    # Output any other errors
                    print("ERROR: {}, {}".format(err, type(err)))

        elif (self._prologix):
            # Configure mode, addr, auto and print out ver
            self._instWrite('++mode 1') # make sure in CONTROLLER mode
            self._instWrite('++auto 0') # will explicitly tell when to read instrument
            self._instWrite('++addr {}'.format(self._gaddr)) # set GPIB address
            self._instWrite('++eos 2') # append '\n' / LF to instrument commands
            self._instWrite('++eoi 1') # enable EOI assertion with commands
            self._instWrite('++read_tmo_ms 600') # Set the Read Timeout to 600 ms
            #@@@#self._instWrite('++eot_char 10') # @@@
            self._instWrite('++eot_enable 0') # Do NOT append character when EOI detected

            # Read and print out Version string. Using write/read to
            # void having '++read' appended if use Query. It is not
            # needed for ++ commands and causes a warning if used.
            self._instWrite('++ver')
            sleep(self._query_delay)
            print(self._inst.read())
            
        #@@@#self.printAllErrors()
        #@@@#self.cls()
            

    def _instQuery(self, queryStr):
        """ Overload _instQuery from SCPI.py so can append the \r if KISS-488 or add ++read if Prologix"""
        # Need to also strip out any leading or trailing white space from the response

        # KISS-488 requires queries to end in '\r' so it knows a response is expected
        if (self._kiss488):
            queryStr += '\r'
        elif (self._prologix):
            # Can use \n or 10 as terminator on reads but not faster than using eoi
            #queryStr += self._write_termination + '++read 10'
            queryStr += self._write_termination + '++read eoi'

        if self._verbosity >= 4:
            print("OUT/" + ":".join("{:02x}".format(ord(c)) for c in queryStr))            
        resp = super(KeysightE364xA, self)._instQuery(queryStr).strip()
        if self._verbosity >= 4:
            print("IN /" + ":".join("{:02x}".format(ord(c)) for c in resp))
            print(resp)
            
        return resp
        
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
        """If KISS-488, disable the system local command for the instrument
           If Prologix, issue GPIB command to unlock the front panel
        """

        if (self._kiss488):
            # NOTE: Unsupported command if using KISS-488 with this power
            # supply. However, instead of raising an exception and
            # breaking any scripts, simply return quietly.
            pass
        elif (self._prologix):
            self._instWrite('++loc') # issue GPIB command to enable front panel

    
    def setRemote(self):
        """If KISS-488, disable the system remote command for the instrument
           If Prologix, issue GPIB command to lock the front panel
        """

        if (self._kiss488):
            # NOTE: Unsupported command if using KISS-488 with this power supply. However,
            # instead of raising an exception and breaking any scripts,
            # simply return quietly.
            pass
        elif (self._prologix):
            self._instWrite('++llo') # issue GPIB command to disable front panel
    
    def setRemoteLock(self):
        """Disable the system remote lock command for the instrument"""
        # NOTE: Unsupported command by this power supply. However,
        # instead of raising an exception and breaking any scripts,
        # simply return quietly.
        pass

        
    
    ###################################################################
    # Commands Specific to E364x
    ###################################################################
    
    def displayMessageOn(self, top=True):
        """Enable Display Message - gets enabled with setDisplayMessage() so ignore this
        
           top     - Only a single display, so ignore this parameter
        """
        pass

    def displayMessageOff(self, top=True):
        """Disable Display Message
        
           top     - Only a single display, so ignore this parameter
        """

        self._instWrite('DISP:WIND1:TEXT:CLE')

            
    def setDisplayMessage(self, message, top=True):
        """Set and display the message for Display. Use displayMessageOff() to
           enable or disable message, respectively.
        
           message - message to set
           top     - Only a single display, so ignore this parameter

        """

        # Maximum of 11 characters for top message
        if (len(message) > 11):
            message = message[:11]
        self._instWrite('DISP:WIND1:TEXT "{}"'.format(message))

        
if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Access and control a HP/Agilent/Keysight E364xA DC Power Supply')
    parser.add_argument('chan', nargs='?', type=int, help='Channel to access/control (max channel: 1)', default=1)
    args = parser.parse_args()

    from time import sleep
    from os import environ
    import sys

    resource = environ.get('E364XA_VISA', 'TCPIP0::192.168.1.20::23::SOCKET')
    dcpwr = KeysightE364xA(resource, gaddr=5, verbosity=1, query_delay=0.75)
    dcpwr.open()

    # Reset to power on default - need to wait a little longer before proceeding
    dcpwr.rst(wait=1.0)
    
    print(dcpwr.idn())
    print()
    
    dcpwr.beeperOff()

    if 0:
        # For test and debug
        dcpwr._instWrite('VOLTage?\n++read eoi')
        sleep(0.25)
        print('VOLTage? response:', dcpwr._inst.read_raw())
        sleep(1.0)
        dcpwr._instWrite('VOLTage?\n++read 10')
        sleep(0.25)
        print('VOLTage? response:', dcpwr._inst.read_raw())
        sys.exit()
    
    # Set display messages - only 'top' message should work
    dcpwr.setDisplayMessage('Bottom Message', top=False)
    dcpwr.setDisplayMessage('All ur base ...', top=True)

    # Enable top one first
    dcpwr.displayMessageOn()
    sleep(1.0)
    dcpwr.displayMessageOn(top=False)
    sleep(2.0)

    # Disable bottom one first
    dcpwr.displayMessageOff(top=False)
    sleep(1.0)
    dcpwr.displayMessageOff(top=True)

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

    print("Changing Output Voltage to 3.55V and clearing OVP Trip")
    dcpwr.setVoltage(3.55)
    dcpwr.voltageProtectionClear()
    print('{:6.4f}V / {:6.4f}A (limit: {:6.4f}A)\n'.format(dcpwr.measureVoltage(), dcpwr.measureCurrent(), dcpwr.queryCurrent()))

    if (dcpwr.isVoltageProtectionTripped()):
        print("OVP is still TRIPPED - FAILURE\n")
    else:
        print("OVP is not TRIPPED as is expected\n")

    
    print("Restoring original Output Voltage setting")
    dcpwr.setVoltage(voltageSave)
    print('{:6.4f}V / {:6.4f}A (limit: {:6.4f}A)\n'.format(dcpwr.measureVoltage(), dcpwr.measureCurrent(), dcpwr.queryCurrent()))

    ## turn off the channel
    dcpwr.outputOff()

    dcpwr.beeperOn()

    ## return to LOCAL mode
    dcpwr.setLocal()
    
    dcpwr.close()
