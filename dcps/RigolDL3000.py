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
#  Control a Rigol DL3000 family of DC Electronic Load with PyVISA
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

class RigolDL3000(SCPI):
    """Basic class for controlling and accessing a Rigol DL3000 Family Electronic Load"""

    ## Dictionary to translate SCPI commands for this device
    _xlateCmdTbl = {
        'setVoltage':                    'SOURce:VOLTage:LEVel:IMMediate {}',
        'setVoltageRangeAuto':           None,
        'setVoltageRange':               'SOURce:VOLTage:RANGe {1:}',
        'setCurrent':                    'SOURce:CURRent:LEVel:IMMediate {}',
        'setCurrentRangeAuto':           None,
        'setCurrentRange':               'SOURce:CURRent:RANGe {1:}',
        'queryVoltage':                  'SOURce:VOLTage:LEVel:IMMediate?',
        'queryVoltageRangeAuto':         None,
        'queryVoltageRange':             'SOURce:VOLTage:RANGe?',
        'queryCurrent':                  'SOURce:CURRent:LEVel:IMMediate?',
        'queryCurrentRangeAuto':         None,
        'queryCurrentRange':             'SOURce:CURRent:RANGe?',        
    }
    
    def __init__(self, resource, wait=1.0, verbosity=0, **kwargs):
        """Init the class with the instruments resource string

        resource - resource string or VISA descriptor, like TCPIP0::172.16.2.13::INSTR
        wait     - float that gives the default number of seconds to wait after sending each command
        verbosity - verbosity output - set to 0 for no debug output
        kwargs    - other named options to pass when PyVISA open() like open_timeout=2.0
        """
        super(RigolDL3000, self).__init__(resource, max_chan=1, wait=wait, cmd_prefix=':', read_termination='\n', verbosity = verbosity, **kwargs)


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

    def setLocal(self):
        """Set the instrument to LOCAL mode where front panel keys
        work again.

        WARNING! MUST BE LAST Command sent or else Instrument goes back to Remote mode

        """

        # enable Virtual Front Panel
        self._instWrite('DEBug:KEY 1')
        sleep(0.5)
        k = 8 # Press Local key
        self._instWrite('SYSTem:KEY {}'.format(k))

        #for k in [9,40,40,40,40,0,8]:
        #    print('Pressing key {}'.format(k))
        #    self._instWrite('SYSTem:KEY {}'.format(k))
        #    sleep(1.0)

    def setRemote(self):
        """Set the instrument to REMOTE mode where it is controlled via VISA
        """

        # NOTE: Unsupported command by this device. However, with any
        # command sent to the DL3000, it automatically goes into
        # REMOTE mode. Instead of raising an exception and breaking
        # any scripts, simply return quietly.
        pass
    
    def setRemoteLock(self):
        """Set the instrument to REMOTE Lock mode where it is
           controlled via VISA & front panel is locked out
        """
        # NOTE: Unsupported command by this device. However, with any
        # command sent to the DL3000, it automatically goes into
        # REMOTE mode.
        #
        # Disable the remote virtual panel, just in case
        self._instWrite('DEBug:KEY 0')
        
    
        
    ###################################################################
    # Commands Specific to DL3000
    ###################################################################

    def setImonExt(self,on):
        """Enable the IMON External output. After a *RST this is
        disabled. Could not find a command that sets this so having to
        use the KEY command and hope it is right since there is no
        feedback.

        """

        #@@@#print("ImonExt")
        
        # enable Virtual Front Panel
        self._instWrite('DEBug:KEY 1')
        sleep(0.3)
        self._instWrite('SYSTem:KEY {}'.format(9))  # Utiliity

        for i in range(7):
            # Send 7 Down Arrows
            self._instWrite('SYSTem:KEY {}'.format(40)) # Down Arrow

        if (on):
            # If turning ON, must assume this is being called AFTER a *RST or when it is known to be OFF
            # Use Left Arrow to Enable it
            self._instWrite('SYSTem:KEY {}'.format(37)) # Left Arrow
        else:
            # If turning OFF, assume that it must be ON (no feedback so must do it this way)
            # Use Right Arrow to Enable it
            self._instWrite('SYSTem:KEY {}'.format(38)) # Right Arrow

        # Give time for someone to see this, if they are interested
        sleep(1.0)
            
        # Leave utility menu by "pressing" the key again
        self._instWrite('SYSTem:KEY {}'.format(9))  # Utiliity

        # disable Virtual Front Panel
        self._instWrite('DEBug:KEY 0')

    def setDigitalOutput(self,left,count):
        """Enable the Digital output. After a *RST this is
        disabled. Could not find a command that sets this so having to
        use the KEY command and hope it is right since there is no
        feedback.

        left  - True/False: if True, use Left Arrow, if False use Right Arrow
        count - number of Left or Right arrows
        """

        #@@@#print("Digital Output")
        
        # enable Virtual Front Panel
        self._instWrite('DEBug:KEY 1')
        sleep(0.3)
        self._instWrite('SYSTem:KEY {}'.format(9))  # Utiliity

        for i in range(4):
            # Send 4 Down Arrows
            self._instWrite('SYSTem:KEY {}'.format(40)) # Down Arrow

        for i in range(count):            
            if (left):
                # using Left Arrow - the caller has to keep track of the position since this function cannot query it
                self._instWrite('SYSTem:KEY {}'.format(37)) # Left Arrow            
            else:
                # using Right Arrow - the caller has to keep track of the position since this function cannot query it
                self._instWrite('SYSTem:KEY {}'.format(38)) # Right Arrow

        # Give time for someone to see this, if they are interested
        sleep(1.0)
            
        # Leave utility menu by "pressing" the key again
        self._instWrite('SYSTem:KEY {}'.format(9))  # Utiliity

        # disable Virtual Front Panel
        self._instWrite('DEBug:KEY 0')
        
    
    def setCurrentVON(self,voltage,wait=None):
        """Set the voltage level for when in Constant Current mode that the load starts to sink.

           voltage - desired voltage value as a floating point number
           wait    - number of seconds to wait after sending command
        """

        # If a wait time is NOT passed in, set wait to the
        # default time
        if wait is None:
            wait = self._wait

        self._instWrite('SOURce:CURRent:VON {}'.format(voltage))

        sleep(wait)             # give some time for device to respond
        
    def queryCurrentVON(self):
        """Query the voltage level when Constant Current mode starts to sink current

           returns the set voltage value as a floating point value
        """

        return self.fetchGenericValue('SOURce:CURRent:VON?', channel)
            
    def setFunctionMode(self, mode, channel=None, wait=None):
        """Set the source function mode/input regulation mode for the channel
        
           mode     - a string which names the desired function mode. valid ones:
                      FIXed|LIST|WAVe|BATTery|OCP|OPP
           wait     - number of seconds to wait after sending command
           channel  - number of the channel starting at 1
        """

        # Check mode to be valid
        if (mode[0:3] not in ["FIX", "WAV", "OCP", "OPP"] and
            mode[0:4] not in ["LIST", "BATT"]):
            raise ValueError('setFunctionMode(): "{}" is an unknown function mode.'.format(mode))
        
        # If a channel number is passed in, make it the
        # current channel
        if channel is not None:
            self.channel = channel

        # If a wait time is NOT passed in, set wait to the
        # default time
        if wait is None:
            wait = self._wait
            
        str = 'SOURce:FUNCtion:MODE {}'.format(mode)
        self._instWrite(str)
        sleep(wait)             # give some time for PS to respond

    def queryFunctionMode(self, channel=None, query_delay=None):
        """Return what the FUNCTION MODE/input regulation mode is set to
        
        channel     - number of the channel starting at 1
        query_delay - number of seconds to wait between write and
                      reading for read data (None uses default seconds)
        """

        return self.fetchGenericString('SOURce:FUNCtion:MODE?', channel, query_delay)

    def setSenseState(self, on, channel=None, wait=None):
        """Enable or Disable the Sense Inputs

           on         - set to True to Enable use of the Sense inputs or False to Disable them
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

        str = 'SOURce:SENSE {}'.format(self._bool2onORoff(on))

        self._instWrite(str)

        sleep(wait)             # give some time for device to respond

    def querySenseState(self, channel=None, query_delay=None):
        """Return the state of the Sense Input
        
        channel     - number of the channel starting at 1
        query_delay - number of seconds to wait between write and
                      reading for read data (None uses default seconds)
        """

        return self.fetchGenericBoolean('SOURce:SENSe?', channel, query_delay)
        
if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Access and control a Rigol DL3000 electronic load')
    parser.add_argument('chan', nargs='?', type=int, help='Channel to access/control (starts at 1)', default=1)
    args = parser.parse_args()

    from time import sleep
    from os import environ
    resource = environ.get('DL3000_VISA', 'TCPIP0::172.16.2.13::INSTR')
    rigol = RigolDL3000(resource)
    rigol.open()

    # Reset
    rigol.rst(wait=1.0)
    rigol.cls(wait=1.0)

    print(rigol.idn())
    
    ## set Remote Lock On
    rigol.setRemoteLock()
    
    rigol.beeperOff()

    if (True):
        print('Current function: {} & mode: {}'.format(rigol.queryFunction(),rigol.queryFunctionMode()))
        sleep(1.0)

        rigol.setFunctionMode("FIX", wait=2.0)            
        
        for func in ["CURRent","RESistance","VOLTage","POWer"]:
            print('Set to function: {} ...'.format(func))
            rigol.setFunction(func,wait=2.0)
            print('Current function: {} & mode: {}'.format(rigol.queryFunction(),rigol.queryFunctionMode()))

        for mode in ["FIXed","LIST","WAVe","BATTERY","OCP","OPP"]:
            print('Set to mode: {} ...'.format(mode))
            rigol.setFunctionMode(mode,wait=2.0)            
            print('Current function: {} & mode: {}'.format(rigol.queryFunction(),rigol.queryFunctionMode()))
                
        #@@@#rigol.setFunctionMode("FIX",wait=0.5)
        rigol.setFunction("CURR", wait=0.5)
        print('Current function: {} & mode: {}'.format(rigol.queryFunction(),rigol.queryFunctionMode()))
        sleep(1.0)

        print('\nCurrent Sense State: {}'.format('ON' if rigol.querySenseState() else 'OFF'))
        print('Enable State Inputs ...')
        rigol.setSenseState(True)
        print('Current Sense State: {}'.format('ON' if rigol.querySenseState() else 'OFF'))
        print('Disable State Inputs ...')
        rigol.setSenseState(False)
        print('Current Sense State: {}'.format('ON' if rigol.querySenseState() else 'OFF'))
        
        rigol.setSenseState(True)
        print('Current Sense State: {}'.format('ON' if rigol.querySenseState() else 'OFF'))
        
        if not rigol.isInputOn(args.chan):
            rigol.inputOn()

        print('Ch. {} Settings: {:6.4f} V  {:6.4f} A'.
                  format(args.chan, rigol.queryVoltage(),
                             rigol.queryCurrent()))

        #print(rigol.idn())
        print('{:6.4f} V'.format(rigol.measureVoltage()))
        print('{:6.4f} A'.format(rigol.measureCurrent()))

        rigol.setCurrent(0.2)

        print('{:6.4f} V'.format(rigol.measureVoltage()))
        print('{:6.4f} A'.format(rigol.measureCurrent()))

        rigol.setCurrent(0.4)

        print('{:6.4f} V'.format(rigol.measureVoltage()))
        print('{:6.4f} A'.format(rigol.measureCurrent()))

    ## turn off the channel
    rigol.inputOff()

    rigol.beeperOn()

    rigol.printAllErrors()    
    rigol.cls()
    
    ## return to LOCAL mode
    rigol.setLocal()

    rigol.close()
