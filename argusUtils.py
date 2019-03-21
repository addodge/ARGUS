#!/usr/bin/env python3
##############################################################################################
# Adam Dodge
# ARGUS Ground Station GUI
# Date Created: 10/24/2018
# Date Modified: 3/5/2019
##############################################################################################
# Description / Notes:

# This file creates a GUI for controlling the ARGUS ground station tracking ability.
# It is able to track the satellite and show the tracking in the GUI. It also can find the 
# location of the ground station eiter using a QTH file or the GPS. It is able to use the 
# Satellite location to follow a satellite across the sky, or can be put in manual mode to
# control the motion of the motors manually. 

# IMPORTANT: I do not recommend using anaconda python for this GUI. The font looks terrible and
# the sizing is way off because of the bad font. It is better to use the system python 3 and 
# make sure that matplotlib is version 2.2.3 because there is an issue with a segmentation fault
# on self.graph.draw() when using matplotlib 3.0.1. 

# The predict section was adapted from predict.py by Jesse Trutna. This is lines 783-end.
##############################################################################################
'''
gm = geomag.geomag.GeoMag()
gm.GeoMag(40.015, -105.27, 1624).dec
'''

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
#       How can we improve the tracking so slew rate is slower? is there a way?
#       Does cost function even do anything? Can i get rid of it?
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
        self.debug = True # Prints motor commands if true
        self.step = 0.2 # step movement for antenna
        self.maxAz = 360 # Maximum ground station azimuth
        self.minAz = -360 # Minimum ground station azimuth
        self.maxEl = 180 # Maximum ground station elevation
        self.minEl = 0 # Minimum ground station elevation
        self.motorAz, self.motorEl = 0, 0 # initialize motor angles
        self.motWaitTime = 0.2 #seconds - how often to send a command
        self.pulse = 10 #Initialize just in case - motor resolution
        # Serial connection paths
        self.motorPath = '/dev/serial/by-id/usb-FTDI_FT232R_USB_UART_AH01B33D-if00-port0'
        self.GPSPath = '/dev/serial/by-id/usb-Prolific_Technology_Inc._USB-Serial_Controller_D-if00-port0'
        self.degree_sign = u'\N{DEGREE SIGN}' # degree sign for printing
        self.buildGUI() # Build the GUI for ARGUS

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
        
        self.qthloc = StringVar() #QTH file location
        self.qthloc.set("ARGUS.qth")
        self.tleloc = StringVar() #TLE file location
        self.tleloc.set("MTI.tle")
        self.trackMode = IntVar() #Variable for program or manual mode
        self.trackMode.set(1)
        self.locMode = IntVar() #Variable for GPS or QTH location
        self.locMode.set(1)
        self.azinput = StringVar() #Variable for inputting azumuth
        self.elinput = StringVar() #Variable for inputting elevation
        
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
        # Map arrow keys to same functions
        #self.root.bind('<Up>', self.uppress)
        #self.root.bind('<Down>', self.downpress)
        #self.root.bind('<Left>', self.leftpress)
        #self.root.bind('<Right>', self.rightpress)
        
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
        
        # GPS location inputs
        self.loclabel = Label(self.t2, text="Ground Station Location:")
        self.findLocationQTH()
        self.R3 = Radiobutton(self.t2, text="ARGUS.qth", variable=self.locMode, 
                                                   value=1, command=self.findLocationQTH)
        self.R4 = Radiobutton(self.t2, text="GPS", variable=self.locMode,
                  value=2, command=self.startGPS)
        self.latlabel = Label(self.t2, text="Latitude: %3.2f" % self.lat+self.degree_sign)
        self.lonlabel = Label(self.t2, text="Longitude: %3.2f" % self.lon+self.degree_sign)
        self.altlabel = Label(self.t2, text="Altitude: %3.2f" % self.alt+"m")
        
        #### Bottom Left Frame - Azimuth/Elevation Plot        
        # TLE file input
        self.tle = Label(self.b, text="TLE File:")
        self.tleentry = Entry(self.b, textvariable=self.tleloc)
        
        # IS MOTOR ON
        self.motstart = Button(self.b, text="Connect Motor", bg="green", fg="black",
                 command=self.motorCall)
        self.motstop = Button(self.b, text="Stop Motor Motion", bg='red', fg='black',
                 command=self.stop)
        
        # Az/El Plot figure creation
        self.fig = Figure()
        self.ax = self.fig.add_subplot(111, projection='polar')
        _, _, self.satname = self.azel_points(str(self.tleloc.get()))
        self.ax.set_title("Azimuth and Elevation of "+self.satname)
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
        
        starttime, endtime, startaz, endaz, maxel, self.satname = \
                self.nextpass(str(self.tleloc.get()))
        self.np_l = Label(self.t1b, text = \
                "Upcoming Passes for "+str(self.satname)+":\n"+
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
        self.tle.pack(side="left")
        self.tleentry.pack(side="left")
        self.motstart.pack(side="right")
        self.motstop.pack(side="right")
        self.np_l.pack(side="top")
        self.np_button.pack(side="top")

##############################################################################################
# Motor Control Code
    def motorCall(self):
        ''' Turn on or turn off motor depending what state it is in. '''
        if self.motorOn:
            self.stopMotor()
        else:
            self.startMotor()
    
    def startMotor(self):
        ''' Connect motor. '''
        try:
            self.MotSer = serial.Serial(port=self.motorPath, baudrate=600, bytesize=8, 
                                  parity='N', stopbits=1, timeout=5) #connect serial port
            self.motorOn = True
            self.motstart['text'] = "Disconnect Motor" #set button
            self.motstart['bg'] = "red"
        except: #No motor connected
            print("No Motor Controller connected to:\n"+self.motorPath+"\nAre you root?\n")
        self.status() #Find current status
    
    def stopMotor(self):
        ''' Disconnect motor. '''
        try:
            self.MotSer.close() #Close connection with motor
        except:
            pass #No motor connected
        self.motorOn = False
        self.motstart['text'] = "Connect Motor" #set button
        self.motstart['bg'] = "green"
    
    def status(self):
        """
        Send a command to the controller to request the current azimuth
        and elevation of the rotor. The azimuth and elevation are then set to the 
        current and motor azimuth and elevation.
        """
        if self.motorOn:
            # Create command
            cmd = [b'\x57', b'\x00', b'\x00', b'\x00', b'\x00', b'\x00', b'\x00', b'\x00',
                                           b'\x00', b'\x00', b'\x00', b'\x1f', b'\x20']
            packet = b"".join(cmd) #join into string
            self.MotSer.write(packet) #Write to serial connection
            self.MotSer.flush() #Flush through

            rec_packet = self.MotSer.read(12) #Received packet
            az = (rec_packet[1] * 100) + (rec_packet[2] * 10) + \
                   rec_packet[3] + (rec_packet[4] / 10) - 360.0
            el = (rec_packet[6] * 100) + (rec_packet[7] * 10) + \
                   rec_packet[8] + (rec_packet[9] / 10) - 360.0
            ph = rec_packet[5]
            pv = rec_packet[10]

            assert(ph == pv) #Asert pulses are equal
            self.pulse = ph
            if self.debug:
                print("STATUS COMMAND SENT")
                print("Sent: " + str(packet))
                print("Azimuth:   " + str(az))
                print("Elevation: " + str(el))
                print("PH: " + str(ph))
                print("PV: " + str(pv) + "\n")
            self.currentAz, self.currentEl = az, el #set az/el's
            self.motorAz, self.motorEl = az, el
    
    def stop(self):
        """
        Send a stop command to the controller, which causes the rotor to stop moving and
        return the current azimuth, elevation and pulse of the rotor where it stopped. The
        azimuth and elevation are set to the current and motor values.
        """
        if self.motorOn:
            # Create command
            cmd = [b'\x57', b'\x00', b'\x00', b'\x00', b'\x00', b'\x00', b'\x00', b'\x00',
                                           b'\x00', b'\x00', b'\x00', b'\x0f', b'\x20']
            packet = b"".join(cmd) #Join into single string
            self.MotSer.write(packet) #Write to serial connection
            self.MotSer.flush() #Flush through

            rec_packet = self.MotSer.read(12) #Received packet
            az = (rec_packet[1] * 100) + (rec_packet[2] * 10) + \
                   rec_packet[3] + (rec_packet[4] / 10) - 360.0
            el = (rec_packet[6] * 100) + (rec_packet[7] * 10) + \
                   rec_packet[8] + (rec_packet[9] / 10) - 360.0
            ph = rec_packet[5]
            pv = rec_packet[10]

            assert(ph == pv) #Assert pulses are equal
            self.pulse = ph
            
            if self.debug:
                print("STOP COMMAND SENT")
                print("Azimuth:   " + str(az))
                print("Elevation: " + str(el))
                print("PH: " + str(ph))
                print("PV: " + str(pv) + "\n")
            self.currentAz, self.currentEl = az, el #Set az/el's
            self.motorAz, self.motorEl = az, el
    
    def set(self):
        """
        Send a set command to the controller, which causes the rotor to adjust its position
        to the azimuth and elevation specified by the motor azimuth and elivation parameters.
        """
        if self.motorOn:
            az1 = self.motorAz
            el1 = self.motorEl
            assert(float(az1) <= self.maxAz) #Ensure az and el values are in correct range
            assert(float(az1) >= self.minAz)
            assert(float(el1) <= self.maxEl)
            assert(float(el1) >= self.minEl)

            # Create command
            az = "0" + str(int(self.pulse * (float(az1) + 360)))
            el = "0" + str(int(self.pulse * (float(el1) + 360)))
            cmd = [b'\x57', az[-4].encode(), az[-3].encode(), az[-2].encode(), az[-1].encode(), 
                   chr(self.pulse).encode(), el[-4].encode(), el[-3].encode(), el[-2].encode(), 
                   el[-1].encode(), chr(self.pulse).encode(), b'\x2f', b'\x20']
            packet = b"".join(cmd)

            self.MotSer.write(packet) #Write to serial connection
            self.MotSer.flush() #Flush through
            if self.debug:
                print("SET COMMAND SENT")
                print("Sent: " + str(packet))
                print("Set Azimuth:   " + str(az1) + " (" + str(az) + ")")
                print("Set Elevation: " + str(el1) + " (" + str(el) + ")")
                print("Pulse: " + chr(self.pulse) + "\n")
    
##############################################################################################
# Define functions for finding ground station location from GPS and QTH
    def startGPS(self):
        ''' Starts a thread to find GPS data. '''
        threading.Thread(target=self.findLocationGPS).start()
    
    def findLocationGPS(self):
        ''' Finds GPS location using serial communication. '''
        try:
            self.GPSser = serial.Serial(self.GPSPath, '4800', timeout=5) #Connect GPS
        except:
            print("No GPS connected to:\n"+self.GPSPath+"\nAre you root?\n")
            self.locMode.set(1) #Return to QTH mode
            return
        # Initialize
        num = 0
        alt = []
        lon = []
        lat = []
        while num < 1: #Number here determines number of measurments to average
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
            if splitline[0] == b'$GPGGA': #Correct GPS format
                latDir = splitline[3].decode('ASCII') #Latitude direction
                latTemp = splitline[2].decode('ASCII') #Latitude value (deg min.mindecimal)
                # Example: 4001.36 is 40 degrees, 1.36 minutes
                ind = latTemp.index(".")
                latTemp = float(latTemp[:ind-2]) + float(latTemp[ind-2:])/60 #Convert to decimal
                if latDir == "N": #Determine sign based on direction
                    lat.append(latTemp)
                elif latDir == "S":
                    lat.append(-latTemp)
                else: #This shouldn't happen
                    print("Latitude not North or South.\n")
                    self.locMode.set(1)
                    return
                
                longDir = splitline[5].decode('ASCII') #Longitude direction
                lonTemp = splitline[4].decode('ASCII') #Latitude value (deg min.mindecimal)
                ind = lonTemp.index(".")
                lonTemp = float(lonTemp[:ind-2]) + float(lonTemp[ind-2:])/60 #Convert to decimal
                if longDir == "E": #Determine sign based on direction
                    lon.append(lonTemp)
                elif longDir == "W":
                    lon.append(-lonTemp)
                else: #This shouldn't happen
                    print("Longitude not East or West.\n")
                    self.locMode.set(1)
                    return
                
                altUnit = splitline[10].decode('ASCII') #Altutide unit (Should be meters)
                assert altUnit == "M"
                alt.append(float(splitline[9].decode('ASCII'))) #Altitude value
                num += 1

        self.lat = np.mean(lat)
        self.lon = -np.mean(lon) #Flip for program
        self.alt = np.mean(alt)
        # Set labels
        self.latlabel['text'] = "Latitude: %3.2f" % self.lat + self.degree_sign
        self.lonlabel['text'] = "Longitude: %3.2f" % self.lon + self.degree_sign
        self.altlabel['text'] = "Altitude: %3.2f" % self.alt + "m"
        self.GPSser.close() #Close connection to GPS

    def findLocationQTH(self):
        ''' Finds ground station location using qth file. '''
        qth = self.load_qth(self.qthloc.get()) #Loat data from qth file
        self.lat = qth[0]
        self.lon = qth[1]
        self.alt = qth[2]
        try:
            #Set label values
            self.latlabel['text'] = "Latitude: %3.2f" % self.lat + self.degree_sign
            self.lonlabel['text'] = "Longitude: %3.2f" % self.lon + self.degree_sign
            self.altlabel['text'] = "Altitude: %3.2f" % self.alt + "m"
        except:
            pass #happens when initially setting up GUI - labels aren't built yet
        
##############################################################################################
# Define Functions for azimuth and elevation plotting
    def azelmotcall(self):
        """ Function to Calculate desired position and call function to set parameters
        on the motor conroller and therefore motor. """
        i = 0 # For plotting (only plots every 5 new values translating to about 1Hz)
        tlefile = str(self.tleloc.get()) #Find tle file
        while self.azelplotflag: #While plotting is active
            az, el, self.satname = self.azel_points(tlefile) #Find az, el, and satname
            
            # If in program track mode AND if norm of difference from current motor values
            # is greater than 0.3 degrees. If this is not here it will oscillate and move
            # very choppy so it is better to only send commands when there are big changes.
            if self.progflag and np.sqrt((az-self.motorAz)**2+(el-self.motorEl)**2) >= 0.3:
                if el<self.minEl: #Ensure elevation is greater than or equal to minimum value
                    el = self.minEl
                
                # Define cost for four different possible values of azimuth and elevation
                # all representing the same pointing location. This ensures that we find
                # the values that require the least motion to get to.
                azvec = []
                azvec.append(az)
                elvec = []
                elvec.append(el)
                if az>180: #if the value is 180-360 the values are all underneath
                    azvec.append(az-180)
                    elvec.append(180-el)
                    azvec.append(az-360)
                    elvec.append(el)
                    azvec.append(az-540)
                    elvec.append(180-el)
                else: #if the value is 0-180 two values are under and one is above
                    azvec.append(az+180)
                    elvec.append(180-el)
                    azvec.append(az-180)
                    elvec.append(180-el)
                    azvec.append(az-360)
                    elvec.append(el)
                # Create cost vector
                cost = []
                cost.append((azvec[0]-self.currentAz)**2+(elvec[0]-self.currentEl)**2)
                cost.append((azvec[1]-self.currentAz)**2+(elvec[1]-self.currentEl)**2)
                cost.append((azvec[2]-self.currentAz)**2+(elvec[2]-self.currentEl)**2)
                cost.append((azvec[3]-self.currentAz)**2+(elvec[3]-self.currentEl)**2)
                ind = cost.index(min(cost)) #Find closest representation of location
                az = azvec[ind] # Azimuth of closest location
                el = elvec[ind] # Elevation of closest location
                self.currentAz, self.currentEl = az, el # Set to current az/el
                
                # If norm of difference between motor location and desired location is less than
                # two degrees AND elevation change is greater than 0.1 degrees,
                # THEN double the change of motor location so that on average the location 
                # of the motors is directly on the location of the satellite.
                # If change is bigger than two it is most likely moving to its initial 
                # location so doubling the change would be a bad thing. If the elevation change
                # is less than 0.1 then it is most likely at the peak of the pass and it will
                # Oscillate around the value.
                if np.sqrt((az-self.motorAz)**2+(el-self.motorEl)**2)<=2 and el-self.motorEl>=0.1:
                        self.motorAz = (az-self.motorAz)*1 + az
                        self.motorEl = (el-self.motorEl)*1 + el
                else: #Otherwise just go to satellite location
                    self.motorAz, self.motorEl = self.currentAz, self.currentEl
                # Start thread to send command to set motor position. This is done with a thread
                # To speed up this thread of finding locations.
                threading.Thread(target=self.set).start()
            if i%5 == 0: #Every fifth value, plot
                self.plotAz, self.plotEl = self.currentAz, self.currentEl
                threading.Thread(target=self.azelplot).start() #Start new process to plot
            i += 1 #increment plotting counter
            #Sleep so that commands can only be sent at minimum every 0.2 seconds.
            time.sleep(self.motWaitTime) 
    
    def azelplot(self):
        ''' Function to plot azimuth and elevation on GUI. '''
        self.ax.cla() #Clear axes
        self.ax.grid(True)
        self.ax.set_rlim(90, 0, 1)
        self.ax.set_yticks(np.arange(0, 91, 10))
        self.ax.set_yticklabels(self.ax.get_yticks()[::-1])
        self.ax.invert_yaxis() #Have to flip so 90 is in the middle
        self.ax.set_theta_zero_location("N") #Set north directly up
        self.ax.set_theta_direction(-1) #Flip positive direction
        sunAz, sunEl = self.findsun() #Find sun location for plotting
        az, el = self.plotAz, self.plotEl
        self.ax.set_title("Azimuth and Elevation of "+self.satname)
        if el > 90: #if el direction has flipped, switch to 0-90 for plotting
            plotel = 180-el
            plotaz = az+180
        elif el <= 0: #Make satellite not visible on plot if at zero
            plotel = -10
            plotaz = az
        else:
            plotel=el
            plotaz=az
        # Plot values
        self.ax.scatter(plotaz*np.pi/180, 90-plotel, marker='o', color='blue', label=self.satname)
        self.ax.scatter(sunAz*np.pi/180, 90-sunEl, marker='o', color='orange', label='Sun')
        self.ax.legend()
        self.graph.draw() #CAUSES ISSUES IN MATPLOTLIB
    
    def azel_handler(self):
        """ Function to Spawn Azimuth and Elevation process, switch state. """
        if self.azelplotflag == False:
            self.azelplotflag = True
            self.b1.configure(text="Stop Tracking", bg="red", fg='black') #configure button
            threading.Thread(target=self.azelmotcall).start() #Start new process to plot
        else:
            self.azelplotflag = False
            self.b1.configure(text="Start Tracking", bg="green", fg='black') #configure button
        
    def azel_points(self, tlefile):
        """ Function to Produce Azimuth and Elevation using Predict. """
        qth = (self.lat, self.lon, self.alt) #Ground station location
        tle, satname = self.load_tle(tlefile) #Satellite tle file
        data = observe(tle, qth) #find current state
        return data['azimuth'], data['elevation'], satname
    
##############################################################################################
# Define Functions to set the azimuth and elevation along with the labels
    def set_azel_label(self):
        """ Function to set Azimuth and Elevation Label on GUI. """
        self.azellabel['text'] = "Current Azimuth: %3.2f, Current Elevation: %3.2f" % \
                                         (self.currentAz, self.currentEl) #Set label text
        self.root.after(1, self.set_azel_label) # Call every second
    
    def set_azel(self):
        """ Function to set azimuth and elevation from input. """
        if self.manflag: #If in manual mode
            azinput_val = float(str(self.azinput.get())) # Get azimuth input value
            elinput_val = float(str(self.elinput.get())) # Get elevation input value
            #Ensure values are in desired range
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
            self.motorAz, self.motorEl = self.currentAz, self.currentEl
            # Set values and send command to motor controller
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
        self.azinput.set(str(0)) #Set inputs to zero 
        self.elinput.set(str(0))
        # Move ground station to (0,0)
        self.currentAz = 0
        self.currentEl = 0
        self.set()
    
##############################################################################################
# Define Functions to load tle and qth files
    def load_qth(self, qthfile):
        """ Function to Load latitude, longitude, elevation from given file. """
        try:
            with open(qthfile, 'r') as myfile: #Try reading file
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
            with open(tlefile, 'r') as myfile: # Try reading file
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
        observer = ephem.Observer() #Find sun observer and set values
        observer.lat = intdeg2dms(qth[0])
        observer.lon = intdeg2dms(-qth[1])
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
        print("Done. SET AZ and EL on Controller!\n")
    
##############################################################################################
# Define Functions for finding sun
    def findsun(self):
        """ Function to find the Sun for plotting. """
        qth = (self.lat, self.lon, self.alt)
        observer = ephem.Observer() # Create observer and set values
        observer.lat = intdeg2dms(qth[0])
        observer.lon = intdeg2dms(-qth[1])
        observer.elevation = qth[2]
        sun = ephem.Sun() # Find sun
        sun.compute(observer)
        sunAz, sunEl = sun.az*180/np.pi, sun.alt*180/np.pi
        return sunAz, sunEl
        
    def recalculate(self):
        """ Function to recalculate future passes if new TLE loaded. """
        starttime, endtime, startaz, endaz, maxel, self.satname = \
                 self.nextpass(str(self.tleloc.get())) #Find upcoming passes
        # Configure label
        self.np_l.configure(text = \
                "Upcoming Passes for "+str(self.satname)+":\n"+
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
            self.motorEl = self.currentEl
            self.set()

    def decrease_elevation(self):
        """ Function to decrease elevation by step size. """
        if self.manflag:
            if self.currentEl-self.step >= self.minEl:
                self.currentEl = self.currentEl - self.step
            else:
                self.currentEl = self.minEl
            self.motorEl = self.currentEl
            self.set()
            
    def increase_azimuth(self):
        """ Function to increase azimuth by step size. """
        if self.manflag:
            if self.currentAz + self.step >= self.maxAz:
                self.currentAz = self.currentAz + self.step - 360
            else:
                self.currentAz = self.currentAz + self.step
            self.motorAz = self.currentAz
            self.set()

    def decrease_azimuth(self):
        """ Function to decrease azimuth by step size. """
        if self.manflag:
            if self.currentAz-self.step < self.minAz:
                self.currentAz = self.currentAz - self.step + 360
            else:
                self.currentAz = self.currentAz - self.step
            self.motorAz = self.currentAz
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
def intdeg2dms(deg):
    """ Function to convert integer to degrees, minutes, and seconds. """
    d = int(deg) #degrees
    md = abs(deg - d) * 60 #minutes with decimal
    m = int(md) #minutes
    sd = (md - m) * 60 #seconds
    return '%d:%d:%f' % (d, m, sd)

##############################################################################################
# Functions and class adapted from predict.py by Jesse Trutna
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
