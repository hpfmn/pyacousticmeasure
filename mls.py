# Generate MLS

import numpy as np
from numpy.random import rand

def generate_mls(n,flag):
	# Initilize buffer
	if flag == 1:
		abuff = np.ones(1,n)
	else:
		np.rand(1,n)
		while True:
			abuff = np.round(rand(1,n))
			# be shure not all bits are zero
			if 1 in abuff:
				break
	# initilize output
	y=np.zeros(2**n-1)
	# shift register loop
	for i in range((0,int((2**n)-1)):
		xorbit = abuff[tap1]^abuff[tap2]

		if taps==4:
			xorbit2 = xorbit^abuff[tap3]
			xorbit3 = xorbit2^abuff[tap4]
			abuff=np.insert(abuff,xorbit3,0)
		else:
			abuff=np.insert(abuff,xorbit,0)
		y[i]=abuff[-1]
		abuff=np.delete(abuff,-1)


