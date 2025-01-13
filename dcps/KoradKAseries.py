#!/usr/bin/env python
# -*- coding: utf-8 -*-
#

# Copyright (c) 2025, Mikkel Jeppesen <mikkel@mikkel.cc>
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
#  Control a KORAD KA-series, or compatible (many brands), powersupply with PyVISA
#-------------------------------------------------------------------------------

try:
    from . import SCPI
    from . import NotImplemented
except (ImportError, ValueError):
    from SCPI import SCPI
    from Warnings import NotImplemented
    
from time import sleep
import pyvisa as visa
import re
import sys
from dataclasses import dataclass
from enum import IntEnum


class tracking_mode(IntEnum):
    independent = 0b00
    series = 0b01
    parallel = 0b11
    undefined = 0b10

class cc_cv_mode(IntEnum):
    CC = 0
    CV = 1

@dataclass
class Status:
    ch1_mode: cc_cv_mode = cc_cv_mode.CV
    ch2_mode: cc_cv_mode = cc_cv_mode.CV
    tracking: tracking_mode = tracking_mode.independent
    beeper: bool = True
    lock: bool = False
    output: bool = False

class KAseries(SCPI):
    """Basic class for controlling and accessing a KORAD KA-Series power supplies
    This series of power supplies don't adhere to any LXI specifications or SCPI syntax.
    It does however implement *IDN?
    The underlying accessor functions of SCPI.py are used but the top level are all re-written
    below to handle the very different command syntax. This shows how
    one might add packages to support other such power supplies that
    only minimally adhere to the command standards.
    """

    def __init__(self, resource, wait=1.0, verbosity=0, max_chan=1, **kwargs):
        """Init the class with the instruments resource string

        resource  - resource string or VISA descriptor, like TCPIP0::192.168.1.100::9221::SOCKET 
        wait      - float that gives the default number of seconds to wait after sending each command
        verbosity - verbosity output - set to 0 for no debug output
        max_chan  - Most KA-series PSUs are single channel. PSUs like the KA3305 however are 3ch. Set this to have more channels
        kwargs    - other named options to pass when PyVISA open() like open_timeout=2.0

        Compatible Velleman rebrand manual https://web.archive.org/web/20250110222632/https://cdn.velleman.eu/downloads/2/ps3005da501.pdf
        Programming manual https://ia600605.us.archive.org/0/items/series-protocol-v-2.0-of-remote-control/Series%20Protocol%20V2.0%20of%20Remote%20Control.pdf
        """


        super(KAseries, self).__init__(resource, max_chan=max_chan, wait=wait,
                                        cmd_prefix='',
                                        verbosity=verbosity,
                                        read_termination='\0',
                                        write_termination='',
                                        **kwargs)

    def setLocal(self):
        """This supply doesn't support this. It'll go to local mode after 8s of no commands
        """
        NotImplemented('Function not implemented on device')
        pass
    
    def setRemote(self):
        """Set the power supply to REMOTE mode where it is controlled via VISA
        """
        # Not supported explicitly by this power supply but the power
        # supply does switch to REMOTE automatically. So send anything to it
        self._instWrite('\n')
    
    def setRemoteLock(self):
        """Set the power supply to REMOTE Lock mode where it is
           controlled via VISA & front panel is locked out
        """
        self.setRemote()

    def beeperOn(self):
        """Enable the system beeper for the instrument"""
        self._instWrite('BEEP1')
        
    def beeperOff(self):
        """Disable the system beeper for the instrument"""
        self._instWrite('BEEP0')

    def get_status(self) -> Status:
        """Parses the 8-bit status message returned from the PSU into a status object
        """

        self._instWrite('STATUS?')
        resp = self._inst.read_bytes(count=1, chunk_size=1)
        resp = int.from_bytes(resp, sys.byteorder)
        #resp = self._inst.read_binary_values(is_big_endian = (sys.byteorder == 'big'), data_points=1, chunk_size=1)

        status = Status()
        status.ch1_mode = cc_cv_mode(resp & 0b00000001 >> 0)
        status.ch2_mode = cc_cv_mode(resp & 0b00000010 >> 1)
        status.tracking = tracking_mode((resp & 0b00001100) >>2)
        status.beeper = bool(resp & 0b00010000)
        status.lock = bool(resp & 0b00100000)
        status.output = bool(resp & 0b01000000)
        
        return status

    def isOutputOn(self, channel=None) -> bool:
        """Return true if the output of channel is ON, else false
        
           channel - ignored. All channels are on/off together
        """

        # If a channel number is passed in, make it the
        # current channel
        if channel is not None:
            self.channel = channel
        
        status = self.get_status()
        return status.output

    def outputOn(self, channel=None, wait=None):
        """Turn on the output for channel
        
           wait    - number of seconds to wait after sending command
           channel - ignored. All channels are on/off together
        """

        # If a channel number is passed in, make it the
        # current channel
        if channel is not None:
            self.channel = channel
            
        # If a wait time is NOT passed in, set wait to the
        # default time
        if wait is None:
            wait = self._wait

        self._instWrite('OUT1')
        sleep(wait)             # give some time for PS to respond
    
    def outputOff(self, channel=None, wait=None):
        """Turn off the output for channel
        
           channel - ignored. All channels are on/off together
        """

        # If a channel number is passed in, make it the
        # current channel
        if channel is not None:
            self.channel = channel
                    
        # If a wait time is NOT passed in, set wait to the
        # default time
        if wait is None:
            wait = self._wait
            
        self._instWrite('OUT0')
        sleep(wait)             # give some time for PS to respond
    
    def outputOnAll(self, wait=None):
        """Turn on the output for ALL channels
        
        """

        self.outputOn(wait=wait)
    
    def outputOffAll(self, wait=None):
        """Turn off the output for ALL channels
        
        """

        self.outputOff(wait=wait)
    
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
            
        # If a wait time is NOT passed in, set wait to the
        # default time
        if wait is None:
            wait = self._wait

        
        str = f'VSET{self.channel}:{voltage:05.2f}'
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

        # If a wait time is NOT passed in, set wait to the
        # default time
        if wait is None:
            wait = self._wait
            
        str = f'ISET{self.channel}:{current:05.3f}'
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
            
        str = f'VSET{self.channel}?'
        self._instWrite(str)
        resp = self._inst.read_bytes(count=5, chunk_size=1)

        return float(resp)
    
    def queryCurrent(self, channel=None):
        """Return what current set value is (not the measured current,
        but the set current)
        
        channel - number of the channel starting at 1
        """

        # If a channel number is passed in, make it the
        # current channel
        if channel is not None:
            self.channel = channel
                    
        str = f'ISET{self.channel}?'
        self._instWrite(str)
        resp = self._inst.read_bytes(count=6, chunk_size=1)

        # There's a bug where the PSU returns 6 characters. The 6th character is garbage, so we drop it
        return float(resp[:5])
    
    def measureVoltage(self, channel=None):
        """Read and return a voltage measurement from channel
        
           channel - number of the channel starting at 1
        """

        NotImplemented("PSU doesn't support measuring voltage. Returing set value")
        return self.queryVoltage(channel)

    def measureCurrent(self, channel=None):
        """Read and return a current measurement from channel
        
           channel - number of the channel starting at 1
        """

        NotImplemented("PSU doesn't support measuring current. Returing set value")
        return self.queryCurrent(channel)

if __name__ == "__main__":
    psu = KAseries("ASRL8::INSTR")
    psu.open()
    print(psu.idn())

    psu.setCurrent(1)
    psu.setVoltage(15)
    psu.outputOn()
    print(psu.get_status())
    print(psu.queryVoltage())
    print(psu.queryCurrent())
    psu.outputOff()
    psu.setVoltage(10)
    psu.setCurrent(2)

    