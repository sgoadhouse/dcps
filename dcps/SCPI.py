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
    """Basic class for controlling and accessing a Power Supply and other related Instruments with Standard SCPI Commands"""

    # Commands that can be "overloaded" by child classes if need a different syntax
    _SCPICmdTbl = {
        'setLocal':                      'SYSTem:LOCal',
        'setRemote':                     'SYSTem:REMote',
        'setRemoteLock':                 'SYSTem:RWLock ON',
        'beeperOn':                      'SYSTem:BEEPer:STATe ON',
        'beeperOff':                     'SYSTem:BEEPer:STATe OFF',
        'chanSelect':                    'INSTrument:NSELect {}',
        'isOutput':                      'OUTPut:STATe?',
        'outputOn':                      'OUTPut:STATe ON',
        'outputOff':                     'OUTPut:STATe OFF',
        'isInput':                       'INPut:STATe?',
        'inputOn':                       'INPut:STATe ON',
        'inputOff':                      'INPut:STATe OFF',
        'setFunction':                   'SOURce:FUNCtion {}',
        'queryFunction':                 'SOURce:FUNCtion?',
        'setVoltage':                    'SOURce:VOLTage:LEVel:IMMediate:AMPLitude {}',
        'setVoltageRangeAuto':           'SOURce{:1d}:VOLTage:RANGe:AUTO {}',
        'setVoltageRange':               'SOURce{:1d}:VOLTage:RANGe {:.3e}',
        'setCurrent':                    'SOURce:CURRent:LEVel:IMMediate:AMPLitude {}',
        'setCurrentRangeAuto':           'SOURce{:1d}:CURRent:RANGe:AUTO {}',
        'setCurrentRange':               'SOURce{:1d}:CURRent:RANGe {:.3e}',
        'queryVoltage':                  'SOURce:VOLTage:LEVel:IMMediate:AMPLitude?',
        'queryVoltageRangeAuto':         'SOURce{:1d}:VOLTage:RANGe:AUTO?',
        'queryVoltageRange':             'SOURce{:1d}:VOLTage:RANGe?',
        'queryCurrent':                  'SOURce:CURRent:LEVel:IMMediate:AMPLitude?',
        'queryCurrentRangeAuto':         'SOURce{:1d}:CURRent:RANGe:AUTO?',
        'queryCurrentRange':             'SOURce{:1d}:CURRent:RANGe?',
        'setMeasureFunction':            'SENse:FUNCtion {}',
        'queryMeasureFunction':          'SENse:FUNCtion?',
        'measureVoltage':                'MEASure:VOLTage:DC?',
        'measureVoltageMax':             'MEASure:VOLTage:MAX?',
        'measureVoltageMin':             'MEASure:VOLTage:MIN?',
        'setMeasureVoltageRangeAuto':    'SENSe{:1d}:VOLTage:RANGe:AUTO {}',
        'setMeasureVoltageRange':        'SENSe{:1d}:VOLTage:RANGe {:.3e}',
        'queryMeasureVoltageRangeAuto':  'SENSe{:1d}:VOLTage:RANGe:AUTO?',
        'queryMeasureVoltageRange':      'SENSe{:1d}:VOLTage:RANGe?',
        'measureCurrent':                'MEASure:CURRent:DC?',
        'measureCurrentMax':             'MEASure:CURRent:MAX?',
        'measureCurrentMin':             'MEASure:CURRent:MIN?',
        'setMeasureCurrentRangeAuto':    'SENSe{:1d}:CURRent:RANGe:AUTO {}',
        'setMeasureCurrentRange':        'SENSe{:1d}:CURRent:RANGe {:.3e}',
        'queryMeasureCurrentRangeAuto':  'SENSe{:1d}:CURRent:RANGe:AUTO?',
        'queryMeasureCurrentRange':      'SENSe{:1d}:CURRent:RANGe?',
        'measureResistance':             'MEASure:RESistance:DC?',        
        'measurePower':                  'MEASure:POWer:DC?',        
        'setVoltageProtection':          'SOURce:VOLTage:PROTection:LEVel {}',
        'setVoltageProtectionDelay':     'SOURce:VOLTage:PROTection:DELay {}',
        'queryVoltageProtection':        'SOURce:VOLTage:PROTection:LEVel?',
        'voltageProtectionOn':           'SOURce:VOLTage:PROTection:STATe ON',
        'voltageProtectionOff':          'SOURce:VOLTage:PROTection:STATe OFF',
        'isVoltageProtectionOn':         'SOURce:VOLTage:PROTection:STATe?',
        'isVoltageProtectionTripped':    'SOURce:VOLTage:PROTection:TRIPped?',
        'voltageProtectionClear':        'SOURce:VOLTage:PROTection:CLEar',
        'setVoltageCompliance':          'SENSe:VOLTage:PROTection:LEVel {}',
        'queryVoltageCompliance':        'SENSe:VOLTage:PROTection:LEVel?',
        'isVoltageComplianceTripped':    'SENSe:VOLTage:PROTection:TRIPped?',
        'voltageComplianceClear':        'SENSe:VOLTage:PROTection:CLEar',
        'setCurrentProtection':          'SOURce:CURRent:PROTection:LEVel {}',
        'setCurrentProtectionDelay':     'SOURce:CURRent:PROTection:DELay {}',
        'queryCurrentProtection':        'SOURce:CURRent:PROTection:LEVel?',
        'currentProtectionOn':           'SOURce:CURRent:PROTection:STATe ON',
        'currentProtectionOff':          'SOURce:CURRent:PROTection:STATe OFF',
        'isCurrentProtectionOn':         'SOURce:CURRent:PROTection:STATe?',
        'isCurrentProtectionTripped':    'SOURce:CURRent:PROTection:TRIPped?',
        'currentProtectionClear':        'SOURce:CURRent:PROTection:CLEar',
        'setCurrentCompliance':          'SENSe:CURRent:PROTection:LEVel {}',
        'queryCurrentCompliance':        'SENSe:CURRent:PROTection:LEVel?',
        'isCurrentComplianceTripped':    'SENSe:CURRent:PROTection:TRIPped?',
        'currentComplianceClear':        'SENSe:CURRent:PROTection:CLEar',
    }

    # Official SCPI numeric value for Not A Number
    NaN = 9.91E37

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
        max_chan   - number of channels in instrument
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

        if (self._verbosity >= 1):
            print('PyVISA Resources Found:')
            print("   " + "\n   ".join(self._rm.list_resources()))

        if (self._verbosity >= 1):
            print('opening resource: ' + self._resource)
            
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
                                 format(value, 1, self._max_chan))
        self._curr_chan = value

    def _instQuery(self, queryStr, delay=None):
        if (queryStr[0] == '-'):
            # Any command that starts with '-' means that it should
            # NOT have a prefix and the '-' needs to be removed.
            queryStr = queryStr[1:]
        elif (queryStr[0] != '*' and queryStr[0:2] != '++'):
            # '*' start SCPI common commands and never have a prefix
            # '++' is used by Prologix Ethernet GPIB interface and should not have prefix prepended either
            queryStr = self._prefix + queryStr
        if self._verbosity >= 3:
            print("QUERY:",queryStr)
        resp = self._inst.query(queryStr, delay=delay)
        if self._verbosity >= 3:
            print("   QUERY Response:", resp)
        return resp
        
    def _instWrite(self, writeStr):
        if (writeStr[0] == '-'):
            # Any command that starts with '-' means that it should
            # NOT have a prefix and the '-' needs to be removed.
            writeStr = writeStr[1:]
        elif (writeStr[0] != '*' and writeStr[0:2] != '++'):
            # '*' start SCPI common commands and never have a prefix
            # '++' is used by Prologix Ethernet GPIB interface and should not have prefix prepended either
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
        
    def _bool2onORoff(self, bool):
        """If bool is True, return ON string, else return OFF string. Use to
        convert boolean input to ON or OFF string output.
        """

        if (bool):
            return 'ON'
        else:
            return 'OFF'

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
        
    def isGenericTrue(self, cmdStr, channel=None):
        """Return true if the result of cmdStr is ON, 1 or YES, else false
        
           cmdStr  - SCPI command string to query
           channel - number of the channel starting at 1
        """

        # If a channel number is passed in, make it the
        # current channel
        if channel is not None:
            self.channel = channel
            
        if (self._max_chan > 1 and channel is not None):
            # If multi-channel device and channel parameter is passed, select it
            self._instWrite(self._Cmd('chanSelect').format(self.channel))
            
        ret = self._instQuery(cmdStr)
        # @@@print("1:", ret)
        return self._onORoff_1OR0_yesORno(ret)
    
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
            if (err[0:3] != '+0,' and err[0:2] != '0,'):
                ## No Error has two possible results across platforms:
                ## '+0,"No error"' or '0,"No error"' Handle either.
                ##
                #@@@#print(":".join("{:02x}".format(ord(c)) for c in err[0:3]))
                print(err)
            else:
                # all errors have been read so return
                break
        
    def cls(self, wait=None):
        """Clear Status and sometimes errors

           wait    - number of seconds to wait after sending command
        """

        # If a wait time is NOT passed in, set wait to the
        # default time
        if wait is None:
            wait = self._wait

        self._instWrite('*CLS')

        sleep(wait)             # give some time for device to respond
        
    def rst(self, wait=None):
        """Reset but not errors

           wait    - number of seconds to wait after sending command
        """

        # If a wait time is NOT passed in, set wait to the
        # default time
        if wait is None:
            wait = self._wait

        self._instWrite('*RST')

        sleep(wait)             # give some time for device to respond
        
        
    def setLocal(self):
        """Set the instrument to LOCAL mode where front panel keys work again
        """

        # Not sure if this is SCPI, but it appears to be supported
        # across different instruments
        self._instWrite(self._Cmd('setLocal'))
    
    def setRemote(self):
        """Set the instrument to REMOTE mode where it is controlled via VISA
        """

        # Not sure if this is SCPI, but it appears to be supported
        # across different instruments
        self._instWrite(self._Cmd('setRemote'))
    
    def setRemoteLock(self):
        """Set the instrument to REMOTE Lock mode where it is
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
        return self._onORoff_1OR0_yesORno(ret)
    
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
    
    def isInputOn(self, channel=None):
        """Return true if the input of channel is ON, else false
        
           channel - number of the channel starting at 1
        """

        # If a channel number is passed in, make it the
        # current channel
        if channel is not None:
            self.channel = channel
            
        if (self._max_chan > 1 and channel is not None):
            # If multi-channel device and channel parameter is passed, select it
            self._instWrite(self._Cmd('chanSelect').format(self.channel))
            
        str = self._Cmd('isInput')
        ret = self._instQuery(str)
        # @@@print("1:", ret)
        return self._onORoff_1OR0_yesORno(ret)
    
    def inputOn(self, channel=None, wait=None):
        """Turn on the input for channel
        
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
            
        str = self._Cmd('inputOn')
        self._instWrite(str)
        sleep(wait)             # give some time for PS to respond
    
    def inputOff(self, channel=None, wait=None):
        """Turn off the input for channel
        
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
            
        str = self._Cmd('inputOff')
        self._instWrite(str)
        sleep(wait)             # give some time for PS to respond
    
    def inputOnAll(self, wait=None):
        """Turn on the input for ALL channels
        
        """

        # If a wait time is NOT passed in, set wait to the
        # default time
        if wait is None:
            wait = self._wait

        for chan in range(1,self._max_chan+1):
            if (self._max_chan > 1):
                # If multi-channel device, select next channel
                self._instWrite(self._Cmd('chanSelect').format(self.channel))
            
            str = self._Cmd('inputOn')
            
        sleep(wait)             # give some time for PS to respond
    
    def inputOffAll(self, wait=None):
        """Turn off the input for ALL channels
        
        """

        # If a wait time is NOT passed in, set wait to the
        # default time
        if wait is None:
            wait = self._wait

        for chan in range(1,self._max_chan+1):
            if (self._max_chan > 1):
                # If multi-channel device, select next channel
                self._instWrite(self._Cmd('chanSelect').format(self.channel))
            
            str = self._Cmd('inputOff')
            
        sleep(wait)             # give some time for PS to respond
    
    def setAsciiPrecision(self, value, wait=None):
        """Set the digit precision of returned values in the ASCII
           format. Keithley DMM6500 uses this but included in SCPI.py in
           case future instruments use this same command.
           NOTE: This value affects ALL channels.

           value      - number of significant digits to return when using the default ASCII data format for returned values
                        0 = Automatic                        
                        value can also be "DEF" for default, "MAX" for maximum or "MIN" for minimum
           wait       - number of seconds to wait after sending command

        """
                    
        # If a wait time is NOT passed in, set wait to the
        # default time
        if wait is None:
            wait = self._wait

        str = 'FORMat:ASCii:PRECision {}'.format(value)

        #@@@#print('Format ASCII Precision String: {}'.format(str))

        self._instWrite(str)

        sleep(wait)             # give some time for device to respond

    def queryAsciiPrecision(self, query_delay=None):
        """Query the digit precision of returned values in the ASCII
           format. Keithley DMM6500 uses this but included in SCPI.py in
           case future instruments use this same command.
           NOTE: This value affects ALL channels.

           query_delay     - number of seconds to wait between sending command and waiting for response
                             None uses the default

        """
                    
        qryValue = 'FORMat:ASCii:PRECision?'

        #@@@#print('Format ASCII Precision Query String: {}'.format(qryValue))

        ret = self._instQuery(qryValue,delay=query_delay)
        return int(ret)
        
        
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

    def setFunction(self, function, channel=None, wait=None):
        """Set the source function for the channel
        
           function - a string which names the function. common ones:
                      VOLTage, CURRent, RESistance, POWer        
           wait     - number of seconds to wait after sending command
           channel  - number of the channel starting at 1
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
            
        str = self._Cmd('setFunction').format(function)
        self._instWrite(str)
        sleep(wait)             # give some time for PS to respond

    def queryFunction(self, channel=None, query_delay=None):
        """Return what FUNCTION is the current one for sourcing
        
        channel     - number of the channel starting at 1
        query_delay - number of seconds to wait between write and
                      reading for read data (None uses default seconds)
        """

        return self.fetchGenericString(self._Cmd('queryFunction'), channel, query_delay)
    
    def setGenericRange(self, value, cmdAuto, cmdRange, channel=None, wait=None):
        """Set a generic range for channel to value using commands cmdAuto and cmdRange

           value    - floating point value to set range, set to None for AUTO
           cmdAuto  - SCPI command string to use to set the range to AUTO or None if no such command
           cmdRange - SCPI command string to use to set the RANGE
           channel  - number of the channel starting at 1
           wait     - number of seconds to wait after sending command
        """

        # If a channel number is passed in, make it the
        # current channel
        if channel is not None:
            self.channel = channel

        # If a wait time is NOT passed in, set wait to the
        # default time
        if wait is None:
            wait = self._wait
            
        if (value is None):
            if (cmdAuto is not None):                
                # Set for AUTO range
                #
                # NOTE: If value and cmdAuto are both None, nothing happens
                str = cmdAuto.format(self.channel, 'ON')
                self._instWrite(str)
        else:
            if (cmdAuto is not None):                
                # Disable AUTO range and set the range to value, unless cmdAuto is None
                str = cmdAuto.format(self.channel, 'OFF')
                self._instWrite(str)
            #@@@#str = cmdRange.format(self.channel, float(value))
            str = cmdRange.format(self.channel, value) # allow strings DEF/MIN/MAX
            self._instWrite(str)
        sleep(wait)             # give some time for PS to respond
        
    def setVoltageRange(self, value, channel=None, wait=None):
        """Set the voltage range for channel

           value    - floating point value for voltage range, set to None for AUTO
           channel  - number of the channel starting at 1
           wait     - number of seconds to wait after sending command
        """

        self.setGenericRange(value, self._Cmd('setVoltageRangeAuto'), self._Cmd('setVoltageRange'), channel, wait)
    
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
        
    def setCurrentRange(self, upper, channel=None, wait=None):
        """Set the current range for channel

           upper    - floating point value for upper current range, set to None for AUTO
           channel  - number of the channel starting at 1
           wait     - number of seconds to wait after sending command
        """

        self.setGenericRange(upper, self._Cmd('setCurrentRangeAuto'), self._Cmd('setCurrentRange'), channel, wait)
                
    def fetchGenericValue(self, qryValue, channel=None, query_delay=None):
        """Perform a SCPI Query that expects a floating point value using qryValue command
        
        qryValue    - SCPI query command string to use to query the VALUE
        channel     - number of the channel starting at 1
        query_delay - number of seconds to wait between write and
                      reading for read data (None uses default seconds)
        """

        # If a channel number is passed in, make it the
        # current channel
        if channel is not None:
            self.channel = channel
            
        if (self._max_chan > 1 and channel is not None):
            # If multi-channel device and channel parameter is passed, select it
            self._instWrite(self._Cmd('chanSelect').format(self.channel))
            
        ret = self._instQuery(qryValue, delay=query_delay)
        return float(ret)
    
    def fetchGenericString(self, qryString, channel=None, query_delay=None):
        """Perform a SCPI Query that expects a STRING returned using qryString command
        
        qryString   - SCPI query command string to use to query the STRING
        channel     - number of the channel starting at 1
        query_delay - number of seconds to wait between write and
                      reading for read data (None uses default seconds)
        """

        # If a channel number is passed in, make it the
        # current channel
        if channel is not None:
            self.channel = channel
            
        if (self._max_chan > 1 and channel is not None):
            # If multi-channel device and channel parameter is passed, select it
            self._instWrite(self._Cmd('chanSelect').format(self.channel))
            
        ret = self._instQuery(qryString, delay=query_delay)
        return ret
    
    def fetchGenericBoolean(self, qryBool, channel=None, query_delay=None):
        """Perform a SCPI Query that expects a Boolean returned using qryBool command
        
        qryBool     - SCPI query command string to use to query the BOOLEAN
        channel     - number of the channel starting at 1
        query_delay - number of seconds to wait between write and
                      reading for read data (None uses default seconds)
        """

        ret = self.fetchGenericString(qryBool, channel, query_delay)
        return self._onORoff_1OR0_yesORno(ret)
    
    def queryVoltage(self, channel=None):
        """Return what voltage set value is (not the measured voltage,
        but the set voltage)
        
        channel - number of the channel starting at 1
        """

        return self.fetchGenericValue(self._Cmd('queryVoltage'), channel)
    
    def queryGenericRange(self, cmdAuto, cmdRange, channel=None):
        """Query the generic range for channel

           cmdAuto  - SCPI command string to use to query if range is AUTO or None if no such command
           cmdRange - SCPI command string to use to query the RANGE
           channel  - number of the channel starting at 1
        """

        # If a channel number is passed in, make it the
        # current channel
        if channel is not None:
            self.channel = channel

        if (cmdAuto is not None):                
            # First, query if AUTO is set (if cmdAuto is not None)
            qry = cmdAuto.format(self.channel)
            auto = self._instQuery(qry)
        else:
            # no cmdAuto so set auto to 0 to assume that it is off since no Auto
            auto = '0'
        
        # and then query UPPER range setting
        qry = cmdRange.format(self.channel)
        upper = self._instQuery(qry)

        # If AUTO is enabled, return string 'AUTO', else return the upper range string
        if (self._onORoff_1OR0_yesORno(auto)):
            #@@@#return 'AUTO'
            return None
        else:
            #@@@#return upper
            return float(upper)
            
    def queryVoltageRange(self, channel=None):
        """Query the voltage range for channel

           channel  - number of the channel starting at 1
        """

        #@@@#qry = 'SENS:VOLT:CHAN{:1d}:RANG:AUTO?'.format(self.channel)
        #@@@#qry = 'SENS:VOLT:CHAN{:1d}:RANG?'.format(self.channel)
        return self.queryGenericRange(self._Cmd('queryVoltageRangeAuto'), self._Cmd('queryVoltageRange'), channel)
        
            
    def queryCurrent(self, channel=None):
        """Return what current set value is (not the measured current,
        but the set current)
        
        channel - number of the channel starting at 1
        """

        return self.fetchGenericValue(self._Cmd('queryCurrent'), channel)
    
    
    def queryCurrentRange(self, channel=None):
        """Query the current range for channel

           channel  - number of the channel starting at 1
        """

        return self.queryGenericRange(self._Cmd('queryCurrentRangeAuto'), self._Cmd('queryCurrentRange'), channel)
            
    def setMeasureFunction(self, function, channel=None, wait=None):
        """Set the measure/sense function for the channel
        
           function - a string which names the function. common ones:
                      VOLTage, CURRent, RESistance, POWer, VOLTage:AC, CURRent:AC,
                      CAPacitance, TEMPerature, FREQuency, PERiod
           wait     - number of seconds to wait after sending command
           channel  - number of the channel starting at 1
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
            
        str = self._Cmd('setMeasureFunction').format(function)
        self._instWrite(str)
        sleep(wait)             # give some time for PS to respond
        
    def queryMeasureFunction(self, channel=None, query_delay=None):
        """Return what FUNCTION is the current one for measuring/sensing
        
        channel     - number of the channel starting at 1
        query_delay - number of seconds to wait between write and
                      reading for read data (None uses default seconds)
        """

        return self.fetchGenericString(self._Cmd('queryMeasureFunction'), channel, query_delay)
    
    def measureVoltage(self, channel=None):
        """Read and return a voltage measurement from channel
        
           channel - number of the channel starting at 1
        """

        return self.fetchGenericValue(self._Cmd('measureVoltage'), channel)
    
    def measureVoltageMax(self, channel=None):
        """Read and return the maximum voltage measurement from channel
        
           channel - number of the channel starting at 1
        """

        return self.fetchGenericValue(self._Cmd('measureVoltageMax'), channel)
    
    def measureVoltageMin(self, channel=None):
        """Read and return the minimum voltage measurement from channel
        
           channel - number of the channel starting at 1
        """

        return self.fetchGenericValue(self._Cmd('measureVoltageMin'), channel)
    
    def setMeasureVoltageRange(self, upper, channel=None, wait=None):
        """Set the measurement voltage range for channel

           upper    - floating point value for upper voltage range, set to None for AUTO
           channel  - number of the channel starting at 1
           wait     - number of seconds to wait after sending command
        """

        self.setGenericRange(upper, self._Cmd('setMeasureVoltageRangeAuto'), self._Cmd('setMeasureVoltageRange'), channel, wait)
            #@@@#str = 'SENS:VOLT:CHAN{:1d}:RANG:AUTO {}'.format(self.channel, 'ON')
            #@@@#str = 'SENS:VOLT:CHAN{:1d}:RANG {:.3e}'.format(self.channel,float(upper))
    
    def queryMeasureVoltageRange(self, channel=None):
        """Query the measurement voltage range for channel

           channel  - number of the channel starting at 1
        """

        #@@@#qry = 'SENS:VOLT:CHAN{:1d}:RANG:AUTO?'.format(self.channel)
        #@@@#qry = 'SENS:VOLT:CHAN{:1d}:RANG?'.format(self.channel)
        return self.queryGenericRange(self._Cmd('queryMeasureVoltageRangeAuto'), self._Cmd('queryMeasureVoltageRange'), channel)
            
    def measureCurrent(self, channel=None):
        """Read and return a current measurement from channel
        
           channel - number of the channel starting at 1
        """

        return self.fetchGenericValue(self._Cmd('measureCurrent'), channel)
    
    def measureCurrentMax(self, channel=None):
        """Read and return the maximum current measurement from channel
        
           channel - number of the channel starting at 1
        """

        return self.fetchGenericValue(self._Cmd('measureCurrentMax'), channel)
    
    def measureCurrentMin(self, channel=None):
        """Read and return the minimum current measurement from channel
        
           channel - number of the channel starting at 1
        """

        return self.fetchGenericValue(self._Cmd('measureCurrentMin'), channel)
    
    def setMeasureCurrentRange(self, upper, channel=None, wait=None):
        """Set the measurement current range for channel

           upper    - floating point value for upper current range, set to None for AUTO
           channel  - number of the channel starting at 1
           wait     - number of seconds to wait after sending command
        """

        self.setGenericRange(upper, self._Cmd('setMeasureCurrentRangeAuto'), self._Cmd('setMeasureCurrentRange'), channel, wait)
    
    def queryMeasureCurrentRange(self, channel=None):
        """Query the measurement current range for channel

           channel  - number of the channel starting at 1
        """

        return self.queryGenericRange(self._Cmd('queryMeasureCurrentRangeAuto'), self._Cmd('queryMeasureCurrentRange'), channel)

    def measureResistance(self, channel=None):
        """Read and return a resistance measurement from channel
        
           channel - number of the channel starting at 1
        """

        return self.fetchGenericValue(self._Cmd('measureResistance'), channel)
    
    def measurePower(self, channel=None):
        """Read and return a power measurement from channel
        
           channel - number of the channel starting at 1
        """

        return self.fetchGenericValue(self._Cmd('measurePower'), channel)
    
    
    #-------------------------------------------------------------------------------
    #-------------------------------------------------------------------------------
    # Functions to handle protections
    #-------------------------------------------------------------------------------
    #
    def setGenericProtection(self, value, cmdProt, cmdDelay, delay=None, channel=None, wait=None):
        """Set the generic protection value for the channel
        
           value    - desired protection value as a floating point number
           cmdProt  - SCPI command string to use to set the PROTECTION LEVEL
           cmdDelay - SCPI command string to use to set the PROTECTION DELAY
           delay    - desired protection delay time in seconds (not always supported)
           wait     - number of seconds to wait after sending command
           channel  - number of the channel starting at 1
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
            
        str = cmdProt.format(value)
        self._instWrite(str)
        sleep(wait)             # give some time for PS to respond
        
        if delay is not None:
            str = cmdDelay.format(delay)
            self._instWrite(str)
            sleep(wait)             # give some time for PS to respond
        
    def queryGenericProtection(self, qryProt, channel=None):
        """Return what the generic protection set value is
        
        qryProt - SCPI query command string to use to query the PROTECTION LEVEL
        channel - number of the channel starting at 1
        """

        # If a channel number is passed in, make it the
        # current channel
        if channel is not None:
            self.channel = channel
            
        if (self._max_chan > 1 and channel is not None):
            # If multi-channel device and channel parameter is passed, select it
            self._instWrite(self._Cmd('chanSelect').format(self.channel))
            
        ret = self._instQuery(qryProt)
        return float(ret)
    
    #-------------------------------------------------------------------------------
    # Functions to handle Voltage protections
    #-------------------------------------------------------------------------------
    #
    def setVoltageProtection(self, ovp, delay=None, channel=None, wait=None):
        """Set the over-voltage protection value for the channel
        
           ovp     - desired over-voltage value as a floating point number
           delay   - desired voltage protection delay time in seconds (not always supported)
           wait    - number of seconds to wait after sending command
           channel - number of the channel starting at 1
        """

        self.setGenericProtection(ovp, self._Cmd('setVoltageProtection'), self._Cmd('setVoltageProtectionDelay'), delay, channel, wait)
        
    def queryVoltageProtection(self, channel=None):
        """Return what the over-voltage protection set value is
        
        channel - number of the channel starting at 1
        """
        
        return self.queryGenericProtection(self._Cmd('queryVoltageProtection'), channel)

    def voltageProtectionOn(self, channel=None, wait=None):
        """Enable Over-Voltage Protection on the output for channel
        
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

    def isVoltageProtectionOn(self, channel=None):
        """Return true if voltage protection for channel is ON, else false

           channel - number of the channel starting at 1
        """
        # If a channel number is passed in, make it the current channel
        if channel is not None:
            self.channel = channel

        if (self._max_chan > 1 and channel is not None):
            # If multi-channel device and channel parameter is passed, select it
            self._instWrite(self._Cmd('chanSelect').format(self.channel))

        ret = self._instQuery(self._Cmd('isVoltageProtectionOn'))
        return self._onORoff_1OR0_yesORno(ret)

    def isVoltageProtectionTripped(self, channel=None):
        """Return true if the OverVoltage Protection of channel is Tripped, else false
        
           channel - number of the channel starting at 1
        """

        return self.isGenericTrue(self._Cmd('isVoltageProtectionTripped'), channel)
    
    def voltageProtectionClear(self, channel=None, wait=None):
        """Clear Over-Voltage Protection Trip on the output for channel
        
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
            
        str = self._Cmd('voltageProtectionClear')
        self._instWrite(str)
        sleep(wait)             # give some time for PS to respond
    
    def setVoltageCompliance(self, ovp, channel=None, wait=None):
        """Set the over-voltage compliance value for the channel. This is the measurement value at which the output is disabled.
        
           ovp     - desired over-voltage compliance value as a floating point number
           channel - number of the channel starting at 1
           wait    - number of seconds to wait after sending command
        """

        self.setGenericProtection(ovp, self._Cmd('setVoltageCompliance'), None, None, channel, wait)

    def queryVoltageCompliance(self, channel=None):
        """Return what the over-voltage compliance set value is
        
        channel - number of the channel starting at 1
        """
        
        return self.queryGenericProtection(self._Cmd('queryVoltageCompliance'), channel)

    def isVoltageComplianceTripped(self, channel=None):
        """Return true if the Voltage Compliance of channel is Tripped, else false
        
           channel - number of the channel starting at 1
        """

        return self.isGenericTrue(self._Cmd('isVoltageComplianceTripped'), channel)

    def voltageComplianceClear(self, channel=None, wait=None):
        """Clear Voltage Compliance Trip on the output for channel
        
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
            
        str = self._Cmd('voltageComplianceClear')
        self._instWrite(str)
        sleep(wait)             # give some time for PS to respond
    #
    #-------------------------------------------------------------------------------
    
    #-------------------------------------------------------------------------------
    # Functions to handle Current protections
    #-------------------------------------------------------------------------------
    #
    def setCurrentProtection(self, ocp, delay=None, channel=None, wait=None):
        """Set the over-current protection value for the channel

           ocp     - desired over-current value as a floating point number
           delay   - desired current protection delay time in seconds (not always supported)
           wait    - number of seconds to wait after sending command
           channel - number of the channel starting at 1
        """

        self.setGenericProtection(ocp, self._Cmd('setCurrentProtection'), self._Cmd('setCurrentProtectionDelay'), delay, channel, wait)

    def queryCurrentProtection(self, channel=None):
        """Return what the over-current protection set value is

        channel - number of the channel starting at 1
        """

        return self.queryGenericProtection(self._Cmd('queryCurrentProtection'), channel)

    def currentProtectionOn(self, channel=None, wait=None):
        """Enable Over-Current Protection on the output for channel

           channel - number of the channel starting at 1
           wait    - number of seconds to wait after sending command
        """

        # If a channel number is passed in, make it the current channel
        if channel is not None:
            self.channel = channel

        if (self._max_chan > 1 and channel is not None):
            # If multi-channel device and channel parameter is passed, select it
            self._instWrite(self._Cmd('chanSelect').format(self.channel))

        # If a wait time is NOT passed in, set wait to the
        # default time
        if wait is None:
            wait = self._wait

        str = self._Cmd('currentProtectionOn')
        self._instWrite(str)
        sleep(wait)             # give some time for PS to respond

    def currentProtectionOff(self, channel=None, wait=None):
        """Disable Over-Current Protection on the output for channel

           channel - number of the channel starting at 1
        """

        # If a channel number is passed in, make it the current channel
        if channel is not None:
            self.channel = channel

        if (self._max_chan > 1 and channel is not None):
            # If multi-channel device and channel parameter is passed, select it
            self._instWrite(self._Cmd('chanSelect').format(self.channel))

        # If a wait time is NOT passed in, set wait to the
        # default time
        if wait is None:
            wait = self._wait

        str = self._Cmd('currentProtectionOff')
        self._instWrite(str)
        sleep(wait)             # give some time for PS to respond

    def isCurrentProtectionOn(self, channel=None):
        """Return true if current protection for channel is ON, else false

           channel - number of the channel starting at 1
        """

        # If a channel number is passed in, make it the current channel
        if channel is not None:
            self.channel = channel

        if (self._max_chan > 1 and channel is not None):
            # If multi-channel device and channel parameter is passed, select it
            self._instWrite(self._Cmd('chanSelect').format(self.channel))

        ret = self._instQuery(self._Cmd('isCurrentProtectionOn'))
        return self._onORoff_1OR0_yesORno(ret)

    def isCurrentProtectionTripped(self, channel=None):
        """Return true if the OverCurrent Protection of channel is Tripped, else false
        
           channel - number of the channel starting at 1
        """

        return self.isGenericTrue(self._Cmd('isCurrentProtectionTripped'), channel)
    
    def currentProtectionClear(self, channel=None, wait=None):
        """Clear Over-Current Protection Trip on the output for channel
        
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
            
        str = self._Cmd('currentProtectionClear')
        self._instWrite(str)
        sleep(wait)             # give some time for PS to respond
    
    def setCurrentCompliance(self, ocp, channel=None, wait=None):
        """Set the over-current compliance value for the channel. This is the measurement value at which the output is disabled.
        
           ocp     - desired over-current compliance value as a floating point number
           channel - number of the channel starting at 1
           wait    - number of seconds to wait after sending command
        """

        self.setGenericProtection(ocp, self._Cmd('setCurrentCompliance'), None, None, channel, wait)

    def queryCurrentCompliance(self, channel=None):
        """Return what the over-current compliance set value is
        
        channel - number of the channel starting at 1
        """
        
        return self.queryGenericProtection(self._Cmd('queryCurrentCompliance'), channel)

    def isCurrentComplianceTripped(self, channel=None):
        """Return true if the Current Compliance of channel is Tripped, else false
        
           channel - number of the channel starting at 1
        """

        return self.isGenericTrue(self._Cmd('isCurrentComplianceTripped'), channel)

    def currentComplianceClear(self, channel=None, wait=None):
        """Clear Current Compliance Trip on the output for channel
        
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
            
        str = self._Cmd('currentComplianceClear')
        self._instWrite(str)
        sleep(wait)             # give some time for PS to respond
    #
    #-------------------------------------------------------------------------------
    #-------------------------------------------------------------------------------
    
