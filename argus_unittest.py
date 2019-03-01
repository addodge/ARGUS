#!/usr/bin/env python3
##############################################################################################
# Adam Dodge
# ARGUS Ground Station GUI Unit Testing
# Date Created: 2.26/2019
# Date Modified: 
##############################################################################################
# Description / Notes:

# This file is a unit testing file for the ARGUS graphical user interface, tracking, and motor
# control code. 

##############################################################################################
### Necessary Modules
import unittest, time
from argusUtils import *
import numpy as np

##############################################################################################
class argusTestCase(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        pass

    @classmethod
    def tearDownClass(cls):
        pass

    def setUp(self):
        self.gui = GUI()

    def tearDown(self):
        self.gui.root.destroy()

    def test_init(self):
        self.assertEqual(self.gui.currentAz, 0, "Initial Azimuth is not Zero")
        self.assertEqual(self.gui.currentEl, 0, "Initial Elevation is not Zero")
    
    def test_motorCall(self):
        motorOn = self.gui.motorOn
        self.gui.motorCall()
        self.assertNotEqual(self.gui.motorOn, motorOn, 
                "Motor Call function does not change state. Is motor connected?")
    
    def test_setANDstatus(self):
        #time.sleep(5)
        self.gui.stopMotor()
        self.assertEqual(self.gui.motstart['bg'], 'green')
        self.gui.startMotor()
        self.assertEqual(self.gui.motstart['bg'], 'red')
        self.gui.currentAz = self.gui.currentAz + 2
        self.gui.currentEl = self.gui.currentEl + 3
        az, el = self.gui.currentAz, self.gui.currentEl
        self.gui.set()
        time.sleep(10)
        self.gui.status()
        time.sleep(1)
        self.gui.status()
        #time.sleep(5)
        self.assertTrue(np.abs(self.gui.currentAz-az) <= 0.3)
        self.assertTrue(np.abs(self.gui.currentEl-el) <= 0.3)
    
    def test_stop(self):
        self.gui.stopMotor()
        self.assertEqual(self.gui.motstart['bg'], 'green')
        self.gui.startMotor()
        self.assertEqual(self.gui.motstart['bg'], 'red')
        self.gui.currentAz = self.gui.currentAz + 50
        self.gui.currentEl = self.gui.currentEl + 20
        az, el = self.gui.currentAz, self.gui.currentEl
        self.gui.set()
        self.gui.stop()
        self.assertNotEqual(az, self.gui.currentAz)
        self.assertNotEqual(el, self.gui.currentEl)
        
    def test_gps(self):
        self.gui.findLocationGPS()
        self.assertEqual(self.gui.locMode.get(), 0)
        
    def test_QTH(self):
        with open('ARGUS.qth','w') as f:
            f.write("Narnia\n30.369\n96.542\n801")
        self.gui.findLocationQTH()
        self.assertEqual(self.gui.lat, 30.369)
        self.assertEqual(self.gui.lon, -96.542)
        self.assertEqual(self.gui.alt, 801)
        with open('ARGUS.qth','w') as f:
            f.write("Boulder\n40.015\n-105.27\n1624")
        self.gui.findLocationQTH()
        self.assertEqual(self.gui.lat, 40.015)
        self.assertEqual(self.gui.lon, 105.27)
        self.assertEqual(self.gui.alt, 1624)
        
    def test_setAzElLabel(self):
        self.gui.currentAz = 50
        self.gui.currentEl = 60
        self.gui.set_azel_label()
        self.assertEqual(self.gui.azellabel['text'], 
                            "Current Azimuth: 50.00, Current Elevation: 60.00")
        
    def test_setAzEl(self):
        # Basic
        self.gui.azinput.set(30)
        self.gui.elinput.set(50)
        self.gui.set_azel()
        self.assertEqual(self.gui.currentAz, 30)
        self.assertEqual(self.gui.currentEl, 50)
        
        # Az too high, El too high
        self.gui.azinput.set(930)
        self.gui.elinput.set(200)
        self.gui.set_azel()
        self.assertEqual(self.gui.currentAz, 210)
        self.assertEqual(self.gui.currentEl, 180)
        
        # Az too low, El too low
        self.gui.azinput.set(-400)
        self.gui.elinput.set(-40)
        self.gui.set_azel()
        self.assertEqual(self.gui.currentAz, -40)
        self.assertEqual(self.gui.currentEl, 0)
        
    def test_goProgram(self):
        self.gui.go_program()
        self.assertEqual(self.gui.progflag, True)
        self.assertEqual(self.gui.manflag, False)
    
    def test_goManual(self):
        self.gui.go_manual()
        self.assertEqual(self.gui.progflag, False)
        self.assertEqual(self.gui.manflag, True)
        self.assertEqual(self.gui.currentAz, 0)
        self.assertEqual(self.gui.currentEl, 0)
        
    def test_loadTLE(self):
        with open('test.tle', 'w') as f:
            f.write('MTI\n1 26102U 00014A   18335.92389211 +.00003214 +00000-0 +56025-4 0  9993\n2 26102 097.5707 178.9696 0010150 129.3477 230.8676 15.51507910037022')
        tle, satname = self.gui.load_tle('test.tle')
        self.assertEqual(satname, "MTI")
        self.assertEqual(tle[0], "MTI")
        self.assertEqual(tle[1], 
            "1 26102U 00014A   18335.92389211 +.00003214 +00000-0 +56025-4 0  9993")
        self.assertEqual(tle[2], 
            "2 26102 097.5707 178.9696 0010150 129.3477 230.8676 15.51507910037022")
        
    def test_calibrate(self):
        az, el = self.gui.currentAz, self.gui.currentEl
        self.gui.call_calibrate()
        self.assertNotEqual(az, self.gui.currentAz)
        self.assertNotEqual(el, self.gui.currentEl)
    
    def test_findsun(self):
        sunAz, sunEl = self.gui.findsun()
        self.assertTrue(sunAz >= 0 and sunAz <= 360)
        self.assertTrue(sunEl >= 0 and sunEl <= 90)
    
    def test_recalculate(self):
        txt = self.gui.np_l['text']
        self.gui.recalculate()
        assert(txt == self.gui.np_l['text'])
    
    def test_nextpass(self):
        with open('test.tle', 'w') as f:
            f.write('MTI\n1 26102U 00014A   18335.92389211 +.00003214 +00000-0 +56025-4 0  9993\n2 26102 097.5707 178.9696 0010150 129.3477 230.8676 15.51507910037022')
        starttime, endtime, startaz, endaz, maxel, satname = self.gui.nextpass("test.tle")
        
        time.mktime(time.strptime(starttime[0], "%a %b %d %H:%M:%S %Y"))
        
        self.assertTrue(time.mktime(time.strptime(starttime[0], "%a %b %d %H:%M:%S %Y")) 
                > time.time() and time.mktime(time.strptime(endtime[0], "%a %b %d %H:%M:%S %Y"))
                > time.mktime(time.strptime(starttime[0], "%a %b %d %H:%M:%S %Y")))
        self.assertTrue(startaz[0] >= 0 and startaz[0] <= 360)
        self.assertTrue(maxel[0] >= 0 and maxel[0] <= 90)
        
        self.assertTrue(time.mktime(time.strptime(starttime[1], "%a %b %d %H:%M:%S %Y"))
                > time.mktime(time.strptime(endtime[0], "%a %b %d %H:%M:%S %Y")) and
                  time.mktime(time.strptime(endtime[1], "%a %b %d %H:%M:%S %Y")) > 
                  time.mktime(time.strptime(starttime[1], "%a %b %d %H:%M:%S %Y")))
        self.assertTrue(startaz[1] >= 0 and startaz[1] <= 360)
        self.assertTrue(maxel[1] >= 0 and maxel[1] <= 90)
        
        self.assertTrue(time.mktime(time.strptime(starttime[2], "%a %b %d %H:%M:%S %Y")) >
                 time.mktime(time.strptime(endtime[1], "%a %b %d %H:%M:%S %Y")) and 
                 time.mktime(time.strptime(endtime[2], "%a %b %d %H:%M:%S %Y")) > 
                 time.mktime(time.strptime(starttime[2], "%a %b %d %H:%M:%S %Y")))
        self.assertTrue(startaz[2] >= 0 and startaz[2] <= 360)
        self.assertTrue(maxel[2] >= 0 and maxel[2] <= 90)
        
    def test_incAz(self):
        self.gui.azinput.set(30)
        self.gui.elinput.set(50)
        self.gui.set_azel()
        az = self.gui.currentAz
        self.gui.increase_azimuth()
        self.assertEqual(self.gui.currentAz, az+self.gui.step)
    
    def test_decAz(self):
        self.gui.azinput.set(30)
        self.gui.elinput.set(50)
        self.gui.set_azel()
        az = self.gui.currentAz
        self.gui.decrease_azimuth()
        self.assertEqual(self.gui.currentAz, az-self.gui.step)
    
    def test_incEl(self):
        self.gui.azinput.set(30)
        self.gui.elinput.set(50)
        self.gui.set_azel()
        el = self.gui.currentEl
        self.gui.increase_elevation()
        self.assertEqual(self.gui.currentEl, el+self.gui.step)
    
    def test_decEl(self):
        self.gui.azinput.set(30)
        self.gui.elinput.set(50)
        self.gui.set_azel()
        el = self.gui.currentEl
        self.gui.decrease_elevation()
        self.assertEqual(self.gui.currentEl, el-self.gui.step)
        
    def test_observe(self):
        with open('test.tle', 'w') as f:
            f.write('MTI\n1 26102U 00014A   18335.92389211 +.00003214 +00000-0 +56025-4 0  9993\n2 26102 097.5707 178.9696 0010150 129.3477 230.8676 15.51507910037022')
        with open('ARGUS.qth','w') as f:
            f.write("Boulder\n40.015\n-105.27\n1624")
        
        tle, _ = self.gui.load_tle('test.tle')
        qth = self.gui.load_qth('ARGUS.qth')
        now = observe(tle, qth)
        self.assertTrue(now['azimuth'] >= 0 and now['azimuth'] <= 360)
        self.assertTrue(now['elevation'] >= -90 and now['elevation'] <= 90)
    
##############################################################################################
# Main: Run Test Cases
if __name__ == '__main__':
    unittest.main()
