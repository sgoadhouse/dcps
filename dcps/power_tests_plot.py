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

def dataLoadCSV(filename, x, y, header=None, meta=None):
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


def dataLoadNPZ(filename):
    """
    filename - filename to load data

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

    header=None
    meta=None
    with np.load(filename,allow_pickle=False) as data:
        x = data['x']
        y = data['y']
        if 'header' in data.files:
            header = data['header']
        if 'meta' in data.files:
            meta = data['meta']
    
    # return data
    return (x, y, header, meta)

@dataclass(frozen=True)
class DCEfficiencyParam:
    upper: float                # upper output voltage so can set a range
    loads: list                 # list of floats to set load to in sequence
    load_wait: float            # number of seconds to wait after changing load before measuring data

DCEfficiencyParams = {
    '1V8-A': DCEfficiencyParam(upper=2.0,loads=[a/10 for a in range(0,31)],load_wait=3.0), # load: step 0.1A for 0-3A
}

def DCEfficiencyPlot(x,data,col,header,circuit):
    if (PLOT and (len(x) == len(data))):
        print("Close the plot window to continue...")
        fig, ax1 = plt.subplots()
        # create list of y from column col in data
        y = [a[col] for a in data]
        print(x)
        print(y)
        ax1.plot(x, y)      # plot the data
        ax1.axvline(x=0.0, color='r', linestyle='--')
        ax1.axhline(y=0.0, color='r', linestyle='--')
        ax1.set_title('Effciency Data for {}'.format(circuit))
        ax1.set_xlabel(header[0])
        ax1.set_ylabel(header[col+1])
        
        #@@@#fig.tight_layout()
        plt.show()

        
if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Plot data from power tests on Power Test Board')

    # Mutuall Exclusive tests - pick one an donly one
    #@@@#mutex_grp = parser.add_mutually_exclusive_group(required=True)
    #mutex_grp.add_argument('-e', '--dc_efficiency',  action='store_true', help='run the DC Power Efficiency test')
    #mutex_grp.add_argument('-i', '--line_regulation', action='store_true', help='run the Line Regulation test')
    #mutex_grp.add_argument('-o', '--load_regulation', action='store_true', help='run the Load Regulation test')

    parser.add_argument('filename', help='filename of NPZ datafile')
    
    args = parser.parse_args()

    try:
        (x, y, header, meta) = dataLoadNPZ(args.filename)

        test = meta[0]
        circ = meta[1]
        
        if (test == "Power Efficiency"):
            DCEfficiencyPlot(x,y,4,header,circ)
        else:
            raise ValueError("Unknown test type '{}'".format(test))
            

    except KeyboardInterrupt:
        exit(2)
