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

    def __init__(self, resource, wait=1.0, verbosity=3, **kwargs):
        """Init the class with the instruments resource string

        resource - resource string or VISA descriptor, like TCPIP0::172.16.2.13::INSTR
        wait     - float that gives the default number of seconds to wait after sending each command
        verbosity - verbosity output - set to 0 for no debug output
        kwargs    - other named options to pass when PyVISA open() like open_timeout=2.0
        """
        super(Keithley6500, self).__init__(resource, max_chan=1, wait=wait, cmd_prefix=':', verbosity = verbosity, **kwargs)


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

    #@@@@@@# Functions from Keithley2400.py - need to update for DMM6500
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
    parser = argparse.ArgumentParser(description='Access and control a Keithley DMM6500 digital multimeter')
    parser.add_argument('chan', nargs='?', type=int, help='Channel to access/control (starts at 1)', default=1)
    args = parser.parse_args()

    from time import sleep
    from os import environ
    resource = environ.get('DMM6500_VISA', 'TCPIP0::172.16.2.13::INSTR')
    dmm = Keithley6500(resource)
    dmm.open()

    print(dmm.idn())
    
    ## set Remote Lock On
    #dmm.setRemoteLock()
    
    dmm.beeperOff()

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

    
    #@@@#if not dmm.isOutputOn(args.chan):
        #@@@#dmm.outputOn()
        
    print('Ch. {} Settings: {:6.4f} V  {:6.4f} A'.
              format(args.chan, dmm.queryVoltage(),
                         dmm.queryCurrent()))

    voltageSave = dmm.queryVoltage()
    
    #print(dmm.idn())
    print('{:6.4f} V'.format(dmm.measureVoltage()))
    print('{:6.4f} A'.format(dmm.measureCurrent()))

    ## turn off the channel
    #@@@#dmm.outputOff()

    dmm.beeperOn()

    ## return to LOCAL mode
    dmm.setLocal()
    
    dmm.close()
