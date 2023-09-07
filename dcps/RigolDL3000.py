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

    def __init__(self, resource, wait=1.0, verbosity=0, **kwargs):
        """Init the class with the instruments resource string

        resource - resource string or VISA descriptor, like TCPIP0::172.16.2.13::INSTR
        wait     - float that gives the default number of seconds to wait after sending each command
        verbosity - verbosity output - set to 0 for no debug output
        kwargs    - other named options to pass when PyVISA open() like open_timeout=2.0
        """
        super(RigolDL3000, self).__init__(resource, max_chan=1, wait=wait, cmd_prefix=':', verbosity = verbosity, **kwargs)


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
    # Commands Specific to DL3000
    ###################################################################

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
            
    
if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Access and control a Rigol DL3000 electronic load')
    parser.add_argument('chan', nargs='?', type=int, help='Channel to access/control (starts at 1)', default=1)
    args = parser.parse_args()

    from time import sleep
    from os import environ
    resource = environ.get('DL3000_IP', 'TCPIP0::172.16.2.13::INSTR')
    rigol = RigolDL3000(resource)
    rigol.open()

    ## set Remote Lock On
    #rigol.setRemoteLock()
    
    rigol.beeperOff()
    
    if not rigol.isOutputOn(args.chan):
        rigol.outputOn()
        
    print('Ch. {} Settings: {:6.4f} V  {:6.4f} A'.
              format(args.chan, rigol.queryVoltage(),
                         rigol.queryCurrent()))

    voltageSave = rigol.queryVoltage()
    
    #print(rigol.idn())
    print('{:6.4f} V'.format(rigol.measureVoltage()))
    print('{:6.4f} A'.format(rigol.measureCurrent()))

    rigol.setVoltage(2.7)

    print('{:6.4f} V'.format(rigol.measureVoltage()))
    print('{:6.4f} A'.format(rigol.measureCurrent()))

    rigol.setVoltage(2.3)

    print('{:6.4f} V'.format(rigol.measureVoltage()))
    print('{:6.4f} A'.format(rigol.measureCurrent()))

    rigol.setVoltage(voltageSave)

    print('{:6.4f} V'.format(rigol.measureVoltage()))
    print('{:6.4f} A'.format(rigol.measureCurrent()))

    ## turn off the channel
    rigol.outputOff()

    rigol.beeperOn()

    ## return to LOCAL mode
    rigol.setLocal()
    
    rigol.close()