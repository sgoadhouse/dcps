#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright (c) 2017, Emmanuel Blot <emmanuel.blot@free.fr>
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#     * Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#     * Neither the name of the Neotion nor the names of its contributors may
#       be used to endorse or promote products derived from this software
#       without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL NEOTION BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA,
# OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE,
# EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

from binascii import hexlify
from dataclasses import dataclass
import argparse

import PowerTestBoard
import BK9115
import Keithley6500
import RigolDL3000

import numpy as np
import csv

from sys import modules, stdout, exit
import logging
from os import environ, path
from datetime import datetime
from time import sleep

PLOT = True
if (PLOT):
    try:
        import matplotlib.pyplot as plt
    except:
        print('matplotlib.pyplot is needed for plotting waveform data to screen')
        print('(very convenient). Please install it with "pip install matplotlib==3.6".\n')
        print('If you do not want to install this very useful Python')
        print('package, then change line "PLOT = True" to "PLOT = False" in')
        print('this script')
        exit(-1)

#@@@#ftdi_url = 'ftdi://ftdi:4232h/1'
ftdi_url_const = 'ftdi://ftdi:4232:FTK1RRYC/1'


def handleFilename(fname, ext, unique=True, timestamp=True):

    # If extension exists in fname, strip it and add it back later
    # after handle versioning
    ext = '.' + ext                       # don't pass in extension with leading '.'
    if (fname.endswith(ext)):
        fname = fname[:-len(ext)]

    # Make sure filename has no path components, nor ends in a '/'
    if (fname.endswith('/')):
        fname = fname[:-1]
        
    pn = fname.split('/')
    fname = pn[-1]
        
    # Assemble full pathname so files go to ~/Downloads    if (len(pp) > 1):
    pn = environ['HOME'] + "/Downloads"
    fn = pn + "/" + fname

    if (timestamp):
        # add timestamp suffix
        fn = fn + '-' + datetime.now().strftime("%Y%0m%0d-%0H%0M%0S")

    suffix = ''
    if (unique):
        # If given filename exists, try to find a unique one
        num = 0
        while(path.isfile(fn + suffix + ext)):
            num += 1
            suffix = "-{}".format(num)

    fn += suffix + ext

    #@@@#print("handleFilename(): Filename '{}'".format(fn))
    
    return fn

def dataSaveCSV(filename, x, y, header=None, meta=None):
    """
    filename - base filename to store the data

    x        - indepedant data to write in first column

    y        - vertical data: expected to be a list of columns to write and can be any number of columns

    header   - a list of header strings, one for each column of data - set to None for no header

    meta     - a list of meta data for data - optional and not used by this function - only here to be like other dataSave functions

    """

    nLength = len(x)

    #@@@#print('Writing data to CSV file "{}". Please wait...'.format(filename))

    # Save data values to CSV file.
    # Determine iterator
    if (isinstance(y[0],list)):
        # Multiple columns in y, so break them out
        it = [[a,*b] for (a,b) in zip(x,y)]
    else:
        # Simply single column of y data
        it = zip(x,y)

    # Open file for output. Only output x & y for simplicity. User
    # will have to copy paste the meta data printed to the
    # terminal
    #@@@#print("dataSaveCSV(): Filename '{}'".format(filename))
    myFile = open(filename, 'w')
    with myFile:
        writer = csv.writer(myFile, dialect='excel', quoting=csv.QUOTE_NONNUMERIC)
        if header is not None:
            writer.writerow(header)

        writer.writerows(it)

    # return number of entries written
    return nLength


def dataSaveNPZ(filename, x, y, header=None, meta=None):
    """
    filename - base filename to store the data

    x        - indepedant data to write in first column

    y        - vertical data: expected to be a list of columns to write and can be any number of columns

    header   - a list of header strings, one for each column of data - set to None for no header

    meta     - a list of meta data for data

    A NPZ file is an uncompressed zip file of the arrays x, y and optionally header and meta if supplied. 
    To load and use the data from python:

    import numpy as np
    header=None
    meta=None
    with np.load(filename) as data:
        x = data['x']
        y = data['y']
        if 'header' in data.files:
            header = data['header']
        if 'meta' in data.files:
            meta = data['meta']

    """

    nLength = len(x)

    #@@@#print('Writing data to Numpy NPZ file "{}". Please wait...'.format(filename))

    arrays = {'x': x, 'y': y}
    if (header is not None):
        arrays['header']=header
    if (meta is not None):
        arrays['meta']=meta
    np.savez(filename, **arrays)

    # return number of entries written
    return nLength

def poweron():
    """enable the power output on the BK9115 power supply.
    """

    resource = environ.get('BK9115_USB', 'USB0::INSTR')
    bkps = BK9115.BK9115(resource)
    bkps.open()

    #@@@#print(bkps.idn())

    # IMPORTANT: 9115 requires Remote to be set or else commands are ignored
    bkps.setRemote()
    
    ## set Remote Lock On
    #bkps.setRemoteLock()
    
    bkps.beeperOff()

    # BK Precision 9115 has a single channel, so force chan to be 1
    chan = 1

    bkps.outputOn()
    #print('BK9115 Values:   {:6.4f} V  {:6.4f} A'.
    #          format(bkps.measureVoltage(),
    #                 bkps.measureCurrent()))
    
    ## return to LOCAL mode
    bkps.setLocal()
    
    bkps.close()
    
def poweroff():
    """Disable the BK 9115 DC power supply output.
    """

    resource = environ.get('BK9115_USB', 'USB0::INSTR')
    bkps = BK9115.BK9115(resource)
    bkps.open()

    # IMPORTANT: 9115 requires Remote to be set or else commands are ignored
    bkps.setRemote()
    
    # BK Precision 9115 has a single channel, so force chan to be 1
    chan = 1

    bkps.outputOff()
        
    ## return to LOCAL mode
    bkps.setLocal()
    
    bkps.close()

def setPowerValues(voltage,current,OVP=None,OCP=None):
    """Set the Voltage and Current values for the BK 9115 DC power supply output.

       voltage - floating point value to set voltage to
       current - floating point value to set current to
       OVP     - floating point value to set overvoltage protection to, or None to not set it
       OCP     - floating point value to set overcurrent protection to, or None to not set it
    """

    resource = environ.get('BK9115_USB', 'USB0::INSTR')
    bkps = BK9115.BK9115(resource)
    bkps.open()

    # IMPORTANT: 9115 requires Remote to be set or else commands are ignored
    bkps.setRemote()
    
    # BK Precision 9115 has a single channel, so force chan to be 1
    chan = 1

    bkps.setVoltage(voltage)
    bkps.setCurrent(current)

    if OVP is not None:
        bkps.setVoltageProtection(OVP, delay=0.010)
        bkps.voltageProtectionOn()

    if OCP is not None:
        bkps.setCurrentProtection(OCP, delay=0.010)
        bkps.currentProtectionOn()

    ## return to LOCAL mode
    bkps.setLocal()
    
    bkps.close()

    return (voltage, current)

def measurePowerValues():
    """Measure the Voltage and Current values from the BK 9115 DC power supply output.
    """

    resource = environ.get('BK9115_USB', 'USB0::INSTR')
    bkps = BK9115.BK9115(resource)
    bkps.open()

    # IMPORTANT: 9115 requires Remote to be set or else commands are ignored
    bkps.setRemote()
    
    # BK Precision 9115 has a single channel, so force chan to be 1
    chan = 1

    voltage = bkps.measureVoltage()
    current = bkps.measureCurrent()
    
    #@@@#print('BK9115 Values:   {:6.4f} V  {:6.4f} A'.format(voltage,current))
            
    ## return to LOCAL mode
    bkps.setLocal()
    
    bkps.close()

    return (voltage, current)

def instrumentInit(instr):
    # Reset
    instr.rst(wait=0.2)
    instr.cls(wait=0.2)

    #@@@#print(instr.idn())
    
    ## set Remote Lock On
    instr.setRemoteLock()

    ## turn off the beeper
    instr.beeperOff()

def instrumentStop(instr):
    instr.inputOff()
    instr.beeperOn()
    #@@@#instr.printAllErrors()    
    #@@@#instr.cls()
    
    ## return to LOCAL mode
    instr.setLocal()

@dataclass(frozen=True)
class DCEfficiencyParam:
    upper: float                # upper output voltage so can set a range
    loads: list                 # list of floats to set load to in sequence
    load_wait: float            # number of seconds to wait after changing load before measuring data

DCEfficiencyParams = {
    '1V8-A': DCEfficiencyParam(upper=2.0,loads=[a/10 for a in range(0,31)],load_wait=3.0), # load: step 0.1A for 0-3A
}

def DCEfficiency(PTB,DMM,ELOAD,circuit,param):

    print("Testing DC Efficiency for '{}'".format(circuit))
    
    ## Make sure power supply is off at start
    poweroff()

    instrumentInit(DMM)
    instrumentInit(ELOAD)

    ## Setup DMM for use
    DMM.setMeasureFunction('VoltageDC')
    DMM.setAutoZero(True)
    DMM.setIntegrationTime(14)
    DMM.setAsciiPrecision(8)
    DMM.setMeasureRange(param.upper)   # Set Range to be constant based on upper limit output voltage
    DMM.inputOn()

    ## Setup ELOAD for use
    #
    ## Make sure Electronic Load Input is OFF
    ELOAD.inputOff()    
    ELOAD.setFunction('current')   # Constant Current
    ELOAD.setSenseState(True)      # Enable Sense inputs

    ## Set for 12V / 5A with protections
    setPowerValues(12.0,5,OVP=16.0,OCP=7.5)
    poweron()
    sleep(2)                    # give some time to settle

    # save the starting voltage and current
    startValues = measurePowerValues() # voltage, current
    
    print(' BK9115 Start Values:     {:6.4f} V  {:6.4f} A'.format(*startValues))

    # Enable power supply output and give some time to settle
    PTB.powerEnable(PTB.circuits[circuit],True)
    sleep(2)

    #@@@#input("Press Enter to continue...") 

    
    # save the baseline voltage and current
    baseValues = measurePowerValues() # voltage, current
    
    print(' BK9115 Baseline Values:  {:6.4f} V  {:6.4f} A'.format(*baseValues))

    ## Main Loop
    ## - Enable/Disable Input of DL3031A and Set next current load
    ## - measure BK9115 Voltage & Current
    ## - subtract start current to get DC circuit current (estimated)
    ## - measure DMM9500 Voltage & DL3031A (E-Load) Current
    ## - compute Power In / Power Out as a percentage
    ## - Save all values to data[]

    ## data will be an array of tuples to save the data
    data = []

    for load in param.loads:
        ## - Enable Input of DL3031A, if non-0 load, and Set next current load
        if (load == 0):
            ELOAD.inputOff()
            sleep(param.load_wait)
        else:
            if (not ELOAD.isInputOn()):
                # If the Input is NOT enabled, then first set the load
                # value to make sure it is not too high from a
                # previous test. However, have noticed that sometimes
                # input will enable at a low current anyway and ignore
                # what it had been set to just recently. So still set
                # the current after enabling the input.
                ELOAD.setCurrent(load,wait=0.2)
                ELOAD.inputOn()
            ELOAD.setCurrent(load,wait=param.load_wait)

        ## - measure BK9115 Voltage & Current
        (psVoltage, psCurrent) = measurePowerValues()

        ## - subtract start current to get DC circuit current (estimated)
        inVoltage = psVoltage
        inCurrent = psCurrent - startValues[1]
        
        ## - measure DMM9500 Voltage & DL3031A (E-Load) Current
        outVoltage = DMM.measureVoltage()
        outCurrent = ELOAD.measureCurrent()
        
        ## - compute Power Out / Power In as a percentage
        outPower = (outVoltage * outCurrent)
        inPower  = (inVoltage * inCurrent)
        efficiency = (outPower / inPower) * 100
        
        ## - Add values to data
        data.append([inVoltage, inCurrent, outVoltage, outCurrent, efficiency])

        print("   Load: {:.03f}A  Power: {:.03f}/{:.03f} W  Eff: {:d} %".format(load, outPower, inPower, int(efficiency)))
        
        #@@@#input("Press Enter to continue...") 

    #@@@#print(data)

    ## Disable ELOAD
    ELOAD.inputOff()
    
    ## - Save all values
    header = ["Load (A)","VIN (V)","IIN (A)","VOUT (V)","IOUT (A)","Efficiency (%)"]
    meta = {'circuit': circuit, 'test': 'Power Efficiency'}
    fnbase = "Eff_data_"+circuit
    # Use NPZ files which write in under a second instead of bulky csv files
    if False:
        fn = handleFilename(fnbase, 'csv')
        dataLen = dataSaveCSV(fn, param.loads, data, header, meta)
    else:
        fn = handleFilename(fnbase, 'npz')
        dataLen = dataSaveNPZ(fn, param.loads, data, header, meta)
    print("Data Output {} points to file {}".format(dataLen,fn))

    #@@@#DCEfficiencyPlot(param.loads, data, 3, header, circuit)
    
    ## - Graph values and save graphs
    ## @@@@
    
    ## Done - so turn off electronic load, board and power
    sleep(1)
    instrumentStop(ELOAD)
    instrumentStop(DMM)

    sleep(1)
    PTB.powerEnable(PTB.circuits[circuit],False)

    sleep(1)
    poweroff()
    
def DCEfficiencyPlot(x,data,col,header,circuit):
    if (PLOT and (len(x) == len(data))):
        print("Close the plot window to continue...")
        fig, (ax1) = plt.subplots(1)
        # create list of y from column col in data
        y = [a[col] for a in data]
        ax1.plot(x, y)      # plot the data
        ax1.axvline(x=0.0, color='r', linestyle='--')
        ax1.axhline(y=0.0, color='r', linestyle='--')
        ax1.set_title('Effciency Data for {}'.format(circuit))
        ax1.set_xlabel(header[0])
        ax1.set_ylabel(header[col+1])
        
        fig.tight_layout()
        plt.show()

        
if __name__ == '__main__':
    #@@@#testmod(modules[__name__])

    ptb = PowerTestBoard.PowerTestBoard(environ.get('FTDI_DEVICE', ftdi_url_const))
    dmm = Keithley6500.Keithley6500(environ.get('DMM6500_VISA', 'TCPIP0::172.16.2.13::INSTR'))
    eload = RigolDL3000.RigolDL3000(environ.get('DL3000_VISA', 'TCPIP0::172.16.2.13::INSTR'))
            
    parser = argparse.ArgumentParser(description='Run various tests on the Power Test Board and collect data')

    # Mutuall Exclusive tests - pick one an donly one
    mutex_grp = parser.add_mutually_exclusive_group(required=True)
    mutex_grp.add_argument('-e', '--dc_efficiency',  action='store_true', help='run the DC Power Efficiency test')
    mutex_grp.add_argument('-i', '--line_regulation', action='store_true', help='run the Line Regulation test')
    mutex_grp.add_argument('-o', '--load_regulation', action='store_true', help='run the Load Regulation test')


    parser.add_argument('list_of_circuits', metavar='circuits', type=ptb.validate_circuits, nargs='*', help='a list of circuits - or all if omitted')
    
    args = parser.parse_args()

    try:
        ## Make sure power supply is off at start
        poweroff()

        ## Open DMM and Eload
        dmm.open()
        eload.open()

        circuit_list = args.list_of_circuits

        # If no list given, then use all circuits
        if len(circuit_list) <= 0:
            circuit_list = ptb.circuits.keys()
        
        for circ in circuit_list:
            if (args.dc_efficiency):
                DCEfficiency(ptb, dmm, eload, circ, DCEfficiencyParams[circ])
            elif (args.line_regulation):
                pass
            elif (args.load_regulation):
                pass
            else:
                raise ValueError("A test was not selected with the command line arguments")
            
        ## Make sure power supply is off at end
        poweroff()

        ## Close DMM and Eload
        eload.close()
        dmm.close()
        
        #@@@#test_i2c_gpio()

        #powerEnable(0,0)
        #powerEnable(1,0)
        #powerEnable(2,0)
        #powerEnable(3,0)
    
        #powerEnable(4,0)
        #powerEnable(5,0)
        #powerEnable(6,0)
        #powerEnable(7,0)
        
        #powerEnable(8,0)
        #powerEnable(9,0)
        #powerEnable(10,0)
        #powerEnable(11,0)

    except KeyboardInterrupt:
        ## Close DMM and Eload
        dmm.close()
        eload.close()
        exit(2)
