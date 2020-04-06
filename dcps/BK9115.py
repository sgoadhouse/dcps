#!/usr/bin/env python
# -*- coding: utf-8 -*-
#

# Copyright (c) 2020, Stephen Goadhouse <sgoadhouse@virginia.edu>
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
#  Control a BK Precision 9115 and related DC Power Supplies with PyVISA
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
import visa

class BK9115(SCPI):
    """Basic class for controlling and accessing a BK Precision 9115 DC Power Supply"""

    def __init__(self, resource, wait=1.0):
        """Init the class with the instruments resource string

        resource - resource string or VISA descriptor, like USB0::INSTR
        wait     - float that gives the default number of seconds to wait after sending each command
        """
        super(BK9115, self).__init__(resource, max_chan=1, wait=wait, cmd_prefix='', read_termination = None, write_termination = '\r\n')

    

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Access and control a BK Precision 9115 DC power supply')
    parser.add_argument('chan', nargs='?', type=int, help='Channel to access/control (starts at 1)', default=1)
    args = parser.parse_args()

    from time import sleep
    from os import environ
    resource = environ.get('BK9115_USB', 'USB0::INSTR')
    bkps = BK9115(resource)
    bkps.open()

    print(bkps.idn())

    # IMPORTANT: 9115 requires Remote to be set or else comands are ignored
    bkps.setRemote()
    bkps._waitCmd()
    
    ## set Remote Lock On
    #bkps.setRemoteLock()
    
    bkps.beeperOff()
    bkps._waitCmd()

    # normally would get channel from args.chan
    chan = args.chan
    # BK Precision 9115 has a single channel, so force chan to be 1
    chan = 1
    
    if not bkps.isOutputOn(chan):
        bkps.outputOn()
        
    print('Ch. {} Settings: {:6.4f} V  {:6.4f} A'.
              format(chan, bkps.queryVoltage(),
                         bkps.queryCurrent()))

    voltageSave = bkps.queryVoltage()
    
    print('{:6.4f} V'.format(bkps.measureVoltage()))
    print('{:6.4f} A'.format(bkps.measureCurrent()))

    bkps.setCurrent(0.1)
    bkps.setVoltage(2.7)

    print('{:6.4f} V'.format(bkps.measureVoltage()))
    print('{:6.4f} A'.format(bkps.measureCurrent()))

    bkps.setVoltage(2.3)

    print('{:6.4f} V'.format(bkps.measureVoltage()))
    print('{:6.4f} A'.format(bkps.measureCurrent()))

    bkps.setVoltage(voltageSave)

    print('{:6.4f} V'.format(bkps.measureVoltage()))
    print('{:6.4f} A'.format(bkps.measureCurrent()))

    ## turn off the channel
    bkps.outputOff()

    # The beeper sucks, do not turn it back on!
    #@@@#bkps.beeperOn()

    ## return to LOCAL mode
    bkps.setLocal()
    
    bkps.close()
