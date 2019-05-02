#!/usr/bin/env python3
import numpy as np
from tkinter import *
from PIL import ImageTk, Image
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import time, threading, os, ephem, serial, curses
from copy import copy
from cpredict import quick_find, quick_predict, PredictException

def load_tle(tlefile):
    """ Function to Load orbital elements. """
    try:
        with open(tlefile, 'r') as myfile: # Try reading file
            tle = myfile.read()
    except IOError:
        print('Error Reading '+tlefile+". Exiting.")
        os._exit(1)
    tle = massage_tle(tle) #use predict.py to separate elements
    satname = tle[0]
    return tle, satname

def load_qth(qthfile):
    """ Function to Load latitude, longitude, elevation from given file. """
    try:
        with open(qthfile, 'r') as myfile: #Try reading file
            qth = myfile.readlines()
    except IOError:
        print('Error Reading '+qthfile+". Exiting.")
        os._exit(1)
    qth = list(map(lambda s: s.strip(), qth))
    locname = qth[0]
    qth = massage_qth(tuple(qth[1:])) #use predict.py to change variable types
    qth = (qth[0], -qth[1], qth[2])
    return qth

def massage_tle(tle):
    """ Function for getting correct tle data format. """
    try:
        # If tle has not been split yet
        if isinstance(tle, str):
            tle = tle.rstrip().split('\n')
        assert len(tle) == 3, "TLE must be 3 lines, not %d: %s" % (len(tle), tle)
        return tle
    except Exception as e:
        raise PredictException(e)

def massage_qth(qth):
    """ Function for getting correct qth data format. """
    try:
        assert len(qth) == 3, "%s must consist of exactly three elements: (lat(N), long(W), alt(m))" % qth
        return (float(qth[0]), float(qth[1]), int(qth[2]))
    except ValueError as e:
        raise PredictException("Unable to convert '%s' (%s)" % (qth, e))
    except Exception as e:
        raise PredictException(e)

def observe(tle, qth, at=None):
    """ Function to find azimuth and elevation at a certain time. """
    tle = massage_tle(tle)
    qth = massage_qth(qth)
    if at is None:
        at = time.time()
    return quick_find(tle, at, qth)

def transits(tle, qth, ending_after=None, ending_before=None):
    """ Function to find upcoming passes of a specific satellite. """
    tle = massage_tle(tle)
    qth = massage_qth(qth)
    if ending_after is None: #If not specified
        ending_after = time.time()
    ts = ending_after
    while True: #Find passes
        transit = quick_predict(tle, ts, qth)
        t = Transit(tle, qth, start=transit[0]['epoch'], end=transit[-1]['epoch'])
        if (ending_before != None and t.end > ending_before):
            break
        if (t.end > ending_after):
            yield t
        # Need to advance time cursor so predict doesn't yield same pass
        ts = t.end + 60 #60 seconds after end
        
class Transit():
    """ Transit is a class representing a pass of a satellite over a groundstation. """
    def __init__(self, tle, qth, start, end):
        """ Initialization class. """
        self.tle = massage_tle(tle)
        self.qth = massage_qth(qth)
        self.start = start
        self.end = end

    def peak(self, epsilon=0.1):
        """ Function to find peak elevation. """
        # NOTE: Assumes elevation is strictly monotonic or concave over the [start,end] interval
        ts =  (self.end + self.start)/2
        step = (self.end - self.start)
        while (step > epsilon):
            step /= 4
            # Ascend the gradient at this step size
            direction = None
            while True:
                mid   = observe(self.tle, self.qth, ts)['elevation']
                left  = observe(self.tle, self.qth, ts - step)['elevation']
                right = observe(self.tle, self.qth, ts + step)['elevation']
                # Break if we're at a peak
                if (left <= mid >= right):
                    break
                # Ascend up slope
                slope = -1 if (left > right) else 1
                # Break if we stepped over a peak (switched directions)
                if direction is None:
                    direction = slope
                if direction != slope:
                    break
                # Break if stepping would take us outside of transit
                next_ts = ts + (direction * step)
                if (next_ts < self.start) or (next_ts > self.end):
                    break
                # Step towards the peak
                ts = next_ts
        return self.at(ts)

    def at(self, t):
        """ Function to return azimuth and elevation at certain time. """
        if t < self.start or t > self.end:
            raise PredictException("time %f outside transit [%f, %f]" % (t, self.start, self.end))
        return observe(self.tle, self.qth, t)



if __name__ == "__main__":
    num = 10
    tlefile = "iridium163.tle"
    qth = load_qth('ARGUS.qth')
    tle, satname = load_tle(tlefile) # load tle
    p = transits(tle, qth) # predict future passes
    starttime, endtime, startaz, endaz, maxel = ([] for i in range(5)) #initialize
    for i in range(num): # Predict 3 passes
        transit = next(p) #Find next pass
        print("Pass "+str(i+1)+":")
        print("Start Time: " + str(time.ctime(transit.start)))
        print("End Time: " + str(time.ctime(transit.end)))
        print("Start Azimuth: " + str(observe(tle, qth, transit.start)['azimuth']))
        print("End Azimuth: " + str(observe(tle, qth, transit.end)['azimuth']))
        print("Max Elevation: " + str(transit.peak()['elevation']) + "\n")
        starttime.append(time.ctime(transit.start))
        endtime.append(time.ctime(transit.end))
        startaz.append(observe(tle, qth, transit.start)['azimuth'])
        endaz.append(observe(tle, qth, transit.end)['azimuth'])
        maxel.append(transit.peak()['elevation'])
