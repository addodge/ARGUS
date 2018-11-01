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
import time, threading, unittest, os
from random import random, randint
import multiprocessing as mp
import predict
from cpredict import quick_find, quick_predict, PredictException

# Globals
azelplotflag = False # True if plot is active
fftplotflag = False # True if plot is active
manflag = True # True if in manual mode
progflag = False # True if in program track mode
autoflag = False # True if in auto track mode
currentAz = 0 # Current Pointing azimuth
currentEl = 0 # Current Pointing Elevation

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
    qth = predict.massage_qth(tuple(qth[1:])) #use predict.py to change variable types
    return qth

# Load orbital elements 
def load_tle(tlefile):
    try:
        with open(tlefile, 'r') as myfile:
            tle = myfile.read()
    except IOError:
        print('Error Reading '+tlefile+". Exiting.")
        os._exit(1)
    tle = predict.massage_tle(tle) #use predict.py to separate elements
    return(tle)
        
# Produce Azimuth and Elevation using Predict
def azel_points(tlefile, qthfile):
    qth = load_qth(qthfile)
    tle = load_tle(tlefile)
    data = predict.observe(tle, qth) #find current state
    return data['azimuth'], data['elevation']

################################################################    
# Produce FFT points - THIS NEEDS TO BE CHANGED TO ACTUAL FFT
def fft_points(cf):
    # This is random for now, eventually need actual signal calculation
    freq = np.sort(np.random.rand(10) * 20000000 + cf - 10000000)
    mag = np.random.rand(10) * 10
    return freq, mag

################################################################
# Calibrate az/el - THIS NEEDS TO ACTUALLY CALIBRATE AND AUTOTRACK
def calibrate():
    print("Calibrated")
    
# Determine Next Pass timing and azimuth of start and finish time/azimuth
def nextpass(tlefile, qthfile):
    qth = load_qth(qthfile) #load qth
    tle = load_tle(tlefile) # load tle
    p = predict.transits(tle, qth) # predict future passes
    starttime, endtime, startaz, endaz, maxel = ([] for i in range(5)) #initialize
    for i in range(3): # Predict 3 passes
        transit = next(p) #Find next pass
        starttime.append(time.ctime(transit.start))
        endtime.append(time.ctime(transit.end))
        startaz.append(predict.observe(tle, qth, transit.start)['azimuth'])
        endaz.append(predict.observe(tle, qth, transit.end)['azimuth'])
        maxel.append(transit.peak()['elevation'])
    return starttime, endtime, startaz, endaz, maxel

################################################################
# Functions for changing the azimuth and elevation - THESE NEED TO DO SOMETHING
def increase_elevation():
    global manflag
    if manflag:
        print("Elevaion Increased")

def decrease_elevation():
    global manflag
    if manflag:
        print("Elevation Decreased")

def increase_azimuth():
    global manflag
    if manflag:
        print("Azimuth Increased")

def decrease_azimuth():
    global manflag
    if manflag:
        print("Azimuth Decreased")

################################################################
# Define Arrow Presses for Manual Mode
def uppress(event):
    increase_elevation()

def downpress(event):
    decrease_elevation()

def rightpress(event):
    increase_azimuth()

def leftpress(event):
    decrease_azimuth()

################################################################
def main():
    global azelplotflag, fftplotflag, manflag, progflag, autoflag
    ###### Create root GUI
    root = Tk()
    root.title("ARGUS Ground Station")
    #root.attributes("-fullscreen", True)
    root.configure(background='grey')
    img = PhotoImage(file='ARGUS_Logo.gif')
    root.tk.call('wm', 'iconphoto', root._w, img)
    
    # Create Frames
    left = Frame(root, borderwidth=2, relief="solid") #Split in half
    right = Frame(root, borderwidth=2, relief="solid")
    tl = Frame(left, borderwidth=2, relief="solid") #Top Left
    tl1 = Frame(tl, borderwidth=2, relief="solid") #Split top left
    tl2 = Frame(tl, borderwidth=2, relief="solid")
    tr = Frame(right, borderwidth=2, relief="solid") #Top Right
    bl = Frame(left, borderwidth=2, relief="solid") #Bottom Left
    br = Frame(right, borderwidth=2, relief="solid") #Bottom Right
    
    ##### Top Left Frame - exit, logo, description
    # exit button
    exitbutton = Button(tl1, text="QUIT", bg="red", fg="black", command=tl.quit)
    
    # logo
    img = Image.open("ARGUS_Logo.png").resize((200,200), Image.ANTIALIAS)
    img = ImageTk.PhotoImage(img)
    logo = Label(tl1, image=img)
    image = img
    
    # GUI Description
    descrip = Label(tl1, text="This is the GUI for the ARGUS \nGround Station for Tracking LEO Satellites.") 
    
    ##### Calibration Frame
    # Calibrate Button
    cbutton = Button(tl2, text="Calibrate", bg="blue", fg="black", command=calibrate)
    
    # Operation Mode Dropdown Menu
    operation = Menubutton(tl2, text="Manual Mode"+'\u25BC')
    picks = Menu(operation)
    operation.config(menu=picks, relief=RAISED, bg='white', fg="black")
    
    # Functions for switching modes
    def go_program():
        global manflag, progflag, autoflag
        progflag=True
        autoflag=False
        manflag=False
        operation.configure(text="Program Track"+'\u25BC')
    def go_manual():
        global manflag, progflag, autoflag
        progflag=False
        autoflag=False
        manflag=True
        operation.configure(text="Manual Mode"+'\u25BC')
    def go_auto():
        global manflag, progflag, autoflag
        progflag=False
        autoflag=True
        manflag=False
        operation.configure(text="Auto Track"+'\u25BC')
        
    # add menu options
    picks.add_command(label="Manual Mode", command=go_manual)
    picks.add_command(label="Program Track", command=go_program)
    picks.add_command(label="Auto Track (?)", command=go_auto)
    
    # Create antenna motion buttons, map arrow keys to same functions
    b_up = Button(tl2, text="+El "+'\u25b2', bg="white", fg="black", command=increase_elevation)
    root.bind('<Up>', uppress)
    b_down = Button(tl2, text="-El "+'\u25BC', bg="white", fg="black", command=decrease_elevation)
    root.bind('<Down>', downpress)
    b_left = Button(tl2, text="-Az "+'\u25C0', bg="white", fg="black", command=increase_azimuth)
    root.bind('<Left>', leftpress)
    b_right = Button(tl2, text="+Az "+'\u25B6', bg="white", fg="black", command=decrease_azimuth)
    root.bind('<Right>', rightpress)
    
    #### Bottom Left Frame - Azimuth/Elevation Plot
    # QTH file input
    qth = Label(bl, text="QTH File:")
    qthloc = StringVar()
    qthentry = Entry(bl, textvariable=qthloc)
    qthloc.set("Boulder.qth")
    
    # TLE file input
    tle = Label(bl, text="TLE File:")
    tleloc = StringVar()
    tleentry = Entry(bl, textvariable=tleloc)
    tleloc.set("MTI.tle")
    
    # Az/El Plot figure creation
    fig = Figure()
    ax = fig.add_subplot(111, projection='polar')
    ax.set_title("Azimuth and Elevation of "+str(tleloc.get()))
    ax.grid(True)
    ax.set_ylim(0, 90)
    graph = FigureCanvasTkAgg(fig, master=bl)
    
    # Function to Plot Azimuth and Elevation
    def azelplot():
        qthfile = str(qthloc.get())
        tlefile = str(tleloc.get())
        while azelplotflag:
            ax.cla()
            ax.set_title("Azimuth and Elevation of "+tlefile)
            ax.grid(True)
            ax.set_ylim(0, 90)
            az, el = azel_points(tlefile, qthfile)
            ax.plot(az, el, marker='o', color='orange')
            graph.draw()
            time.sleep(0.5)

    # Spawn Azimuth and Elevation process, switch state
    def azel_handler():
        global azelplotflag
        if azelplotflag == False:
            azelplotflag = True
            b.configure(text="Stop", bg="red", fg='black')
        else:
            azelplotflag = False
            b.configure(text="Start", bg="green", fg='black')
        threading.Thread(target=azelplot).start() #Start new process to plot
    # Start/stop plotting button
    b = Button(bl, text="Start", command=azel_handler, bg="green", fg='black')
    
    ##### Top Right Frame - FFT Plot
    # Input for Desired Frequency
    cf = Label(tr, text="Center Frequency [MHz]:")
    centerfreq = StringVar()
    freqentry = Entry(tr, textvariable=centerfreq)
    centerfreq.set("2250")
    
    # FFT Plot figure creation
    fig2 = Figure()
    ax2 = fig2.add_subplot(111)
    ax2.set_xlabel("Frequency [MHz]")
    ax2.set_title("Signal Frequency Distribution")
    ax2.set_xlim(2000, 2500)
    ax2.set_ylim(0,10)
    ax2.grid()
    graph2 = FigureCanvasTkAgg(fig2, master=tr)
    
    # Plot fft points
    def fftplot():
        while fftplotflag:
            ax2.cla()
            ax2.set_xlabel("Frequency [MHz]")
            ax2.set_title("Signal Frequency Distribution")
            ax2.set_xlim(2200, 2300)
            ax2.set_ylim(0,10)
            ax2.grid()
            freq, mag = fft_points(int(str(centerfreq.get())) * 1000000)
            ax2.plot(freq/1000000, mag, marker='o', color='blue')
            graph2.draw()
            time.sleep(0.5)

    # Spawn FFT process, change state
    def fft_handler():
        global fftplotflag
        if fftplotflag == False:
            fftplotflag = True
            b2.configure(text="Stop", bg="red", fg='black')
        else:
            fftplotflag = False
            b2.configure(text="Start", bg="green", fg='black')
        threading.Thread(target=fftplot).start() #Start new plotting process
    
    # Start/Stop Plotting button
    b2 = Button(tr, text="Start", command=fft_handler, bg="green", fg='black')
    
    # Bottom Right Frame - Future Passes
    degree_sign= u'\N{DEGREE SIGN}'
    starttime, endtime, startaz, endaz, maxel = nextpass(str(tleloc.get()), str(qthloc.get()))
    np_l = Label(br, text="Upcoming Passes for "+str(tleloc.get())+":\n"+
        "\nPass 1:\nStart: "+starttime[0]+", Azimuth: "+
        str(round(startaz[0],2))+degree_sign+"\nFinish: "+endtime[0]+
        ", Azimuth: "+str(round(endaz[0],2))+degree_sign+
        "\nMaximum Elevation: "+str(round(maxel[0],2))+degree_sign+
        "\nPass 2:\nStart: "+starttime[1]+", Azimuth: "+
        str(round(startaz[1],2))+degree_sign+"\nFinish: "+endtime[1]+
        ", Azimuth: "+str(round(endaz[1],2))+degree_sign+
        "\nMaximum Elevation: "+str(round(maxel[1],2))+degree_sign+
        "\nPass 3:\nStart: "+starttime[2]+", Azimuth: "+
        str(round(startaz[2],2))+degree_sign+"\nFinish: "+endtime[2]+
        ", Azimuth: "+str(round(endaz[2],2))+degree_sign+
        "\nMaximum Elevation: "+str(round(maxel[2],2))+degree_sign)
    
    # Function to recalculate future passes if new TLE loaded
    def recalculate():
        starttime, endtime, startaz, endaz, maxel = nextpass(str(tleloc.get()), str(qthloc.get()))
        np_l.configure(text="Upcoming Passes for "+str(tleloc.get())+":\n"+
            "\nPass 1:\nStart: "+starttime[0]+", Azimuth: "+
            str(round(startaz[0],2))+degree_sign+"\nFinish: "+endtime[0]+
            ", Azimuth: "+str(round(endaz[0],2))+degree_sign+
            "\nMaximum Elevation: "+str(round(maxel[0],2))+degree_sign+
            "\nPass 2:\nStart: "+starttime[1]+", Azimuth: "+
            str(round(startaz[1],2))+degree_sign+"\nFinish: "+endtime[1]+
            ", Azimuth: "+str(round(endaz[1],2))+degree_sign+
            "\nMaximum Elevation: "+str(round(maxel[1],2))+degree_sign+
            "\nPass 3:\nStart: "+starttime[2]+", Azimuth: "+
            str(round(startaz[2],2))+degree_sign+"\nFinish: "+endtime[2]+
            ", Azimuth: "+str(round(endaz[2],2))+degree_sign+
            "\nMaximum Elevation: "+str(round(maxel[2],2))+degree_sign)
    
    # Button for recalculation of future passes
    np_button = Button(br, text="Recalculate", command=recalculate, bg="blue", fg="black")
    
    # Pack Frames
    left.pack(side="left", expand=True, fill="both")
    right.pack(side="right", expand=True, fill="both")
    tl.pack(expand=True, fill="both", padx=10, pady=10)
    tl1.pack(side="left", expand=True, fill="both", padx=10, pady=10)
    tl2.pack(side="right",expand=True, fill="both", padx=10, pady=10)
    tr.pack(expand=True, fill="both", padx=10, pady=10)
    bl.pack(expand=True, fill="both", padx=10, pady=10)
    br.pack(expand=True, fill="both", padx=10, pady=10)
    
    # Pack everything else into frames
    exitbutton.pack(side="top")
    logo.pack(side="top")
    descrip.pack(side="top")
    cbutton.pack(side="top")
    operation.pack(side="top", padx=10, pady=10)
    b_up.pack(side="top")
    b_down.pack(side="top")
    b_left.pack(side="top")
    b_right.pack(side="top")
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
