#!/usr/bin/env python3

import numpy as np

filename_in = "/home/addodge/test1"
filename_out = "/home/addodge/test2"

# In file
i = 0
bit_in = []
with open(filename_in, "rb") as f:
    temp = f.read(1)
    while temp != b"":
        bit_in.append(temp[0])
        #print(temp)
        i = i+1
        temp = f.read(1)
print("Number in:", i)
bit_in = bit_in[:-18]

# Out file
i = 0
j = 0
bit_out = []
with open(filename_out, "rb") as f:
    temp = f.read(1)
    while temp!=b"":
        if i > 83 and i%8==3:
            bit_out.append(temp[0])
            #print(temp)
            j = j+1
        i = i+1
        temp = f.read(1)
print("Number out:", j)

ind = np.not_equal(bit_in, bit_out)

ne = sum(ind)
tot = len(bit_out)
print("Number not equal:", ne)
print("Total bits:", tot)
if ne == 0:
    BER = 0
else:
    BER = ne/tot
print("BER:",BER)
