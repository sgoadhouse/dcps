#!/usr/bin/env python
# -*- coding: utf-8 -*-
#

# Copyright (c) 2023, Mikkel Jeppesen <mikkel@mikkel.cc>
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
#  Control an ITECH IT6500C/D series 2-quadrant power supply with PyVISA
#-------------------------------------------------------------------------------

# For future Python3 compatibility:
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

try:
    from . import SCPI
except (ValueError, ImportError):
    from SCPI import SCPI
    
import time
import pyvisa as visa
import re
from warnings import warn

class IT6500C(SCPI):
    """Basic class for controlling and accessing an ITECH 6500C/D series 2 quadrant DC Power Supply/load"""

    _xlateCmdTbl = {
        # Overrides
        'isInput':                      'LOAD:STATe?',
        'inputOn':                      'LOAD ON',
        'inputOff':                     'LOAD OFF',
        'isVoltageProtectionTripped':   'PROTection:TRIGgered?',
        'voltageProtectionClear':       'PROTection:CLEar',
        # new
        'setCurrentRise':               'CURRent:Rise {}',
        'setCurrentFall':               'CURRent:Fall {}',
        'queryCurrentRise':             'CURRent:RISE?',
        'queryCurrentFall':             'CURRent:Fall?',
        'setVoltageRise':               'VOLTage:Rise {}',
        'setVoltageFall':               'VOLTage:Fall {}',
        'queryVoltageRise':             'VOLTage:RISE?',
        'queryVoltageFall':             'VOLTage:Fall?',
        'setPowerRise':                 'POWer:Rise {}',
        'setPowerFall':                 'POWer:Fall {}',
        'queryPowerRise':               'POWer:RISE?',
        'queryPowerFall':               'POWer:Fall?',
        'setDCRCapacity':               'DCR:BATTery:CAPACity {}',
        'queryDCRCapacity':             'DCR:BATTery:CAPACity?',
        'DCROn':                        'DCR ON',
        'DCROff':                       'DCR OFF',
        'isDCR':                        'DCR?',
        'DCRData':                      'DCR:DATA?',        
    }

    def __init__(self, resource, wait=1.0, verbosity=0, **kwargs):
        """Init the class with the instruments resource string

        resource  - resource string or VISA descriptor, like USB0::INSTR
        wait      - float that gives the default number of seconds to wait after sending each command
        verbosity - verbosity output - set to 0 for no debug output
        kwargs    - other named options to pass when PyVISA open() like open_timeout=2.0
        """
        super(IT6500C, self).__init__(
            resource, 
            max_chan=1, 
            wait=wait, 
            cmd_prefix='', 
            verbosity=verbosity, 
            read_termination = '\n', 
            write_termination = '\n', 
            **kwargs)

    #------------------------------------------------
    # Additional functions
    #------------------------------------------------
    def setInternalResistance(self, resistance, wait=None):
        """Set the internal resistance of the PSU. Useful for battery simulation.

           resistance  - floating point value for the internal resistance. 
                         Supports suffixes like E+2, M, K, m or u.
           wait        - float of seconds to wait after sending command
        """
        
        if wait is None:
            wait = self._wait
        
        str = "RES {}".format(resistance)
        self._instWrite(str)
        time.sleep(wait)
    
    def queryInternalResistance(self):
        """Returns what resistance the the PSU is configured to.
        """

        return self.fetchGenericValue("RES?")

    def setCVPriority(self, priority, wait=None):
        """Set the priority of CV-loop.

           priority     - LOW or HIGH
           wait         - float of seconds to wait after sending command
        """

        try:
            priority = priority.upper()
            assert priority in ['LOW', 'HIGH']
        except (AttributeError, AssertionError):
            warn("Invalid priority: {priority}")
        
        if wait is None:
            wait = self._wait

        str = "CV:PRIority {}".format(priority)
        self._instWrite(str)
        time.sleep(wait)
    
    def setCCPriority(self, priority, wait=None):
        """Set the priority of CC-loop. High priority CC-loop is useful for example for LEDs or lasers

           priority     - LOW or HIGH
           wait         - float of seconds to wait after sending command
        """

        try:
            priority = priority.upper()
            assert priority in ['LOW', 'HIGH']
        except (AttributeError, AssertionError):
            warn("Invalid priority: {priority}")

        if wait is None:
            wait = self._wait

        str = "CC:PRIority {}".format(priority)
        self._instWrite(str)

    def queryCVPriority(self):
        """Returns what the current priority of the constant voltage loop is
        """

        return self.fetchGenericString("CV:PRIority?")
    
    def queryCCPriority(self):
        """Returns what the current priority of the constant current loop is
        """

        return self.fetchGenericString("CC:PRIority?")

    def setCurrentRise(self, seconds, wait=None):
        """Set the rise time of the output current

           seconds  - The rise time in seconds
           wait     - float of seconds to wait after sending command
        """

        if wait is None:
            wait = self._wait
        
        str = self._Cmd('setCurrentRise').format(seconds)
        self._instWrite(str)
        time.sleep(wait)
    
    def setCurrentRise(self, seconds, wait=None):
        """Set the fall time of the output current

           seconds  - The fall time in seconds
           wait     - float of seconds to wait after sending command
        """

        if wait is None:
            wait = self._wait
        
        str = self._Cmd('setCurrentFall').format(seconds)
        self._instWrite(str)
        time.sleep(wait)
    
    def queryCurrentRise(self):
        """Return what the current rise time is configured to
        """

        return self.fetchGenericValue(self._Cmd('queryCurrentRise'))
        
    def queryCurrentFall(self):
        """Return what the current fall time is configured to
        """

        return self.fetchGenericValue(self._Cmd('queryCurrentFall'))

    def setVoltageRise(self, seconds, wait=None):
        """Set the rise time of the output voltage

           seconds  - The rise time in seconds
           wait     - float of seconds to wait after sending command
        """

        if wait is None:
            wait = self._wait
        
        str = self._Cmd('setVoltageRise').format(seconds)
        self._instWrite(str)
        time.sleep(wait)
    
    def setVoltageRise(self, seconds, wait=None):
        """Set the fall time of the output voltage

           seconds  - The fall time in seconds
           wait     - float of seconds to wait after sending command
        """

        if wait is None:
            wait = self._wait
        
        str = self._Cmd('setVoltageFall').format(seconds)
        self._instWrite(str)
        time.sleep(wait)
    
    def queryVoltageRise(self):
        """Return what the voltage rise time is configured to
        """

        return self.fetchGenericValue(self._Cmd('queryVoltageRise'))
        
    def queryVoltageFall(self):
        """Return what the voltage fall time is configured to
        """

        return self.fetchGenericValue(self._Cmd('queryVoltageFall'))

    def setPowerRise(self, seconds, wait=None):
        """Set the rise time of the output power

           seconds  - The rise time in seconds
           wait     - float of seconds to wait after sending command
        """

        if wait is None:
            wait = self._wait
        
        str = self._Cmd('setPowerRise').format(seconds)
        self._instWrite(str)
        time.sleep(wait)
    
    def setPowerRise(self, seconds, wait=None):
        """Set the fall time of the output power

           seconds  - The fall time in seconds
           wait     - float of seconds to wait after sending command
        """

        if wait is None:
            wait = self._wait
        
        str = self._Cmd('setPowerFall').format(seconds)
        self._instWrite(str)
        time.sleep(wait)
    
    def queryPowerRise(self):
        """Return what the power rise time is configured to
        """

        return self.fetchGenericValue(self._Cmd('queryPowerRise'))
        
    def queryPowerFall(self):
        """Return what the power fall time is configured to
        """

        return self.fetchGenericValue(self._Cmd('queryPowerFall'))
    
    def setDCRCapacity(self, amp_hours, wait=None):
        """Set the capacity of the battery under test
           
           amp_hours    - The capacity of the battery in amp amp_hours
           wait         - float of seconds to wait after sending command
        """

        if wait is None:
            wait = self._wait
        
        str = self._Cmd('setDCRCapacity').format(amp_hours)
        self._instWrite(str)
        time.sleep(wait)
    
    def queryDCRCapacity(self):
        """Returns the configured battery capacity of the DCR DUT
        """
       
        return self.fetchGenericValue(self._Cmd('queryDCRCapacity'))

    def DCROn(self, wait=None):
        """Enables the DCR measurement
        """

        if wait is None:
            wait = self._wait

        str = self._Cmd('DCROn')
        self._instWrite(str)
        time.sleep(wait)
    
    def DCROff(self, wait=None):
        """Disables the DCR measurement
        """

        if wait is None:
            wait = self._wait

        str = self._Cmd('DCROff')
        self._instWrite(str)
        time.sleep(wait)
    
    def isDCROn(self):
        """Returns True if the DCR measurement is enabled
        """

        str = self._Cmd('isDCR')
        return self.fetchGenericBoolean(str)
    
    def measureDCR(self):
        """Returns the DC resistance of the battery DUT being charged
        """

        str = self._Cmd('DCRData')
        return self.fetchGenericValue(str)
    
    #------------------------------------------------
    # Unsupported function overloads. Will warn user
    #------------------------------------------------
    def queryVoltageRange(self, channel=None):
        """UNSUPPORTED: Query the voltage range for channel

           channel  - number of the channel starting at 1
        """

        warn("Not supported on this device")

    def queryCurrentRange(self, channel=None):
        """UNSUPPORTED: Query the voltage range for channel

           channel  - number of the channel starting at 1
        """

        warn("Not supported on this device")

    def setFunction(self, function, channel=None, wait=None):
        """UNSUPPORTED: Set the source function for the channel
        
           function - a string which names the function. common ones:
                      VOLTage, CURRent, RESistance, POWer        
           wait     - number of seconds to wait after sending command
           channel  - number of the channel starting at 1
        """

        warn("Not supported on this device")

    def queryFunction(self, channel=None, query_delay=None):
        """UNSUPPORTED Return what FUNCTION is the current one for sourcing
        
        channel     - number of the channel starting at 1
        query_delay - number of seconds to wait between write and
                      reading for read data (None uses default seconds)
        """

        warn("Not supported on this device")

    def setCurrentRange(self, upper, channel=None, wait=None):
        """UNSUPPORTED Set the current range for channel

           upper    - floating point value for upper current range, set to None for AUTO
           channel  - number of the channel starting at 1
           wait     - number of seconds to wait after sending command
        """

        warn("Not supported on this device")
    
    def setVoltageRange(self, value, channel=None, wait=None):
        """Unsupported Set the voltage range for channel

           value    - floating point value for voltage range, set to None for AUTO
           channel  - number of the channel starting at 1
           wait     - number of seconds to wait after sending command
        """

        warn("Not supported on this device")

    def measureVoltageMax(self, channel=None):
        """UNSUPPORTED: Read and return the maximum voltage measurement from channel
        
           channel - number of the channel starting at 1
        """

        warn("Not supported on this device")
    
    def measureVoltageMin(self, channel=None):
        """UNSUPPORTED: Read and return the minimum voltage measurement from channel
        
           channel - number of the channel starting at 1
        """

        warn("Not supported on this device")
    
    def measureCurrentMax(self, channel=None):
        """UNSUPPORTED: Read and return the maximum current measurement from channel
        
           channel - number of the channel starting at 1
        """

        warn("Not supported on this device")
    
    def measureCurrentMin(self, channel=None):
        """UNSUPPORTED: Read and return the minimum current measurement from channel
        
           channel - number of the channel starting at 1
        """

        warn("Not supported on this device")

    def setMeasureVoltageRange(self, upper, channel=None, wait=None):
        """UNSUPPORTED: Set the measurement voltage range for channel

           upper    - floating point value for upper voltage range, set to None for AUTO
           channel  - number of the channel starting at 1
           wait     - number of seconds to wait after sending command
        """

        warn("Not supported on this device")
    
    def queryMeasureVoltageRange(self, channel=None):
        """UNSUPPORTED: Query the measurement voltage range for channel

           channel  - number of the channel starting at 1
        """

        warn("Not supported on this device")

    def measureResistance(self, channel=None):
        """UNSUPPORTED: Read and return a resistance measurement from channel
        
           channel - number of the channel starting at 1
        """

        warn("Not supported on this device")
    
    def setVoltageCompliance(self, ovp, channel=None, wait=None):
        """UNSUPPORTED: Set the over-voltage compliance value for the channel. This is the measurement value at which the output is disabled.
        
           ovp     - desired over-voltage compliance value as a floating point number
           channel - number of the channel starting at 1
           wait    - number of seconds to wait after sending command
        """

        warn("Not supported on this device")
    
    def queryVoltageCompliance(self, channel=None):
        """UNSUPPORTED: Return what the over-voltage compliance set value is
        
        channel - number of the channel starting at 1
        """

        warn("Not supported on this device")
    
    def isVoltageComplianceTripped(self, channel=None):
        """UNSUPPORTED: Return true if the Voltage Compliance of channel is Tripped, else false
        
           channel - number of the channel starting at 1
        """

        warn("Not supported on this device")

    def voltageComplianceClear(self, channel=None, wait=None):
        """UNSUPPORTED: Clear Voltage Compliance Trip on the output for channel
        
           channel - number of the channel starting at 1
           wait    - number of seconds to wait after sending command
        """

        warn("Not supported on this device")

    def isCurrentProtectionTripped(self, channel=None):
        """UNSUPPORTED: Return true if the OverCurrent Protection of channel is Tripped, else false
        
           channel - number of the channel starting at 1
        """

        warn("Not supported on this device")
    
    def currentProtectionClear(self, channel=None, wait=None):
        """UNSUPPORTED: Clear Over-Current Protection Trip on the output for channel
        
           channel - number of the channel starting at 1
           wait    - number of seconds to wait after sending command
        """

        warn("Not supported on this device")
    
    def setCurrentCompliance(self, ocp, channel=None, wait=None):
        """UNSUPPORTED: Set the over-current compliance value for the channel. This is the measurement value at which the output is disabled.
        
           ocp     - desired over-current compliance value as a floating point number
           channel - number of the channel starting at 1
           wait    - number of seconds to wait after sending command
        """

        warn("Not supported on this device")

    def queryCurrentCompliance(self, channel=None):
        """UNSUPPORTED: Return what the over-current compliance set value is
        
        channel - number of the channel starting at 1
        """
        
        warn("Not supported on this device")

    def isCurrentComplianceTripped(self, channel=None):
        """UNSUPPORTED: Return true if the Current Compliance of channel is Tripped, else false
        
           channel - number of the channel starting at 1
        """

        warn("Not supported on this device")

    def currentComplianceClear(self, channel=None, wait=None):
        """UNSUPPORTED: Clear Current Compliance Trip on the output for channel
        
           channel - number of the channel starting at 1
           wait    - number of seconds to wait after sending command
        """

        warn("Not supported on this device")




if __name__ == '__main__':
    import pyvisa
    
    rm = pyvisa.ResourceManager('@py')
    devices = rm.list_resources()

    print(devices)

    resource = None

    if len(devices) == 1:
        resource = devices[0]
    else:
        # Print 5 devices at a time, 
        # have the user pick one of them by entering their ID or 'n' for next 5
        offset = 0
        while resource is None:
            dev_slice = devices[offset:offset+5]
            for idx, dev in enumerate(dev_slice):
                print("{}: {}".format(idx+offset, dev))

            print('n: for next 5 resources')
            while True:
                choice = input("Pick a resource (enter the number)")
                if choice == 'n':
                    offset += 5
                    if offset > len(devices):
                        offset = 0
                    print('')
                    break
            
                try:
                    choice = int(choice)
                except ValueError:
                    pass
                else:
                    if choice >= offset and choice < offset + 5-1:
                        resource = devices[choice]
                        break
                
                # If we get here the user didn't provide a valid input
                print("Invalid input")

    psu = IT6500C(resource)
    psu.open()

    ## set Remote mode
    psu.setRemote()
    
    # psu.beeperOff()
    
    if not psu.isOutputOn():
        psu.outputOn()
    

    vol = psu.queryVoltage()
    cur = psu.queryCurrent()
    print(f'Settings: {vol:6.4f} V  {cur:6.4f} A')

    voltageSave = psu.queryVoltage()
    
    #print(psu.idn())
    print('{:6.4f} V'.format(psu.measureVoltage()))
    print('{:6.4f} A'.format(psu.measureCurrent()))
    print('{:6.4f} W'.format(psu.measurePower()))

    psu.setVoltage(2.7)

    print('{:6.4f} V'.format(psu.measureVoltage()))
    print('{:6.4f} A'.format(psu.measureCurrent()))
    print('{:6.4f} W'.format(psu.measurePower()))
    time.sleep(2)
    psu.setVoltage(2.3)

    print('{:6.4f} V'.format(psu.measureVoltage()))
    print('{:6.4f} A'.format(psu.measureCurrent()))
    print('{:6.4f} W'.format(psu.measurePower()))

    time.sleep(2)
    psu.setVoltage(voltageSave)
   
    print('{:6.4f} V'.format(psu.measureVoltage()), end='\t')
    print('{:6.4f} A'.format(psu.measureCurrent()), end='\t')
    print('{:6.4f} W'.format(psu.measurePower()))
    time.sleep(1)

    ## turn off the channel
    psu.outputOff()

    psu.beeperOn()

    ## return to LOCAL mode
    psu.setLocal()
    
    psu.close()
