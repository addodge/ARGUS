#! /usr/bin/env python3
# Written by Dan Mandle http://dan.mandle.me September 2012
# License: GPL 2.0

import serial, sys
import numpy as np

#ser = serial.Serial('/dev/ttyUSB0', '4800', timeout=5)
try:
    ser = serial.Serial('/dev/ttyUSB0', '4800', timeout=5)
except:
    print("No GPS connected to /dev/ttyUSB0")
    sys.exit(0)
num = 0
alt = []
long = []
lat = []
while num < 10:
    line = ser.readline()
    splitline = line.split(b',')
    if splitline[0] == b'$GPGGA':
        latDir = splitline[3].decode('ASCII')
        if latDir == "N":
            lat.append(float(splitline[2].decode('ASCII'))/100)
        elif latDir == "S":
            lat.append(float(splitline[2].decode('ASCII'))/-100)
        else:
            print("Latitude not North or South")
            sys.exit(0)
        
        longDir = splitline[5].decode('ASCII')
        if longDir == "E":
            long.append(float(splitline[4].decode('ASCII'))/100)
        elif longDir == "W":
            long.append(float(splitline[4].decode('ASCII'))/-100)
        else:
            print("Longitude not North or South")
            sys.exit(0)
        
        altUnit = splitline[10].decode('ASCII')
        assert altUnit == "M"
        alt.append(float(splitline[9].decode('ASCII')))
        num = num+1

lat = np.mean(lat)
long = np.mean(long)
alt = np.mean(alt)
print("Latitude: ", lat)
print("Longitude:", long)
print("Altitude: ", alt)
