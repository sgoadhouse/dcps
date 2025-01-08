#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import numpy as np
import pandas as pd

parser = argparse.ArgumentParser(description='Fix data file by adding missing meta data')

parser.add_argument('filename', help='filename of NPZ datafile')

args = parser.parse_args()


header=None
meta=None
with np.load(args.filename,allow_pickle=False) as data:
    rows = data['rows']
    if 'header' in data.files:
        header = data['header']
    if 'meta' in data.files:
        meta = data['meta']

print(rows[0:10])

if (True):
    # Add missing boardName & circuit name
    boardName = '1'
    circuit = '1V8-A'
    newrows = [ [boardName,circuit,int(r[0])]+list(r[1:]) for r in rows ]
    newheader = ["Board","Circuit"]+list(header)
    newmeta = [meta[0], meta[1], boardName, meta[2]]

    print('')
    print(newrows[0:10])

df = pd.DataFrame(newrows,columns=newheader)
print('')
print(df[0:10].info())
print(df[0:10])
print(type(df['Board'][0]))

if (True):
    ## Save as a pandas pickle file
    df.to_pickle(args.filename+'.pkl')
    
if (False):
    ## Save back as a NPZ file
    arrays = {'rows': newrows}
    if (newheader is not None):
        arrays['header']=newheader
    if (newmeta is not None):
        arrays['meta']=newmeta
    np.savez(args.filename+'.npz', **arrays)


