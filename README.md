ARGUS
=======

__Senior Projects Ground Station Software__<br />
__University of Colorado, Boulder__<br />
__Smead Department of Aerospace Engineering Sciences__ <br />
<br />
__Team:__ <br />
Adam Dodge, Trevor Barth, Anahid Blaisdell, Geraldine Fuentes,<br />
Thomas Fulton, Adam Hess, Janell Lopez, Diana Mata, <br />
Tyler Murphy, Stuart Penkowsky, Michael Tzimourakas

### Requirements:

  - Python 3
  - numpy
  - tkinter
  - PIL
  - matplotlib==2.2.3
  - ephem

### Setup:

```
sudo python3 setup.py install 
```

### Usage:

```sudo ./argus.py```

__Note:__ Running as root is required to be able to access the GPS and Motor Controller serial port.

__Note 2:__ python3 version must be in /usr/bin/env python3.

__Note 3:__ QTH file in Location Name, Latitude (N), Longitude (E), Elevation (meters) format

__Note 4:__ TLE in following format:
```
ISS
1 25544U 98067A   04236.56031392  .00020137  00000-0  16538-3 0  9993
2 25544  51.6335 344.7760 0007976 126.2523 325.9359 15.70406856328906
```

### Acknowledgements:
predict.py and predict.c adapted from PyPredict (https://github.com/nsat/pypredict)
