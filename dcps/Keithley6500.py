#!/usr/bin/env python
# -*- coding: utf-8 -*-
#

# Copyright (c) 2018, 2021, 2023, Stephen Goadhouse <sgoadhouse@virginia.edu>
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
#  Control a Keithley DMM6500 Digital Multimeter (DMM) with PyVISA
#-------------------------------------------------------------------------------

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


class Keithley6500(SCPI):
    """Basic class for controlling and accessing a Keithley/Tektronix DMM6500 digital multimeter"""

    ## Dictionary to translate SCPI commands for this device
    _xlateCmdTbl = {
        'setMeasureVoltageRange':        'SENSe{:1d}:VOLTage:RANGe {}', # removed format of value so can use DEF/MIN/MAX
        'setMeasureCurrentRange':        'SENSe{:1d}:CURRent:RANGe {}', # removed format of value so can use DEF/MIN/MAX
    }

    def __init__(self, resource, wait=0.01, verbosity=0, **kwargs):
        """Init the class with the instruments resource string

        resource - resource string or VISA descriptor, like TCPIP0::172.16.2.13::INSTR
        wait     - float that gives the default number of seconds to wait after sending each command
        verbosity - verbosity output - set to 0 for no debug output
        kwargs    - other named options to pass when PyVISA open() like open_timeout=2.0
        """
        self._functions = { 'VoltageDC':   'VOLT:DC',
                            'VoltageAC':   'VOLT:AC',
                            'CurrentDC':   'CURR:DC',
                            'CurrentAC':   'CURR:AC',
                            'Resistance2W':'RES',
                            'Resistance4W':'FRES',
                            'Diode':       'DIOD',
                            'Capacitance': 'CAP',
                            'Temperature': 'TEMP',
                            'Continuity':  'CONT',
                            'Frequency':   'FREQ:VOLT',
                            'Period':      'PER:VOLT',
                            'VoltageRatio':'VOLT:DC:RAT',
                           }
        # default measurement function if not supplied as parameter into the method
        self._functionStr = None
        
        super(Keithley6500, self).__init__(resource, max_chan=1, wait=wait, cmd_prefix=':',
                                           verbosity = verbosity,
                                           read_termination = '\n',
                                           query_delay=0.01,
                                           **kwargs)
    @property
    def functions(self):
        return self._functions

    def _handleMeasureFunction(self,function,methodName,allowedCmdFunctions=None):
        """Process the passed-in measure/sense function name and return the Funciton Command String to use"""

        if (function is None):
            # Ask the instrument what function is the current one
            functionCmdStr = self.queryMeasureFunction()
            functionPrint = functionCmdStr
        else:
            # Else, use the passed in function string
            #
            # Lookup function
            functionCmdStr = self._functions.get(function)
            functionPrint = function
            if not functionCmdStr:
                raise ValueError('{}: "{}" is an unknown function.'.format(methodName,functionPrint))

        if (allowedCmdFunctions is not None):
            ## if allowedCmdFunctions is not None, check to see if
            ## functionCmdStr is listed. If not, it is not a supported
            ## function for the method calling this.  Raise
            ## ValueError() in that case.
            if (functionCmdStr not in allowedCmdFunctions):
                raise ValueError('{}: this method is invalid for function "{}".'.format(methodName,functionPrint))

        #@@@#print("_handleMeasureFunction(): Measure Function Cmd String: " + functionCmdStr)
            
        return functionCmdStr
        
    def setLocal(self):
        """Set the instrument to LOCAL mode where front panel keys
        work again. Also restore Continuous reading mode.

        """
        self._instWrite('TRIG:CONT REST')
        sleep(0.01)
        self._instQuery('-LOGOUT')

    def setRemote(self):
        """Set the instrument to REMOTE mode where it is controlled via VISA
        """

        # NOTE: Unsupported command by this device. However, with any
        # command sent to the DMM6500, it automatically goes into
        # REMOTE mode. Instead of raising an exception and breaking
        # any scripts, simply return quietly.
        pass
    
    def setRemoteLock(self):
        """Set the instrument to REMOTE Lock mode where it is
           controlled via VISA & front panel is locked out
        """
        # NOTE: Unsupported command by this device. However, with any
        # command sent to the DMM6500, it automatically goes into
        # REMOTE mode. Instead of raising an exception and breaking
        # any scripts, simply return quietly.
        #
        # Truth be told, there is a SYSTEM:ACCESS command which has
        # various options and could be used here but for simplicity,
        # ignore that for now.
        pass
        
    def beeperOn(self):
        """Enable the system beeper for the instrument"""
        # NOTE: Unsupported command by this device. However,
        # instead of raising an exception and breaking any scripts,
        # simply return quietly.
        pass
        
    def beeperOff(self):
        """Disable the system beeper for the instrument"""
        # NOTE: Unsupported command by this device. However,
        # instead of raising an exception and breaking any scripts,
        # simply return quietly.
        pass
        
    def isOutputOn(self, channel=None):
        """Return true if the output of channel is ON, else false
        
           channel - number of the channel starting at 1
        """
        # NOTE: Unsupported command by this device. However,
        # instead of raising an exception and breaking any scripts,
        # simply return False as there is NO output for the DMM6500.
        return False

    def outputOn(self, channel=None, wait=None):
        """Turn on the output for channel
        
           wait    - number of seconds to wait after sending command
           channel - number of the channel starting at 1
        """
        # NOTE: Unsupported command by this device. However,
        # instead of raising an exception and breaking any scripts,
        # simply return quietly.
        pass
        
    def outputOff(self, channel=None, wait=None):
        """Turn off the output for channel
        
           channel - number of the channel starting at 1
        """
        # NOTE: Unsupported command by this device. However,
        # instead of raising an exception and breaking any scripts,
        # simply return quietly.
        pass

    def outputOnAll(self, wait=None):
        """Turn on the output for ALL channels
        
        """
        # NOTE: Unsupported command by this device. However,
        # instead of raising an exception and breaking any scripts,
        # simply return quietly.
        pass

    def outputOffAll(self, wait=None):
        """Turn off the output for ALL channels
        
        """
        # NOTE: Unsupported command by this device. However,
        # instead of raising an exception and breaking any scripts,
        # simply return quietly.
        pass

    def isInputOn(self, channel=None):
        """Return true if the input of channel is ON, else false
        
           channel - number of the channel starting at 1
        """
        # NOTE: Unsupported command by this device. However,
        # instead of raising an exception and breaking any scripts,
        # simply return True as the "INPUT" is always On for the DMM6500.
        return True

    def inputOn(self, channel=None, wait=None):
        """Turn on the input for channel
        
           wait    - number of seconds to wait after sending command
           channel - number of the channel starting at 1
        """
        # NOTE: Unsupported command by this device. However,
        # instead of raising an exception and breaking any scripts,
        # simply return quietly.
        pass

    def inputOff(self, channel=None, wait=None):
        """Turn off the input for channel
        
           channel - number of the channel starting at 1
        """
        # NOTE: Unsupported command by this device. However,
        # instead of raising an exception and breaking any scripts,
        # simply return quietly.
        pass

    def inputOnAll(self, wait=None):
        """Turn on the input for ALL channels
        
        """
        # NOTE: Unsupported command by this device. However,
        # instead of raising an exception and breaking any scripts,
        # simply return quietly.
        pass

    def inputOffAll(self, wait=None):
        """Turn off the input for ALL channels
        
        """
        # NOTE: Unsupported command by this device. However,
        # instead of raising an exception and breaking any scripts,
        # simply return quietly.
        pass

        
    ###################################################################
    # Commands Specific to DMM6500
    ###################################################################

    def displayMessageOn(self, top=True):
        """Enable Display Message
           NOTE: using same format as from Keithley622x.py but this one works a little differently
        
           top     - True if enabling the Top message, else enable Bottom message
        """

        ## top is ignored
        ## swipe screen to show User text
        self._instWrite('DISPlay:SCReen SWIPE_USER')

    def displayMessageOff(self, top=True):
        """Disable Display Message
           NOTE: using same format as from Keithley622x.py but this one works a little differently
        
           top     - True if disabling the Top message, else disable Bottom message
        """

        ## top is ignored
        ## first clear out user message and then ...
        ## swipe screen to show HOME - does not have a display disable as Keithley622x does
        self._instWrite('DISPlay:CLE')
        self._instWrite('DISPlay:SCReen HOME')

            
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
            self._instWrite('DISP:USER1:TEXT "{}"'.format(message))
        else:
            # Maximum of 32 characters for bottom message
            if (len(message) > 32):
                message = message[:32]
            self._instWrite('DISP:USER2:TEXT "{}"'.format(message))

    def setMeasureFunction(self, function, channel=None, wait=None):
        """Set the Measure Function for channel

           function   - a key from self._functions{} that selects the measurement function
           channel    - number of the channel starting at 1
           wait       - number of seconds to wait after sending command

           NOTE: Error raised if function is unknown
        """

        # Lookup function command string
        functionCmdStr = self._functions.get(function)
        if not functionCmdStr:
            raise ValueError('setMeasureFunction(): "{}" is an unknown function.'.format(function))

        # function must be valid, so save it for future use
        self._functionStr = function
        
        # If a channel number is passed in, make it the
        # current channel
        if channel is not None:
            self.channel = channel

        # If a wait time is NOT passed in, set wait to the
        # default time
        if wait is None:
            wait = self._wait

        str = 'SENS{}:FUNC:ON "{}"'.format(self.channel, functionCmdStr)            
        #@@@#print("   setMeasureFunction() string: '{}'".format(str))
        
        self._instWrite(str)

    def setAutoZero(self, on, function=None, channel=None, wait=None):
        """Enable or Disable the AutoZero mode for the function

           on         - set to True to Enable AutoZero or False to Disable AutoZero
           function   - a key from self._functions{} to select the measurement function or None for default
           channel    - number of the channel starting at 1
           wait       - number of seconds to wait after sending command
        """

        functionCmdStr = self._handleMeasureFunction(function,"setAutoZero()",
                                                     ['VOLT:DC','CURR:DC','RES','FRES','DIOD','TEMP','VOLT:DC:RAT',])
                    
        # If a channel number is passed in, make it the
        # current channel
        if channel is not None:
            self.channel = channel

        # If a wait time is NOT passed in, set wait to the
        # default time
        if wait is None:
            wait = self._wait

        str = 'SENS{}:{}:AZERo:STATe {}'.format(self.channel, functionCmdStr, self._bool2onORoff(on))
        #@@@#print('AutoZero State String: {}'.format(str))

        self._instWrite(str)

        sleep(wait)             # give some time for device to respond
        
        
    def autoZeroOnce(self, channel=None, wait=None):
        """Issue an AutoZero command to be performed once. Oddly, it takes no function name.

           channel    - number of the channel starting at 1
           wait       - number of seconds to wait after sending command
        """
        
        # If a channel number is passed in, make it the
        # current channel
        if channel is not None:
            self.channel = channel

        # If a wait time is NOT passed in, set wait to the
        # default time
        if wait is None:
            wait = self._wait

        str = 'SENS{}:AZERo:ONCE'.format(self.channel)
        #@@@#print('AutoZero Once String: {}'.format(str))

        self._instWrite(str)

        sleep(wait)             # give some time for device to respond

        self._waitCmd()         # make sure command is complete in instrument

        
    def setRelativeOffset(self, offset=None, function=None, channel=None, wait=None):
        """Set the Relative Offset for the Function

           offset     - floating point value to set as relative offset or, if None, have instrument acquire it
                        offset can also be "DEF" for default, "MAX" for maximum or "MIN" for minimum
           function   - a key from self._functions{} to select the measurement function or None for default
           channel    - number of the channel starting at 1
           wait       - number of seconds to wait after sending command
        """

        functionCmdStr = self._handleMeasureFunction(function,"setRelativeOffset()")
                    
        # If a channel number is passed in, make it the
        # current channel
        if channel is not None:
            self.channel = channel

        # If a wait time is NOT passed in, set wait to the
        # default time
        if wait is None:
            wait = self._wait

        if (offset is None):
            ## Have the instrument acquire the relative offset
            str = 'SENS{}:{}:REL:ACQuire'.format(self.channel, functionCmdStr)
        else:
            str = 'SENS{}:{}:REL {}'.format(self.channel, functionCmdStr, offset)

        #@@@#print('Relative Offset String: {}'.format(str))

        self._instWrite(str)

        sleep(wait)             # give some time for device to respond
        
        
    def queryRelativeOffset(self, function=None, channel=None, wait=None):
        """Query the Relative Offset for the Function

           function   - a key from self._functions{} to select the measurement function or None for default
           channel    - number of the channel starting at 1
           wait       - number of seconds to wait after sending command
        """

        functionCmdStr = self._handleMeasureFunction(function,"queryRelativeOffset()")

                    
        # If a channel number is passed in, make it the
        # current channel
        if channel is not None:
            self.channel = channel

        # If a wait time is NOT passed in, set wait to the
        # default time
        if wait is None:
            wait = self._wait


        str = 'SENS{}:{}:REL?'.format(self.channel, functionCmdStr)

        #@@@#print('Relative Offset Query String: {}'.format(str))

        offset = self._instQuery(str)

        sleep(wait)             # give some time for device to respond

        return float(offset)
    
    def setRelativeOffsetState(self, on, function=None, channel=None, wait=None):
        """Set the Relative Offset State for the Function

           on         - set to True to Enable use of Relative Offset or False to Disable it
           function   - a key from self._functions{} to select the measurement function or None for default
           channel    - number of the channel starting at 1
           wait       - number of seconds to wait after sending command
        """

        functionCmdStr = self._handleMeasureFunction(function,"setRelativeOffsetState()")

                    
        # If a channel number is passed in, make it the
        # current channel
        if channel is not None:
            self.channel = channel

        # If a wait time is NOT passed in, set wait to the
        # default time
        if wait is None:
            wait = self._wait

        str = 'SENS{}:{}:REL:STATe {}'.format(self.channel, functionCmdStr, self._bool2onORoff(on))

        #@@@#print('Relative Offset State String: {}'.format(str))

        self._instWrite(str)

        sleep(wait)             # give some time for device to respond

        
    def setIntegrationTime(self, nplc, function=None, channel=None, wait=None):
        """Set the time that the input signal is measured for the selected Function

           nplc       - number of power-line cycles as a floating point number
                        nplc can also be "DEF" for default, "MAX" for maximum or "MIN" for minimum
           function   - a key from self._functions{} to select the measurement function or None for default
           channel    - number of the channel starting at 1
           wait       - number of seconds to wait after sending command
        """

        functionCmdStr = self._handleMeasureFunction(function,"setIntegrationTime()")
                    
        # If a channel number is passed in, make it the
        # current channel
        if channel is not None:
            self.channel = channel

        # If a wait time is NOT passed in, set wait to the
        # default time
        if wait is None:
            wait = self._wait

        str = 'SENS{}:{}:NPLC {}'.format(self.channel, functionCmdStr, nplc)

        #@@@#print('Integration Time String: {}'.format(str))

        self._instWrite(str)

        sleep(wait)             # give some time for device to respond
        
        
    def queryIntegrationTime(self, function=None, channel=None, wait=None):
        """Query the set time to measure the input signal for the selected function

           function   - a key from self._functions{} to select the measurement function or None for default
           channel    - number of the channel starting at 1
           wait       - number of seconds to wait after sending command
        """

        functionCmdStr = self._handleMeasureFunction(function,"queryIntegrationTime()")
                    
        # If a channel number is passed in, make it the
        # current channel
        if channel is not None:
            self.channel = channel

        # If a wait time is NOT passed in, set wait to the
        # default time
        if wait is None:
            wait = self._wait


        str = 'SENS{}:{}:NPLC?'.format(self.channel, functionCmdStr)

        #@@@#print('Integration Time Query String: {}'.format(str))

        offset = self._instQuery(str)

        sleep(wait)             # give some time for device to respond

        return float(offset)

    ## Can use setMeasureVoltageRange()/setMeasureCurrentRange()
    ## inherited from SCPI.py. This method is here to support the
    ## other functions of the DMM9500 using the multiple function
    ## parameter format. Voltage and Current can be used here too.
    def setMeasureRange(self, upper, function=None, channel=None, wait=None):
        """Set the measurement range for the selected function and channel

           upper    - floating point value for (upper) range, set to None for AUTO
           function - a key from self._functions{} to select the measurement function or None for default
           channel  - number of the channel starting at 1
           wait     - number of seconds to wait after sending command
        """

        functionCmdStr = self._handleMeasureFunction(function,"setMeasureRange()",
                                                     ['VOLT:DC','VOLT:AC','CURR:DC','CURR:AC','RES','FRES','CAP','VOLT:DC:RAT',])
        
        cmdAuto =  'SENSe{:1d}:' + functionCmdStr + ':RANGe:AUTO {}'
        cmdRange = 'SENSe{:1d}:' + functionCmdStr + ':RANGe {}'
        
        self.setGenericRange(upper, cmdAuto, cmdRange, channel, wait)
    
    ## Can use queryMeasureVoltageRange()/queryMeasureCurrentRange()
    ## inherited from SCPI.py. This method is here to support the
    ## other functions of the DMM9500 using the multiple function
    ## parameter format. Voltage and Current can be used here too.
    def queryMeasureRange(self, function=None, channel=None):
        """Query the measurement range for selected function and channel

           function - a key from self._functions{} to select the measurement function or None for default
           channel  - number of the channel starting at 1
        """

        functionCmdStr = self._handleMeasureFunction(function,"queryMeasureRange()",
                                                     ['VOLT:DC','VOLT:AC','CURR:DC','CURR:AC','RES','FRES','CAP','VOLT:DC:RAT',])

        cmdAuto =  'SENSe{:1d}:' + functionCmdStr + ':RANGe:AUTO?'
        cmdRange = 'SENSe{:1d}:' + functionCmdStr + ':RANGe?'

        return self.queryGenericRange(cmdAuto, cmdRange, channel)


    def measureVoltage(self, channel=None, query_delay=None):
        """Read and return a DC Voltage measurement from channel
        
           channel - number of the channel starting at 1
        """

        self.setMeasureFunction(function="VoltageDC",channel=channel)

        #@@@#vals = self._instQuery('READ?').split(',')
        val = self._instQuery('READ?',delay=query_delay)        
        #@@@#print('Value: "{}" / {}'.format(val,float(val)))
        return float(val)
        
    def measureVoltageAC(self, channel=None, query_delay=None):
        """Read and return an AC Voltage measurement from channel
        
           channel - number of the channel starting at 1
        """

        self.setMeasureFunction(function="VoltageAC",channel=channel)

        val = self._instQuery('READ?',delay=query_delay)
        return float(val)
        
    def measureCurrent(self, channel=None, query_delay=None):
        """Read and return a DC Current measurement from channel
        
           channel - number of the channel starting at 1
        """

        self.setMeasureFunction(function="CurrentDC",channel=channel)

        val = self._instQuery('READ?',delay=query_delay)        
        return float(val)
        
    def measureCurrentAC(self, channel=None, query_delay=None):
        """Read and return an AC Current measurement from channel
        
           channel - number of the channel starting at 1
        """

        self.setMeasureFunction(function="CurrentAC",channel=channel)

        val = self._instQuery('READ?',delay=query_delay)        
        return float(val)

    def measureResistance(self, channel=None, query_delay=None):
        """Read and return a resistance measurement from channel
        
           channel - number of the channel starting at 1
        """

        self.setMeasureFunction(function="Resistance2W",channel=channel)

        val = self._instQuery('READ?',delay=query_delay)        
        return float(val)
        
    def measureResistance4W(self, channel=None, query_delay=None):
        """Read and return a resistance measurement using 4-Wire from channel
        
           channel - number of the channel starting at 1
        """

        self.setMeasureFunction(function="Resistance4W",channel=channel)

        val = self._instQuery('READ?',delay=query_delay)        
        return float(val)
        
    def measureDiode(self, channel=None, query_delay=None):
        """Read and return a diode measurement from channel
        
           channel - number of the channel starting at 1
        """

        self.setMeasureFunction(function="Diode",channel=channel)

        val = self._instQuery('READ?',delay=query_delay)        
        return float(val)
        
    def measureCapacitance(self, channel=None, query_delay=None):
        """Read and return a capacitance measurement from channel
        
           channel - number of the channel starting at 1
        """

        self.setMeasureFunction(function="Capacitance",channel=channel)

        val = self._instQuery('READ?',delay=query_delay)        
        return float(val)

    def measureTemperature(self, channel=None, query_delay=None):
        """Read and return a temperature measurement from channel
        
           channel - number of the channel starting at 1
        """

        self.setMeasureFunction(function="Temperature",channel=channel)

        val = self._instQuery('READ?',delay=query_delay)        
        return float(val)

    def measureContinuity(self, channel=None, query_delay=None):
        """Read and return a continuity measurement from channel
        
           channel - number of the channel starting at 1
        """

        self.setMeasureFunction(function="Continuity",channel=channel)

        val = self._instQuery('READ?',delay=query_delay)        
        return float(val)

    def measureFrequency(self, channel=None, query_delay=None):
        """Read and return a frequency measurement from channel
        
           channel - number of the channel starting at 1
        """

        self.setMeasureFunction(function="Frequency",channel=channel)

        val = self._instQuery('READ?',delay=query_delay)        
        return float(val)

    def measurePeriod(self, channel=None, query_delay=None):
        """Read and return a period measurement from channel
        
           channel - number of the channel starting at 1
        """

        self.setMeasureFunction(function="Period",channel=channel)

        val = self._instQuery('READ?',delay=query_delay)        
        return float(val)

    def measureVoltageRatio(self, channel=None, query_delay=None):
        """Read and return a voltage ratio measurement from channel
        
           channel - number of the channel starting at 1
        """

        self.setMeasureFunction(function="VoltageRatio",channel=channel)

        val = self._instQuery('READ?',delay=query_delay)        
        return float(val)

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Access and control a Keithley DMM6500 digital multimeter')
    parser.add_argument('chan', nargs='?', type=int, help='Channel to access/control (starts at 1)', default=1)
    args = parser.parse_args()

    from time import sleep
    from os import environ
    resource = environ.get('DMM6500_VISA', 'TCPIP0::172.16.2.13::INSTR')
    dmm = Keithley6500(resource)
    dmm.open()

    # Reset
    dmm.rst(wait=1.0)
    dmm.cls(wait=1.0)

    print(dmm.idn())


    ## set Remote Lock On
    dmm.setRemoteLock()

    dmm.beeperOff()

    ## For determing the Functiona names output when querying the current function
    #for i in range(0,14):
    #    dmm.queryMeasureFunctionStr()
    #    dmm.setLocal()
    #    input("Press Enter to continue...") 
    #    dmm.setRemoteLock()
    
    # Set display messages
    dmm.setDisplayMessage('Bottom Message', top=False)
    dmm.setDisplayMessage('Top Message', top=True)

    # Enable messages
    dmm.displayMessageOn()
    sleep(2.0)

    dmm.setDisplayMessage('New Top Message', top=True)
    dmm.setDisplayMessage('New Bottom Message', top=False)
    sleep(2.0)

    # Disable messages
    dmm.displayMessageOff()

    if not dmm.isInputOn(args.chan):
        dmm.inputOn()

    dmm.measureVoltage()
    dmm.setAutoZero(False)
    dmm.setAutoZero(False,function='CurrentDC')
    dmm.setAutoZero(True)
    dmm.setAutoZero(True,function='CurrentDC')
    #@@@#dmm.setMeasureFunction(function='CurrentAC')
    dmm.autoZeroOnce()

    dmm.setRelativeOffset()
    dmm.setRelativeOffset(0.0034567, function='CurrentDC')

    print('Relative Offsets: {:9.7g} V {:9.7g} A'.format(dmm.queryRelativeOffset(),dmm.queryRelativeOffset(function='CurrentDC')))

    dmm.setRelativeOffsetState(True)
    dmm.setRelativeOffsetState(True,function='CurrentDC')

    print('{:9.7g} V'.format(dmm.measureVoltage()))
    print('{:9.7g} V'.format(dmm.measureVoltage()))
    print('{:9.7g} V'.format(dmm.measureVoltage()))
    print('{:9.7g} V'.format(dmm.measureVoltage()))
    print('{:9.7g} V'.format(dmm.measureVoltage()))

    print('{:6.4g} A'.format(dmm.measureCurrent()))
    print('{:6.4g} A'.format(dmm.measureCurrent()))
    print('{:6.4g} A'.format(dmm.measureCurrent()))
    print('{:6.4g} A'.format(dmm.measureCurrent()))
    print('{:6.4g} A'.format(dmm.measureCurrent()))
    print('')

    dmm.setRelativeOffsetState(False,function='VoltageDC')
    dmm.setRelativeOffsetState(False)

    print('Integration Time (DC Voltage): {} NPLC'.format(dmm.queryIntegrationTime(function='VoltageDC')))
    print('Integration Time (DC Current): {} NPLC'.format(dmm.queryIntegrationTime(function='CurrentDC')))

    print('{:9.7g} V'.format(dmm.measureVoltage()))
    print('{:9.7g} V'.format(dmm.measureVoltage()))
    print('{:9.7g} V'.format(dmm.measureVoltage()))
    print('{:9.7g} V'.format(dmm.measureVoltage()))
    print('{:9.7g} V'.format(dmm.measureVoltage()))

    print('{:6.4g} A'.format(dmm.measureCurrent()))
    print('{:6.4g} A'.format(dmm.measureCurrent()))
    print('{:6.4g} A'.format(dmm.measureCurrent()))
    print('{:6.4g} A'.format(dmm.measureCurrent()))
    print('{:6.4g} A'.format(dmm.measureCurrent()))

    dmm.setRelativeOffset("MAXIMUM", function='VoltageDC')
    dmm.setRelativeOffset("DEF", function='CurrentDC')

    print('Relative Offsets: {:9.7g} V {:9.7g} A'.format(dmm.queryRelativeOffset(function='VoltageDC'),dmm.queryRelativeOffset(function='CurrentDC')))

    print('')
    dmm.setIntegrationTime(10.0,function='VoltageDC')
    dmm.setIntegrationTime(10.0,function='CurrentDC')
    print('Integration Time (DC Voltage): {} NPLC'.format(dmm.queryIntegrationTime(function='VoltageDC')))
    print('Integration Time (DC Current): {} NPLC'.format(dmm.queryIntegrationTime(function='CurrentDC')))

    print('{:9.7g} V'.format(dmm.measureVoltage()))
    print('{:9.7g} V'.format(dmm.measureVoltage()))
    print('{:9.7g} V'.format(dmm.measureVoltage()))
    print('{:9.7g} V'.format(dmm.measureVoltage()))
    print('{:9.7g} V'.format(dmm.measureVoltage()))

    print('{:6.4g} A'.format(dmm.measureCurrent()))
    print('{:6.4g} A'.format(dmm.measureCurrent()))
    print('{:6.4g} A'.format(dmm.measureCurrent()))
    print('{:6.4g} A'.format(dmm.measureCurrent()))
    print('{:6.4g} A'.format(dmm.measureCurrent()))

    print('')
    print('ASCII SIG FIGs: {}'.format(dmm.queryAsciiPrecision()))
    print('{:16.14g} V'.format(dmm.measureVoltage()))
    print('Set Sig Figs to MAX:')
    dmm.setAsciiPrecision('MAX')
    print('ASCII SIG FIGs: {}'.format(dmm.queryAsciiPrecision()))
    print('{:16.14g} V'.format(dmm.measureVoltage()))
    print('Set Sig Figs to 0 (automatic):')
    dmm.setAsciiPrecision(0)
    print('ASCII SIG FIGs: {}'.format(dmm.queryAsciiPrecision()))
    print('{:16.14g} V'.format(dmm.measureVoltage()))
    print('Set Sig Figs to 10:')
    dmm.setAsciiPrecision(10)
    print('ASCII SIG FIGs: {}'.format(dmm.queryAsciiPrecision()))
    print('{:16.14g} V'.format(dmm.measureVoltage()))

    print('')
    print('Voltage DC    Range: {}'.format(dmm.queryMeasureVoltageRange()))
    print('Voltage DC    Range: {}'.format(dmm.queryMeasureRange(function='VoltageDC')))
    print('Voltage AC    Range: {}'.format(dmm.queryMeasureRange(function='VoltageAC')))
    print('Current DC    Range: {}'.format(dmm.queryMeasureCurrentRange()))
    print('Current AC    Range: {}'.format(dmm.queryMeasureRange(function='CurrentDC')))
    print('Current AC    Range: {}'.format(dmm.queryMeasureRange(function='CurrentAC')))
    print('Resistance 2W Range: {}'.format(dmm.queryMeasureRange(function='Resistance2W')))
    print('Resistance 4W Range: {}'.format(dmm.queryMeasureRange(function='Resistance4W')))
    #@@@#print('Diode         Range: {}'.format(dmm.queryMeasureRange(function='Diode')))
    print('Capacitance   Range: {}'.format(dmm.queryMeasureRange(function='Capacitance')))
    #@@@#print('Temperature   Range: {}'.format(dmm.queryMeasureRange(function='Temperature')))
    #@@@#print('Continuity    Range: {}'.format(dmm.queryMeasureRange(function='Continuity')))
    #@@@#print('Frequency     Range: {}'.format(dmm.queryMeasureRange(function='Frequency')))
    #@@@#print('Period        Range: {}'.format(dmm.queryMeasureRange(function='Period')))
    print('VoltageRatio  Range: {}'.format(dmm.queryMeasureRange(function='VoltageRatio')))

    print('\nSetting ranges')
    dmm.setMeasureVoltageRange(3e-3)
    dmm.setMeasureRange(4e-2,function='VoltageAC')
    dmm.setMeasureCurrentRange(5e-6)
    dmm.setMeasureRange(2,function='CurrentAC')
    dmm.setMeasureRange(6e3,function='Resistance2W')
    dmm.setMeasureRange(7e-4,function='Resistance4W')
    dmm.setMeasureRange(8e-9,function='Capacitance')
    dmm.setMeasureRange(9e-4,function='VoltageRatio')
    
    print('Voltage DC    Range: {}'.format(dmm.queryMeasureVoltageRange()))
    print('Voltage AC    Range: {}'.format(dmm.queryMeasureRange(function='VoltageAC')))
    print('Current DC    Range: {}'.format(dmm.queryMeasureCurrentRange()))
    print('Current AC    Range: {}'.format(dmm.queryMeasureRange(function='CurrentAC')))
    print('Resistance 2W Range: {}'.format(dmm.queryMeasureRange(function='Resistance2W')))
    print('Resistance 4W Range: {}'.format(dmm.queryMeasureRange(function='Resistance4W')))
    print('Capacitance   Range: {}'.format(dmm.queryMeasureRange(function='Capacitance')))
    print('VoltageRatio  Range: {}'.format(dmm.queryMeasureRange(function='VoltageRatio')))

    print('\nSetting ranges #2')
    dmm.setMeasureVoltageRange('MAX')
    dmm.setMeasureRange('MIN',function='VoltageAC')
    dmm.setMeasureCurrentRange(None)
    dmm.setMeasureRange('DEF',function='CurrentAC')
    dmm.setMeasureRange('MAX',function='Resistance2W')
    dmm.setMeasureRange('MIN',function='Resistance4W')
    dmm.setMeasureRange(None,function='Capacitance')
    dmm.setMeasureRange('Def',function='VoltageRatio')
    
    print('Voltage DC    Range: {}'.format(dmm.queryMeasureVoltageRange()))
    print('Voltage AC    Range: {}'.format(dmm.queryMeasureRange(function='VoltageAC')))
    print('Current DC    Range: {}'.format(dmm.queryMeasureCurrentRange()))
    print('Current AC    Range: {}'.format(dmm.queryMeasureRange(function='CurrentAC')))
    print('Resistance 2W Range: {}'.format(dmm.queryMeasureRange(function='Resistance2W')))
    print('Resistance 4W Range: {}'.format(dmm.queryMeasureRange(function='Resistance4W')))
    print('Capacitance   Range: {}'.format(dmm.queryMeasureRange(function='Capacitance')))
    print('VoltageRatio  Range: {}'.format(dmm.queryMeasureRange(function='VoltageRatio')))


    if (1):
        # Reset again and try reading from all functions, except DIODE
        # which may be determental to any circuits we are connected to
        # during testing.
        dmm.rst(wait=1.0)
        dmm.cls(wait=1.0)

        print('')
        #@@@#print('Integration Time (DC Voltage): {} NPLC'.format(dmm.queryIntegrationTime(function='VoltageDC')))
        #@@@#print('Integration Time (DC Current): {} NPLC'.format(dmm.queryIntegrationTime(function='CurrentDC')))    
        print('AC Voltage:  {:6.4g} V'.format(dmm.measureVoltageAC(query_delay=3.0)))
        print('AC Current:  {:6.4g} A'.format(dmm.measureCurrentAC(query_delay=3.0)))
        print('Resistance:  {:6.4g} Ohm'.format(dmm.measureResistance()))
        print('Resistance (4W): {:6.4g} Ohm'.format(dmm.measureResistance4W()))
        #@@@#print('{:6.4g} V'.format(dmm.measureDiode()))
        print('Capacitance: {:6.4g} F'.format(dmm.measureCapacitance()))
        print('Temperature: {:6.4g} C'.format(dmm.measureTemperature()))
        print('Continuity:  {:6.4g} Ohm'.format(dmm.measureContinuity()))
        print('Frequency:   {:6.4g} Hz'.format(dmm.measureFrequency(query_delay=3.0)))
        print('Period:      {:6.4g} s'.format(dmm.measurePeriod(query_delay=3.0)))
        print('Volt Ratio:  {:6.4g} V/V'.format(dmm.measureVoltageRatio()))
    
    ## turn off the channel
    dmm.inputOff()

    dmm.beeperOn()

    ## return to LOCAL mode
    dmm.setLocal()
    
    dmm.close()
