#!/usr/bin/env python3
##############################################################################################
# Adam Dodge
# ARGUS Ground Station GUI
# Date Created: 10/24/2018
# Date Modified: 1/22/2019
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
##############################################################################################
### Necessary Modules
from argusUtils import *
import os
##############################################################################################
# Define main function
if __name__ == "__main__":
    argus = GUI()
    argus.set_azel_label()
    argus.root.mainloop()
    try:
        argus.root.destroy()
    except:
        pass
    os._exit(1)
