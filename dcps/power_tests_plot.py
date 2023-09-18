#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright (c) 2023, Stephen Goadhouse <sdg@cern.ch>
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
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import csv
from scipy import interpolate

from sys import modules, stdout, exit
import logging
from os import environ, path
from datetime import datetime
from time import sleep


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
        rows = data['rows']
        if 'header' in data.files:
            header = data['header']
        if 'meta' in data.files:
            meta = data['meta']

    """

    header=None
    meta=None
    with np.load(filename,allow_pickle=False) as data:
        rows = data['rows']
        if 'header' in data.files:
            header = data['header']
        if 'meta' in data.files:
            meta = data['meta']
    
    # return data
    return (rows, header, meta)

def data2Pandas(rows, header, meta):

    #@@@#print(x)
    #print(y)
    #print(type(y))
    #print(type(y[0]))
    #print(header)
    
    #@@@#print(rows)
    
    df = pd.DataFrame(rows, columns=header)

    #@@@#print(df)
    return (df, meta)

def dataLoadPKL(filename):
    """
    filename - pickle filename to load data

    A PKL, or pickle, file is a file used to store a Pandas
    DataFrame. DataFrames allow different types of data in a single
    row whereas numpy only allows a single type. So if add a string,
    like boardName, ALL data becomes strings which explodes the file
    size.

    To load and use the data from python:

    import pandas as pd
    df = pd.read_pickle("my_data.pkl")
    """

    df = pd.read_pickle(filename)
    
    # return data
    return df

    
@dataclass(frozen=True)
class DCEfficiencyParam:
    upper: float                # upper output voltage so can set a range
    loads: list                 # list of floats to set load to in sequence
    load_wait: float            # number of seconds to wait after changing load before measuring data

DCEfficiencyParams = {
    '1V8-A': DCEfficiencyParam(upper=2.0,loads=[a/10 for a in range(0,31)],load_wait=3.0), # load: step 0.1A for 0-3A
}

def DCEfficiencyPlotOLD(x,data,col,header,circuit):
    if (len(x) == len(data)):
        print("Close the plot window to continue...")
        fig, ax1 = plt.subplots()
        # create list of y from column col in data
        y = [a[col] for a in data]
        #@@@#print(x)
        #@@@#print(y)
        ax1.plot(x, y, color='blue', ls='-', marker='.')      # plot the data
        #@@@#ax1.axvline(x=0.0, color='r', linestyle='--')
        #@@@#ax1.axhline(y=0.0, color='r', linestyle='--')
        ax1.set_title('Effciency Data for {}'.format(circuit))
        ax1.set_xlabel(header[0])
        ax1.set_ylabel(header[col+1])
        
        #@@@#fig.tight_layout()
        plt.show()

def DCEfficiencyPlot(df,x,y):
    print("Close the plot window to continue...")

    #@@@#print(df[x].values)
    #@@@#print(df[y].values)
    
    # Apply the default theme
    sns.set_theme()

    interp = False
    
    if (True):
        # Create a visualization
        #@@@#sns.relplot(data=df,x=x, y=y)

        #@@@#sns.lmplot(x=x, y=y, data=df, order=3, ci=None) #@@@#, scatter_kws={"s": 80})
        #@@@#sns.lmplot(x=x, y=y, data=df, lowess=True, line_kws={"color": "C1"})
        #@@@#sns.lineplot(data=df, x=x, y=y, markers=True, dashes=False, style="Trial", err_style = "band")
        #@@@#sns.lineplot(data=df, x=x, y=y)
        #@@@#sns.lineplot(data=df, x=x, y=y, orient="y")
        #@@@#sns.lineplot(data=df, x=x, y=y, hue="Trial")
        #@@@#sns.lineplot(data=df, x=x, y=y, markers=True, dashes=False, hue="Trial", style="Trial")

        #@@@#df = df.sort_values(by=x)
        
        #@@@#sns.lineplot(data=df, x=x, y=y, marker='o', sort=True)
        
        lw = 0 if interp else None
        #@@@#sns.lineplot(data=df, x=x, y=y, marker='o', linewidth=lw)
        #@@@#sns.lineplot(data=df, x=x, y=y, marker='o', linewidth=lw, hue="Set VIN")

        #@@@#df1 = df.drop(df[df['Set VIN'] not in [10.8, 12.0, 13.2]].index)
        #@@@#df1 = df.query("'Set VIN' == 10.8 | 'Set VIN' == 13.2")
        df1 = df[ (df['Set VIN'] ==10.8) |
                  (df['Set VIN'] == 11.4) |
                  (df['Set VIN'] == 12.0) |
                  (df['Set VIN'] == 12.6) |
                  (df['Set VIN'] == 13.2)]

        palette = sns.color_palette("hls",5)
        sns.lineplot(data=df1, x=x, y=y, linewidth=lw, hue="Set VIN", palette = palette)
        plt.xlabel("Load (A)")
        #@@@#plt.get_legend().set_title("title")
        plt.legend().set_title("VIN (V)")
        
    if (False):
        xl = df[x].values[0:31]
        yl = df[y].values[0:31]

        poly = np.polyfit(xl,yl,5)
        poly_y = np.poly1d(poly)(xl)
        plt.plot(xl,poly_y)
        plt.plot(xl,yl)

    if (False):
        xl = df[x].values[0:31]
        yl = df[y].values[0:31]
        #@@@#df = df.sort_values(by=x)
        #@@@#xl = df[x].values
        #@@@#yl = df[y].values

        print(xl)
        print(yl)
        
        tck,u     = interpolate.splprep( [xl,yl], s = 0 )
        #@@@#xnew,ynew = interpolate.splev( np.linspace( 0, 1, 100 ), tck,der = 0)    
        xnew,ynew = interpolate.splev( np.arange(0, 1.01, 0.01), tck)

        #@@@#plt.plot( xl, yl, 'orange', xnew ,ynew )
        plt.plot( xnew ,ynew, 'orange' )

        
    if (interp):

        # Delete rows where the 'Efficiency (%)'] < 40 since that throws off the spline generation
        #@@@#df = df.drop(df[df['Load (A)'] == 0].index)
        df = df.drop(df[df['Efficiency (%)'] < 40].index)
        
        # It appears that there is too much data or that sequentially
        # it goes back and forth with changing of two variables. So
        # remove all put data where VIN is set to the nominal value,
        # 12.0.
        df = df.drop(df[df['Set VIN'] != 12.0].index)

        # Sort because that seems to be what interpolate needs
        df = df.sort_values(by=x)
        xl = df[x].values
        yl = df[y].values
        
        #@@@#plt.figure()
        #@@@#bspl = interpolate.splrep(xl,yl,s=0.1*len(yl))
        bspl = interpolate.splrep(xl,yl,s=5)
        bspl_y = interpolate.splev(xl,bspl)
        #@@@#plt.plot(xl,yl, 'orange', xl,bspl_y)
        #@@@#plt.plot( xl , bspl_y, 'orange' )
        #@@@#plt.plot( xl , bspl_y, 'blue' )
        #@@@#plt.plot( xl , bspl_y, 'purple', alpha=0.7, linestyle='dashed')

        # Insert a point 0,0 so line is complete)
        plt.plot( np.insert(xl, 0, 0) , np.insert(bspl_y, 0, 0), 'C0')
        
    if (False):
        import statsmodels.api as sm

        #@@@#x = df[x].values[0:31]
        #@@@#y = df[y].values[0:31]
        df = df.sort_values(by=x)
        xl = df[x].values
        yl = df[y].values

        print(xl)
        print(yl)
        
        y_lowess = sm.nonparametric.lowess(yl, xl, frac = 0.20)  # 20 % lowess smoothing
        plt.plot(xl, yl, 'orange', y_lowess[:, 0], y_lowess[:, 1])

    if (False):
        from scipy.signal import savgol_filter

        df = df.sort_values(by=x)
        xl = df[x].values
        yl = df[y].values
        
        window = 21
        order = 2
        y_sf = savgol_filter(yl, window, order)
        plt.plot(xl, y_sf)

    plt.show()
        
if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Plot data from power tests on Power Test Board')

    # Mutuall Exclusive tests - pick one an donly one
    mutex_grp = parser.add_mutually_exclusive_group(required=True)
    mutex_grp.add_argument('-e', '--power_efficiency',  action='store_true', help='plot the Power Efficiency test data')
    mutex_grp.add_argument('-i', '--line_regulation',   action='store_true', help='plot the Line Regulation test data')
    mutex_grp.add_argument('-o', '--load_regulation',   action='store_true', help='plot the Load Regulation test data')

    parser.add_argument('filename', help='filename of NPZ datafile')
    
    args = parser.parse_args()

    try:
        if False:
            (df, meta) = data2Pandas(*dataLoadNPZ(args.filename))

            test = None
            circ = None
            trials = None
        
            if (len(meta) >= 1):
                test = meta[0]
            if (len(meta) >= 2):
                circ = meta[1]
            if (len(meta) >= 3):
                boardName = meta[2]
            if (len(meta) >= 4):
                trials = meta[3]
        else:
            df = dataLoadPKL(args.filename)
            
        if (args.power_efficiency):
            #@@@#DCEfficiencyPlot(df,"Set Load","Efficiency (%)",circ, trials)
            DCEfficiencyPlot(df,"Set Load","Efficiency (%)")
        else:
            raise ValueError("Unknown test type '{}'".format(test))
        

    except KeyboardInterrupt:
        exit(2)
