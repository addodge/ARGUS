#!/usr/bin/env python3

import numpy as np

filename_in = "/home/addodge/ARGUS/SDRSDRTest/transmitted.bin"
filename_out = "/home/addodge/ARGUS/SDRSDRTest/received.bin"

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
#bit_in = bit_in[:-18]

# Out file
i = 0
j = 0
bit_out = []
with open(filename_out, "rb") as f:
    temp = f.read(1)
    while temp!=b"":
        #if i > 83 and i%8==3:
        bit_out.append(temp[0])
            #print(temp)
        j = j+1
        i = i+1
        temp = f.read(1)
print("Number out:", j)

bit_in = "".join([bin(x)[2:].zfill(8) for x in bit_in])
bit_out = "".join([str(x) for x in bit_out])

print(len(bit_in), len(bit_out))

index = bit_out.find(bit_in[:100])
print(index)

#print(bit_in)
#print(bit_out)
#ind = np.not_equal(bit_in, bit_out)

#ne = sum(ind)
#tot = len(bit_out)
#print("Number not equal:", ne)
#print("Total bits:", tot)
#if ne == 0:
#    BER = 0
#else:
#    BER = ne/tot
#print("BER:",BER)
