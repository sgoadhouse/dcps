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
import argparse
#@@@#from doctest import testmod
from os import environ
from pyftdi import FtdiLogger
from pyftdi.i2c import I2cController, I2cIOError, I2cNackError
from pyftdi.misc import hexdump
#@@@#from i2cflash.serialeeprom import SerialEepromManager
from sys import modules, stdout
#@@@#from math import floor
import logging
#@@@#import unittest
from time import sleep

#@@@#ftdi_url = 'ftdi://ftdi:4232h/1'
ftdi_url_const = 'ftdi://ftdi:4232:FTK1RRYC/1'

class I2cPca9534(object):
    """Simple Class to access a PCA9534 GPIO device on I2C bus
    """

    def __init__(self, address=0x20):
        self._i2c = I2cController()
        self._addr = address
        self.regs = {'INPUT':0, 'OUTPUT':1, 'POLARITY':2, 'CONFIG':3}
        self._freq = 400000

    def open(self, url):
        """Open an I2c connection, specified by url, to a slave"""
        self._i2c.configure(url, frequency=self._freq)
        self._port = self._i2c.get_port(self._addr)   # open a port to the I2C PCA9533 device

    def flush(self):
        """Flush the I2C connection"""
        self._i2c.flush()

    def close(self):
        """Close the I2C connection"""
        #@@@#self._i2c.flush()
        self._i2c.terminate()
        #pyftdi.ftdi.ftdi.close()

    def readReg(self, reg):
        regVal = [reg]
        regVal = [regVal[0]]                # make sure only a single value for reg and not a list
        return self._port.exchange(regVal, 1)[0]

    def writeReg(self, reg, val):
        # Create data array to send. Start with the register number for
        # LS0 and add the desired value
        #data = bytes([reg])
        #data = bytes(data[0]) + bytes([val])              # Make sure that reg parameter is a single value
        self._port.write_to(reg, [val])

    def writeVal(self, val):
        """ Only send a value to write without preceeding with a register number """

        # Create data array to send. Start with the register number for
        # LS0 and add the desired value
        #data = bytes([reg])
        #data = bytes(data[0]) + bytes([val])              # Make sure that reg parameter is a single value
        self._port.write([val])

    def writeBit(self, reg, bit, val):
        msk = 0x01
        vvv = val and 0x01
        ## Bit shift over to the corresponding bit
        for x in range(0,bit):
            msk <<= 1
            vvv <<= 1
        tmp = self.readReg(reg)     # read from the register
        tmp &= ~msk                 # clear out the selected bit
        tmp |= vvv                  # OR in the new bit value 
        self.writeReg(reg, tmp)

    def setBit(self, reg, bit):
        self.writeBit(reg, bit, 1)
        
    def clrBit(self, reg, bit):
        self.writeBit(reg, bit, 0)

    def readBit(self, reg, bit):
        msk = 0x01
        ## Bit shift over to the corresponding bit
        tmp = self.readReg(reg)     # read from the register
        for x in range(0,bit):
            tmp >>= 1
        tmp &= msk                  # mask out the bit
        return tmp
        
    def read_all(self):
        """Read all registers and print their values out"""

        for regname in self.regs:
            print("{:10} (0x{:02x}): 0x{:02x}".format(regname, self.regs[regname], self.readReg(self.regs[regname])))
        
        print('')


class PowerTestBoard(object):
    """Simple Class to enable/disable DC circuits on the Power Test Board
    """

    def __init__(self, ftdi_url):
        self._ftdi_url = ftdi_url
        self._circuits = { '0V85':0,
                           '1V2-A':1,
                           '1V2-B':2,
                           '0V9':3,
                           '1V8-A':4,
                           '1V8-B':5,
                           '1V8-C':6,
                           '1V8-D':7,
                           '3V3-A':8,
                           '3V3-B':8, # 3V75-B circuit with switch set for 3.3V - so really using 3V3-A
                           '3V75-B':9,# 3V75-B circuit with switch set for 3.75V
                           '3V3-C':10,
                           '3V3-D':11,
                          }

        FtdiLogger.log.addHandler(logging.StreamHandler(stdout))
        level = environ.get('FTDI_LOGLEVEL', 'info').upper()
        try:
            loglevel = getattr(logging, level)
        except AttributeError:
            raise ValueError('Invalid log level: %s', level)
        FtdiLogger.set_level(loglevel)


    @property
    def circuits(self):
        return self._circuits
        
    def test_i2c_gpio(self):
        i2c = I2cPca9534()
        i2c.open(self._ftdi_url)

        try:
            for x in range(0, 8):
                i2c.read_all()
                i2c.setBit(i2c.regs['POLARITY'], x)
                print('')

            i2c.read_all()
            print('')

            for x in range(0, 8):
                i2c.read_all()
                i2c.clrBit(i2c.regs['POLARITY'], x)
                print('')

            i2c.read_all()
            print('')

            
        except I2cIOError:
            print("I2C I/O Error!\n")
            #print("\nI2C Flush!")
            i2c.flush()

        except I2cNackError:
            print("I2C NACK Error!\n")
            #print("\nI2C Flush!")
            i2c.flush()

        except KeyboardInterrupt:
            #print("\nI2C Flush!")
            i2c.flush()

        #print("\nI2C Close!")
        #sleep(0.1)
        i2c.close()

    def powerEnable(self, circuit, on):
        # circuit is a value 0 - 11
        # on is 0 to turn off and non-o to turn on
        addrs = [0x20, 0x21, 0x22]  # I2C addresses of PCA9534
        myaddr = addrs[circuit // 4]
        bit = circuit % 4

        i2c = I2cPca9534(myaddr)
        i2c.open(self._ftdi_url)

        try:
            # If circuit is 4-7 (i.e. addr 0x21) be sure to setup POLARITY
            # different than default
            if myaddr == 0x21:
                i2c.writeReg(i2c.regs['POLARITY'],0x30)

            # Write the OUTPUT bit
            i2c.writeBit(i2c.regs['OUTPUT'], bit, on)
            # Make sure bit is configured as an OUTPUT
            i2c.clrBit(i2c.regs['CONFIG'], bit)

            #@@@#i2c.read_all()
            #@@@#print('')


        except I2cIOError:
            print("I2C I/O Error!\n")
            #print("\nI2C Flush!")
            i2c.flush()

        except I2cNackError:
            print("I2C NACK Error!\n")
            #print("\nI2C Flush!")
            i2c.flush()

        except KeyboardInterrupt:
            #print("\nI2C Flush!")
            i2c.flush()

        #print("\nI2C Close!")
        #sleep(0.1)
        i2c.close()


    def powerStatus(self, circuit):
        # check circuit status
        #@@@ Make this a function! @@@
        addrs = [0x20, 0x21, 0x22]  # I2C addresses of PCA9534
        myaddr = addrs[circuit // 4]
        enBit = circuit % 4
        pgBit = enBit + 4

        # Set return values to -1 to indicate error if it does not work
        en = -1
        pg = -1

        i2c = I2cPca9534(myaddr)
        i2c.open(self._ftdi_url)

        try:
            # If circuit is 4-7 (i.e. addr 0x21) be sure to setup POLARITY
            # different than default
            if myaddr == 0x21:
                i2c.writeReg(i2c.regs['POLARITY'],0x30)

            # Read the enable INPUT bit
            en = i2c.readBit(i2c.regs['INPUT'], enBit)
            # Read the power good INPUT bit
            pg = i2c.readBit(i2c.regs['INPUT'], pgBit)                

        except I2cIOError:
            print("I2C I/O Error!\n")
            #print("\nI2C Flush!")
            i2c.flush()

        except I2cNackError:
            print("I2C NACK Error!\n")
            #print("\nI2C Flush!")
            i2c.flush()

        except KeyboardInterrupt:
            #print("\nI2C Flush!")
            i2c.flush()

        #print("\nI2C Close!")
        #sleep(0.1)
        i2c.close()

        return (en, pg)


    def validate_circuits(self, value):
        value = value.upper()
        if value in self._circuits:
            return value
        else:
            raise argparse.ArgumentTypeError(f"'{value}' is not in recognized circuit list: \n{list(self._circuits.keys())}")

if __name__ == '__main__':
    #@@@#testmod(modules[__name__])

    ptb = PowerTestBoard(environ.get('FTDI_DEVICE', ftdi_url_const))
            
    parser = argparse.ArgumentParser(description=f'Enable/Disable/Status DC Circuits on the Power Test Board. List of circuits: {list(ptb.circuits.keys())}')

    # Choose EITHER ON or OFF and the circuits on the command line
    # will be enabled or disable. If neither of these is selected,
    # then get status of all circuits.
    mutex_grp = parser.add_mutually_exclusive_group(required=False)        
    mutex_grp.add_argument('-1', '--on',  action='store_true', help='enable/turn ON the circuits')
    mutex_grp.add_argument('-0', '--off', action='store_true', help='disable/turn OFF the circuits')


    parser.add_argument('list_of_circuits', metavar='circuits', type=ptb.validate_circuits, nargs='*', help='a list of circuits - or all if omitted')
    
    args = parser.parse_args()

    try:
        circuit_list = args.list_of_circuits

        # If no list given, then use all circuits
        if len(circuit_list) <= 0:
            circuit_list = ptb.circuits.keys()
        
        for circ in circuit_list:
            if args.on:
                ptb.powerEnable(ptb.circuits[circ],1)
                print(f"{circ:8s}\tTurned ON")
            elif args.off:
                ptb.powerEnable(ptb.circuits[circ],0)
                print(f"{circ:8s}\tTurned OFF")
            else:
                (en, pg) = ptb.powerStatus(ptb.circuits[circ])
                if (en == -1):
                    print(f"{circ:8s}\tEN: ?\tPG: ?")
                else:
                    print(f"{circ:8s}\tEN: {en}\tPG: {pg}")
            
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
        exit(2)
        
