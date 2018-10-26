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
import time, threading
from random import random, randint
import multiprocessing as mp

# Booleans for plotting on/off
continuePlotting1 = False
continuePlotting2 = False
################################################################
# switch az/el plot on/off
def change_azel_state():
    global continuePlotting1
    if continuePlotting1 == True:
        continuePlotting1 = False
    else:
        continuePlotting1 = True
        
# Produce Azimuth and Elevation - THIS NEEDS TO BE CHANGED TO ACTUAL AZ/EL
def azel_points():
    az = random() * 2*np.pi
    el = random() * np.pi/2
    return az, el

################################################################
# switch fft plot on/off
def change_fft_state():
    global continuePlotting2
    if continuePlotting2 == True:
        continuePlotting2 = False
    else:
        continuePlotting2 = True
    
# Produce FFT points - THIS NEEDS TO BE CHANGED TO ACTUAL FFT
def fft_points(cf):
    freq = np.sort(np.random.rand(10) * 20000000 + cf - 10000000)
    mag = np.random.rand(10) * 10
    return freq, mag

################################################################
# Calibrate az/el - THIS NEEDS TO ACTUALLY CALIBRATE AND AUTOTRACK
def calibrate():
    print("Calibrated")

################################################################
def main():
    global continuePlotting1, continuePlotting2
    # Create root GUI
    root = Tk()
    root.title("ARGUS Ground Station")
    #root.attributes("-fullscreen", True)
    #root.geometry("800x800")
    root.configure(background='grey')
    
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
    exitbutton = Button(tl1, text="QUIT", fg="red", command=tl.quit)
    
    path = "ARGUS_Logo.png"
    img = Image.open(path)
    img = img.resize((200,200), Image.ANTIALIAS)
    img = ImageTk.PhotoImage(img)
    logo = Label(tl1, image=img)
    image = img
    
    descrip = Label(tl1, text="This is the GUI for the ARGUS \nGround Station for Tracking LEO Satellites.") 
    
    # Calibration Frame
    cbutton = Button(tl2, text="Calibrate", fg="green", command=calibrate)
    
    # Bottom Left Frame - Azimuth/Elevation Plot
    qth = Label(bl, text="QTH File:")
    
    qthloc = StringVar()
    qthentry = Entry(bl, textvariable=qthloc)
    qthloc.set("boulder.qth")
    
    tle = Label(bl, text="TLE File:")
    
    tleloc = StringVar()
    tleentry = Entry(bl, textvariable=tleloc)
    tleloc.set("MTI.tle")
    
    fig = Figure()
    ax = fig.add_subplot(111, projection='polar')
    ax.set_title("Azimuth and Elevation of Satellite")
    ax.grid(True)
    ax.set_ylim(0, np.pi/2)
    graph = FigureCanvasTkAgg(fig, master=bl)
    
    # Plot Azimuth and Elevation - THIS NEEDS TO BE UPDATED
    def azelplot():
        while continuePlotting1:
            ax.cla()
            ax.set_title("Azimuth and Elevation of Satellite")
            ax.grid(True)
            ax.set_ylim(0, np.pi/2)
            az, el = azel_points()
            ax.plot(az, el, marker='o', color='orange')
            graph.draw()
            time.sleep(0.5)

    # Spawn Azimuth and Elevation process
    def azel_handler():
        change_azel_state()
        threading.Thread(target=azelplot).start()
    
    b = Button(bl, text="Start/Stop", command=azel_handler, bg="red", fg="white")
    
    # Top Right Frame - FFT Plot
    cf = Label(tr, text="Center Frequency:")
    
    centerfreq = StringVar()
    freqentry = Entry(tr, textvariable=centerfreq)
    centerfreq.set("2250000000")
    
    fig2 = Figure()
    ax2 = fig2.add_subplot(111)
    ax2.set_xlabel("Frequency [Hz]")
    ax2.set_title("FFT Frequency Plot")
    ax2.set_xlim(2000000000, 2500000000)
    ax2.set_ylim(0,10)
    ax2.grid()
    graph2 = FigureCanvasTkAgg(fig2, master=tr)
    
    # Plot fft points - THIS NEEDS TO BE UPDATED
    def fftplot():
        while continuePlotting2:
            ax2.cla()
            ax2.set_xlabel("Frequency [Hz]")
            ax2.set_title("FFT Frequency Plot")
            ax2.set_xlim(2200000000, 2300000000)
            ax2.set_ylim(0,10)
            ax2.grid()
            freq, mag = fft_points(int(str(centerfreq.get())))
            ax2.plot(freq, mag, marker='o', color='blue')
            graph2.draw()
            time.sleep(0.5)

    # Spawn FFT process
    def fft_handler():
        change_fft_state()
        threading.Thread(target=fftplot).start()
    
    b2 = Button(tr, text="Start/Stop", command=fft_handler, bg="red", fg="white")
    
    # Bottom Right Frame - 
    
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
    
    # Start GUI
    root.mainloop()
    root.destroy()
################################################################
if __name__ == "__main__":
    main()
