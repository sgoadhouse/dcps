#!/usr/bin/env python
# -*- coding: utf-8 -*-
#

# Copyright (c) 2018-2026, Stephen Goadhouse <sgoadhouse@virginia.edu>
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
#  Control a Keithley DAQ6510 DAQ with PyVISA
#-------------------------------------------------------------------------------

# For future Python3 compatibility:
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

try:
    from . import Keithley6500
except:
    from Keithley6500 import Keithley6500
    
from time import sleep
import pyvisa as visa


class Keithley6510(Keithley6500):
    """Basic class for controlling and accessing a Keithley/Tektronix DAQ6510 data acquisition multi-channel digital multimeter"""

    ## Dictionary to translate SCPI commands for this device
    #_xlateCmdTbl = {
    #    'setMeasureVoltageRange':        'SENSe{:1d}:VOLTage:RANGe {}', # removed format of value so can use DEF/MIN/MAX
    #    'setMeasureCurrentRange':        'SENSe{:1d}:CURRent:RANGe {}', # removed format of value so can use DEF/MIN/MAX
    #}

    def __init__(self, resource, wait=0.01, verbosity=0, **kwargs):
        """Init the class with the instruments resource string

        resource - resource string or VISA descriptor, like TCPIP0::172.16.2.13::INSTR
        wait     - float that gives the default number of seconds to wait after sending each command
        verbosity - verbosity output - set to 0 for no debug output
        kwargs    - other named options to pass when PyVISA open() like open_timeout=2.0
        """
        #self._functions = { 'VoltageDC':   'VOLT:DC',
        #                    'VoltageAC':   'VOLT:AC',
        #                    'CurrentDC':   'CURR:DC',
        #                    'CurrentAC':   'CURR:AC',
        #                    'Resistance2W':'RES',
        #                    'Resistance4W':'FRES',
        #                    'Diode':       'DIOD',
        #                    'Capacitance': 'CAP',
        #                    'Temperature': 'TEMP',
        #                    'Continuity':  'CONT',
        #                    'Frequency':   'FREQ:VOLT',
        #                    'Period':      'PER:VOLT',
        #                    'VoltageRatio':'VOLT:DC:RAT',
        #                   }
        ## default measurement function if not supplied as parameter into the method
        #self._functionStr = None
        
        super(Keithley6510, self).__init__(resource, max_chan=299, wait=wait,
                                           verbosity = verbosity,
                                           **kwargs)
    #@property
    #def functions(self):
    #    return self._functions

    ###################################################################
    # Commands Specific to DAQ6510
    ###################################################################

    def measureResistanceOLDOLDOLD(self, channel=None, query_delay=None):
        """Read and return a resistance measurement from channel
        
           channel - number of the channel starting at 1
        """

        self.setMeasureFunction(function="Resistance2W",channel=channel)

        self.closeChannel()

        val = self._instQuery('READ?',delay=query_delay)        
        return float(val)
        

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Access and control a Keithley DAQ6510 digital multimeter')
    parser.add_argument('chan', nargs='?', type=int, help='Channel to access/control (starts at 1)', default=1)
    args = parser.parse_args()

    from time import sleep
    from os import environ
    resource = environ.get('DAQ6510_VISA', 'TCPIP0::172.16.2.13::INSTR')
    daq = Keithley6510(resource)
    daq.open()

    # Reset
    daq.rst(wait=1.0)
    daq.cls(wait=1.0)

    print(daq.idn())


    ## set Remote Lock On
    daq.setRemoteLock()

    daq.beeperOff()

    ## For determing the Function names output when querying the current function
    #for i in range(0,14):
    #    daq.queryMeasureFunctionStr()
    #    daq.setLocal()
    #    input("Press Enter to continue...") 
    #    daq.setRemoteLock()

    if None:
        ## Set None to True to see these examples of putting messages on the screen operate
        #
        # Set display messages
        daq.setDisplayMessage('Bottom Message', top=False)
        daq.setDisplayMessage('Top Message', top=True)

        # Enable messages
        daq.displayMessageOn()
        sleep(2.0)

        if daq.isRearTermEnabled():
            daq.setDisplayMessage('Using REAR Terminals', top=True)
        else:
            daq.setDisplayMessage('Using Front Terminals', top=True)
        daq.setDisplayMessage('New Bottom Message', top=False)
        sleep(2.0)

        # Disable messages
        daq.displayMessageOff()

    if not daq.isInputOn(args.chan):
        daq.inputOn()

    if daq.isRearTermEnabled():
        print("REAR  Terminals are being used for the following test\n")
    else:
        print("FRONT Terminals are being used for the following test\n")

    ## Check the card slot of the channel
    canMeasCurr = True
    cardIDN = daq.queryCardIDN()
    if cardIDN is not None:
        print('IDN of card of channel "{}": {}'.format(args.chan,','.join(cardIDN)))

        ## Check that it can handle current
        canMeasCurr = daq.isCurrentCapableCard(cardIDN[0])
        if (not canMeasCurr):
            print('Card used for channel {}, "{}",\n  cannot measure current so those functions will be skipped.\n'.format(args.chan, ','.join(cardIDN)))
    
    daq.measureVoltage()
    daq.setAutoZero(False)
    #@@@#if canMeasCurr: daq.measureCurrent()
    if canMeasCurr: daq.setAutoZero(False,function='CurrentDC')
    # Cannot choose a different function for setAutoZero() unless Front channel 1
    if args.chan == 1: daq.setAutoZero(False,function='Resistance2W')

    daq.setAutoZero(True)
    if canMeasCurr: daq.setAutoZero(True,function='CurrentDC')
    # Cannot choose a different function for setAutoZero() unless Front channel 1
    if args.chan == 1: daq.setAutoZero(True,function='Resistance2W')

    daq.autoZeroOnce()

    #@@@#print(daq._instQuery("ROUT:DEL? (@slot1)"))
    print('(Channel Delay: {:1.3f})  {:9.7g} V \t'.format(daq.queryChannelDelay(), daq.measureVoltage(query_delay=.1)))
    daq.setChannelDelay(0.01)
    print('(Channel Delay: {:1.3f})  {:9.7g} V \t'.format(daq.queryChannelDelay(), daq.measureVoltage(query_delay=.1)))
    daq.setChannelDelay(0.1)
    print('(Channel Delay: {:1.3f})  {:9.7g} V \t'.format(daq.queryChannelDelay(), daq.measureVoltage(query_delay=.1)))
    daq.setChannelDelay(2)
    print('(Channel Delay: {:1.3f})  {:9.7g} V \t'.format(daq.queryChannelDelay(), daq.measureVoltage(query_delay=.1)))
    #@@@#print(daq._instQuery("ROUT:DEL? (@slot1)"))
    daq.setChannelDelay(0.01)
    print()

    print('(Channel Connection Rule: {})  {:9.7g} V \t'.format(daq.queryChannelConnectRule(), daq.measureVoltage()))
    daq.setChannelConnectRuleBBM()
    print('(Channel Connection Rule: {})  {:9.7g} V \t'.format(daq.queryChannelConnectRule(), daq.measureVoltage()))
    daq.setChannelConnectRuleMBB()
    print('(Channel Connection Rule: {})  {:9.7g} V \t'.format(daq.queryChannelConnectRule(), daq.measureVoltage()))
    daq.setChannelConnectRuleCONC()
    print('(Channel Connection Rule: {})  {:9.7g} V \t'.format(daq.queryChannelConnectRule(), daq.measureVoltage()))
    daq._setChannelConnectRule('bBm')
    print('(Channel Connection Rule: {})  {:9.7g} V \t'.format(daq.queryChannelConnectRule(), daq.measureVoltage()))
    print()
    
    print('(Channel Label: "{}")  {:9.7g} V \t'.format(daq.queryChannelLabel(), daq.measureVoltage()))
    daq.setChannelLabel("Bob")
    print('(Channel Label: "{}")  {:9.7g} V \t'.format(daq.queryChannelLabel(), daq.measureVoltage()))
    daq.clearChannelLabel()
    print('(Channel Label: "{}")  {:9.7g} V \t'.format(daq.queryChannelLabel(), daq.measureVoltage()))
    daq.setChannelLabel("D_3V3")
    print('(Channel Label: "{}")  {:9.7g} V \t'.format(daq.queryChannelLabel(), daq.measureVoltage()))
    print()

    #@@@@@ START HERE with Averagign Window function tests
    
    
    
    quit()
    
    daq.setRelativeOffset()
    if canMeasCurr: daq.setRelativeOffset(0.0034567, function='CurrentDC')

    str = 'Relative Offsets: {:9.7g} V'.format(daq.queryRelativeOffset())
    if canMeasCurr: str += ' {:9.7g} A'.format(daq.queryRelativeOffset(function='CurrentDC'))
    print(str)
    
    print('Resistance:  {:6.4g} Ohm'.format(daq.measureResistance(args.chan)))
    
    daq.setRelativeOffsetState(True)
    if canMeasCurr: daq.setRelativeOffsetState(True,function='CurrentDC')

    print('{:9.7g} V'.format(daq.measureVoltage()))
    print('{:9.7g} V'.format(daq.measureVoltage()))
    print('{:9.7g} V'.format(daq.measureVoltage()))
    print('{:9.7g} V'.format(daq.measureVoltage()))
    print('{:9.7g} V'.format(daq.measureVoltage()))

    if canMeasCurr: 
        print('{:6.4g} A'.format(daq.measureCurrent()))
        print('{:6.4g} A'.format(daq.measureCurrent()))
        print('{:6.4g} A'.format(daq.measureCurrent()))
        print('{:6.4g} A'.format(daq.measureCurrent()))
        print('{:6.4g} A'.format(daq.measureCurrent()))
        
    print('')

    daq.setRelativeOffsetState(False,function='VoltageDC')
    daq.setRelativeOffsetState(False)
    
    print('Integration Time (DC Voltage): {} NPLC'.format(daq.queryIntegrationTime(function='VoltageDC')))
    if canMeasCurr: print('Integration Time (DC Current): {} NPLC'.format(daq.queryIntegrationTime(function='CurrentDC')))

    print('{:9.7g} V'.format(daq.measureVoltage()))
    print('{:9.7g} V'.format(daq.measureVoltage()))
    print('{:9.7g} V'.format(daq.measureVoltage()))
    print('{:9.7g} V'.format(daq.measureVoltage()))
    print('{:9.7g} V'.format(daq.measureVoltage()))

    if canMeasCurr: 
        print('{:6.4g} A'.format(daq.measureCurrent()))
        print('{:6.4g} A'.format(daq.measureCurrent()))
        print('{:6.4g} A'.format(daq.measureCurrent()))
        print('{:6.4g} A'.format(daq.measureCurrent()))
        print('{:6.4g} A'.format(daq.measureCurrent()))

    daq.setRelativeOffset("MAXIMUM", function='VoltageDC')
    if canMeasCurr: daq.setRelativeOffset("DEF", function='CurrentDC')

    str = 'Relative Offsets: {:9.7g} V'.format(daq.queryRelativeOffset(function='VoltageDC'))
    if canMeasCurr: str += ' {:9.7g} A'.format(daq.queryRelativeOffset(function='CurrentDC'))
    print(str)

    print('')
    daq.setIntegrationTime(10.0,function='VoltageDC')
    if canMeasCurr: daq.setIntegrationTime(10.0,function='CurrentDC')
    print('Integration Time (DC Voltage): {} NPLC'.format(daq.queryIntegrationTime(function='VoltageDC')))
    if canMeasCurr: print('Integration Time (DC Current): {} NPLC'.format(daq.queryIntegrationTime(function='CurrentDC')))

    print('{:9.7g} V'.format(daq.measureVoltage()))
    print('{:9.7g} V'.format(daq.measureVoltage()))
    print('{:9.7g} V'.format(daq.measureVoltage()))
    print('{:9.7g} V'.format(daq.measureVoltage()))
    print('{:9.7g} V'.format(daq.measureVoltage()))

    if canMeasCurr: 
        print('{:6.4g} A'.format(daq.measureCurrent()))
        print('{:6.4g} A'.format(daq.measureCurrent()))
        print('{:6.4g} A'.format(daq.measureCurrent()))
        print('{:6.4g} A'.format(daq.measureCurrent()))
        print('{:6.4g} A'.format(daq.measureCurrent()))

    print('')
    print('ASCII SIG FIGs: {}'.format(daq.queryAsciiPrecision()))
    print('{:16.14g} V'.format(daq.measureVoltage()))
    print('Set Sig Figs to MAX:')
    daq.setAsciiPrecision('MAX')
    print('ASCII SIG FIGs: {}'.format(daq.queryAsciiPrecision()))
    print('{:16.14g} V'.format(daq.measureVoltage()))
    print('Set Sig Figs to 0 (automatic):')
    daq.setAsciiPrecision(0)
    print('ASCII SIG FIGs: {}'.format(daq.queryAsciiPrecision()))
    print('{:16.14g} V'.format(daq.measureVoltage()))
    print('Set Sig Figs to 10:')
    daq.setAsciiPrecision(10)
    print('ASCII SIG FIGs: {}'.format(daq.queryAsciiPrecision()))
    print('{:16.14g} V'.format(daq.measureVoltage()))

    print('')
    print('Voltage DC    Range: {}'.format(daq.queryMeasureVoltageRange()))
    print('Voltage DC    Range: {}'.format(daq.queryMeasureRange(function='VoltageDC')))
    print('Voltage AC    Range: {}'.format(daq.queryMeasureRange(function='VoltageAC')))
    if canMeasCurr: print('Current DC    Range: {}'.format(daq.queryMeasureCurrentRange()))
    if canMeasCurr: print('Current AC    Range: {}'.format(daq.queryMeasureRange(function='CurrentDC')))
    if canMeasCurr: print('Current AC    Range: {}'.format(daq.queryMeasureRange(function='CurrentAC')))
    print('Resistance 2W Range: {}'.format(daq.queryMeasureRange(function='Resistance2W')))
    print('Resistance 4W Range: {}'.format(daq.queryMeasureRange(function='Resistance4W')))
    #@@@#print('Diode         Range: {}'.format(daq.queryMeasureRange(function='Diode')))
    print('Capacitance   Range: {}'.format(daq.queryMeasureRange(function='Capacitance')))
    #@@@#print('Temperature   Range: {}'.format(daq.queryMeasureRange(function='Temperature')))
    #@@@#print('Continuity    Range: {}'.format(daq.queryMeasureRange(function='Continuity')))
    #@@@#print('Frequency     Range: {}'.format(daq.queryMeasureRange(function='Frequency')))
    #@@@#print('Period        Range: {}'.format(daq.queryMeasureRange(function='Period')))
    print('VoltageRatio  Range: {}'.format(daq.queryMeasureRange(function='VoltageRatio')))

    print('\nSetting ranges')
    daq.setMeasureVoltageRange(3e-3)
    daq.setMeasureRange(4e-2,function='VoltageAC')
    if canMeasCurr: daq.setMeasureCurrentRange(5e-6)
    if canMeasCurr: daq.setMeasureRange(2,function='CurrentAC')
    daq.setMeasureRange(6e3,function='Resistance2W')
    daq.setMeasureRange(7e-4,function='Resistance4W')
    daq.setMeasureRange(8e-9,function='Capacitance')
    daq.setMeasureRange(9e-4,function='VoltageRatio')
    
    print('Voltage DC    Range: {}'.format(daq.queryMeasureVoltageRange()))
    print('Voltage AC    Range: {}'.format(daq.queryMeasureRange(function='VoltageAC')))
    if canMeasCurr: print('Current DC    Range: {}'.format(daq.queryMeasureCurrentRange()))
    if canMeasCurr: print('Current AC    Range: {}'.format(daq.queryMeasureRange(function='CurrentAC')))
    print('Resistance 2W Range: {}'.format(daq.queryMeasureRange(function='Resistance2W')))
    print('Resistance 4W Range: {}'.format(daq.queryMeasureRange(function='Resistance4W')))
    print('Capacitance   Range: {}'.format(daq.queryMeasureRange(function='Capacitance')))
    print('VoltageRatio  Range: {}'.format(daq.queryMeasureRange(function='VoltageRatio')))
    
    print('\nSetting ranges #2')
    daq.setMeasureVoltageRange('MAX')
    daq.setMeasureRange('MIN',function='VoltageAC')
    if canMeasCurr: daq.setMeasureCurrentRange(None)
    if canMeasCurr: daq.setMeasureRange('DEF',function='CurrentAC')
    daq.setMeasureRange('MAX',function='Resistance2W')
    daq.setMeasureRange('MIN',function='Resistance4W')
    daq.setMeasureRange(None,function='Capacitance')
    daq.setMeasureRange('Def',function='VoltageRatio')
    
    print('Voltage DC    Range: {}'.format(daq.queryMeasureVoltageRange()))
    print('Voltage AC    Range: {}'.format(daq.queryMeasureRange(function='VoltageAC')))
    if canMeasCurr: print('Current DC    Range: {}'.format(daq.queryMeasureCurrentRange()))
    if canMeasCurr: print('Current AC    Range: {}'.format(daq.queryMeasureRange(function='CurrentAC')))
    print('Resistance 2W Range: {}'.format(daq.queryMeasureRange(function='Resistance2W')))
    print('Resistance 4W Range: {}'.format(daq.queryMeasureRange(function='Resistance4W')))
    print('Capacitance   Range: {}'.format(daq.queryMeasureRange(function='Capacitance')))
    print('VoltageRatio  Range: {}'.format(daq.queryMeasureRange(function='VoltageRatio')))

    if (1):
        # Reset again and try reading from all functions, except DIODE
        # which may be determental to any circuits we are connected to
        # during testing.
        daq.rst(wait=1.0)
        daq.cls(wait=1.0)

        print('')
        #@@@#print('Integration Time (DC Voltage): {} NPLC'.format(daq.queryIntegrationTime(function='VoltageDC')))
        #@@@#print('Integration Time (DC Current): {} NPLC'.format(daq.queryIntegrationTime(function='CurrentDC')))    
        print('AC Voltage:  {:6.4g} V'.format(daq.measureVoltageAC(query_delay=3.0)))
        if canMeasCurr: print('AC Current:  {:6.4g} A'.format(daq.measureCurrentAC(query_delay=3.0)))
        print('Resistance:  {:6.4g} Ohm'.format(daq.measureResistance()))
        print('Resistance (4W): {:6.4g} Ohm'.format(daq.measureResistance4W()))
        #@@@#print('{:6.4g} V'.format(daq.measureDiode()))
        print('Capacitance: {:6.4g} F'.format(daq.measureCapacitance()))
        print('Temperature: {:6.4g} C'.format(daq.measureTemperature()))
        print('Continuity:  {:6.4g} Ohm'.format(daq.measureContinuity()))
        print('Frequency:   {:6.4g} Hz'.format(daq.measureFrequency(query_delay=3.0)))
        print('Period:      {:6.4g} s'.format(daq.measurePeriod(query_delay=3.0)))
        print('Volt Ratio:  {:6.4g} V/V'.format(daq.measureVoltageRatio()))

    ## Do Not Need to do Both openChannels - just testing both of them
    #
    ## open the last channel used
    daq.openChannel()
    #
    ## open All channels
    daq.openChannelAll()
        
    ## turn off the channel
    daq.inputOff()

    daq.beeperOn()

    ## return to LOCAL mode
    daq.setLocal()
    
    daq.close()
