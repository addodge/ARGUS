#!/usr/bin/python3
################################################################
# Adam Dodge
# ARGUS Ground Station GUI
# Date Created: 10/24/2018
################################################################
# Necessary Modules
import numpy as np
from tkinter import *
from PIL import ImageTk, Image
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import time, threading, unittest
from random import random, randint
import multiprocessing as mp
import predict
from cpredict import quick_find, quick_predict, PredictException

# Booleans for plotting on/off
continuePlotting1 = False
continuePlotting2 = False
################################################################
# Load latitude, longitude, elevation
def load_qth(qthfile):
    with open(qthfile, 'r') as myfile:
        qth = myfile.readlines()
    qth = list(map(lambda s: s.strip(), qth))
    qth = predict.massage_qth(tuple(qth[1:]))
    return qth

# Load orbital elements 
def load_tle(tlefile):
    with open(tlefile, 'r') as myfile:
        tle = myfile.read()
    tle = predict.massage_tle(tle)
    return(tle)
        
# Produce Azimuth and Elevation using Predict
def azel_points(tlefile, qthfile):
    qth = load_qth(qthfile)
    tle = load_tle(tlefile)
    data = predict.observe(tle, qth)
    return data['azimuth'], data['elevation']

################################################################    
# Produce FFT points - THIS NEEDS TO BE CHANGED TO ACTUAL FFT
def fft_points(cf):
    freq = np.sort(np.random.rand(10) * 20000000 + cf - 10000000)
    mag = np.random.rand(10) * 10
    return freq, mag

################################################################
# Calibrate az/el - THIS NEEDS TO ACTUALLY CALIBRATE AND AUTOTRACK
def calibrate():
    print("Calibrated")
    
# Determine Next Pass timing and azimuth of start and finish - THIS NEEDS TO ACTUALLY CALCULATE
def nextpass(tlefile, qthfile):
    qth = load_qth(qthfile)
    tle = load_tle(tlefile)
    p = predict.transits(tle, qth)
    starttime = []
    endtime = []
    startaz = []
    endaz = []
    maxel = []
    for i in range(0,3):
        transit = next(p)
        starttime.append(time.ctime(transit.start))
        endtime.append(time.ctime(transit.end))
        startaz.append(predict.observe(tle, qth, transit.start)['azimuth'])
        endaz.append(predict.observe(tle, qth, transit.end)['azimuth'])
        maxel.append(transit.peak()['elevation'])
    start = "10:30:04 November 1 2018, Az = 36 degrees"
    finish = "10:41:16 November 1 2018, Az = 197 degrees"
    maxel1 = "26 degrees"
    return starttime, endtime, startaz, endaz, maxel
        
################################################################
def main():
    global continuePlotting1, continuePlotting2
    # Create root GUI
    root = Tk()
    root.title("ARGUS Ground Station")
    #root.attributes("-fullscreen", True)
    #root.geometry("800x800")
    root.configure(background='grey')
    img = PhotoImage(file='ARGUS_Logo.gif')
    root.tk.call('wm', 'iconphoto', root._w, img)
    
    # Create Frames
    left = Frame(root, borderwidth=2, relief="solid")
    right = Frame(root, borderwidth=2, relief="solid")
    tl = Frame(left, borderwidth=2, relief="solid")
    tl1 = Frame(tl, borderwidth=2, relief="solid")
    tl2 = Frame(tl, borderwidth=2, relief="solid")
    tr = Frame(right, borderwidth=2, relief="solid")
    bl = Frame(left, borderwidth=2, relief="solid")
    br = Frame(right, borderwidth=2, relief="solid")
    
    # Top Left Frame - exit, logo, description
    exitbutton = Button(tl1, text="QUIT", bg="red", fg="white", command=tl.quit)
    
    path = "ARGUS_Logo.png"
    img = Image.open(path)
    img = img.resize((200,200), Image.ANTIALIAS)
    img = ImageTk.PhotoImage(img)
    logo = Label(tl1, image=img)
    image = img
    
    descrip = Label(tl1, text="This is the GUI for the ARGUS \nGround Station for Tracking LEO Satellites.") 
    
    # Calibration Frame
    cbutton = Button(tl2, text="Calibrate", bg="blue", fg="white", command=calibrate)
    
    # Bottom Left Frame - Azimuth/Elevation Plot
    qth = Label(bl, text="QTH File:")
    
    qthloc = StringVar()
    qthentry = Entry(bl, textvariable=qthloc)
    qthloc.set("Boulder.qth")
    
    tle = Label(bl, text="TLE File:")
    
    tleloc = StringVar()
    tleentry = Entry(bl, textvariable=tleloc)
    tleloc.set("MTI.tle")
    
    fig = Figure()
    ax = fig.add_subplot(111, projection='polar')
    ax.set_title("Azimuth and Elevation of "+str(tleloc.get()))
    ax.grid(True)
    ax.set_ylim(0, 90)
    graph = FigureCanvasTkAgg(fig, master=bl)
    
    # Plot Azimuth and Elevation
    def azelplot():
        while continuePlotting1:
            ax.cla()
            ax.set_title("Azimuth and Elevation of "+str(tleloc.get()))
            ax.grid(True)
            ax.set_ylim(0, 90)
            az, el = azel_points(str(tleloc.get()), str(qthloc.get()))
            ax.plot(az, el, marker='o', color='orange')
            graph.draw()
            time.sleep(0.5)

    # Spawn Azimuth and Elevation process
    def azel_handler():
        global continuePlotting1
        if continuePlotting1 == False:
            continuePlotting1 = True
            b.configure(text="Stop", fg="red")
        else:
            continuePlotting1 = False
            b.configure(text="Start", fg="green")
    
    b = Button(bl, text="Start", command=azel_handler, fg="green")
    
    # Top Right Frame - FFT Plot
    cf = Label(tr, text="Center Frequency [MHz]:")
    
    centerfreq = StringVar()
    freqentry = Entry(tr, textvariable=centerfreq)
    centerfreq.set("2250")
    
    fig2 = Figure()
    ax2 = fig2.add_subplot(111)
    ax2.set_xlabel("Frequency [MHz]")
    ax2.set_title("FFT Frequency Plot")
    ax2.set_xlim(2000, 2500)
    ax2.set_ylim(0,10)
    ax2.grid()
    graph2 = FigureCanvasTkAgg(fig2, master=tr)
    
    # Plot fft points - THIS NEEDS TO BE UPDATED
    def fftplot():
        while continuePlotting2:
            ax2.cla()
            ax2.set_xlabel("Frequency [MHz]")
            ax2.set_title("FFT Frequency Plot")
            ax2.set_xlim(2200, 2300)
            ax2.set_ylim(0,10)
            ax2.grid()
            freq, mag = fft_points(int(str(centerfreq.get())) * 1000000)
            ax2.plot(freq/1000000, mag, marker='o', color='blue')
            graph2.draw()
            time.sleep(0.5)

    # Spawn FFT process
    def fft_handler():
        global continuePlotting2
        if continuePlotting2 == False:
            continuePlotting2 = True
            b2.configure(text="Stop", fg="red")
        else:
            continuePlotting2 = False
            b2.configure(text="Start", fg="green")
        threading.Thread(target=fftplot).start()
    
    b2 = Button(tr, text="Start", command=fft_handler, fg="green")
    
    # Bottom Right Frame - 
    starttime, endtime, startaz, endaz, maxel = nextpass(str(tleloc.get()), str(qthloc.get()))
    np_l = Label(br, text="Upcoming Passes for "+str(tleloc.get())+":\n"+
        "\nPass 1:\nStart: "+starttime[0]+", Azimuth: "+str(round(startaz[0],2))+"\nFinish: "+endtime[0]+
        ", Azimuth: "+str(round(endaz[0],2))+"\nMaximum Elevation: "+str(round(maxel[0],2))+
        "\nPass 2:\nStart: "+starttime[1]+", Azimuth: "+str(round(startaz[1],2))+"\nFinish: "+endtime[1]+
        ", Azimuth: "+str(round(endaz[1],2))+"\nMaximum Elevation: "+str(round(maxel[1],2))+
        "\nPass 3:\nStart: "+starttime[2]+", Azimuth: "+str(round(startaz[2],2))+"\nFinish: "+endtime[2]+
        ", Azimuth: "+str(round(endaz[2],2))+"\nMaximum Elevation: "+str(round(maxel[2],2)))
    
    def recalculate():
        starttime, endtime, startaz, endaz, maxel = nextpass(str(tleloc.get()), str(qthloc.get()))
        np_l.configure(text="Upcoming Passes for "+str(tleloc.get())+":\n"+
            "\nPass 1:\nStart: "+starttime[0]+", Azimuth: "+str(round(startaz[0],2))+"\nFinish: "+endtime[0]+
            ", Azimuth: "+str(round(endaz[0],2))+"\nMaximum Elevation: "+str(round(maxel[0],2))+
            "\nPass 2:\nStart: "+starttime[1]+", Azimuth: "+str(round(startaz[1],2))+"\nFinish: "+endtime[1]+
            ", Azimuth: "+str(round(endaz[1],2))+"\nMaximum Elevation: "+str(round(maxel[1],2))+
            "\nPass 3:\nStart: "+starttime[2]+", Azimuth: "+str(round(startaz[2],2))+"\nFinish: "+endtime[2]+
            ", Azimuth: "+str(round(endaz[2],2))+"\nMaximum Elevation: "+str(round(maxel[2],2)))
    np_button = Button(br, text="Recalculate", command=recalculate, bg="blue", fg="white")
    
    # Pack Frames
    left.pack(side="left", expand=True, fill="both")
    right.pack(side="right", expand=True, fill="both")
    tl.pack(expand=True, fill="both", padx=10, pady=10)
    tl1.pack(side="left", expand=True, fill="both", padx=10, pady=10)
    tl2.pack(side="right",expand=True, fill="both", padx=10, pady=10)
    tr.pack(expand=True, fill="both", padx=10, pady=10)
    bl.pack(expand=True, fill="both", padx=10, pady=10)
    br.pack(expand=True, fill="both", padx=10, pady=10)
    
    # Pack everything else
    exitbutton.pack(side="top")
    logo.pack(side="top")
    descrip.pack(side="top")
    cbutton.pack(side="top")
    graph.get_tk_widget().pack(side="bottom",fill='both', expand=True)
    b.pack(side='left')
    qth.pack(side="left")
    qthentry.pack(side="left")
    tle.pack(side="left")
    tleentry.pack(side="left")
    graph2.get_tk_widget().pack(side="bottom",fill='both', expand=True)
    b2.pack(side='left')
    cf.pack(side="left")
    freqentry.pack(side="left")
    np_l.pack(side="top")
    np_button.pack(side="top")
    
    # Start GUI
    root.mainloop()
    root.destroy()
################################################################
if __name__ == "__main__":
    main()
