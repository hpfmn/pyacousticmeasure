# Golay Generation Based on the realsimp Project at the Stanford University
# Source Code can be found at:
#	https://ccrma.stanford.edu/realsimple/imp_meas/golay_response.m
#	https://ccrma.stanford.edu/realsimple/imp_meas/generate_golay.m
import numpy as np
def generate_golay(N):
	""" Generate the Golay codes a and b with length 2**N """
	# These initial a and b values are Golay
	a = np.array([1, 1])
	b = np.array([1, -1])

	# Iterate to create a longer Golay sequence
	while N>1:
		olda = a
		oldb = b
		a = np.concatenate((olda, oldb))
		b = np.concatenate((olda, -1*oldb))

		N -= 1

	return a, b

from scipy.signal import fftconvolve
import numpy as np
def golayIR(respa, respb, a, b):
	# Comptute impulse response h for Signle Channel answers a and b
	L = len(a)
	h = np.array(np.zeros(respa.shape))
	h = fftconvolve(a[-1::-1],respa,mode='same')+fftconvolve(b[-1::-1], respb,mode='same')
	h = h / (2*L)
	return h
