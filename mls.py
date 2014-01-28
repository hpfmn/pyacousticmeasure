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
		abuff = np.ones(n,dtype=np.int8)
	else:
		while True:
			abuff = np.array(np.round(rand(n)),dtype=np.int32)
			# be shure not all bits are zero
			if 1 in abuff:
				break
	# initilize output
	y=np.zeros(2**n-1,dtype=np.int8)
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


def generateIR_MLS(signal, mls, N):
	P=(2**N)-1
	tagS=generatetagS(mls,P,N)
	tagL=generatetagL(mls,P,N,tagS)
	sigshape=np.shape(signal)
	resp=np.zeros(sigshape)
	for i in range(0,sigshape[0]):
		perm=PermuteSignal(signal,TagS,P)
		had=FastHadamard(perm,P+1,N)
		resp[i,:]=PermuteResponse(had,tagL,P)
	return resp

def generatetagS(mls,P,N):
	# Convert [-1,1] to binary
	binmls=(mls-1)/(-2)

	powerindices=np.arange(N-1,-1,-1)
	powers=2**powerindices

	S=np.matrix(np.zeros(N,P))
	# Make S matrix by right shift mls every subsequent row up to N
	for i in range(0,N):
		S[i,0:i]=binmls[P-i:P]
		S[i,i:P]=binmls[0:P-i]
	return np.array(powers*S)


def generatetagL(mls,P,N,S):
	# Convert [-1,1] to binary
	binmls=(mls-1)/(-2)

	index=np.zeros(N)
	for i in range(0,P):
		for j in range(0,N):
			if (S[i]==(2**j)):
				index[j]=i
	powerindices=np.arange(0,N)
	powers=2**powerindices
	
	L=np.matix(np.zeros((N,P)))
	for i in range(0,N):
		L[i, 0:(index[i]%P)]=binmls(((index[i]%P)-1)::-1)
		L[i, (index[i]%P):P]=binmls((P-1):((index[i]%P)-1):-1)
	return np.array(powers*L)


def PermuteSignal(signal,tagS,P):
	perm=np.zeros(P+1)
	perm[0]=0
	perm[1:]=signal[tagS]
	return perm

def PermuteResponse(perm,tagL,P):
	fact = 1/(P+1)
	perm=perm[1:]
	resp=perm[tagL]*fact
	resp[P+1]=0

def FastHadamard(x,P1,N)
	k1=P1
	for k in range(0,N):
		k2=k1/2
		for j in range(0,k2):
			for i in range(j,P1,k1):
				i1=i+k2
				temp=x[i]+x[i1]
				x[i1]=x[i]-x[i1]
				x[i]=temp
		k1=k1/2
	return x
