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
from matplotlib.ticker import FuncFormatter, NullFormatter, LogLocator
import seaborn as sns
import csv
from scipy import interpolate

from sys import modules, stdout, exit
import logging
from os import environ, path
from datetime import datetime
from time import sleep
from pathlib import PurePath

## DPI when saving plots to an image file
saveFigDPI = 1200


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


def rangef(start, stop, step, ndigits, extra=None, sort=True):
    """Return a floating point range from start to stop, INCLUSIVE, using step. The values in the returned list are rounded to ndigits digits
    """
    
    n = int(round(((stop+step)-start)/step,0))
    lst = [round(a,ndigits) for a in np.linspace(start,stop,n)]
    
    if (extra is not None):
        ## Insert these values
        if isinstance(extra,int) or isinstance(extra,float):
            ## if extra is a single value, add it to list appropriately
            lst = [extra]+lst
        elif isinstance(extra,list):
            ## extra is a list so simply add it
            lst = extra+lst
        else:
            ## do not know how to handle this type
            raise ValueError("rangef(): Incorrect type for 'extra' parameter: {}".format(type(extra)))
        
    if sort:
        ## Sort values
        lst.sort()
        
    return lst

@dataclass(frozen=True)
class CircuitParam:
    voutMin: float                # Minimum allowed output voltage (set horizontal line or a background gradient)
    voutMax: float                # Maximum allowed output voltage (set horizontal line or a background gradient)
    voutAbsMax: float             # Absolute Maximum VOUT
    vinListEff: list              # list of VINs to plot on Efficiency
    vinListLRg: list              # list of VINs to plot on Load Regulations
    ioutList: list                # list of IOUTs to plot on Line Regulation

defVinList = [10.8, 11.4, 12.0, 12.6, 13.2]
defVinLRg  = [12.0]
minVolt1v8 = 1.71
maxVolt1v8 = 1.89
minFpga1v8 = 1.746
maxFpga1v8 = 1.854

CircuitParams = {
    ## FPGA 1.8V has a tighter voltage range: 1.746V - 1.854V, but everything else is 1.71V to 1.89V. To better compare, use the FPGA range
    '1V8-A': CircuitParam(voutMin=1.746, voutMax=1.854, voutAbsMax=2.0, vinListEff=defVinList, vinListLRg=defVinLRg, ioutList=[0.1, 1.0, 2.0, 3.0]),
    '1V8-B': CircuitParam(voutMin=1.746, voutMax=1.854, voutAbsMax=2.0, vinListEff=defVinList, vinListLRg=defVinLRg, ioutList=[0.1, 1.0, 2.0, 3.0]),
    '1V8-C': CircuitParam(voutMin=1.746, voutMax=1.854, voutAbsMax=1.9, vinListEff=defVinList, vinListLRg=defVinLRg, ioutList=[0.1, 1.0, 2.0, 3.0, 4.0, 6.0]),  ###rangef(0.5,6.0,0.5,1)),
    '1V8-D': CircuitParam(voutMin=1.746, voutMax=1.854, voutAbsMax=2.0, vinListEff=defVinList, vinListLRg=defVinLRg, ioutList=[0.1, 1.0, 2.0, 3.0]),

    ## FireFly and ELM want 3.15V to 3.45V range but clocks and SSD are fine with 3.135V to 3.465V, so set to 3.15 to 3.45
    '3V3-A':  CircuitParam(voutMin=3.15, voutMax=3.45, voutAbsMax=3.6, vinListEff=defVinList, vinListLRg=defVinLRg, ioutList=[0.1, 1.0, 2.0, 3.0]),
    '3V3-B':  CircuitParam(voutMin=3.15, voutMax=3.45, voutAbsMax=3.6, vinListEff=defVinList, vinListLRg=defVinLRg, ioutList=[0.1, 1.0, 2.0, 2.5]),
    '3V75-B': CircuitParam(voutMin=3.60, voutMax=3.90, voutAbsMax=4.5, vinListEff=defVinList, vinListLRg=defVinLRg, ioutList=[0.1, 1.0, 2.0, 2.5]),
    '3V3-C':  CircuitParam(voutMin=3.15, voutMax=3.45, voutAbsMax=3.6, vinListEff=defVinList, vinListLRg=defVinLRg, ioutList=[0.1, 1.0, 2.0, 3.0]),
    '3V3-D':  CircuitParam(voutMin=3.15, voutMax=3.45, voutAbsMax=3.6, vinListEff=defVinList, vinListLRg=defVinLRg, ioutList=[0.1, 1.0, 3.0, 6.0, 10.0]),

    '0V9':    CircuitParam(voutMin=0.873, voutMax=0.927, voutAbsMax=1.0, vinListEff=defVinList, vinListLRg=defVinLRg, ioutList=[0.1, 3.0, 6.0, 10.0, 15.0]),

    '1V2-A':  CircuitParam(voutMin=1.164, voutMax=1.236, voutAbsMax=1.30, vinListEff=defVinList, vinListLRg=defVinLRg, ioutList=[0.1, 6.0, 10.0, 20.0, 40.0]),
    '1V2-B':  CircuitParam(voutMin=1.164, voutMax=1.236, voutAbsMax=1.30, vinListEff=defVinList, vinListLRg=defVinLRg, ioutList=[0.1, 6.0, 10.0, 20.0, 40.0]),

    #@@@#'0V85':   CircuitParam(voutMin=0.825, voutMax=0.876, voutAbsMax=1.00, vinListEff=defVinList, vinListLRg=defVinLRg, ioutList=[0.1, 1.0, 5.0, 20.0, 30.0, 40.0, 50.0, 60.0]),
    '0V85':   CircuitParam(voutMin=0.825, voutMax=0.876, voutAbsMax=1.00, vinListEff=defVinList, vinListLRg=defVinLRg, ioutList=[0.1, 10.0, 20.0, 30.0, 40.0, 48.0]),
}
                          
        
def DCEfficiencyPlot(df,x,y,saveFilename=None,circuit=None):
    print("Close the plot window to continue...")

    #@@@#print(df[x].values)
    #@@@#print(df[y].values)
    
    # Apply the default theme
    sns.set_theme()

    # Assume parameters to use with first row Circuit value
    #@@@#print("Circuit: {}".format(df['Circuit'][0]))
    params = CircuitParams[df['Circuit'][0]]
    
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
        #df1 = df[ (df['Set VIN'] == 10.8) |
        #          (df['Set VIN'] == 11.4) |
        #          (df['Set VIN'] == 12.0) |
        #          (df['Set VIN'] == 12.6) |
        #          (df['Set VIN'] == 13.2)]
        df1 = df[ (df['Set VIN'].isin(params.vinListEff)) ]

        palette = sns.color_palette("hls",len(params.vinListEff))
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

    yticks = list(range(0,110,10))
    #print(yticks)
    plt.yticks(yticks)
        
    #plt.xlabel("Input Voltage (V)")
    #plt.ylabel("Output Voltage (V)")

    title = "Efficiency"
    if circuit is None:
        plt.title(title)
    else:
        plt.title(circuit+": "+title)

    if (saveFilename is not None):
        # Handle output of plot as an image file
        saveFilename = saveFilename.with_stem(saveFilename.stem+"_Eff")
        #@@@#print(saveFilename)
        plt.savefig(saveFilename,dpi=saveFigDPI,bbox_inches='tight',pad_inches = 0,facecolor=(1, 1, 1, 0)) # facecolor makes the border transparent
        print("Saved plot image to {}".format(saveFilename))
        
    plt.show()

def LineRegulatonPlot(df,x,y,saveFilename=None,circuit=None):
    """Plot VOUT vs VIN with a different color hue for a set of IOUT loads"""
    
    print("Close the plot window to continue...")

    #@@@#print(df[x].values)
    #@@@#print(df[y].values)
    
    # Apply the default theme
    sns.set_theme()

    # Assume parameters to use with first row Circuit value
    #@@@#print("Circuit: {}".format(df['Circuit'][0]))
    params = CircuitParams[df['Circuit'][0]]
    
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
        
        #@@@#lw = 0 if interp else None
        lw = None
        
        #@@@#sns.lineplot(data=df, x=x, y=y, marker='o', linewidth=lw)
        #@@@#sns.lineplot(data=df, x=x, y=y, marker='o', linewidth=lw, hue="Set VIN")

        #@@@#df1 = df.drop(df[df['Set VIN'] not in [10.8, 12.0, 13.2]].index)
        #@@@#df1 = df.query("'Set VIN' == 10.8 | 'Set VIN' == 13.2")

        #df1 = df[ (df['Set Load'] == 0.5) |
        #          (df['Set Load'] == 1.0) |
        #          (df['Set Load'] == 1.5) |
        #          (df['Set Load'] == 2.0) |
        #          (df['Set Load'] == 2.5) |
        #          (df['Set Load'] == 3.0)]
        df1 = df[ (df['Set Load'].isin(params.ioutList)) ]
        
        palette = sns.color_palette("hls",len(params.ioutList))
        sns.lineplot(data=df1, x=x, y=y, linewidth=lw, hue="Set Load", palette = palette)

        print("Voltage Range Req. {:.3f} to {:.3f}V / Actual {:.3f} to {:.3f}V".format(params.voutMin, params.voutMax, np.min(df1['VOUT (V)']), np.max(df1['VOUT (V)'])))        
        
        plt.xlabel("VIN (V)")
        #@@@#plt.get_legend().set_title("title")
        plt.legend().set_title("Load (A)")

    ax = plt.gca()
    #@@@#ax.set_ylim(ymin=1.79,ymax=1.81)

    if (True):
        ## Show a green band of valid VOUT
        plt.axhspan(params.voutMin, params.voutMax, facecolor='lightgreen', alpha=0.25)
        xlocs, xlabels = plt.xticks()
        xmid = np.mean(xlocs)
        #@@@#print(xlocs)
        #@@@#print(xmid)
        plt.text(xmid, params.voutMin, '{}'.format(params.voutMin), color='green', horizontalalignment='center', verticalalignment='bottom')
        plt.text(xmid, params.voutMax-.001, '{}'.format(params.voutMax), color='green', horizontalalignment='center', verticalalignment='top')

    plt.xlabel("Input Voltage (V)")
    plt.ylabel("Output Voltage (V)")
    
    #@@@#title = "Line Regulation"
    title = "Line and Load Regulation"

    if circuit is None:
        plt.title(title)
    else:
        plt.title(circuit+": "+title)
    
    #@@@#ax.tick_params(axis="y", bottom=True, top=True, labelbottom=True, labeltop=True)
    #@@@#print(plt.yticks())

    if (saveFilename is not None):
        # Handle output of plot as an image file
        saveFilename = saveFilename.with_stem(saveFilename.stem+"_LiR")
        plt.savefig(saveFilename,dpi=saveFigDPI,bbox_inches='tight',pad_inches = 0,facecolor=(1, 1, 1, 0)) # facecolor makes the border transparent
        print("Saved plot image to {}".format(saveFilename))

    plt.show()
        


## from https://stackoverflow.com/questions/44078409/how-to-display-all-minor-tick-marks-on-a-semi-log-plot    
def restore_minor_ticks_log_plot(ax = None, n_subticks=9) -> None:
    """For axes with a logrithmic scale where the span (max-min) exceeds
    10 orders of magnitude, matplotlib will not set logarithmic minor ticks.
    If you don't like this, call this function to restore minor ticks.

    Args:
        ax:
        n_subticks: Number of Should be either 4 or 9.

    Returns:
        None
    """
    if ax is None:
        ax = plt.gca()
    # Method from SO user importanceofbeingernest at
    # https://stackoverflow.com/a/44079725/5972175
    locmaj = LogLocator(base=10, numticks=1000)
    ax.xaxis.set_major_locator(locmaj)
    locmin = LogLocator(
        base=10.0, subs=np.linspace(0, 1.0, n_subticks + 2)[1:-1], numticks=1000
    )
    ax.xaxis.set_minor_locator(locmin)
    ax.xaxis.set_minor_formatter(NullFormatter())
    
def LoadRegulatonPlot(df,x,y,saveFilename=None,circuit=None):
    """Plot VOUT vs IOUT with a different color hue for a set of VINs"""

    print("Close the plot window to continue...")

    #@@@#print(df[x].values)
    #@@@#print(df[y].values)
    
    # Apply the default theme
    sns.set_theme()

    # Assume parameters to use with first row Circuit value
    #@@@#print("Circuit: {}".format(df['Circuit'][0]))
    params = CircuitParams[df['Circuit'][0]]
    
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
        
        #@@@#lw = 0 if interp else None
        lw = None
        
        #@@@#sns.lineplot(data=df, x=x, y=y, marker='o', linewidth=lw)
        #@@@#sns.lineplot(data=df, x=x, y=y, marker='o', linewidth=lw, hue="Set VIN")

        #@@@#df1 = df.drop(df[df['Set VIN'] not in [10.8, 12.0, 13.2]].index)
        #@@@#df1 = df.query("'Set VIN' == 10.8 | 'Set VIN' == 13.2")

        df1 = df[ (df['Set VIN'].isin(params.vinListLRg)) ]
        
        palette = sns.color_palette("hls",len(params.vinListLRg))
        sns.lineplot(data=df1, x=x, y=y, linewidth=lw, hue="Set VIN", palette = palette)

        print("Voltage Range Req. {:.3f} to {:.3f}V / Actual {:.3f} to {:.3f}V".format(params.voutMin, params.voutMax, np.min(df1['VOUT (V)']), np.max(df1['VOUT (V)'])))        
        
        plt.xlabel("Load (A)")
        #@@@#plt.get_legend().set_title("title")
        plt.legend().set_title("VIN (V)")

    # Use a logarithmic scale for X axis
    plt.xscale("log")
    #plt.xticks([.01, .02, .03, .04, .05, .06, .07, .08 ,.09,.1, .2, .3, .4, .5, .6, .7, .8 ,.9,1,2,3])
    #@@@#maxIout = int(np.ceil(params.ioutList[-1]))
    maxIout = int(np.ceil(np.max(params.ioutList)))
    # Create a list of log ticks from 1e-2 to 9e2
    xTickList = []
    for mag in range(-2,3):
        xTickList += list(np.linspace(1,9, 9)*(10**mag))
    # xticks is a list with xTickList values <= maxIout
    xticks = [xt for xt in xTickList if xt <= maxIout]
     
    #@@@#print(xticks)
    plt.xticks(xticks)
    #@@@#plt.xticklabels([0.01, 0.1, 1])

    ax = plt.gca()
    #ax.set_xscale("log")
    #@@@#ax.axis(xmin=0.01, xmax=10)
    #restore_minor_ticks_log_plot(ax)
    #ax.xaxis.get_major_locator().set_params(numticks=99)
    #ax.xaxis.get_minor_locator().set_params(numticks=99, subs=[.2, .4, .6, .8])
    #ax.xaxis.set_major_locator(LogLocator(numticks=9999))
    #ax.xaxis.set_minor_locator(LogLocator(numticks=9999, subs="auto"))

    n = 9  # Keeps every 9th label
    [l.set_visible(False) for (i,l) in enumerate(ax.xaxis.get_ticklabels()) if i % n != 0]
    
    formatter = FuncFormatter(lambda x, _: '{:.16g}'.format(x))
    ax.xaxis.set_major_formatter(formatter)
    
    #@@@#ax.set_ylim(ymin=1.79,ymax=1.81)

    if (True):
        ## Show a green band of valid VOUT
        plt.axhspan(params.voutMin, params.voutMax, facecolor='lightgreen', alpha=0.25)
        xlocs, xlabels = plt.xticks()
        #@@@#xmid = (xlocs[0] + xlocs[-1])/2
        #@@@#xmid = xlocs[((len(xlocs)+1)//2)]
        #@@@#xmid = np.log10(np.mean(10 ** xlocs))
        xmid = 10 ** np.mean(np.log10(xlocs))
        #@@@#print(xlocs)
        #@@@#print(xmid)
        plt.text(xmid, params.voutMin, '{}'.format(params.voutMin), color='green', horizontalalignment='center', verticalalignment='bottom')
        plt.text(xmid, params.voutMax-.001, '{}'.format(params.voutMax), color='green', horizontalalignment='center', verticalalignment='top')
        
    plt.xlabel("Load (A)")
    plt.ylabel("Output Voltage (V)")

    title = "Load Regulation"

    if circuit is None:
        plt.title(title)
    else:
        plt.title(circuit+": "+title)
    
        #@@@#ax.tick_params(axis="y", bottom=True, top=True, labelbottom=True, labeltop=True)
    #@@@#print(plt.yticks())

    if (saveFilename is not None):
        # Handle output of plot as an image file
        saveFilename = saveFilename.with_stem(saveFilename.stem+"_LoR")
        plt.savefig(saveFilename,dpi=saveFigDPI,bbox_inches='tight',pad_inches = 0,facecolor=(1, 1, 1, 0)) # facecolor makes the border transparent
        print("Saved plot image to {}".format(saveFilename))

    plt.show()
        
if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Plot data from power tests on Power Test Board')

    # Mutuall Exclusive tests - pick one an donly one
    mutex_grp = parser.add_mutually_exclusive_group(required=True)
    mutex_grp.add_argument('-e', '--power_efficiency',  action='store_true', help='plot the Power Efficiency test data')
    mutex_grp.add_argument('-i', '--line_regulation',   action='store_true', help='plot the Line Regulation test data')
    mutex_grp.add_argument('-o', '--load_regulation',   action='store_true', help='plot the Load Regulation test data')

    parser.add_argument('filename', help='filename of NPZ datafile')
    parser.add_argument('-c', '--circuit', action='store', type=str, help='name of circuit for the plot title')
    parser.add_argument('-s', '--svg', action='store_true', help='save as a SVG image using filename with .svg extension')
    parser.add_argument('-p', '--png', action='store_true', help='save as a PNG image using filename with .png extension')
    parser.add_argument('-j', '--jpg', action='store_true', help='save as a JPEG image using filename with .jpg extension')
    
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

        ## Create output image filename if requested
        path = PurePath(args.filename)
        if (args.svg):
            saveFilename = path.with_suffix('.svg')            
        elif (args.png):
            saveFilename = path.with_suffix('.png')            
        elif (args.jpg):
            saveFilename = path.with_suffix('.jpg')            
        else:
            # indicate nothing to be saved
            saveFilename = None
            
        if (args.power_efficiency):
            #@@@#DCEfficiencyPlot(df,"Set Load","Efficiency (%)",circ, trials)
            DCEfficiencyPlot(df,"Set Load","Efficiency (%)",saveFilename,args.circuit)
        elif (args.line_regulation):
            LineRegulatonPlot(df,"Set VIN","VOUT (V)",saveFilename,args.circuit)
        elif (args.load_regulation):
            LoadRegulatonPlot(df,"Set Load","VOUT (V)",saveFilename,args.circuit)
        else:
            raise ValueError("Unknown test type '{}'".format(test))
        

    except KeyboardInterrupt:
        exit(2)
