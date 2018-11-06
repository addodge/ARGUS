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
  - matplotlib
  - random
  - ephem

### Setup:

```
sudo python setup.py install 
cp build/lib.*string relating to operating system*/cpredict.*string relating to operating system*.so .
mv cpredict.*string relating to operating system*.so cpredict.so
```
__Note:__ change `*string relating to operating system*` to the actual directory/file names in your folder.

### Usage:

```./argus.py```

__Note:__ python3 must be in /usr/bin/python3.

__Note 2:__ QTH file in Location Name, Latitude (N), Longitude (E), Elevation (meters) format

__Note 3:__ TLE in following format:
```
ISS
1 25544U 98067A   04236.56031392  .00020137  00000-0  16538-3 0  9993
2 25544  51.6335 344.7760 0007976 126.2523 325.9359 15.70406856328906
```

### Acknowledgements:
predict.py, setup.py, and predict.c adapted from PyPredict (https://github.com/nsat/pypredict)
