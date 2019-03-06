#!/usr/bin/env python3
import matplotlib.pyplot as plt
import numpy as np

figname = '82degPass_5smid.png'

fMOT = "mot_t_az_el.txt"
fCOMM = "comm_t_az_el.txt"
fspeed = "speed.txt"
timeM, timeC, timeS, azM, azC, elM, elC, speed = ([] for i in range(8))
with open(fMOT, 'r') as f:
    for line in f:
        data = [x.strip() for x in line.split(' ')]
        timeM.append(float(data[0]))
        azM.append(float(data[1]))
        elM.append(float(data[2]))
with open(fCOMM, 'r') as f:
    for line in f:
        data = [x.strip() for x in line.split(' ')]
        timeC.append(float(data[0]))
        azC.append(float(data[1]))
        elC.append(float(data[2]))
with open(fspeed,'r') as f:
    for line in f:
        data = [x.strip() for x in line.split(' ')]
        timeS.append(float(data[0]))
        speed.append(float(data[1]))
speed, timeS = speed[1:], timeS[1:]

t = timeM[0]
timeM = [x - t for x in timeM]
timeC = [x - t for x in timeC]
timeS = [x - t for x in timeS]
if figname[-5:] == 's.png':
    sec = int(figname[-7:-5])
    indM = [n for n, i in enumerate(timeM) if i<sec ]
    indC = [n for n, i in enumerate(timeC) if i<sec ]
    indS = [n for n, i in enumerate(timeS) if i<sec ]
    timeM = [timeM[i] for i in indM]
    timeC = [timeC[i] for i in indC]
    timeS = [timeS[i] for i in indS]
    azM = [azM[i] for i in indM]
    azC = [azC[i] for i in indC]
    speed = [speed[i] for i in indS]
    elM = [elM[i] for i in indM]
    elC = [elC[i] for i in indC]

elif figname[-7:] == 'mid.png':
    sec1 = 305
    sec2 = 310
    indM = [n for n, i in enumerate(timeM) if i<sec2 and i>sec1]
    indC = [n for n, i in enumerate(timeC) if i<sec2 and i>sec1]
    indS = [n for n, i in enumerate(timeS) if i<sec2 and i>sec1]
    timeM = [timeM[i] for i in indM]
    timeC = [timeC[i] for i in indC]
    timeS = [timeS[i] for i in indS]
    azM = [azM[i] for i in indM]
    azC = [azC[i] for i in indC]
    speed = [speed[i] for i in indS]
    elM = [elM[i] for i in indM]
    elC = [elC[i] for i in indC]


indsp = [n for n, i in enumerate(speed) if i<50]
speed = [speed[i] for i in indsp]
timeS = [timeS[i] for i in indsp]

fig, axs = plt.subplots(3, 1, sharex=True)
axs[0].plot(timeC, elC, 'b', label="Commanded")
axs[0].step(timeM, elM, 'rd', where='post', label="Motor")
axs[0].set_ylabel("Elevation above horizon [deg]")
axs[0].legend()

axs[1].plot(timeC, azC, 'b', label="Commanded")
axs[1].step(timeM, azM, 'rd', where='post', label="Motor")
axs[1].set_ylabel("Azimuth [deg]")
axs[1].legend()

axs[2].plot(timeS, speed, 'b')
axs[2].set_ylabel("Required Motor Speed [deg/s]")
axs[2].set_xlabel("Seconds after beginning of pass")

fig.suptitle('Simulated Pass Data')
plt.savefig(figname)
