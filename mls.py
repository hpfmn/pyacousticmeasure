# Generate MLS

import numpy as np
from numpy.random import rand

# Taps from Table 1 in JOHN VANDERKOOY: Aspects of MLS Measuring Systems

tap1=range(2,33)
tap2=[1,1,1,2,1,1,6,4,7,2,11,4,13,14,5,3,7,6,3,2,1,5,4,3,8,8,3,2,16,3,28]
tap3=[0,0,0,0,0,0,5,0,0,0,10,3,12, 0,3,0,0,5,0,0,0,0,3,0,7,7,0,0,15,0,27]
tap4=[0,0,0,0,0,0,1,0,0,0, 2,1, 2, 0,2,0,0,1,0,0,0,0,1,0,1,1,0,0, 1,0, 1]

def generate_mls(n,flag):
	# Initilize buffer
	if flag == 1:
		abuff = np.ones(n,dtype=np.int32)
	else:
		while True:
			abuff = np.array(np.round(rand(n)),dtype=np.int32)
			# be shure not all bits are zero
			if 1 in abuff:
				break
	# initilize output
	y=np.zeros(2**n-1,dtype=np.int32)
	# shift register loop
	for i in range(1,int((2**n))):
		xorbit = abuff[tap1[n-2]-1]^abuff[tap2[n-2]-1]

		if (tap3[n-2]+tap4[n-2])>0:
			xorbit2 = xorbit^abuff[tap3[n-2]-1]
			xorbit3 = xorbit2^abuff[tap4[n-2]-1]
			abuff=np.insert(abuff,0,xorbit3)
		else:
			abuff=np.insert(abuff,0,xorbit)
		y[i-1]=int((-2*abuff[-1])+1)
		abuff=np.delete(abuff,-1)
	return y

