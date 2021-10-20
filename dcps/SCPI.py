#!/usr/bin/env python
# -*- coding: utf-8 -*-
#

# Copyright (c) 2018-2020, Stephen Goadhouse <sgoadhouse@virginia.edu>
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
 
#-------------------------------------------------------------------------------
#  Control DC Power Supplies using standard SCPI commands with PyVISA
#
# For more information on SCPI, see:
# https://en.wikipedia.org/wiki/Standard_Commands_for_Programmable_Instruments
# http://www.ivifoundation.org/docs/scpi-99.pdf
#-------------------------------------------------------------------------------

# For future Python3 compatibility:
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from time import sleep
import pyvisa

class SCPI(object):
    """Basic class for controlling and accessing a Power Supply with Standard SCPI Commands"""

    # Commands that can be "overloaded" by child classes if need a different syntax
    _SCPICmdTbl = {
        'setLocal':                  'SYSTem:LOCal',
        'setRemote':                 'SYSTem:REMote',
        'setRemoteLock':             'SYSTem:RWLock ON',
        'beeperOn':                  'SYSTem:BEEPer:STATe ON',
        'beeperOff':                 'SYSTem:BEEPer:STATe OFF',
        'chanSelect':                'INSTrument:NSELect {}',
        'isOutput':                  'OUTPut:STATe?',
        'outputOn':                  'OUTPut:STATe ON',
        'outputOff':                 'OUTPut:STATe OFF',
        'setVoltage':                'SOURce:VOLTage:LEVel:IMMediate:AMPLitude {}',
        'setCurrent':                'SOURce:CURRent:LEVel:IMMediate:AMPLitude {}',
        'queryVoltage':              'SOURce:VOLTage:LEVel:IMMediate:AMPLitude?',
        'queryCurrent':              'SOURce:CURRent:LEVel:IMMediate:AMPLitude?',
        'measureVoltage':            'MEASure:VOLTage:DC?',
        'measureCurrent':            'MEASure:CURRent:DC?',
        'setVoltageProtection':      'SOURce:VOLTage:PROTection:LEVel {}',
        'setVoltageProtectionDelay': 'SOURce:VOLTage:PROTection:DELay {}',
        'queryVoltageProtection':    'SOURce:VOLTage:PROTection:LEVel?',
        'voltageProtectionOn':       'SOURce:VOLTage:PROTection:STATe ON',
        'voltageProtectionOff':      'SOURce:VOLTage:PROTection:STATe OFF',
        'isVoltageProtectionTripped':'VOLTage:PROTection:TRIPped?',
        'voltageProtectionClear':    'VOLTage:PROTection:CLEar',
    }
    
    def __init__(self,
                 resource, max_chan=1, wait=1.0,
                 cmd_prefix = '',
                 verbosity = 0,
                 read_termination = '',
                 write_termination = '',
                 **kwargs
                 ):
        """Init the class with the instruments resource string

        resource   - resource string or VISA descriptor, like TCPIP0::172.16.2.13::INSTR
        max_chan   - number of channels in power supply
        wait       - float that gives the default number of seconds to wait after sending each command
        cmd_prefix - optional command prefix (ie. some instruments require a ':' prefix)
        verbosity  - optional verbosity value - set to 0 to disable debug outputs, or non-0 for outputs
        read_termination - optional read_termination parameter to pass to open_resource()
        write_termination - optional write_termination parameter to pass to open_resource()
        kwargs - optional keyword arguments to pass to open_resource()
        """
        self._resource = resource
        self._max_chan = max_chan                # number of channels
        self._wait = wait
        self._prefix = cmd_prefix
        self._verbosity = verbosity
        self._curr_chan = 1                      # set the current channel to the first one
        self._read_termination = read_termination
        self._write_termination = write_termination
        self._kwargs = kwargs
        self._inst = None

        #@@@
        #for key, value in kwargs.items():
        #    print ("%s == %s" %(key, value))


    def open(self):
        """Open a connection to the VISA device with PYVISA-py python library"""
        self._rm = pyvisa.ResourceManager('@py')
        self._inst = self._rm.open_resource(self._resource,
                                            read_termination=self._read_termination,
                                            write_termination=self._write_termination,                                            
                                            **self._kwargs)

    def close(self):
        """Close the VISA connection"""
        self._inst.close()

    @property
    def channel(self):
        return self._curr_chan
    
    @channel.setter
    def channel(self, value):
        if (value < 1) or (value > self._max_chan):
            raise ValueError('Invalid channel number: {}. Must be between {} and {}, inclusive.'.
                                 format(channel, 1, self._max_chan))
        self._curr_chan = value

    def _instQuery(self, queryStr):
        if (queryStr[0] != '*'):
            queryStr = self._prefix + queryStr
        if self._verbosity >= 3:
            print("QUERY:",queryStr)
        return self._inst.query(queryStr)
        
    def _instWrite(self, writeStr):
        if (writeStr[0] != '*'):
            writeStr = self._prefix + writeStr
        if self._verbosity >= 3:
            print("WRITE:",writeStr)
        return self._inst.write(writeStr)
        
    def _chStr(self, channel):
        """return the channel string given the channel number and using the format CHx"""

        return 'CH{}'.format(channel)
    
    def _chanStr(self, channel):
        """return the channel string given the channel number and using the format x"""

        return '{}'.format(channel)
    
    def _onORoff(self, str):
        """Check if string says it is ON or OFF and return True if ON
        and False if OFF
        """

        # Only check first two characters so do not need to deal with
        # trailing whitespace and such
        if str[:2] == 'ON':
            return True
        else:
            return False
        
    def _onORoff_1OR0_yesORno(self, str):
        """Check if string says it is ON or OFF and return True if ON
        and False if OFF OR check if '1' or '0' and return True for '1' 
        OR check if 'YES' or 'NO' and return True for 'YES'
        """

        # trip out whitespace
        str = str.strip()
        
        if str == 'ON':
            return True
        elif str == 'YES':
            return True
        elif str == '1':
            return True
        else:
            return False
        
    def _waitCmd(self):
        """Wait until all preceeding commands complete"""
        #self._instWrite('*WAI')
        self._instWrite('*OPC')
        wait = True
        while(wait):
            ret = self._instQuery('*OPC?')
            if ret[0] == '1':
                wait = False
        
    def _Cmd(self, key):
        """Lookup the needed command string. If child class has not defined it, then pull from local dictionary."""
        if ('_xlateCmdTbl' in dir(self) and key in self._xlateCmdTbl):
            # child class can create a dictionary named '_xlateCmdTbl' and add keys to translate for the specific hardware
            return self._xlateCmdTbl[key]
        else:
            # not found in child class so pull from SCPI table
            # NOTE: do not assume if in _SCPICmdTbl that is is an official SCPI command
            return self._SCPICmdTbl[key]
        
    def idn(self):
        """Return response to *IDN? message"""
        return self._instQuery('*IDN?')

    def readError(self):
        """Return response to SYSTem:ERRor? message - should be next error"""
        return self._instQuery('SYSTem:ERRor?')

    def printAllErrors(self):
        """Repeatedly read and print out errors until reach the +0,'No error' message"""
        while True:
            err = self.readError()
            if (err[0:3] != '+0,'):
                #@@@#print(":".join("{:02x}".format(ord(c)) for c in err[0:3]))
                print(err)
            else:
                # all errors have been read so return
                break
        
    def cls(self):
        """Clear Status and sometimes errors"""
        self._instWrite('*CLS')

    def rst(self):
        """Reset but not errors"""
        self._instWrite('*RST')

    def setLocal(self):
        """Set the power supply to LOCAL mode where front panel keys work again
        """

        # Not sure if this is SCPI, but it appears to be supported
        # across different instruments
        self._instWrite(self._Cmd('setLocal'))
    
    def setRemote(self):
        """Set the power supply to REMOTE mode where it is controlled via VISA
        """

        # Not sure if this is SCPI, but it appears to be supported
        # across different instruments
        self._instWrite(self._Cmd('setRemote'))
    
    def setRemoteLock(self):
        """Set the power supply to REMOTE Lock mode where it is
           controlled via VISA & front panel is locked out
        """

        # Not sure if this is SCPI, but it appears to be supported
        # across different instruments
        self._instWrite(self._Cmd('setRemoteLock'))

    def beeperOn(self):
        """Enable the system beeper for the instrument"""
        self._instWrite(self._Cmd('beeperOn'))
        
    def beeperOff(self):
        """Disable the system beeper for the instrument"""
        self._instWrite(self._Cmd('beeperOff'))
        
    def isOutputOn(self, channel=None):
        """Return true if the output of channel is ON, else false
        
           channel - number of the channel starting at 1
        """

        # If a channel number is passed in, make it the
        # current channel
        if channel is not None:
            self.channel = channel
            
        if (self._max_chan > 1 and channel is not None):
            # If multi-channel device and channel parameter is passed, select it
            self._instWrite(self._Cmd('chanSelect').format(self.channel))
            
        str = self._Cmd('isOutput')
        ret = self._instQuery(str)
        # @@@print("1:", ret)
        return self._onORoff(ret)
    
    def outputOn(self, channel=None, wait=None):
        """Turn on the output for channel
        
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
                        
        # If a wait time is NOT passed in, set wait to the
        # default time
        if wait is None:
            wait = self._wait
            
        str = self._Cmd('outputOn')
        self._instWrite(str)
        sleep(wait)             # give some time for PS to respond
    
    def outputOff(self, channel=None, wait=None):
        """Turn off the output for channel
        
           channel - number of the channel starting at 1
        """

        # If a channel number is passed in, make it the
        # current channel
        if channel is not None:
            self.channel = channel
                    
        if (self._max_chan > 1 and channel is not None):
            # If multi-channel device and channel parameter is passed, select it
            self._instWrite(self._Cmd('chanSelect').format(self.channel))
            
        # If a wait time is NOT passed in, set wait to the
        # default time
        if wait is None:
            wait = self._wait
            
        str = self._Cmd('outputOff')
        self._instWrite(str)
        sleep(wait)             # give some time for PS to respond
    
    def outputOnAll(self, wait=None):
        """Turn on the output for ALL channels
        
        """

        # If a wait time is NOT passed in, set wait to the
        # default time
        if wait is None:
            wait = self._wait

        for chan in range(1,self._max_chan+1):
            if (self._max_chan > 1):
                # If multi-channel device, select next channel
                self._instWrite(self._Cmd('chanSelect').format(self.channel))
            
            str = self._Cmd('outputOn')
            
        sleep(wait)             # give some time for PS to respond
    
    def outputOffAll(self, wait=None):
        """Turn off the output for ALL channels
        
        """

        # If a wait time is NOT passed in, set wait to the
        # default time
        if wait is None:
            wait = self._wait

        for chan in range(1,self._max_chan+1):
            if (self._max_chan > 1):
                # If multi-channel device, select next channel
                self._instWrite(self._Cmd('chanSelect').format(self.channel))
            
            str = self._Cmd('outputOff')
            
        sleep(wait)             # give some time for PS to respond
    
    def setVoltage(self, voltage, channel=None, wait=None):
        """Set the voltage value for the channel
        
           voltage - desired voltage value as a floating point number
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
            
        # If a wait time is NOT passed in, set wait to the
        # default time
        if wait is None:
            wait = self._wait
            
        str = self._Cmd('setVoltage').format(voltage)
        self._instWrite(str)
        sleep(wait)             # give some time for PS to respond
        
    def setCurrent(self, current, channel=None, wait=None):
        """Set the current value for the channel
        
           current - desired current value as a floating point number
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
            
        # If a wait time is NOT passed in, set wait to the
        # default time
        if wait is None:
            wait = self._wait
            
        str = self._Cmd('setCurrent').format(current)
        self._instWrite(str)
        sleep(wait)             # give some time for PS to respond

        
    def queryVoltage(self, channel=None):
        """Return what voltage set value is (not the measured voltage,
        but the set voltage)
        
        channel - number of the channel starting at 1
        """

        # If a channel number is passed in, make it the
        # current channel
        if channel is not None:
            self.channel = channel
            
        if (self._max_chan > 1 and channel is not None):
            # If multi-channel device and channel parameter is passed, select it
            self._instWrite(self._Cmd('chanSelect').format(self.channel))
            
        str = self._Cmd('queryVoltage')
        ret = self._instQuery(str)
        return float(ret)
    
    def queryCurrent(self, channel=None):
        """Return what current set value is (not the measured current,
        but the set current)
        
        channel - number of the channel starting at 1
        """

        # If a channel number is passed in, make it the
        # current channel
        if channel is not None:
            self.channel = channel
                    
        if (self._max_chan > 1 and channel is not None):
            # If multi-channel device and channel parameter is passed, select it
            self._instWrite(self._Cmd('chanSelect').format(self.channel))
            
        str = self._Cmd('queryCurrent')
        ret = self._instQuery(str)
        return float(ret)
    
    def measureVoltage(self, channel=None):
        """Read and return a voltage measurement from channel
        
           channel - number of the channel starting at 1
        """

        # If a channel number is passed in, make it the
        # current channel
        if channel is not None:
            self.channel = channel
                    
        if (self._max_chan > 1 and channel is not None):
            # If multi-channel device and channel parameter is passed, select it
            self._instWrite(self._Cmd('chanSelect').format(self.channel))
            
        str = self._Cmd('measureVoltage')
        val = self._instQuery(str)
        return float(val)
    
    def measureCurrent(self, channel=None):
        """Read and return a current measurement from channel
        
           channel - number of the channel starting at 1
        """

        # If a channel number is passed in, make it the
        # current channel
        if channel is not None:
            self.channel = channel
            
        if (self._max_chan > 1 and channel is not None):
            # If multi-channel device and channel parameter is passed, select it
            self._instWrite(self._Cmd('chanSelect').format(self.channel))
            
        str = self._Cmd('measureCurrent')
        val = self._instQuery(str)
        return float(val)
    
    def setVoltageProtection(self, ovp, delay=None, channel=None, wait=None):
        """Set the over-voltage protection value for the channel
        
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
            
        # If a wait time is NOT passed in, set wait to the
        # default time
        if wait is None:
            wait = self._wait
            
        str = self._Cmd('setVoltageProtection').format(ovp)
        self._instWrite(str)
        sleep(wait)             # give some time for PS to respond
        
        if delay is not None:
            str = self._Cmd('setVoltageProtectionDelay').format(delay)
            self._instWrite(str)
            sleep(wait)             # give some time for PS to respond
        
    def queryVoltageProtection(self, channel=None):
        """Return what the over-voltage protection set value is
        
        channel - number of the channel starting at 1
        """

        # If a channel number is passed in, make it the
        # current channel
        if channel is not None:
            self.channel = channel
            
        if (self._max_chan > 1 and channel is not None):
            # If multi-channel device and channel parameter is passed, select it
            self._instWrite(self._Cmd('chanSelect').format(self.channel))
            
        str = self._Cmd('queryVoltageProtection')
        ret = self._instQuery(str)
        return float(ret)
    
    def voltageProtectionOn(self, channel=None, wait=None):
        """Enable Over-Voltage Protection on the output for channel
        
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
                        
        # If a wait time is NOT passed in, set wait to the
        # default time
        if wait is None:
            wait = self._wait
            
        str = self._Cmd('voltageProtectionOn')
        self._instWrite(str)
        sleep(wait)             # give some time for PS to respond
    
    def voltageProtectionOff(self, channel=None, wait=None):
        """Disable Over-Voltage Protection on the output for channel
        
           channel - number of the channel starting at 1
        """

        # If a channel number is passed in, make it the
        # current channel
        if channel is not None:
            self.channel = channel
                    
        if (self._max_chan > 1 and channel is not None):
            # If multi-channel device and channel parameter is passed, select it
            self._instWrite(self._Cmd('chanSelect').format(self.channel))
            
        # If a wait time is NOT passed in, set wait to the
        # default time
        if wait is None:
            wait = self._wait
            
        str = self._Cmd('voltageProtectionOff')
        self._instWrite(str)
        sleep(wait)             # give some time for PS to respond

    def voltageProtectionClear(self, channel=None, wait=None):
        """Clear Over-Voltage Protection Trip on the output for channel
        
           channel - number of the channel starting at 1
        """

        # If a channel number is passed in, make it the
        # current channel
        if channel is not None:
            self.channel = channel
                    
        if (self._max_chan > 1 and channel is not None):
            # If multi-channel device and channel parameter is passed, select it
            self._instWrite(self._Cmd('chanSelect').format(self.channel))
            
        # If a wait time is NOT passed in, set wait to the
        # default time
        if wait is None:
            wait = self._wait
            
        str = self._Cmd('voltageProtectionClear')
        self._instWrite(str)
        sleep(wait)             # give some time for PS to respond
    
    def isVoltageProtectionTripped(self, channel=None):
        """Return true if the OverVoltage Protection of channel is Tripped, else false
        
           channel - number of the channel starting at 1
        """

        # If a channel number is passed in, make it the
        # current channel
        if channel is not None:
            self.channel = channel
            
        if (self._max_chan > 1 and channel is not None):
            # If multi-channel device and channel parameter is passed, select it
            self._instWrite(self._Cmd('chanSelect').format(self.channel))
            
        ret = self._instQuery(self._Cmd('isVoltageProtectionTripped'))
        # @@@print("1:", ret)
        return self._onORoff_1OR0_yesORno(ret)
    

