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
currentAz = 0 # Current Pointing azimuth
currentEl = 0 # Current Pointing Elevation
step = 0.05 #step movement for antenna
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
    global manflag, currentEl, step
    if manflag:
        if currentEl+step <= 90:
            currentEl = currentEl + step
        else:
            currentEl=90

def decrease_elevation():
    global manflag, currentEl, step
    if manflag:
        if currentEl-step >= 0:
            currentEl = currentEl - step
        else:
            currentEl=0
        

def increase_azimuth():
    global manflag, currentAz, step
    if manflag:
        if currentAz+step >= 360:
            currentAz = currentAz + step - 360
        else:
            currentAz = currentAz + step

def decrease_azimuth():
    global manflag, currentAz, step
    if manflag:
        if currentAz-step < 0:
            currentAz = currentAz - step + 360
        else:
            currentAz = currentAz - step

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
    global azelplotflag, fftplotflag, manflag, progflag, autoflag, currentAz, currentEl
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
    
    # Calibrate Button
    cbutton = Button(tl1, text="Calibrate", bg="blue", fg="black", command=calibrate)
    
    ##### Pointing Frame

    # Functions for switching modes
    def go_program():
        global manflag, progflag, autoflag
        progflag=True
        manflag=False
    def go_manual():
        global manflag, progflag, autoflag
        progflag=False
        manflag=True
    
    # Create Radio Buttons for mode selection
    var = IntVar()
    var.set(1)
    R1 = Radiobutton(tl2, text="Manual Mode", variable=var, value=1, command=go_manual)
    R2 = Radiobutton(tl2, text="Program Track", variable=var, value=2, command=go_program)
        
    # Create antenna motion buttons, map arrow keys to same functions
    b_up = Button(tl2, text="+El "+'\u25b2', bg="white", fg="black", command=increase_elevation)
    root.bind('<Up>', uppress)
    b_down = Button(tl2, text="-El "+'\u25BC', bg="white", fg="black", command=decrease_elevation)
    root.bind('<Down>', downpress)
    b_left = Button(tl2, text="-Az "+'\u25C0', bg="white", fg="black", command=increase_azimuth)
    root.bind('<Left>', leftpress)
    b_right = Button(tl2, text="+Az "+'\u25B6', bg="white", fg="black", command=decrease_azimuth)
    root.bind('<Right>', rightpress)
    
    # Show azimuth and elevation, allow for input
    def set_azel():
        global currentAz, currentEl, manflag
        if manflag:
            azinput_val = float(str(azinput.get()))
            elinput_val = float(str(elinput.get()))
            if elinput_val > 90:
                currentEl = 90
            elif elinput_val < 0:
                currentEl = 0
            else:
                currentEl = elinput_val
            while azinput_val > 360:
                azinput_val = azinput_val-360
            while azinput_val < 0:
                azinput_val = azinput_val+360
            currentAz = azinput_val
            azinput.set(str(round(currentAz, 2)))
            elinput.set(str(round(currentEl, 2)))
    
    azlabel = Label(tl2, text="Input Azimuth: ")
    ellabel = Label(tl2, text="Input Elevation: ")
    azinput = StringVar()
    elinput = StringVar()
    azentry = Entry(tl2, textvariable=azinput)
    elentry = Entry(tl2, textvariable=elinput)
    azinput.set(str(round(currentAz, 2)))
    elinput.set(str(round(currentEl, 2)))
    b_azelinput = Button(tl2, text="Set Az/El", bg="white", fg="black", command=set_azel)
    azellabel = Label(tl2, text="Current Azimuth: %3.2f, Current Elevation: %3.2f" % (currentAz, currentEl))
    pointlabel = Label(tl2, text="Antenna Pointing:")
    
    def set_azel_label():
        global currentAz, currentEl
        azellabel['text'] = "Current Azimuth: %3.2f, Current Elevation: %3.2f" % (currentAz, currentEl)
        root.after(1, set_azel_label)
    
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
    ax.set_rlim(90, 0, 1)
    ax.set_yticks(np.arange(0, 91, 10))
    ax.set_yticklabels(ax.get_yticks()[::-1])
    ax.invert_yaxis()
    ax.set_theta_zero_location("N")
    graph = FigureCanvasTkAgg(fig, master=bl)
    
    # Function to Plot Azimuth and Elevation
    def azelplot():
        global azelplotflag, progflag, currentAz, currentEl
        qthfile = str(qthloc.get())
        tlefile = str(tleloc.get())
        while azelplotflag:
            ax.cla()
            ax.set_title("Azimuth and Elevation of "+tlefile)
            ax.grid(True)
            ax.set_rlim(90, 0, 1)
            ax.set_yticks(np.arange(0, 91, 10))
            ax.set_yticklabels(ax.get_yticks()[::-1])
            ax.invert_yaxis()
            ax.set_theta_zero_location("N")
            az, el = azel_points(tlefile, qthfile)
            #az, el = np.pi, 10
            ax.plot(az*np.pi/180, 90-el, marker='o', color='orange')
            graph.draw()
            time.sleep(0.2)
            if progflag:
                currentAz = az
                if el>0:
                    currentEl = el
                else:
                    currentEl = 0
    
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
            time.sleep(0.2)

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
    pointlabel.pack(side="top")
    R1.pack(side="top")
    R2.pack(side="top")
    b_up.pack(side="top")
    b_down.pack(side="top")
    b_left.pack(side="top")
    b_right.pack(side="top")
    azellabel.pack(side="bottom")
    b_azelinput.pack(side="bottom")
    elentry.pack(side="bottom")
    ellabel.pack(side="bottom")
    azentry.pack(side="bottom")
    azlabel.pack(side="bottom")
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
    set_azel_label()
    root.mainloop()
    try:
        root.destroy()
    except:
        pass
    os._exit(1)
################################################################
if __name__ == "__main__":
    main()
