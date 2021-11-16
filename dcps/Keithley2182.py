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
#  Control a Keithley/Tektronix 2182/2182A Nanovoltmeter
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

class Keithley2182(SCPI):
    """Basic class for controlling and accessing a Keithley/Tektronix
       2182/2182A Nanovoltmeter. Although this is not a traditional DC
       power supply, it uses many of the same interface commands so
       including here seems logical.

       If the VISA resource string is of the form TCPIP[n]::*::23::SOCKET,
       it is assumed that the power supply is being accessed using a
       KISS-488 Ethernet to GPIB adapter
       (https://www.ebay.com/itm/114514724752) that is properly
       configured to access the power supply at its GPIB address
       (default is 7).
  
       If the VISA resource string is of the form TCPIP[n]::*::1234::SOCKET, 
       it is assumed that the power supply is being accessed using a
       Prologix Ethernet to GPIB adapter
       (http://prologix.biz/gpib-ethernet-controller.html). The
       Prologix has meta-commands to set GPIB address and such.
  
       It should be possible to use this directly over GPIB or with a
       USB to GPIB interface by modifying the resource string but some
       minor code edits may be needed. For now, this code has only
       been tested with a KISS-488 or Prologix Ethernet to GPIB interface.

       Currently, could not get the KISS-488 interface to fully
       support the Keithley 2182 although it works with other devices.
       The Prologix interface worked great with the 2182.

    """

    ## Dictionary to translate SCPI commands for this device
    _xlateCmdTbl = {
        'chanSelect':                'SENS:CHAN {}',
    }

    def __init__(self, resource, gaddr=7, wait=0.25, verbosity=0, query_delay=0.8, **kwargs):
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

        super(Keithley2182, self).__init__(resource, max_chan=2, wait=wait, cmd_prefix=':',
                                           verbosity = verbosity,
                                           read_termination = '\n', write_termination = '\n',
                                           timeout=2, # found that needed longer timeout
                                           query_delay=query_delay,  # for open_resource()
                                           **kwargs)

        # NaN for this instrument
        self.NaN = +9.9E37

    
    def open(self):
        """ Overloaded open() so can handle GPIB interfaces after opening the connection """

        super(Keithley2182, self).open()

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
            self._instWrite('++read_tmo_ms 1200') # Set the Read Timeout to 1200 ms
            #@@@#self._instWrite('++eot_char 10') # @@@
            self._instWrite('++eot_enable 0') # Do NOT append character when EOI detected

            # Read and print out Version string. Using write/read to
            # avoid having '++read' appended if use Query. It is not
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
        resp = super(Keithley2182, self)._instQuery(queryStr).strip()
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
        """The 2182 has no way to set the output voltage. Ignoring command.
        
           voltage - desired voltage value as a floating point number
           wait    - number of seconds to wait after sending command
           channel - number of the channel starting at 1
        """
        print('NOTE: The Keithley 2182 cannot set a voltage. It can only measure voltages.\nIgnoring this command')

    def queryVoltage(self, channel=None):
        """The 2182 has no way to query the output voltage setting. Return invalid value.
        
        channel - number of the channel starting at 1
        """
        # If a channel number is passed in, make it the
        # current channel
        if channel is not None:
            self.channel = channel
            
        if (self._max_chan > 1 and channel is not None):
            # If multi-channel device and channel parameter is passed, select it
            self._instWrite(self._Cmd('chanSelect').format(self.channel))

        return (self.NaN)
    
    def queryCurrent(self, channel=None):
        """The 2182 has no way to query the output current setting. Return invalid value.
        
        channel - number of the channel starting at 1
        """
        # If a channel number is passed in, make it the
        # current channel
        if channel is not None:
            self.channel = channel
            
        if (self._max_chan > 1 and channel is not None):
            # If multi-channel device and channel parameter is passed, select it
            self._instWrite(self._Cmd('chanSelect').format(self.channel))

        return (self.NaN)

    def measureVoltage(self, channel=None):
        """Read and return a voltage measurement from channel
        
           channel - number of the channel starting at 1
        """

        # If a channel number is passed in, make it the
        # current channel
        if channel is not None:
            self.channel = channel
                    
        # select voltage function
        #
        # NOTE: not sure if it slows things down to do this every time
        # so may want to make this smarter if need to speed up measurements.
        self._instWrite("SENS:FUNC 'VOLT'") 

        # Always select channel, even if channel parameter is not passed in.
        self._instWrite(self._Cmd('chanSelect').format(self.channel))

        val = self._instQuery('READ?')
        return float(val)
    
    def measureCurrent(self, channel=None):
        """The 2182 performs no current measurements so override this command
        
           channel - number of the channel starting at 1
        """
        print('NOTE: The Keithley 2182 performs no current measurements. Ignoring this command')
        return (self.NaN)

    def setVoltageProtection(self, ovp, delay=None, channel=None, wait=None):
        """The 2182 has no output voltage protection/compliance to be set. Ignore except for any channel setting.
        
           ovp     - desired over-voltage value as a floating point number
           delay   - desired voltage protection delay time in seconds (not always supported)
           wait    - number of seconds to wait after sending command
           channel - number of the channel starting at 1
        """

        # If a channel number is passed in, make it the
        # current channel
        if channel is not None:
            self.channel = channel
            
        if (self._max_chan > 1 and channel is not None):
            # If multi-channel device and channel parameter is passed, select it
            self._instWrite(self._Cmd('chanSelect').format(self.channel))

    def queryVoltageProtection(self, channel=None):
        """The 2182 has no output voltage protection/compliance setting to query. Return invalid value.
        
        channel - number of the channel starting at 1
        """
        # If a channel number is passed in, make it the
        # current channel
        if channel is not None:
            self.channel = channel
            
        if (self._max_chan > 1 and channel is not None):
            # If multi-channel device and channel parameter is passed, select it
            self._instWrite(self._Cmd('chanSelect').format(self.channel))

        return (self.NaN)

    def voltageProtectionOn(self, channel=None, wait=None):
        """The 2182 has no voltage protection/compliance. Ignore command.
        
           wait    - number of seconds to wait after sending command
           channel - number of the channel starting at 1
        """
        # If a channel number is passed in, make it the
        # current channel
        if channel is not None:
            self.channel = channel
            
        if (self._max_chan > 1 and channel is not None):
            # If multi-channel device and channel parameter is passed, select it
            self._instWrite(self._Cmd('chanSelect').format(self.channel))

        pass
        
    def voltageProtectionOff(self, channel=None, wait=None):
        """The 2182 has no voltage protection/compliance. Ignore command.
        
           channel - number of the channel starting at 1
        """
        # If a channel number is passed in, make it the
        # current channel
        if channel is not None:
            self.channel = channel
            
        if (self._max_chan > 1 and channel is not None):
            # If multi-channel device and channel parameter is passed, select it
            self._instWrite(self._Cmd('chanSelect').format(self.channel))

        pass

    def voltageProtectionClear(self, channel=None, wait=None):
        """The 2182 has no voltage protection/compliance. Ignore command.
        
           channel - number of the channel starting at 1
        """
        # If a channel number is passed in, make it the
        # current channel
        if channel is not None:
            self.channel = channel
            
        if (self._max_chan > 1 and channel is not None):
            # If multi-channel device and channel parameter is passed, select it
            self._instWrite(self._Cmd('chanSelect').format(self.channel))

        pass
    
    def isVoltageProtectionTripped(self, channel=None):
        """The 2182 cannot tell if the compliance limit has been reached or
           not.  So always return True so if someone uses this,
           hopefully the True will force them to figure out what is
           going on.
        
           channel - number of the channel starting at 1

        """
        # If a channel number is passed in, make it the
        # current channel
        if channel is not None:
            self.channel = channel
            
        if (self._max_chan > 1 and channel is not None):
            # If multi-channel device and channel parameter is passed, select it
            self._instWrite(self._Cmd('chanSelect').format(self.channel))

        return True

    ###################################################################
    # Commands Specific to 2182
    ###################################################################
    
    def setLineSync(self,on,wait=None):
        """Enable/Disable Line Cycle Synchronization to reduce/increase measurement noise at expense of acquisition time.

           on      - if True, Enable LSYNC, else Disable LSYNC
           wait    - number of seconds to wait after sending command (need some time)
        """

        # If a wait time is NOT passed in, set wait to the
        # default time
        if wait is None:
            wait = self._wait

        self._instWrite('SYSTem:LSYNc {}'.format(self._bool2onORoff(on)))

        sleep(wait)             # give some time for device to respond
        
    def queryLineSync(self):
        """Query state of Line Cycle Synchronization

           returns True if LSYNC is Enabled, else returns False
        """

        ret = self._instQuery('SYSTem:LSYNc?')
        return self._onORoff_1OR0_yesORno(ret)
            
    def displayMessageOn(self, top=True):
        """Enable Display Message
        
           top     - Ignored (used by other models)
        """

        self._instWrite('DISP:WIND1:TEXT:STAT ON')

    def displayMessageOff(self, top=True):
        """Disable Display Message
        
           top     - Ignored (used by other models)
        """

        self._instWrite('DISP:WIND1:TEXT:STAT OFF')

            
    def setDisplayMessage(self, message, top=True):
        """Set the Message for Display. Use displayMessageOn() or
           displayMessageOff() to enable or disable message, respectively.
        
           message - message to set
           top     - Ignored (used by other models)

        """

        # Maximum of 12 characters for top message
        if (len(message) > 12):
            message = message[:12]
        self._instWrite('DISP:WIND1:TEXT:DATA "{}"'.format(message))

    def queryIntTemperature(self):
        """Return the internal temperature of meter
        """

        ret = self._instQuery('SENS:TEMP:RTEM?')
        return float(ret)
    
    def setVoltageRange(self, upper, channel=None):
        """Set the voltage range for channel

           upper    - floating point value for upper voltage range, set to None for AUTO
           channel  - number of the channel starting at 1
        """

        # If a channel number is passed in, make it the
        # current channel
        if channel is not None:
            self.channel = channel

        if (upper is None):
            # Set for AUTO range
            str = 'SENS:VOLT:CHAN{:1d}:RANG:AUTO ON'.format(self.channel)
            self._instWrite(str)
        else:
            # Disable AUTO range and set the upper value to upper argument
            str = 'SENS:VOLT:CHAN{:1d}:RANG:AUTO OFF'.format(self.channel)
            self._instWrite(str)
            str = 'SENS:VOLT:CHAN{:1d}:RANG {:.3e}'.format(self.channel,float(upper))
            self._instWrite(str)
    
    def queryVoltageRange(self, channel=None):
        """Query the voltage range for channel

           channel  - number of the channel starting at 1
        """

        # If a channel number is passed in, make it the
        # current channel
        if channel is not None:
            self.channel = channel

        # First, query if AUTO is set and then query UPPER range setting
        qry = 'SENS:VOLT:CHAN{:1d}:RANG:AUTO?'.format(self.channel)
        auto = self._instQuery(qry)
        
        qry = 'SENS:VOLT:CHAN{:1d}:RANG?'.format(self.channel)
        upper = self._instQuery(qry)

        # If AUTO is enabled, return string 'AUTO', else return the upper range string
        if (self._onORoff_1OR0_yesORno(auto)):
            return 'AUTO'
        else:
            return upper
            
if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Access and control a Keithley/Tektronix 2182 Nanovoltmeter')
    parser.add_argument('chan', nargs='?', type=int, help='Channel to access/control (max channel: 2)', default=1)
    args = parser.parse_args()

    from time import sleep
    from os import environ
    import sys

    resource = environ.get('K2182_VISA', 'TCPIP0::192.168.1.20::23::SOCKET')
    nanovm = Keithley2182(resource, gaddr=7, verbosity=1, query_delay=0.8)
    nanovm.open()

    # Reset to power on default
    nanovm.rst()        

    print(nanovm.idn())
    print()

    # See if any errors in queue and print them if there are
    print('\nQuerying and printing out any SCPI errors in error queue of instrument:')
    nanovm.printAllErrors()
    print()
    
    nanovm.beeperOff()

    origLineSync = nanovm.queryLineSync()
    if (not origLineSync):
        # Enable Line Sync if not enabled
        nanovm.setLineSync(True)

    # Set Voltage Range to AUTO
    nanovm.setVoltageRange(None)
    
    print('Internal Temperature: {:6.4f} C'.
              format(nanovm.queryIntTemperature()))
                
    print('Voltage: {:6.4e} V\n'.format(nanovm.measureVoltage()))
    sleep(2.0)

    # Set display messages
    nanovm.setDisplayMessage('Hey Man!')

    # Enable it
    nanovm.displayMessageOn()
    sleep(2.0)

    # Disable it
    nanovm.displayMessageOff()
    sleep(1.0)

    ## NOTE: Most of the following functions are attempting to treat
    ## the 2182 like a power supply. The 2182 will either ignore most
    ## of these or return self.NaN. These functions are here mainly to
    ## make sure that these unused functions are handled cleanly.

    print('Ch. {} Settings: {:6.4f} V  {:6.4f} A  {:4.2f} C '.
              format(args.chan, nanovm.queryVoltage(),
                     nanovm.queryCurrent(),
                     nanovm.queryIntTemperature()))

    voltageSave = nanovm.queryVoltage()
    
    print('{:6.4f}V / {:6.4f}A (limit: {:6.4f}A)\n'.format(nanovm.measureVoltage(), nanovm.measureCurrent(), nanovm.queryCurrent()))

    print("Changing Output Voltage to 2.3V")
    nanovm.setVoltage(2.3)
    print('{:6.4f}V / {:6.4f}A (limit: {:6.4f}A)\n'.format(nanovm.measureVoltage(), nanovm.measureCurrent(), nanovm.queryCurrent()))

    print("Set Over-Voltage Protection to 3.6V")
    nanovm.setVoltageProtection(3.6)
    print('OVP: {:6.4f}V\n'.format(nanovm.queryVoltageProtection()))

    nanovm.voltageProtectionOff()
    
    print("Changing Output Voltage to 3.7V with OVP off")
    nanovm.setVoltage(3.7)
    print('{:6.4f}V / {:6.4f}A (limit: {:6.4f}A)\n'.format(nanovm.measureVoltage(), nanovm.measureCurrent(), nanovm.queryCurrent()))

    ## Now, lets get to what 2182 can actually do

    print("Step through different channel and voltage range settings.")
    print("Ch. 1 has five ranges: 10mV, 100mV, 1V, 10V, 100V")
    print("Ch. 2 has three ranges: 100mV, 1V, 10V\n")
    
    test_list = [(1,None,'AUTO'),
                 (1,100, '100.000000'),
                 (1,110, '100.000000'),
                 (2,None, 'AUTO'),
                 (2,1.0,  '1.000000'),
                 (2,8,   '10.000000'),
                 (2,11,  '10.000000'),
                 (2,0.9,  '1.000000'),
                 (2,10.1,'10.000000'),
                 (2,1e-6, '0.100000'),
                 (1,1e-3, '0.010000'),
                 (1,0.001,'0.010000'),
                 (2,1e-8, '0.100000'),
                 (1,1e-8, '0.010000'),
                 (1,0.007,'0.010000'),
                 (1, 10, '10.000000'),
                 (1,0.8,  '1.000000'),
                 (1,2e-2, '0.100000'),
                 ]

    for vals in test_list:
        nanovm.setVoltageRange(vals[1],channel=vals[0])

        volt = nanovm.measureVoltage()
        if volt == nanovm.NaN:
            voltstr = '    Ovrflow'
        else:
            voltstr = '{:6.4e}'.format(volt)

        rangestr = nanovm.queryVoltageRange()
        print('Test: Ch. {}/VRange {:5s} |{:10s}|  Results: {} V  {:4.2f} C '.
              format(nanovm.channel, str(vals[1]), rangestr, voltstr,
                     nanovm.queryIntTemperature()))
        if (vals[2] != rangestr):
            print('Unexpected Voltage Range Query: Exp. {}  Act. {}'.format(vals[2],rangestr))

        #@@@#nanovm.printAllErrors()
        print()
        

    # Turn off Line Sync if it was off originally
    if (not origLineSync):
        # Restore Line Sync
        nanovm.setLineSync(False)

    nanovm.beeperOn()

    # See if any errors in queue and print them if there are
    print('\nQuerying and printing out any SCPI errors in error queue of instrument:')
    nanovm.printAllErrors()
    print()
        
    ## return to LOCAL mode
    nanovm.setLocal()
    
    nanovm.close()
