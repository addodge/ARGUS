#!/usr/bin/env python3
##############################################################################################
# Adam Dodge
# ARGUS Ground Station GUI
# Date Created: 10/24/2018
# Date Modified: 2/26/2019
##############################################################################################
# Description / Notes:

# This file creates a GUI for controlling the ARGUS ground station tracking ability. Currently
# it is able to track the satellite and show the tracking in the GUI. The next steps are to 
# add the motor control functions and figure out how exactly it will track over a path when the 
# controller only takes in position commands, as well as to implement the GPS receiver to take
# in the latitude and longitude of the ground station. 

# IMPORTANT: I do not recommend using anaconda python for this GUI. The font looks terrible and
# the sizing is way off because of the bad font. It is better to use the system python 3 and 
# make sure that matplotlib is version 2.2.3 because there is an issue with a segmentation fault
# on self.graph.draw() when using matplotlib 3.0.1. 

# The predict section was adapted from predict.py by Jesse Trutna. This is lines 549 through 689.
##############################################################################################
### Necessary Modules
import numpy as np
from tkinter import *
from PIL import ImageTk, Image
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import time, threading, os, ephem, serial, curses
from copy import copy
from cpredict import quick_find, quick_predict, PredictException

##############################################################################################
# THINGS TO DO:
#       Look at 0-90 vs 0-180 elevation to figure out how to do overhead passes better
#       Ports - By Serial ID
#       Can we just send position commands every second or do we need to come up with something?
#       Does elevation work in positive or negative direction?
##############################################################################################
class GUI:
    """ This is a class for creating the GUI for the ARGUS ground station. """
##############################################################################################
    # Define initialization Function
    def __init__(self):
        """ Function to initialize GUI. """
        self.azelplotflag = False # True if plot is active
        self.manflag = True # True if in manual mode
        self.progflag = False # True if in program track mode
        self.currentAz = 0 # Current Pointing azimuth
        self.currentEl = 0 # Current Pointing Elevation
        self.motorOn = False # True if motor is on
        self.debug = False
        self.step = 0.1 #step movement for antenna
        self.maxAz = 360
        self.minAz = -360
        self.maxEl = 180
        self.minEl = 0
        self.motorPath = '/dev/serial/by-id/usb-FTDI_FT232R_USB_UART_AH01B33D-if00-port0'
        self.GPSPath = '/dev/serial/by-id/usb-Prolific_Technology_Inc._USB-Serial_Controller_D-if00-port0'
        self.degree_sign = u'\N{DEGREE SIGN}'
        self.buildGUI()
        #self.startMotor()

##############################################################################################
    # Define function to build the GUI
    def buildGUI(self):
        """ Function to build GUI. """
        ##### Build root and frames
        self.root = Tk()
        self.root.title("ARGUS Ground Station")
        #root.attributes("-fullscreen", True)
        self.root.configure(background='grey')
        self.root.tk.call('wm', 'iconphoto', self.root._w, PhotoImage(file='ARGUS_Logo.gif'))
        self.root.option_add('*Font', 'fixed')
        self.t = Frame(self.root, borderwidth=2, relief="solid") #Top
        self.t1 = Frame(self.t, borderwidth=2, relief="solid") #Top left
        self.t2 = Frame(self.t, borderwidth=2, relief="solid") #Top Right
        self.t1t = Frame(self.t1, borderwidth=2, relief="solid") #Top left top
        self.t1b = Frame(self.t1, borderwidth=2, relief="solid") #Top left bottom
        self.b = Frame(self.root, borderwidth=2, relief="solid") #Bottom
        
        self.qthloc = StringVar()
        self.qthloc.set("ARGUS.qth")
        self.tleloc = StringVar()
        self.tleloc.set("MTI.tle")
        self.trackMode = IntVar()
        self.trackMode.set(1)
        self.locMode = IntVar()
        self.locMode.set(1)
        self.azinput = StringVar()
        self.elinput = StringVar()
        
        ##### Top Left Frame - exit, logo, description
        # exit button
        self.exitbutton = Button(self.t1t, text="QUIT", bg="red", fg="black",
                                                        command=self.t1.quit)
        # Logo
        img = ImageTk.PhotoImage(Image.open("ARGUS_Logo.png").resize((80,80), Image.ANTIALIAS))
        self.logo = Label(self.t1t, image=img)
        self.logo.image = img
        
        # GUI Description
        self.descrip = Label(self.t1t, text="ARGUS\nTracking\nGUI") 
        # Calibrate Button
        self.cbutton = Button(self.t1t, text="Calibrate", bg="green", fg="black",
                                                    command=self.call_calibrate)
        
        ##### Pointing Frame
        # Track Mode buttons
        self.R1 = Radiobutton(self.t2, text="Manual Mode", variable=self.trackMode, 
                                                   value=1, command=self.go_manual)
        self.R2 = Radiobutton(self.t2, text="Program Track", variable=self.trackMode,
                                                    value=2, command=self.go_program)
        # Create antenna motion buttons, map arrow keys to same functions
        self.b_up = Button(self.t2, text="+El "+'\u25b2', bg="white", fg="black",
                                                 command=self.increase_elevation)
        self.root.bind('<Up>', self.uppress)
        self.b_down = Button(self.t2, text="-El "+'\u25BC', bg="white", fg="black", 
                                              command=self.decrease_elevation)
        self.root.bind('<Down>', self.downpress)
        self.b_left = Button(self.t2, text="+Az "+'\u25B6', bg="white", fg="black", 
                                                command=self.increase_azimuth)
        self.root.bind('<Left>', self.leftpress)
        self.b_right = Button(self.t2, text="-Az "+'\u25C0', bg="white", fg="black", 
                                                 command=self.decrease_azimuth)
        self.root.bind('<Right>', self.rightpress)
        # Value inputs
        self.azlabel = Label(self.t2, text="Input Azimuth: ")
        self.ellabel = Label(self.t2, text="Input Elevation: ")
        self.azentry = Entry(self.t2, textvariable=self.azinput)
        self.elentry = Entry(self.t2, textvariable=self.elinput)
        self.azinput.set(str(round(self.currentAz, 2)))
        self.elinput.set(str(round(self.currentEl, 2)))
        self.b_azelinput = Button(self.t2, text="Set Az/El", bg="white", fg="black",
                             command=self.set_azel)
        self.azellabel = Label(self.t2, text="Current Azimuth: %3.2f, Current Elevation: %3.2f" %
                                                                (self.currentAz, self.currentEl))
        self.pointlabel = Label(self.t2, text="Antenna Pointing:")
        
        self.loclabel = Label(self.t2, text="Ground Station Location:")
        self.findLocationQTH()
        self.R3 = Radiobutton(self.t2, text="ARGUS.qth", variable=self.locMode, 
                                                   value=1, command=self.findLocationQTH)
        self.R4 = Radiobutton(self.t2, text="GPS", variable=self.locMode,
                  value=2, command=self.startGPS)
        self.latlabel = Label(self.t2, text="Latitude: %3.2f" % self.lat)
        self.lonlabel = Label(self.t2, text="Longitude: %3.2f" % self.lon)
        self.altlabel = Label(self.t2, text="Altitude: %3.2f" % self.alt)
        
        #### Bottom Left Frame - Azimuth/Elevation Plot
        # QTH file input
        self.qth = Label(self.b, text="QTH File:")
        self.qthentry = Entry(self.b, textvariable=self.qthloc)
        
        # TLE file input
        self.tle = Label(self.b, text="TLE File:")
        self.tleentry = Entry(self.b, textvariable=self.tleloc)
        
        # IS MOTOR ON
        #self.mot = Label(self.b, text="Motor: NOT CONNECTED")
        self.motstart = Button(self.b, text="Connect Motor", bg="green", fg="black", command=self.motorCall)
        self.motstop = Button(self.b, text="Stop Motor Motion", bg='red', fg='black', command=self.stop)
        
        # Az/El Plot figure creation
        self.fig = Figure()
        self.ax = self.fig.add_subplot(111, projection='polar')
        _, _, satname = self.azel_points(str(self.tleloc.get()))
        self.ax.set_title("Azimuth and Elevation of "+satname)
        self.ax.grid(True)
        self.ax.set_rlim(90, 0, 1)
        self.ax.set_yticks(np.arange(0, 91, 10))
        self.ax.set_yticklabels(self.ax.get_yticks()[::-1])
        self.ax.invert_yaxis()
        self.ax.set_theta_zero_location("N")
        self.ax.set_theta_direction(-1)
        self.graph = FigureCanvasTkAgg(self.fig, master=self.b)
        
        # Start/stop plotting button
        self.b1 = Button(self.b, text="Start Tracking", command=self.azel_handler, bg="green", fg='black')
        
        starttime, endtime, startaz, endaz, maxel, satname = \
                self.nextpass(str(self.tleloc.get()))
        self.np_l = Label(self.t1b, text = \
                "Upcoming Passes for "+str(satname)+":\n"+
                "\nPass 1:\nStart: "+starttime[0]+", Azimuth: "+
                str(round(startaz[0],2))+self.degree_sign+"\nFinish: "+endtime[0]+
                ", Azimuth: "+str(round(endaz[0],2))+self.degree_sign+
                "\nMaximum Elevation: "+str(round(maxel[0],2))+self.degree_sign+
                "\nPass 2:\nStart: "+starttime[1]+", Azimuth: "+
                str(round(startaz[1],2))+self.degree_sign+"\nFinish: "+endtime[1]+
                ", Azimuth: "+str(round(endaz[1],2))+self.degree_sign+
                "\nMaximum Elevation: "+str(round(maxel[1],2))+self.degree_sign+
                "\nPass 3:\nStart: "+starttime[2]+", Azimuth: "+
                str(round(startaz[2],2))+self.degree_sign+"\nFinish: "+endtime[2]+
                ", Azimuth: "+str(round(endaz[2],2))+self.degree_sign+
                "\nMaximum Elevation: "+str(round(maxel[2],2))+self.degree_sign)
        
        # Button for recalculation of future passes
        self.np_button = Button(self.t1b, text="Recalculate", command=self.recalculate, 
                                                            bg="blue", fg="black")
        
        # Pack Frames
        self.t.pack(side='top', expand=True, fill="both", padx=10, pady=10)
        self.t1.pack(side="left", expand=True, fill="both", padx=10, pady=10)
        self.t2.pack(side="right",expand=True, fill="both", padx=10, pady=10)
        self.t1t.pack(side='top', expand=True, fill="both", padx=10, pady=10)
        self.t1b.pack(side='bottom', expand=True, fill="both", padx=10, pady=10)
        self.b.pack(side="bottom", expand=True, fill="both", padx=10, pady=10)
        
        # Pack everything else into frames
        self.exitbutton.pack(side="left")
        self.cbutton.pack(side="left")
        self.logo.pack(side="left")
        self.descrip.pack(side="left")
        self.pointlabel.pack(side="top")
        self.R1.pack(side="top")
        self.R2.pack(side="top")
        #self.b_up.pack(side="top")
        #self.b_down.pack(side="top")
        #self.b_left.pack(side="top")
        #self.b_right.pack(side="top")
        self.azellabel.pack(side="top")
        self.azlabel.pack(side="top")
        self.azentry.pack(side="top")
        self.ellabel.pack(side="top")
        self.elentry.pack(side="top")
        self.b_azelinput.pack(side="top")
        self.loclabel.pack(side="top")
        self.R3.pack(side="top")
        self.R4.pack(side="top")
        self.latlabel.pack(side="top")
        self.lonlabel.pack(side="top")
        self.altlabel.pack(side="top")
        self.graph.get_tk_widget().pack(side="bottom",fill='both', expand=True)
        self.b1.pack(side='left')
        #self.qth.pack(side="left")
        #self.qthentry.pack(side="left")
        self.tle.pack(side="left")
        self.tleentry.pack(side="left")
        self.motstart.pack(side="right")
        self.motstop.pack(side="right")
        #self.mot.pack(side="right")
        self.np_l.pack(side="top")
        self.np_button.pack(side="top")

##############################################################################################
# Motor Control Code
    def motorCall(self):
        if self.motorOn:
            self.stopMotor()
        else:
            self.startMotor()
    
    def startMotor(self):
        try:
            self.MotSer = serial.Serial(port=self.motorPath, baudrate=600, bytesize=8, 
                                             parity='N', stopbits=1, timeout=5)
            self.motorOn = True
            self.motstart['text'] = "Disconnect Motor"
            self.motstart['bg'] = "red"
        except:
            print("No Motor Controller connected to:\n"+self.motorPath+"\nAre you root?\n")
        self.status()
    
    def stopMotor(self):
        try:
            self.MotSer.close()
        except:
            pass
        self.motorOn = False
        self.motstart['text'] = "Connect Motor"
        self.motstart['bg'] = "green"
    
    def status(self):
        """
        Send a STATUS command to the controller, which requests the current azimuth
        and elevation of the rotor. The azimuth, elevation and pulse are then computed,
        the pulse is set and the azimuth, elevation and pulse are returned as a list (first
        element being azimuth, the second being elevation, and the third being pulse).
        """
        if self.motorOn:
            cmd = [b'\x57', b'\x00', b'\x00', b'\x00', b'\x00', b'\x00', b'\x00', b'\x00',
                                           b'\x00', b'\x00', b'\x00', b'\x1f', b'\x20']
            packet = b"".join(cmd)
            self.MotSer.write(packet)
            self.MotSer.flush()

            rec_packet = self.MotSer.read(12)
            az = (rec_packet[1] * 100) + (rec_packet[2] * 10) + \
                   rec_packet[3] + (rec_packet[4] / 10) - 360.0
            el = (rec_packet[6] * 100) + (rec_packet[7] * 10) + \
                   rec_packet[8] + (rec_packet[9] / 10) - 360.0
            ph = rec_packet[5]
            pv = rec_packet[10]

            assert(ph == pv)
            self.pulse = ph
            if self.debug:
                print("STATUS COMMAND SENT")
                print("Sent: " + str(packet))
                print("Azimuth:   " + str(az))
                print("Elevation: " + str(el))
                print("PH: " + str(ph))
                print("PV: " + str(pv) + "\n")
            self.currentAz = az
            self.currentEl = el
    
    def stop(self):
        """
        Send a STOP command to the controller, which causes the rotor to stop moving and
        return the current azimuth, elevation and pulse of the rotor where it stopped. The
        azimuth, elevation and pulse are then computed, the pulse is set and the azimuth,
        elevation and pulse are returned as a list (first element being azimuth, sencond
        being elevation and the third being pulse).
        """
        if self.motorOn:
            cmd = [b'\x57', b'\x00', b'\x00', b'\x00', b'\x00', b'\x00', b'\x00', b'\x00',
                                           b'\x00', b'\x00', b'\x00', b'\x0f', b'\x20']
            packet = b"".join(cmd)
            self.MotSer.write(packet)
            self.MotSer.flush()

            rec_packet = self.MotSer.read(12)
            az = (rec_packet[1] * 100) + (rec_packet[2] * 10) + \
                   rec_packet[3] + (rec_packet[4] / 10) - 360.0
            el = (rec_packet[6] * 100) + (rec_packet[7] * 10) + \
                   rec_packet[8] + (rec_packet[9] / 10) - 360.0
            ph = rec_packet[5]
            pv = rec_packet[10]

            assert(ph == pv)
            self.pulse = ph
            
            if self.debug:
                print("STOP COMMAND SENT")
                print("Azimuth:   " + str(az))
                print("Elevation: " + str(el))
                print("PH: " + str(ph))
                print("PV: " + str(pv) + "\n")
            self.currentAz = az
            self.currentEl = el
    
    def set(self):
        """
        send a SET command to the controller, which causes the rotor to adjust its position
        to the azimuth and elevation specified by the azi and eli parameters respecitvely.
        The azi and eli parameters are floating point values that specify the desired position.
        There is no response to the SET command, thus nothing to return.
        """
        if self.motorOn:
            az1 = self.currentAz
            el1 = self.currentEl
            assert(float(az1) <= self.maxAz)
            assert(float(az1) >= self.minAz)
            assert(float(el1) <= self.maxEl)
            assert(float(el1) >= self.minEl)

            az = "0" + str(int(self.pulse * (float(az1) + 360)))
            el = "0" + str(int(self.pulse * (float(el1) + 360)))
            cmd = [b'\x57', az[-4].encode(), az[-3].encode(), az[-2].encode(), az[-1].encode(), 
                   chr(self.pulse).encode(), el[-4].encode(), el[-3].encode(), el[-2].encode(), 
                   el[-1].encode(), chr(self.pulse).encode(), b'\x2f', b'\x20']
            packet = b"".join(cmd)

            self.MotSer.write(packet)
            self.MotSer.flush()
            if self.debug:
                print("SET COMMAND SENT")
                print("Sent: " + str(packet))
                print("Set Azimuth:   " + str(az1) + " (" + str(az) + ")")
                print("Set Elevation: " + str(el1) + " (" + str(el) + ")")
                print("Pulse: " + chr(self.pulse) + "\n")
    
##############################################################################################
    def startGPS(self):
        threading.Thread(target=self.findLocationGPS).start()
    
    def findLocationGPS(self):
        try:
            self.GPSser = serial.Serial(self.GPSPath, '4800', timeout=5)
        except:
            print("No GPS connected to:\n"+self.GPSPath+"\nAre you root?\n")
            self.locMode.set(1)
            return
        num = 0
        alt = []
        long = []
        lat = []
        while num < 1:
            line = self.GPSser.readline()
            splitline = line.split(b',')
            try:
                if splitline[1] == b'':
                    print('No GPS data received from:\n'+self.GPSPath+'\nCheck if red light is blinking.\n')
                    self.locMode.set(1)
                    return
            except:
                print('No GPS data received from:\n'+self.GPSPath+'\nCheck if red light is blinking.\n')
                self.locMode.set(1)
                return
            if splitline[0] == b'$GPGGA':
                latDir = splitline[3].decode('ASCII')
                if latDir == "N":
                    lat.append(float(splitline[2].decode('ASCII'))/100)
                elif latDir == "S":
                    lat.append(float(splitline[2].decode('ASCII'))/-100)
                else:
                    print("Latitude not North or South.\n")
                    self.locMode.set(1)
                    return
                
                longDir = splitline[5].decode('ASCII')
                if longDir == "E":
                    long.append(float(splitline[4].decode('ASCII'))/100)
                elif longDir == "W":
                    long.append(float(splitline[4].decode('ASCII'))/-100)
                else:
                    print("Longitude not East or West.\n")
                    self.locMode.set(1)
                    return
                
                altUnit = splitline[10].decode('ASCII')
                assert altUnit == "M"
                alt.append(float(splitline[9].decode('ASCII')))
                num = num+1

        self.lat = np.mean(lat)
        self.lon = -np.mean(long)
        self.alt = np.mean(alt)
        self.latlabel['text'] = "Latitude: %3.2f" % self.lat
        self.lonlabel['text'] = "Longitude: %3.2f" % self.lon
        self.altlabel['text'] = "Altitude: %3.2f" % self.alt
        
        self.GPSser.close()

    def findLocationQTH(self):
        qth = self.load_qth(self.qthloc.get())
        self.lat = qth[0]
        self.lon = qth[1]
        self.alt = qth[2]
        try:
            self.latlabel['text'] = "Latitude: %3.2f" % self.lat
            self.lonlabel['text'] = "Longitude: %3.2f" % self.lon
            self.altlabel['text'] = "Altitude: %3.2f" % self.alt
        except:
            pass
        
##############################################################################################
    # Define Functions for azimuth and elevation plotting
    def azelplot(self):
        """ Function to Plot Azimuth and Elevation. """
        tlefile = str(self.tleloc.get())
        while self.azelplotflag:
            self.ax.cla()
            self.ax.grid(True)
            self.ax.set_rlim(90, 0, 1)
            self.ax.set_yticks(np.arange(0, 91, 10))
            self.ax.set_yticklabels(self.ax.get_yticks()[::-1])
            self.ax.invert_yaxis()
            self.ax.set_theta_zero_location("N")
            self.ax.set_theta_direction(-1)
            az, el, satname = self.azel_points(tlefile)
            sunAz, sunEl = self.findsun()
            self.ax.set_title("Azimuth and Elevation of "+satname)
            if el > 90:
                plotel = 180-el
                plotaz = az+180
            else:
                plotel=el
                plotaz=az
            self.ax.scatter(plotaz*np.pi/180, 90-plotel, marker='o', color='blue', label=satname)
            self.ax.scatter(sunAz*np.pi/180, 90-sunEl, marker='o', color='orange', label='Sun')
            self.ax.legend()
            self.graph.draw() #CAUSES ISSUES IN MATPLOTLIB
            time.sleep(0.2)
            if self.progflag:
                if el<self.minEl:
                    el = self.minEl
                azvec = []
                azvec.append(az)
                elvec = []
                elvec.append(el)
                if az>180:
                    azvec.append(az-180)
                    elvec.append(180-el)
                    azvec.append(az-360)
                    elvec.append(el)
                    azvec.append(az-540)
                    elvec.append(180-el)
                else:
                    azvec.append(az+180)
                    elvec.append(180-el)
                    azvec.append(az-180)
                    elvec.append(180-el)
                    azvec.append(az-360)
                    elvec.append(el)
                
                cost = []
                cost.append((azvec[0]-self.currentAz)**2+(elvec[0]-self.currentEl)**2)
                cost.append((azvec[1]-self.currentAz)**2+(elvec[1]-self.currentEl)**2)
                cost.append((azvec[2]-self.currentAz)**2+(elvec[2]-self.currentEl)**2)
                cost.append((azvec[3]-self.currentAz)**2+(elvec[3]-self.currentEl)**2)
                ind = cost.index(min(cost))
                az = azvec[ind]
                el = elvec[ind]
                self.currentAz = az
                self.currentEl = el
                self.set()
                self.oldAz = az
                self.oldEl = el
    
    def azel_handler(self):
        """ Function to Spawn Azimuth and Elevation process, switch state. """
        if self.azelplotflag == False:
            self.azelplotflag = True
            self.b1.configure(text="Stop Tracking", bg="red", fg='black')
            threading.Thread(target=self.azelplot).start() #Start new process to plot
        else:
            self.azelplotflag = False
            self.b1.configure(text="Start Tracking", bg="green", fg='black')
        
    def azel_points(self, tlefile):
        """ Function to Produce Azimuth and Elevation using Predict. """
        qth = (self.lat, self.lon, self.alt)
        tle, satname = self.load_tle(tlefile)
        data = observe(tle, qth) #find current state
        return data['azimuth'], data['elevation'], satname
    
##############################################################################################
    # Define Functions to set the azimuth and elevation along with the labels
    def set_azel_label(self):
        """ Function to set Azimuth and Elevation Label on GUI. """
        self.azellabel['text'] = "Current Azimuth: %3.2f, Current Elevation: %3.2f" % \
                                                (self.currentAz, self.currentEl)
        self.root.after(1, self.set_azel_label)
    
    def set_azel(self):
        """ Function to set azimuth and elevation from input. """
        if self.manflag:
            azinput_val = float(str(self.azinput.get()))
            elinput_val = float(str(self.elinput.get()))
            if elinput_val > self.maxEl:
                self.currentEl = self.maxEl
            elif elinput_val < self.minEl:
                self.currentEl = self.minEl
            else:
                self.currentEl = elinput_val
            while azinput_val > self.maxAz:
                azinput_val = azinput_val-360
            while azinput_val < self.minAz:
                azinput_val = azinput_val+360
            self.currentAz = azinput_val
            self.azinput.set(str(round(self.currentAz, 2)))
            self.elinput.set(str(round(self.currentEl, 2)))
            self.set()
    
##############################################################################################
    # Define Functions to switch mode
    def go_program(self):
        """ Function for switching to program tracking mode. """
        self.progflag=True
        self.manflag=False
        
    def go_manual(self):
        """ Function for switching to manual tracking mode. """
        self.progflag=False
        self.manflag=True
        self.azinput.set(str(0))
        self.elinput.set(str(0))
        self.currentAz = 0
        self.currentEl = 0
        self.set()
    
##############################################################################################
    # Define Functions to load tle and qth files
    def load_qth(self, qthfile):
        """ Function to Load latitude, longitude, elevation from given file. """
        try:
            with open(qthfile, 'r') as myfile:
                qth = myfile.readlines()
        except IOError:
            print('Error Reading '+qthfile+". Exiting.")
            os._exit(1)
        qth = list(map(lambda s: s.strip(), qth))
        self.locname = qth[0]
        qth = massage_qth(tuple(qth[1:])) #use predict.py to change variable types
        qth = (qth[0], -qth[1], qth[2])
        return qth
    
    def load_tle(self, tlefile):
        """ Function to Load orbital elements. """
        try:
            with open(tlefile, 'r') as myfile:
                tle = myfile.read()
        except IOError:
            print('Error Reading '+tlefile+". Exiting.")
            os._exit(1)
        tle = massage_tle(tle) #use predict.py to separate elements
        satname = tle[0]
        return tle, satname
    
##############################################################################################
    # Define Calibration Functions
    def call_calibrate(self):
        """ Function to call the calibrate function. """
        self.calibrate()
        
    def calibrate(self):
        """ Fuction to Calibrate Pointing angles using the Sun. """
        print("Calibrating...")
        qth = (self.lat, self.lon, self.alt)
        observer = ephem.Observer()
        observer.lat = self.intdeg2dms(qth[0])
        observer.lon = self.intdeg2dms(-qth[1])
        observer.elevation = qth[2]

        # Track Sun to determine azimuth and elevation
        sun = ephem.Sun()
        sun.compute(observer)
        if sun.alt<0:
            print("Sun not visible, Calibration not possible. Exiting.")
            os._exit(1)
        # Assume pointing close enough to the sun to get a signal
        # Set current Az/El to this azimuth and elevation
        self.currentAz, self.currentEl = sun.az*180/np.pi, sun.alt*180/np.pi
        print("Done.\n")
    
##############################################################################################
    # Define Functions for finding sun
    def findsun(self):
        """ Function to find the Sun for plotting. """
        qth = (self.lat, self.lon, self.alt)
        observer = ephem.Observer()
        observer.lat = self.intdeg2dms(qth[0])
        observer.lon = self.intdeg2dms(-qth[1])
        observer.elevation = qth[2]
        sun = ephem.Sun()
        sun.compute(observer)
        sunAz, sunEl = sun.az*180/np.pi, sun.alt*180/np.pi
        return sunAz, sunEl
        
    def recalculate(self):
        """ Function to recalculate future passes if new TLE loaded. """
        starttime, endtime, startaz, endaz, maxel, satname = \
                 self.nextpass(str(self.tleloc.get()))
        self.np_l.configure(text = \
                "Upcoming Passes for "+str(satname)+":\n"+
                "\nPass 1:\nStart: "+starttime[0]+", Azimuth: "+
                str(round(startaz[0],2))+self.degree_sign+"\nFinish: "+endtime[0]+
                ", Azimuth: "+str(round(endaz[0],2))+self.degree_sign+
                "\nMaximum Elevation: "+str(round(maxel[0],2))+self.degree_sign+
                "\nPass 2:\nStart: "+starttime[1]+", Azimuth: "+
                str(round(startaz[1],2))+self.degree_sign+"\nFinish: "+endtime[1]+
                ", Azimuth: "+str(round(endaz[1],2))+self.degree_sign+
                "\nMaximum Elevation: "+str(round(maxel[1],2))+self.degree_sign+
                "\nPass 3:\nStart: "+starttime[2]+", Azimuth: "+
                str(round(startaz[2],2))+self.degree_sign+"\nFinish: "+endtime[2]+
                ", Azimuth: "+str(round(endaz[2],2))+self.degree_sign+
                "\nMaximum Elevation: "+str(round(maxel[2],2))+self.degree_sign)
    
    def intdeg2dms(self, deg):
        """ Function to convert integer to degrees, minutes, and seconds. """
        d = int(deg)
        md = abs(deg - d) * 60
        m = int(md)
        sd = (md - m) * 60
        return '%d:%d:%f' % (d, m, sd)
        
##############################################################################################
    # Define Function for finding upcoming passes
    def nextpass(self, tlefile):
        """ Determine Next 3 Pass timing and azimuth of start and finish time/azimuth. """
        qth = (self.lat, self.lon, self.alt)
        tle, satname = self.load_tle(tlefile) # load tle
        p = transits(tle, qth) # predict future passes
        starttime, endtime, startaz, endaz, maxel = ([] for i in range(5)) #initialize
        for i in range(3): # Predict 3 passes
            transit = next(p) #Find next pass
            starttime.append(time.ctime(transit.start))
            endtime.append(time.ctime(transit.end))
            startaz.append(observe(tle, qth, transit.start)['azimuth'])
            endaz.append(observe(tle, qth, transit.end)['azimuth'])
            maxel.append(transit.peak()['elevation'])
        return starttime, endtime, startaz, endaz, maxel, satname

##############################################################################################
    # Define Azimuth and Elevation changes for Manual Mode
    def increase_elevation(self):
        """ Function to increase elevation by step size. """
        if self.manflag:
            if self.currentEl+self.step <= self.maxEl:
                self.currentEl = self.currentEl + self.step
            else:
                self.currentEl = self.maxEl
            self.set()

    def decrease_elevation(self):
        """ Function to decrease elevation by step size. """
        if self.manflag:
            if self.currentEl-self.step >= self.minEl:
                self.currentEl = self.currentEl - self.step
            else:
                self.currentEl = self.minEl
            self.set()
            
    def increase_azimuth(self):
        """ Function to increase azimuth by step size. """
        if self.manflag:
            if self.currentAz + self.step >= self.maxAz:
                self.currentAz = self.currentAz + self.step - 360
            else:
                self.currentAz = self.currentAz + self.step
            self.set()

    def decrease_azimuth(self):
        """ Function to decrease azimuth by step size. """
        if self.manflag:
            if self.currentAz-self.step < self.minAz:
                self.currentAz = self.currentAz - self.step + 360
            else:
                self.currentAz = self.currentAz - self.step
            self.set()
    
##############################################################################################
    # Define Arrow Presses for Manual Mode
    def uppress(self, event):
        """ Function to map up press to increase elevation. """
        self.increase_elevation()

    def downpress(self, event):
        """ Function to map down press to decrease elevation. """
        self.decrease_elevation()

    def rightpress(self, event):
        """ Function to map right press to increase azimuth. """
        self.increase_azimuth()

    def leftpress(self, event):
        """ Function to map left press to decrease azimuth. """
        self.decrease_azimuth()
# End of GUI Class
##############################################################################################
# Functions and class adapted from predict.py by Jesse Trutna
def massage_tle(tle):
    """ Function for getting correct tle data format. """
    try:
        # TLE may or may not have been split into lines already
        if isinstance(tle, str):
            tle = tle.rstrip().split('\n')
        assert len(tle) == 3, "TLE must be 3 lines, not %d: %s" % (len(tle), tle)
        return tle
        #TODO: print a warning if TLE is 'too' old
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
    if ending_after is None:
        ending_after = time.time()
    ts = ending_after
    while True:
        transit = quick_predict(tle, ts, qth)
        t = Transit(tle, qth, start=transit[0]['epoch'], end=transit[-1]['epoch'])
        if (ending_before != None and t.end > ending_before):
            break
        if (t.end > ending_after):
            yield t
        # Need to advance time cursor so predict doesn't yield same pass
        ts = t.end + 60     #seconds seems to be sufficient
        
# Transit is a convenience class representing a pass of a satellite over a groundstation.
class Transit():
    """ Transit is a class representing a pass of a satellite over a groundstation. """
    def __init__(self, tle, qth, start, end):
        """ Initialization function. """
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

    def above(self, elevation):
        """ Function to return portion of transit above a certain elevation. """
        return self.prune(lambda ts: self.at(ts)['elevation'] >= elevation)

    def prune(self, fx, epsilon=0.1):
        """ Function to return section of a transit where a pruning function is valid. """
        # Currently used to set elevation threshold, unclear what other uses it might have.
        # fx must either return false everywhere or true for a contiguous period including the peak
        peak = self.peak()['epoch']
        if not fx(peak):
            start = peak
            end = peak
        else:
            if fx(self.start):
                start = self.start
            else:
                # Invariant is that fx(right) is True
                left, right = self.start, peak
                while ((right - left) > epsilon):
                    mid = (left + right)/2
                    if fx(mid):
                        right = mid
                    else:
                        left = mid
                start = right
            if fx(self.end):
                end = self.end
            else:
                # Invariant is that fx(left) is True
                left, right = peak, self.end
                while ((right - left) > epsilon):
                    mid = (left + right)/2
                    if fx(mid):
                        left = mid
                    else:
                        right = mid
                end = left
        # Use copy to allow subclassing of Transit object
        pruned = copy(self)
        pruned.start = start
        pruned.end = end
        return pruned

    def duration(self):
        """ Function to return pass duration. """
        return self.end - self.start

    def at(self, t):
        """ Function to return azimuth and elevation at certain time. """
        if t < self.start or t > self.end:
            raise PredictException("time %f outside transit [%f, %f]" % (t, self.start, self.end))
        return observe(self.tle, self.qth, t)
