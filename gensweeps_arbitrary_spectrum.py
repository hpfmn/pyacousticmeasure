import scipy.signal
import numpy as np
from numpy.fft import ifft, ifftshift, fftshift, irfft

def nextpow2(m):
	return 2**np.ceil(np.log2(m))

def find_nearest(array,value):
	idx = (np.abs(array-value)).argmin()
	return idx 

def generate_spectralsweep(fs,samples,tg_start,tg_end,fstart,fstop,specfact):
	print(fs,samples,tg_start,tg_end,fstart,fstop,specfact)
	fs=float(fs)
	#fs=48000
	#samples=int((nextpow2(fs*3)))#3)/2)+1)
	samples=float(samples/2)+1
	delta_f=fs/samples
	#tg_start=0.1#05#2400/fs
	#tg_end=((samples)/fs)/3
	#x=int(20/delta_f)
	#h=(np.ones((samples/2)-10))**2

	t_g=np.zeros(samples)
	t_g[0]=tg_start
	f=np.linspace(0,fs/2,samples)
	#H=f**(-0.5)
	H=np.zeros(len(f))
	start=find_nearest(f,fstart)
	stop=find_nearest(f,fstop)
	#H[start:stop]=np.ones(len(f[start:stop]))
	H[start:stop]=(f[start:stop]/f[start])**(specfact)
	#H[stop:]=np.arange(1,len(H)-stop+1)**(-0.5)


	C=(tg_end-tg_start)/np.sum(np.abs(H)**2)
	B=(tg_end-tg_start)/(np.log2(f[-1]/f[0]))
	A=tg_start-(B*np.log2(tg_start))


	for i in range(int(samples)):
	    t_g[i]=t_g[i-1]+(C*(np.abs(H[i]**2)))
	     
	phi_start=0
	a=np.zeros(samples)
	a[0]=phi_start
	#a[0]=tg_start
	for i in range(1,int(samples)):
		a[i]=a[i-1]-(2*np.pi*delta_f*t_g[i])
	a=a%(2*np.pi)
	a_new=np.zeros(samples)
	for i in range(0,int(samples)):
		a_new[i]=a[i]-((f[i]/(fs/2))*(a[-1]))
		#a=np.linspace(phi_start,phi_start-samples*(2*np.pi*delta_f*t_g), samples)
	Im=np.sin(a_new)
	Re=np.cos(a_new)
	#Re=np.sqrt(1-(Im**2))

	y=H*(Re+1j*Im)

	signal=np.real((irfft(y)))
	signal=signal/max(signal)
	return signal
