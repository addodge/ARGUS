#!/usr/bin/env python3
import numpy as np
from tkinter import *
from PIL import ImageTk, Image
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import time, threading, unittest, os
from random import random, randint
import multiprocessing as mp
import predict
from cpredict import quick_find, quick_predict, PredictException
import ephem

################################################################
# Load latitude, longitude, elevation
def load_qth(qthfile):
    try:
        with open(qthfile, 'r') as myfile:
            qth = myfile.readlines()
    except IOError:
        print('Error Reading '+qthfile+". Exiting.")
        os._exit(1)
    qth = list(map(lambda s: s.strip(), qth))
    locname = qth[0]
    qth = predict.massage_qth(tuple(qth[1:])) #use predict.py to change variable types
    qth = (qth[0], -qth[1], qth[2])
    return qth, locname

# Load orbital elements 
def load_tle(tlefile):
    try:
        with open(tlefile, 'r') as myfile:
            tle = myfile.read()
    except IOError:
        print('Error Reading '+tlefile+". Exiting.")
        os._exit(1)
    tle = predict.massage_tle(tle) #use predict.py to separate elements
    satname = tle[0]
    return tle, satname
        
# Produce Azimuth and Elevation using Predict
def azel_points(tlefile, qthfile, t):
    qth, locname = load_qth(qthfile)
    tle, satname = load_tle(tlefile)
    data = predict.observe(tle, qth, t) #find current state
    return data['azimuth'], data['elevation'], locname, satname

################################################################

if __name__ == "__main__":
    qthfile = 'ARGUS.qth'
    tlefile = 'iridium139.tle'
    # Find passes
    qth, locname = load_qth(qthfile) #load qth
    tle, satname = load_tle(tlefile) # load tle
    p = predict.transits(tle, qth) # predict future passes
    starttime, endtime, startaz, endaz, maxel = ([] for i in range(5)) #initialize
    
    # Create Figure
    fig = plt.figure()
    ax = plt.subplot(111, projection='polar')
    
    # For each pass plot ....
    for i in range(3): # Predict 3 passes
        transit = next(p) #Find next pass
        starttime.append(time.ctime(transit.start))
        endtime.append(time.ctime(transit.end))
        startaz.append(predict.observe(tle, qth, transit.start)['azimuth'])
        endaz.append(predict.observe(tle, qth, transit.end)['azimuth'])
        maxel.append(transit.peak()['elevation'])
        azvec, elvec = [], []
        t = transit.start
        if i==0:
            while t < transit.end:
                az, el, locname, satname = azel_points(tlefile, qthfile, t)
                azvec.append(az*np.pi/180)
                elvec.append(90-el)
                t = t+1
            ax.plot(azvec, elvec, color='blue')
    
    print(maxel)
    # Fix
    ax.set_title("Azimuth and Elevation of "+satname+" over "+locname)
    ax.grid(True)
    ax.set_rlim(90, 0, 1)
    ax.set_yticks(np.arange(0, 91, 10))
    ax.set_yticklabels(ax.get_yticks()[::-1])
    ax.invert_yaxis()
    ax.set_theta_direction(-1)
    ax.set_theta_zero_location("N")
    
    
    fig.savefig('AzElPlot.png')
    
