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
#  Control a Keithley/Tektronix 622x series Precision Current Source
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

class Keithley622x(SCPI):
    """Basic class for controlling and accessing a Keithley/Tektronix 622x
       series Precision Current Source. Although this is not a
       traditional DC power supply, it uses many of the same interface
       commands so including here seems logical.

       If the VISA resource string is of the form TCPIP[n]::*::23::SOCKET,
       it is assumed that the power supply is being accessed using a
       KISS-488 Ethernet to GPIB adapter
       (https://www.ebay.com/itm/114514724752) that is properly
       configured to access the power supply at its GPIB address
       (default is 12).
  
       If the VISA resource string is of the form TCPIP[n]::*::1234::SOCKET, 
       it is assumed that the power supply is being accessed using a
       Prologix Ethernet to GPIB adapter
       (http://prologix.biz/gpib-ethernet-controller.html). The
       Prologix has commands to set GPIB address and such.
  
       It should be possible to use this directly over GPIB or with a
       USB to GPIB interface by modifying the resource string but some
       minor code edits may be needed. For now, this code has only
       been tested with a KISS-488 or Prologix Ethernet to GPIB interface.

       Currently, could not get the KISS-488 interface to fully
       support the Keithley 622x although it works with other
       devices. So recommend to only attempt to use the Prologix with
       the 622x.

    """

    ## Dictionary to translate SCPI commands for this device
    _xlateCmdTbl = {
#        'isOutput':                  'OUTP?',
#        'outputOn':                  'OUTPut ON',
#        'outputOff':                 'OUTPut OFF',
        'setCurrent':                'SOURce:CURRent:RANGe {0:.2e}\nSOURce:CURRent {0:.2e}',
        'setVoltageProtection':      'SOURce:CURRent:COMPliance {}', # not exactly the same but analogous
    }

    def __init__(self, resource, gaddr=12, wait=0.25, verbosity=0, query_delay=0.75, **kwargs):
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
        elif (resprologix.match(resource)):
            self._enetgpib = True
            self._prologix = True

        # save some parameters in case need it
        self._gaddr = gaddr
        self._query_delay = query_delay

        super(Keithley622x, self).__init__(resource, max_chan=1, wait=wait, cmd_prefix='',
                                           verbosity = verbosity,
                                           read_termination = '\n', write_termination = '\n',
                                           timeout=2, # found that needed longer timeout
                                           query_delay=query_delay,  # for open_resource()
                                           **kwargs)
    
    def open(self):
        """ Overloaded open() so can handle GPIB interfaces after opening the connection """

        super(Keithley622x, self).open()

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
            queryStr += self._write_termination + '++read eoi'

        if self._verbosity >= 4:
            print("OUT/" + ":".join("{:02x}".format(ord(c)) for c in queryStr))            
        resp = super(Keithley622x, self)._instQuery(queryStr).strip()
        if self._verbosity >= 4:
            print("IN /" + ":".join("{:02x}".format(ord(c)) for c in resp))
            print(resp)
            
        return resp
        
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

    def setVoltage(self, voltage, channel=None, wait=None):
        """The 622x has no way to set the output voltage. Ignoring command.
        
           voltage - desired voltage value as a floating point number
           wait    - number of seconds to wait after sending command
           channel - number of the channel starting at 1
        """
        print('NOTE: The Keithley 622x cannot set a voltage. Perhaps you meant setVoltageProtection()?.\nIgnoring this command')

    def queryVoltage(self, channel=None):
        """The 622x has no way to query the output voltage setting. Return invalid value.
        
        channel - number of the channel starting at 1
        """
        return (SCPI.NaN)
    
    def queryCurrent(self, channel=None):
        """The 622x has no way to query the output current setting. Return invalid value.
        
        channel - number of the channel starting at 1
        """
        return (SCPI.NaN)
        
    def measureVoltage(self, channel=None):
        """The 622x performs no measurements so override this command
        
           channel - number of the channel starting at 1
        """
        print('NOTE: The Keithley 622x performs no measurements of its own. Ignoring this command')
        return (SCPI.NaN)

    def measureCurrent(self, channel=None):
        """The 622x performs no measurements so override this command
        
           channel - number of the channel starting at 1
        """
        print('NOTE: The Keithley 622x performs no measurements of its own. Ignoring this command')
        return (SCPI.NaN)

    def queryVoltageProtection(self, channel=None):
        """The 622x has no way to query the output voltage protection/compliance setting. Return invalid value.
        
        channel - number of the channel starting at 1
        """
        return (SCPI.NaN)

    def voltageProtectionOn(self, channel=None, wait=None):
        """The 622x always has voltage protection/compliance. Ignore command.
        
           wait    - number of seconds to wait after sending command
           channel - number of the channel starting at 1
        """
        pass
        
    def voltageProtectionOff(self, channel=None, wait=None):
        """The 622x always has voltage protection/compliance. Ignore command.
        
           channel - number of the channel starting at 1
        """
        pass

    def voltageProtectionClear(self, channel=None, wait=None):
        """The 622x always has voltage protection/compliance. Ignore command.
        
           channel - number of the channel starting at 1
        """
        pass
    
    def isVoltageProtectionTripped(self, channel=None):
        """The 622x cannot tell if the compliance limit has been reached or
           not.  So always return True so if someone uses this,
           hopefully the True will force them to figure out what is
           going on.
        
           channel - number of the channel starting at 1

        """
        return True
    
    ###################################################################
    # Commands Specific to 622x
    ###################################################################
    
    def displayMessageOn(self, top=True):
        """Enable Display Message
        
           top     - True if enabling the Top message, else enable Bottom message
        """

        if (top):
            self._instWrite('DISP:TEXT:STAT ON')
        else:
            self._instWrite('DISP:WIND2:TEXT:STAT ON')

    def displayMessageOff(self, top=True):
        """Disable Display Message
        
           top     - True if disabling the Top message, else disable Bottom message
        """

        if (top):
            self._instWrite('DISP:TEXT:STAT OFF')
        else:
            self._instWrite('DISP:WIND2:TEXT:STAT OFF')

            
    def setDisplayMessage(self, message, top=True):
        """Set the Message for Display. Use displayMessageOn() or
           displayMessageOff() to enable or disable message, respectively.
        
           message - message to set
           top     - True if setting the Top message, else set Bottom message

        """

        if (top):
            # Maximum of 20 characters for top message
            if (len(message) > 20):
                message = message[:20]
            self._instWrite('DISP:TEXT "{}"'.format(message))
        else:
            # Maximum of 32 characters for bottom message
            if (len(message) > 32):
                message = message[:32]
            self._instWrite('DISP:WIND2:TEXT "{}"'.format(message))

    def isInterlockTripped(self):
        """Return true if the Interlock is Tripped, else false
        """

        ret = self._instQuery('OUTP:INT:TRIP?')
        # For whatever reason, command returns '0' if interlock is
        # tripped, so logical invert it
        return (not self._onORoff_1OR0_yesORno(ret))
            
            
if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Access and control a Keithley/Tektronix 622x series Precision Current Source')
    parser.add_argument('chan', nargs='?', type=int, help='Channel to access/control (max channel: 1)', default=1)
    args = parser.parse_args()

    from time import sleep
    from os import environ
    import sys

    resource = environ.get('K622X_VISA', 'TCPIP0::192.168.1.20::23::SOCKET')
    currsrc = Keithley622x(resource, gaddr=12, verbosity=1, query_delay=0.75)
    currsrc.open()

    # Reset to power on default
    currsrc.rst()        

    print(currsrc.idn())
    print()
    
    currsrc.beeperOff()

    if 0:
        # For test and debug
        currsrc._instWrite('OUTPut?\n++read eoi')
        sleep(2.0)
        print('OUTP? response:', currsrc._inst.read_raw())
        print('OUTP? response:', currsrc._inst.read_raw())
        print('OUTP? response:', currsrc._inst.read_raw())
        print('OUTP? response:', currsrc._inst.read_raw())

    # Set display messages
    currsrc.setDisplayMessage('Bottom Message', top=False)
    currsrc.setDisplayMessage('Top Message', top=True)

    # Enable top one first
    currsrc.displayMessageOn()
    sleep(1.0)
    currsrc.displayMessageOn(top=False)
    sleep(2.0)

    # Disable bottom one first
    currsrc.displayMessageOff(top=False)
    sleep(1.0)
    currsrc.displayMessageOff(top=True)

    if currsrc.isInterlockTripped():
        print('Interlock is tripped. Stopping')
        sys.exit()
    else:
        print('Interlock is NOT tripped. Continuing')


    ## NOTE: Most of the following functions are attempting to treat
    ## the 622x like a power supply. The 622x will either ignore most
    ## of these or return SCPI.NaN. These functions are here mainly to
    ## make sure that these unused functions are handled cleanly.
    
    print('Ch. {} Settings: {:6.4f} V  {:6.4f} A'.
              format(args.chan, currsrc.queryVoltage(),
                         currsrc.queryCurrent()))

    voltageSave = currsrc.queryVoltage()
    
    print('{:6.4f}V / {:6.4f}A (limit: {:6.4f}A)\n'.format(currsrc.measureVoltage(), currsrc.measureCurrent(), currsrc.queryCurrent()))

    print("Changing Output Voltage to 2.3V")
    currsrc.setVoltage(2.3)
    print('{:6.4f}V / {:6.4f}A (limit: {:6.4f}A)\n'.format(currsrc.measureVoltage(), currsrc.measureCurrent(), currsrc.queryCurrent()))

    print("Set Over-Voltage Protection to 3.6V")
    currsrc.setVoltageProtection(3.6)
    print('OVP: {:6.4f}V\n'.format(currsrc.queryVoltageProtection()))

    currsrc.voltageProtectionOff()
    
    print("Changing Output Voltage to 3.7V with OVP off")
    currsrc.setVoltage(3.7)
    print('{:6.4f}V / {:6.4f}A (limit: {:6.4f}A)\n'.format(currsrc.measureVoltage(), currsrc.measureCurrent(), currsrc.queryCurrent()))

    if (currsrc.isVoltageProtectionTripped()):
        print("OVP is TRIPPED as expected\n")
    else:
        print("OVP is not TRIPPED - FAILURE!\n")
        
    print("Enable OVP")
    currsrc.voltageProtectionOn()
    
    if (currsrc.isVoltageProtectionTripped()):
        print("OVP is TRIPPED as expected.\n")
    else:
        print("OVP is not TRIPPED - FAILURE!\n")

    print("Changing Output Voltage to 3.55V and clearing OVP Trip")
    currsrc.setVoltage(3.55)
    currsrc.voltageProtectionClear()
    print('{:6.4f}V / {:6.4f}A (limit: {:6.4f}A)\n'.format(currsrc.measureVoltage(), currsrc.measureCurrent(), currsrc.queryCurrent()))

    if (currsrc.isVoltageProtectionTripped()):
        print("OVP is TRIPPED as expected.\n")
    else:
        print("OVP is not TRIPPED - FAILURE!\n")

    ## Now, lets get to what 622x can actually do
    test_list = [(105e-3,0.1), (-105e-3,0.2), (1e-10,0.3), (-2.3e-12,1.4), (-567e-15,1.5), (50e-15,1.6), ]

    for vals in test_list:
        currsrc.setCurrent(vals[0])
        currsrc.setVoltageProtection(vals[1])

        if not currsrc.isOutputOn(args.chan):
            currsrc.outputOn()

        print ("Expect to see CURRENT set to {:3.4G} and Compliance set to {:3.4G}".format(*vals))

        sleep (2.0)
        currsrc.outputOff()    
        
    currsrc.beeperOn()

    ## return to LOCAL mode
    currsrc.setLocal()
    
    currsrc.close()
