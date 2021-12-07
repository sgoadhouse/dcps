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
#  Control a Keithley/Tektronix 2400, 2401, 2420, 2440, 2410 SourceMeter
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

class Keithley2400(SCPI):
    """Basic class for controlling and accessing a Keithley/Tektronix 2400
       SourceMeter. This also supports 2400 variations list 2401,
       2420, 2440 and 2410. Although this is not a traditional DC
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
       support the Keithley 2400 although it works with other devices.
       The Prologix interface worked great with the 2400.

    """

    ## Dictionary to translate SCPI commands for this device
    _xlateCmdTbl = {
        #@@@'chanSelect':                'SENS:CHAN {}',
    }

    def __init__(self, resource, gaddr=24, wait=0.25, verbosity=0, query_delay=0.8, **kwargs):
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

        super(Keithley2400, self).__init__(resource, max_chan=1, wait=wait, cmd_prefix=':',
                                           verbosity = verbosity,
                                           read_termination = '\n', write_termination = '\n',
                                           timeout=2, # found that needed longer timeout
                                           query_delay=query_delay,  # for open_resource()
                                           **kwargs)
        
        # NaN for this instrument
        self.NaN = +9.91E37

    
    def open(self):
        """ Overloaded open() so can handle GPIB interfaces after opening the connection """

        super(Keithley2400, self).open()

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
            self._instWrite('++read_tmo_ms 800') # Set the Read Timeout to 800 ms
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
        resp = super(Keithley2400, self)._instQuery(queryStr).strip()
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

    def measureVoltage(self, channel=None):
        """Read and return a voltage measurement from channel
        
           channel - number of the channel starting at 1
        """

        # If this function is used, assume non-concurrent measurements
        self.setMeasureFunction(concurrent=False,voltage=True,channel=channel)

        # vals is a list of the return string [0] is voltage, [1] is current, [2] is resistance, [3] is timestamp, [4] is status
        vals = self._instQuery('READ?').split(',')
        return float(vals[0])
    
    def measureCurrent(self, channel=None):
        """Read and return a current measurement from channel
        
           channel - number of the channel starting at 1
        """

        # If this function is used, assume non-concurrent measurements
        self.setMeasureFunction(concurrent=False,current=True,channel=channel)
        
        # vals is a list of the return string [0] is voltage, [1] is current, [2] is resistance, [3] is timestamp, [4] is status
        vals = self._instQuery('READ?').split(',')
        return float(vals[1])
    
    def voltageProtectionOn(self, channel=None, wait=None):
        """The 2400 has no way to enable/disable voltage protection. Ignore command.
        
           channel - number of the channel starting at 1
           wait    - number of seconds to wait after sending command
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
        """The 2400 has no way to enable/disable voltage protection. Ignore command.
        
           channel - number of the channel starting at 1
           wait    - number of seconds to wait after sending command
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
        """The 2400 automatically clears voltage protection trips. Ignore command.
        
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
    
    ###################################################################
    # Commands Specific to 2400
    ###################################################################
    
    def displayMessageOn(self, top=True):
        """Enable Display Message
        
           top     - True if enabling the Top message, else enable Bottom message
        """

        if (top):
            window = 'WIND1:'
        else:
            window = 'WIND2:'

        self._instWrite('DISP:{}TEXT:STAT ON'.format(window))
            
    def displayMessageOff(self, top=True):
        """Disable Display Message
        
           top     - True if disabling the Top message, else disable Bottom message
        """

        if (top):
            window = 'WIND1:'
        else:
            window = 'WIND2:'

        self._instWrite('DISP:{}TEXT:STAT OFF'.format(window))

            
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
            window = 'WIND1:'
        else:
            # Maximum of 32 characters for bottom message
            if (len(message) > 32):
                message = message[:32]
            window = 'WIND2:'

        self._instWrite('DISP:{}TEXT "{}"'.format(window,message))

    def setSourceFunction(self, voltage=False, current=False, channel=None, wait=None):
        """Set the Source Function for channel - either Voltage or Current

           voltage    - set to True to measure voltage, else False
           current    - set to True to measure current, else False
           channel    - number of the channel starting at 1
           wait       - number of seconds to wait after sending command

           NOTE: Error returned if more than one mode (voltage or current) is True.
        """

        # Check that one and only one mode is True
        if (not (voltage     and not current) and
            not (not voltage and current    )):

            raise ValueError('setSourceFunction(): one and only one mode can be True.')

        # If a channel number is passed in, make it the
        # current channel
        if channel is not None:
            self.channel = channel

        # If a wait time is NOT passed in, set wait to the
        # default time
        if wait is None:
            wait = self._wait

        str = 'SOUR{}:FUNC:MODE'.format(self.channel)            

        if (voltage):
            self._instWrite(str+' VOLT')
            
        if (current):
            self._instWrite(str+' CURR')

            
    def setMeasureFunction(self, concurrent=False, voltage=False, current=False, resistance=False, channel=None, wait=None):
        """Set the Measure Function for channel

           concurrent - set to True for multiple, concurrent measurements; otherwise False
           voltage    - set to True to measure voltage, else False
           current    - set to True to measure current, else False
           resistance - set to True to measure resistance, else False
           channel    - number of the channel starting at 1
           wait       - number of seconds to wait after sending command

           NOTE: Error returned if concurrent is False and more than one mode (voltage, current or resistance) is True.
        """

        # Check that at least 1 mode is True
        if (not voltage and not current and not resistance):
            raise ValueError('setMeasureFunction(): At least one mode (voltage, current or resistance) must be True.')
        
        # Check that if current is False, only one mode is True
        if (not concurrent and
            not (voltage     and not current and not resistance) and
            not (not voltage and current     and not resistance) and
            not (not voltage and not current and resistance)):

            raise ValueError('setMeasureFunction(): If concurrent is False, only one mode can be True.')

        # If a channel number is passed in, make it the
        # current channel
        if channel is not None:
            self.channel = channel

        # If a wait time is NOT passed in, set wait to the
        # default time
        if wait is None:
            wait = self._wait

        str = 'SENS{}:FUNC'.format(self.channel)            

        if (concurrent):
            self._instWrite(str+':CONC ON')
        else:
            self._instWrite(str+':CONC OFF')

        # The :OFF commands should only execute if concurrent is True
        if (voltage):
            self._instWrite(str+':ON "VOLT"')
        elif (concurrent):
            self._instWrite(str+':OFF "VOLT"')
            
        if (current):
            self._instWrite(str+':ON "CURR"')
        elif (concurrent):
            self._instWrite(str+':OFF "CURR"')
            
        if (resistance):
            self._instWrite(str+':ON "RES"')
        elif (concurrent):
            self._instWrite(str+':OFF "RES"')
            
    def measureResistance(self, channel=None):
        """Read and return a resistance measurement from channel
        
           channel - number of the channel starting at 1
        """

        # If this function is used, assume non-concurrent measurements
        self.setMeasureFunction(concurrent=False,resistance=True,channel=channel)

        # vals is a list of the return string [0] is voltage, [1] is current, [2] is resistance, [3] is timestamp, [4] is status        
        vals = self._instQuery('READ?').split(',')
        return float(vals[2])
    
    def measureVCR(self, channel=None):
        """Read and return a voltage, current and resistance measurement from channel
        
           channel - number of the channel starting at 1

           NOTE: This does not force CONCURRENT measurements but for
                 best results, before calling this, call
                 setMeasureFunction(True,True,True,True).

        """

        # NOTE: DO NOT change MeasureFunction. Allow it to be whatever has been set so far (for speed of execution)

        # valstrs is a list of the return string [0] is voltage, [1] is current, [2] is resistance, [3] is timestamp, [4] is status        
        valstrs = self._instQuery('READ?').split(',')
        # convert to floating point
        vals = [float(f) for f in valstrs]
        # status is really a binary value, so convert to int
        vals[4] = int(vals[4])
        # vals is a list of the return floats [0] is voltage, [1] is current, [2] is resistance, [3] is timestamp, [4] is status
        # status is a binary integer - bit definitions from documentation:
        #   Bit 0 (OFLO) — Set to 1 if measurement was made while in over-range.
        #   Bit 1 (Filter) — Set to 1 if measurement was made with the filter enabled.
        #   Bit 2 (Front/Rear) — Set to 1 if FRONT terminals are selected.
        #   Bit 3 (Compliance) — Set to 1 if in real compliance.
        #   Bit 4 (OVP) — Set to 1 if the over voltage protection limit was reached.
        #   Bit 5 (Math) — Set to 1 if math expression (calc1) is enabled.
        #   Bit 6 (Null) — Set to 1 if Null is enabled.
        #   Bit 7 (Limits) — Set to 1 if a limit test (calc2) is enabled.
        #   Bits 8 and 9 (Limit Results) — Provides limit test results (see grading and sorting modes below).
        #   Bit 10 (Auto-ohms) — Set to 1 if auto-ohms enabled.
        #   Bit 11 (V-Meas) — Set to 1 if V-Measure is enabled.
        #   Bit 12 (I-Meas) — Set to 1 if I-Measure is enabled.
        #   Bit 13 (Ω-Meas) — Set to 1 if Ω-Measure is enabled.
        #   Bit 14 (V-Sour) — Set to 1 if V-Source used.
        #   Bit 15 (I-Sour) — Set to 1 if I-Source used.
        #   Bit 16 (Range Compliance) — Set to 1 if in range compliance.
        return vals
    
    
if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Access and control a Keithley/Tektronix 2400 SourceMeter')
    parser.add_argument('chan', nargs='?', type=int, help='Channel to access/control (max channel: 1)', default=1)
    args = parser.parse_args()

    from time import sleep
    from os import environ
    import sys

    resource = environ.get('K2400_VISA', 'TCPIP0::192.168.1.20::23::SOCKET')
    srcmtr = Keithley2400(resource, gaddr=24, verbosity=1, query_delay=0.8)
    srcmtr.open()

    # Reset to power on default
    srcmtr.rst()        

    print(srcmtr.idn())
    print()

    # See if any errors in queue and print them if there are
    print('\nQuerying and printing out any SCPI errors in error queue of instrument:')
    srcmtr.printAllErrors()
    print()
    
    srcmtr.beeperOff()

    # Set Voltage Range to AUTO
    srcmtr.setVoltageRange(None)
    
    # Set display messages
    srcmtr.setDisplayMessage('Bottom Message', top=False)
    srcmtr.setDisplayMessage('Hey Man!', top=True)

    # Enable top one first
    srcmtr.displayMessageOn()
    sleep(1.0)
    srcmtr.displayMessageOn(top=False)
    sleep(2.0)

    # Disable bottom one first
    srcmtr.displayMessageOff(top=False)
    sleep(1.0)
    srcmtr.displayMessageOff(top=True)

    # Test unique setMeasureFunction()
    #
    # Should get ValueError exception since no mode is true
    test_params = ([False], [True],
                   [False, True, True, False],
                   [False, True, True, True],
                   [False, False, True, True],
                   [False, True, False, True])
    for tp in test_params:
        try:
            srcmtr.setMeasureFunction(*tp)
        except ValueError as err:
            print('Got ValueError as expected: {}'.format(err))
        else:
            print('ERROR! Should have gotten a ValueError but did not. STOP TEST!')
            srcmtr.outputOff()
            srcmtr.beeperOn()
            srcmtr.setLocal()
            srcmtr.close()
            sys.exit(2)

    # Disable concurrent measurements
    srcmtr.setMeasureFunction(concurrent=False, resistance=True)
            
    if not srcmtr.isOutputOn(args.chan):
        srcmtr.outputOn()
        
    print('Ch. {} Settings: {:6.4f} V  {:6.4f} A '.
              format(args.chan, srcmtr.queryVoltage(), srcmtr.queryCurrent()))

    voltageSave = srcmtr.queryVoltage()
    
    print('Voltage: {:6.4e} V\n'.format(srcmtr.measureVoltage()))
    sleep(2.0)

    print('{:6.4e}V / {:6.4e}A (limit: {:6.4e}A)\n'.format(srcmtr.measureVoltage(), srcmtr.measureCurrent(), srcmtr.queryCurrent()))

    if (srcmtr.isVoltageComplianceTripped()):
        print('Good! Voltage Compliance Tripped as expected.')
    else:
        print('ERROR! Voltage Compliance should be Tripped!')
        srcmtr.outputOff()
        srcmtr.beeperOn()
        srcmtr.setLocal()
        srcmtr.close()
        sys.exit(2)
    
    print("Changing Output Voltage to 2.3V")
    srcmtr.setVoltage(2.3)
    print('{:6.4e}V / {:6.4e}A (limit: {:6.4e}A)\n'.format(srcmtr.measureVoltage(), srcmtr.measureCurrent(), srcmtr.queryCurrent()))

    print("Set Over-Voltage Protection to 10V")
    srcmtr.setVoltageProtection(10)
    print('OVP: {:6.4g}V\n'.format(srcmtr.queryVoltageProtection()))

    print("Set Voltage Compliance to 3.6V")
    srcmtr.setVoltageCompliance(3.6)
    print('Cmpl: {:6.4g}V\n'.format(srcmtr.queryVoltageCompliance()))

    srcmtr.outputOff()
    print("Source Voltage")
    srcmtr.setSourceFunction(voltage=True)
    srcmtr.outputOn()
    
    print('{:6.4e}V / {:6.4e}A (limit: {:6.4e}V)\n'.format(srcmtr.measureVoltage(), srcmtr.measureCurrent(), srcmtr.queryVoltage()))

    srcmtr.voltageProtectionOff()
    
    print("Changing Output Voltage to 23.7V - protection cannot be off")
    srcmtr.setVoltage(23.7)

    if (srcmtr.isVoltageProtectionTripped()):
        print('Good! Voltage Protection Tripped as expected.')
    else:
        print('ERROR! Voltage Protection should be Tripped!')
        srcmtr.outputOff()
        srcmtr.beeperOn()
        srcmtr.setLocal()
        srcmtr.close()
        sys.exit(2)
        
    print('{:6.4f}V / {:6.4f}A (limit: {:6.4f}V)\n'.format(srcmtr.measureVoltage(), srcmtr.measureCurrent(), srcmtr.queryVoltage()))

    ########################################
    
    srcmtr.outputOff()
    print("Source Current")
    srcmtr.setSourceFunction(current=True)
    # Set Auto current range
    srcmtr.setCurrentRange(None)
    # Set Concurrent Measurements
    srcmtr.setMeasureFunction(concurrent=True,voltage=True,current=True,resistance=False)
    srcmtr.setCurrent(1.34e-3)
    srcmtr.outputOn()
    
    print('{:6.4f}V / {:6.4g}A / {:6.4f}ohms\n'.format(*srcmtr.measureVCR()[0:3]))
    
    ########################################

    srcmtr.outputOff()

    srcmtr.beeperOn()

    # See if any errors in queue and print them if there are
    print('\nQuerying and printing out any SCPI errors in error queue of instrument:')
    srcmtr.printAllErrors()
    print()
        
    ## return to LOCAL mode
    srcmtr.setLocal()
    
    srcmtr.close()
