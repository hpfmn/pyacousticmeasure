# coding=utf8
import numpy as np
import json
import os
import os.path
import gc
import scipy
import scipy.io.wavfile
import pysoundfile
import scipy.signal
import sys
if sys.version_info<(3,0,0):
	import Tkinter as tkinter
	import tkFileDialog as filedialog
	import ttk as ttk
else:
	import tkinter
	import tkinter.filedialog as filedialog
	import tkinter.ttk as ttk
import tkinter.simpledialog as spldlg
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
import matplotlib.mlab
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
import matplotlib.colors
from numpy.fft import fft,ifft,fftshift,ifftshift
from cfgdlg import cfgdlg
from mpl_toolkits.mplot3d import Axes3D

def find_neares(array,value):
	idx = (np.abs(array-value)).argmin()
	return idx

cc = matplotlib.colors.ColorConverter()

def butter_bandpass(lowcut, highcut, fs, order=5):
    nyq = 0.5 * fs
    low = lowcut / nyq
    high = highcut / nyq
    b, a = scipy.signal.butter(order, [low, high], btype='band')
    return b, a

def butter_bandpass_filter(data, lowcut, highcut, fs, order=5):
    b, a = butter_bandpass(lowcut, highcut, fs, order=order)
    y = scipy.signal.lfilter(b, a, data)
    #y = scipy.signal.filtfilt(b, a, data,padlen=150)
    return y

def nextpow2(i):
	return 2**np.ceil(np.log2(i))

class EVA_GUI:
	def __init__(self, parent):
		self.plotdata_dict={'wvplot': self.wvplot, 'psd': self.psdplot, 'spec': self.specplot, 'angle': self.angleplot, 'groupdelay': self.gd_plot, 'polar': self.polarplot,'welchpsd':self.welchplot, 'surf3d':self.surf3dplot,'surf2d': self.surf2dplot}
		self.plotcfg_dict={'spec': self.specplotcfg, 'polar': self.polarplotcfg,'wvplot':self.wvplotcfg,'welchpsd':self.welchplotcfg}

		self.specplotvalues={'NFFT': 256,'window':'hann','noverlap':128,'Logarithmisch':0}
		self.welchplotvalues={'NFFT': 256,'window':'boxcar','noverlap':128,'padto':256}
		self.polarplotvalues={'Radius in Grad': 360,'Frequenz': 1000}
		self.wvplotvalues={'Linienart': '-','Zeichenmodus': 'default','Filter':0,'Startfrequenz':50,'Endfrequenz':20000,'Filterordnung':5}

		self.myParent = parent
		self.pany=ttk.PanedWindow(parent,orient=tkinter.VERTICAL)
		self.pany.pack(fill=tkinter.BOTH,expand=1)
		#self.pany.grid(row=0,column=0)
		self.panx=ttk.PanedWindow(self.pany,orient=tkinter.HORIZONTAL)
		self.filesframe = ttk.Frame(self.pany)

		self.pany.add(self.filesframe)
		self.pany.add(self.panx)
		#self.filesframe.grid(row=0, column=0, columnspan=2, sticky=(tkinter.N, tkinter.S, tkinter.E, tkinter.W))
		self.filesframe.columnconfigure(0, weight=1)
		self.filesframe.columnconfigure(1, weight=0)
		self.filesframe.columnconfigure(2, weight=0) 
		self.filesframe.rowconfigure(0, weight=1)
		self.filesframe.rowconfigure(1, weight=1)
		self.treeframe = ttk.Frame(self.panx)
		self.treeframe.rowconfigure(0, weight=1)
		self.treeframe.columnconfigure(0, weight=1)
		#self.treeframe.grid(row=1,column=0, sticky=(tkinter.N, tkinter.S, tkinter.E, tkinter.W))
		self.plotframe = ttk.Frame(self.panx)
		self.panx.add(self.treeframe)
		self.panx.add(self.plotframe)
		#self.plotframe.grid(row=1,column=1, sticky=(tkinter.N, tkinter.S, tkinter.E, tkinter.W))
		self.plotframe.rowconfigure(0, weight=1)
		self.plotframe.columnconfigure(0, weight=1)
		self.datas = dict()

		# Files Frame Widgets
		self.fileslist = tkinter.Listbox(self.filesframe,selectmode=tkinter.EXTENDED, exportselection=0)
		self.fileslist.grid(row=0,column=0, rowspan=3, sticky=(tkinter.N, tkinter.S, tkinter.E, tkinter.W))

		self.fileslistscroll = ttk.Scrollbar(self.filesframe, orient=tkinter.VERTICAL, command=self.fileslist.yview)
		self.fileslistscroll.grid(row=0, column=1, rowspan=3, sticky=(tkinter.N, tkinter.S, tkinter.E))
		self.fileslist['yscrollcommand'] = self.fileslistscroll.set

		self.addbutton = ttk.Button(self.filesframe, text='+', command = self.add_measure)
		self.addbutton.grid(row=0, column=2, sticky=(tkinter.N, tkinter.E, tkinter.S))
		self.rembutton = ttk.Button(self.filesframe, text='-', command = self.rem_selected)
		self.rembutton.grid(row=1, column=2, sticky=(tkinter.S, tkinter.E, tkinter.N))
		self.chsortbutton = ttk.Button(self.filesframe, text='Kanäle sort.', command = self.chsort)
		self.chsortbutton.grid(row=2, column=2, sticky=(tkinter.S, tkinter.E, tkinter.N))
		
		# Tree Frame Widgets

		self.evatree = ttk.Treeview(self.treeframe)
		self.evatree.grid(row=0,column=0,columnspan=3, sticky=(tkinter.N, tkinter.W, tkinter.S, tkinter.E))
		self.evatree.insert('','end','wvplot', text='Plot Wellenform')
		self.evatree.insert('','end','Amplitudengang',text='Amplitudengang',open=True)
		self.evatree.insert('Amplitudengang','end','psd', text='Plot Periodogram')
		self.evatree.insert('Amplitudengang','end','welchpsd', text='Plot Welch Periodogram')
		self.evatree.insert('','end','angle', text='Plot Phasengang')
		self.evatree.insert('','end','groupdelay', text='Plot Gruppenlaufzeit')
		self.evatree.insert('','end','spec', text='Plot Spektrogram')
		self.evatree.insert('','end','polar', text='Plot Polar')
		self.evatree.insert('','end','surf3d', text='SurfacePlot 3D')
		self.evatree.insert('','end','surf2d', text='SurfacePlot 2D')
		self.evatree.selection_set('wvplot')
		self.fileslist.bind('<<ListboxSelect>>', self.plotdata)
		self.evatree.bind('<<TreeviewSelect>>', self.plotdata)
		self.cfgbtn=ttk.Button(self.treeframe,text='Konfigurieren',command=self.plotcfg)
		self.cfgbtn.grid(row=1,column=0,columnspan=3, sticky=(tkinter.N,tkinter.W,tkinter.S,tkinter.E))


		# Widgets for selection saving and loading in sidebar


		self.selectionlist=tkinter.Listbox(self.treeframe)
		self.selectionstate=tkinter.IntVar()
		self.selectioncb=ttk.Checkbutton(self.treeframe, text='Speichern', variable=self.selectionstate)
		self.selectionadd=ttk.Button(self.treeframe, text='+',command=self.seladdclick)
		self.selectiondel=ttk.Button(self.treeframe, text='-',command=self.seldelclick)
		self.selectionren=ttk.Button(self.treeframe, text='R',command=self.selrenclick)

		self.selectionlist.grid(row=2,column=0,columnspan=3, sticky=(tkinter.N,tkinter.W,tkinter.S,tkinter.E))
		self.selectioncb.grid(row=3,column=0,columnspan=3, sticky=(tkinter.N,tkinter.W,tkinter.S,tkinter.E))
		self.selectionadd.grid(row=4,column=0, sticky=(tkinter.N,tkinter.W,tkinter.S,tkinter.E))
		self.selectiondel.grid(row=4,column=1, sticky=(tkinter.N,tkinter.W,tkinter.S,tkinter.E))
		self.selectionren.grid(row=4,column=2, sticky=(tkinter.N,tkinter.W,tkinter.S,tkinter.E))
		self.selectionlist.bind('<<ListboxSelect>>', self.selchange)
		self.selectiondict={}

		# Plot Frame Widgets

		
		self.fig = Figure(figsize=(5,4), dpi=100)
		self.plotcanvas = FigureCanvasTkAgg(self.fig, master=self.plotframe)
		self.plotcanvas.show()
		self.plotcanvas.get_tk_widget().pack(side=tkinter.TOP, fill=tkinter.BOTH, expand=1)#grid(row=0,column=0, sticky=(tkinter.N, tkinter.S, tkinter.W, tkinter.E))
		self.plottoolb = NavigationToolbar2TkAgg(self.plotcanvas, self.plotframe)
		self.plottoolb.update()
		self.plotcanvas._tkcanvas.pack(side=tkinter.TOP, fill=tkinter.BOTH, expand=1)#grid(row=1,column=0)
	def add_measure(self):
		filenames = filedialog.askopenfilenames(filetypes=[('Wav-Files','*.wav')])
		#fs,data_read = scipy.io.wavfile.read(filename)
		for filename in filenames:
			wav = pysoundfile.SoundFile(filename)
			fs = wav.sample_rate
			data = wav.read(wav.frames)
			del wav
			print(data.shape)
			fname = filename[filename.rfind(os.sep)+1:]
			for i in range(0,data.shape[1]):
				if data.shape[1] > 1:
					name = fname+'CH'+str(i+1)
				else:
					name = fname
				while name in list(self.datas.keys()):
					name='_'+name
				self.fileslist.insert(tkinter.END, name)
				self.datas[name] = (fs, data[:,i], filename)
			gc.collect()

	def rem_selected(self):
		while () != self.fileslist.curselection():
			element=self.fileslist.curselection()[0]
			del self.datas[self.fileslist.get(element)]
			self.fileslist.delete(element)
		gc.collect()
	def plotdata(self, event):
		try:
			self.subpl.close()
		except:
			pass
		self.fig.clear()
		gc.collect()
		self.plotdata_dict[self.evatree.selection()[0]]()
	def wvplot(self):
		self.subpl = self.fig.add_subplot(111)
		self.subpl.hold(False)
		linestyle=self.wvplotvalues['Linienart']
		drawmode=self.wvplotvalues['Zeichenmodus']
		print(drawmode+linestyle)
		filteract=int(self.wvplotvalues['Filter'])
		bandstart=int(self.wvplotvalues['Startfrequenz'])
		bandstop=int(self.wvplotvalues['Endfrequenz'])
		filterorder=int(self.wvplotvalues['Filterordnung'])
		for i in self.fileslist.curselection():
			data=self.datas[self.fileslist.get(i)][1]
			fs=self.datas[self.fileslist.get(i)][0]
			if filteract:
				data=butter_bandpass_filter(data,bandstart,bandstop,fs,filterorder)
			p = self.subpl.plot(data,ls=drawmode+linestyle)
			self.fileslist.itemconfig(i,selectforeground=matplotlib.colors.rgb2hex(cc.to_rgb(p[0].get_c())))
			self.subpl.hold(True)
		self.plotcanvas.show()
	def psdplot(self):
		self.subpl = self.fig.add_subplot(111)
		self.subpl.hold(False)
		maximum=0
		for i in self.fileslist.curselection():
			fs=self.datas[self.fileslist.get(i)][0]
			data=self.datas[self.fileslist.get(i)][1]
			f,psd = scipy.signal.periodogram(data,fs,nfft=nextpow2(len(data)))
			if maximum<np.max(psd):
				maximum=np.max(psd)
		for i in self.fileslist.curselection():
			fs=self.datas[self.fileslist.get(i)][0]
			data=self.datas[self.fileslist.get(i)][1]
			f,psd = scipy.signal.periodogram(data,fs,nfft=nextpow2(len(data)))
			psd = 20*np.log10(psd/maximum)
			p = self.subpl.semilogx(f, psd)
			self.fileslist.itemconfig(i,selectforeground=matplotlib.colors.rgb2hex(cc.to_rgb(p[0].get_c())))
			self.subpl.hold(True)
		self.subpl.set_ylim((-70,0.5))
		self.subpl.set_xlim((20,20500))
		self.plotcanvas.show()
	def angleplot(self):
		self.subpl = self.fig.add_subplot(111)
		self.subpl.hold(True)
		for i in self.fileslist.curselection():
			fs=self.datas[self.fileslist.get(i)][0]
			data=self.datas[self.fileslist.get(i)][1]
			nfft=int(nextpow2(len(data)))
			data_fft=fftshift(fft(data,n=nfft))
			data_fft=data_fft[nfft/2:]
			angle_fft=np.angle(data_fft)
			angle_fft=np.unwrap(angle_fft)
			#angle_fft=angle_fft[nfft/2:]
			#angle_fft=phaseunwrap(angle_fft)
			f=np.linspace(0,fs/2,nfft/2)
			p = self.subpl.plot(f, angle_fft)
			self.subpl.set_xscale('log')
			self.fileslist.itemconfig(i,selectforeground=matplotlib.colors.rgb2hex(cc.to_rgb(p[0].get_c())))
		self.plotcanvas.show()
	def gd_plot(self):
		self.subpl = self.fig.add_subplot(111)
		self.subpl.hold(True)
		for i in self.fileslist.curselection():
			fs=self.datas[self.fileslist.get(i)][0]
			data=self.datas[self.fileslist.get(i)][1]
			nfft=int(nextpow2(len(data)))
			data_fft=fft(data,n=nfft)
			f=np.linspace(0,fs/2,nfft/2)
			#gd=-1*(phaseunwrap(np.angle(data_fft[nfft/2:]))/(2*np.pi*f))
			delta_f=fs/nfft
			phase=np.angle(data_fft[nfft/2:])
			phase=np.unwrap(phase)
			gd=np.zeros(len(phase))
			for n in range(1,len(phase)-1):
				#gd[n]=-1*((phase[n+1]-phase[n-1])/((f[n+1]*2*np.pi)-(f[n-1])*2*np.pi))
				gd[n]=-1*((phase[n+1]-phase[n-1])/((f[n+1])-(f[n-1])))
				#gd[n]=(phase[n-1]-phase[n])/(2*np.pi*delta_f)
			p = self.subpl.semilogx(f, gd)
			self.fileslist.itemconfig(i,selectforeground=matplotlib.colors.rgb2hex(cc.to_rgb(p[0].get_c())))
		self.plotcanvas.show()
	def specplot(self):
		elements=len(self.fileslist.curselection())
		#self.fig.clear()
		#self.subpl = self.fig.add_subplot(elements,1,1)
		#self.subpl.hold(False)
		print(self.specplotvalues)
		nfft=int(self.specplotvalues['NFFT'])
		window=scipy.signal.get_window(window=self.specplotvalues['window'],Nx=nfft)
		noverlap=int(self.specplotvalues['noverlap'])
		logarithmic=int(self.specplotvalues['Logarithmisch'])
		e=1
		for i in self.fileslist.curselection():
			self.subpl = self.fig.add_subplot(elements,1,e)
			fs=self.datas[self.fileslist.get(i)][0]
			data=self.datas[self.fileslist.get(i)][1]
			if logarithmic:
				Pxx,freq,t=matplotlib.mlab.specgram(data,Fs=fs,NFFT=nfft,window=window,noverlap=noverlap)
				Pxx[Pxx==0]=10**(-10)
				pxxplot=10. * np.log10(Pxx)
				#pxxplot=np.nan_to_num(pxxplot)
				self.subpl.pcolormesh(t,freq,pxxplot)
				self.subpl.set_yscale('symlog')
				self.subpl.set_ylim((20,20500))
			else:
				Pxx,freq,t,im=	self.subpl.specgram(data,Fs=fs,NFFT=nfft,window=window,noverlap=noverlap,cmap='CMRmap')
				print(np.min(Pxx))
				print(np.max(Pxx))
				print(10*np.log10(np.min(Pxx)/np.max(Pxx)))
				print(10*np.log10(np.max(Pxx)/np.max(Pxx)))
				cbar=self.fig.colorbar(im)
				self.subpl.set_ylim((20,20500))
			e+=1
		self.plotcanvas.show()
	def welchplot(self):
		self.subpl = self.fig.add_subplot(111)
		self.subpl.hold(True)
		elements=len(self.fileslist.curselection())
		#self.subpl = self.fig.add_subplot(elements,1,1)
		#self.subpl.hold(False)
		print(self.welchplotvalues)
		nfft=int(self.welchplotvalues['NFFT'])
		padto=int(self.welchplotvalues['padto'])
		window=scipy.signal.get_window(window=self.welchplotvalues['window'],Nx=nfft)
		noverlap=int(self.welchplotvalues['noverlap'])
		for i in self.fileslist.curselection():
			fs=self.datas[self.fileslist.get(i)][0]
			data=self.datas[self.fileslist.get(i)][1]
			self.subpl.psd(data,Fs=fs,NFFT=nfft,window=window,noverlap=noverlap,pad_to=padto)
			self.subpl.set_xscale('log')
			p=self.subpl.get_lines()
			self.fileslist.itemconfig(i,selectforeground=matplotlib.colors.rgb2hex(cc.to_rgb(p[-1].get_c())))
		self.plotcanvas.show()
	def polarplot(self):
		degree=int(self.polarplotvalues['Radius in Grad'])
		freq=int(self.polarplotvalues['Frequenz'])
		#self.fig.clear()
		self.subpl = self.fig.add_subplot(111, polar=True)
		self.subpl.hold(False)
		elements=len(self.fileslist.curselection())
		print(elements)
		plot_degree=np.radians(degree)
		r = np.linspace(0,plot_degree,elements)
		theta = np.zeros(elements)
		x = 0
		maximum=0
		for i in self.fileslist.curselection():
			fs=self.datas[self.fileslist.get(i)][0]
			data=self.datas[self.fileslist.get(i)][1]
			f,psd = scipy.signal.periodogram(data,fs,nfft=nextpow2(len(data)))
			theta[x]=np.abs(psd[find_nearest(f,freq)])
			x+=1
		print(theta)
		theta=20*np.log10(theta/np.max(theta))
		#theta=-theta
		#theta=theta+np.abs(np.min(theta))
		#theta=theta+np.abs(np.min(theta))+1
		print(theta)
		p = self.subpl.plot(r,theta)
		self.subpl.set_rmax(0.5)
		self.subpl.set_rmin(-70)
	#	self.subpl.set_rscale('log')
		self.plotcanvas.show()
	def surf3dplot(self):
		degree=180
		# Z = Degrees = Files
		# X = freqz
		# Y = magnitue/freq
		#self.fig.clear()
		self.subpl = self.fig.add_subplot(111,projection='3d')
		self.subpl.hold(False)
		elements=len(self.fileslist.curselection())
		print(elements)
		r = np.linspace(-degree/2,degree/2,elements)
		magnitudes=np.zeros(((nextpow2(len(self.datas[self.fileslist.get(self.fileslist.curselection()[0])][1]))/2)+1,elements))
		x=0
		for i in self.fileslist.curselection():
			fs=self.datas[self.fileslist.get(i)][0]
			data=self.datas[self.fileslist.get(i)][1]
			f,psd = scipy.signal.periodogram(data,fs,nfft=int(nextpow2(len(data))))
			magnitudes[:,x]=psd
			x+=1
		magnitudes=20*np.log10(magnitudes/np.max(magnitudes))

		smaller=100
		smallmagnitudes=np.zeros((len(magnitudes)/smaller,x))
		smallf=np.zeros(len(f)/smaller)
		for i in range(1,int(len(magnitudes)/smaller)):
			smallmagnitudes[i,:]=np.sum(magnitudes[(i-1)*smaller:i*smaller,:],axis=0)/smaller
			smallf[i]=np.sum(f[(i-1)*smaller:i*smaller])/smaller


		print(np.min(magnitudes))
		print(np.max(magnitudes))
		smallf,r=np.meshgrid(smallf,r)	
		print(smallf.shape)
		print(r.shape)
		print(smallmagnitudes.shape)
		self.subpl.set_xscale('symlog')
		self.subpl.set_zlim3d((-60,0))
		#self.subpl.set_ylim3d((-100,100))
		self.subpl.set_xlim3d((20,20000))
		self.subpl.plot_surface(X=smallf,Y=r,Z=smallmagnitudes.transpose(),cmap='spectral', antialiased=False, linewidth=0,vmin=-60,vmax=0)
		self.plotcanvas.show()
	def surf2dplot(self):
		degree=180
		# Z = Degrees = Files
		# X = freqz
		# Y = magnitue/freq
		#self.fig.clear()
		self.subpl = self.fig.add_subplot(111)
		self.subpl.hold(False)
		elements=len(self.fileslist.curselection())
		print(elements)
		r = np.linspace(-degree/2,degree/2,elements)
		magnitudes=np.zeros(((nextpow2(len(self.datas[self.fileslist.get(self.fileslist.curselection()[0])][1]))/2)+1,elements))
		x=0
		for i in self.fileslist.curselection():
			fs=self.datas[self.fileslist.get(i)][0]
			data=self.datas[self.fileslist.get(i)][1]
			f,psd = scipy.signal.periodogram(data,fs,nfft=int(nextpow2(len(data))))
			magnitudes[:,x]=psd
			x+=1
		magnitudes=20*np.log10(magnitudes/np.max(magnitudes))
		#pxxplot=np.nan_to_num(pxxplot)
		#reduce number of points

		smaller=1
		i=0
		fsmaller=[]
		smallmagnitudes=np.array([])
		while i+smaller<len(f):
			fsmaller.append((1/smaller)*sum(f[i:i+smaller]))
			if i==0:
				smallmagnitudes=(1/smaller)*np.sum(magnitudes[i:i+smaller,:],axis=0)
			else:
				smallmagnitudes=np.vstack((smallmagnitudes,(1/smaller)*np.sum(magnitudes[i:i+smaller,:],axis=0)))
			smaller*=2**(1/12)
			i+=smaller


		
		im=self.subpl.pcolormesh(np.array(fsmaller),r,smallmagnitudes.transpose(),vmin=-30,vmax=0)
		cbar=self.fig.colorbar(im)
		self.subpl.set_xscale('symlog')
		self.subpl.set_xlim((20,20500))

		#smaller=100
		#smallmagnitudes=np.zeros((len(magnitudes)/smaller,x))
		#smallf=np.zeros(len(f)/smaller)
		#for i in range(1,int(len(magnitudes)/smaller)):
	#		smallmagnitudes[i,:]=np.sum(magnitudes[(i-1)*smaller:i*smaller,:],axis=0)/smaller
#			smallf[i]=np.sum(f[(i-1)*smaller:i*smaller])/smaller

		#self.subpl.plot_surface(X=smallf,Y=r,Z=smallmagnitudes.transpose(),cmap='spectral', antialiased=False, linewidth=0,vmin=-60,vmax=0)
		self.plotcanvas.show()

	def plotcfg(self):
		self.plotcfg_dict[self.evatree.selection()[0]]()
	def specplotcfg(self):
		nfft=self.specplotvalues['NFFT']
		window=self.specplotvalues['window']
		noverlap=self.specplotvalues['noverlap']
		logarithmic=self.specplotvalues['Logarithmisch']
		cfgvalues=['Spektrogramm Konfiguration',['NFFT','e',str(nfft)],['window','cbro',window,'boxcar', 'triang', 'blackman', 'hamming', 'hann', 'bartlett', 'flattop', 'parzen', 'bohman', 'blackmanharris', 'nuttall', 'barthann'],['noverlap','e',str(noverlap)],['Logarithmisch','c',logarithmic]]
		self.specplotvalues=cfgdlg(cfgvalues)
		self.fig.clear()
		self.specplot()
	def polarplotcfg(self):
		degree=int(self.polarplotvalues['Radius in Grad'])
		freq=int(self.polarplotvalues['Frequenz'])
		cfgvalues=['Polardiagramm Konfiguration',['Radius in Grad','e',str(degree)],['Frequenz','e',str(freq)]]
		self.polarplotvalues=cfgdlg(cfgvalues)
		self.fig.clear()
		self.polarplot()
	def wvplotcfg(self):
		linestyle=self.wvplotvalues['Linienart']
		drawmode=self.wvplotvalues['Zeichenmodus']
		filteract=self.wvplotvalues['Filter']
		bandstart=self.wvplotvalues['Startfrequenz']
		bandstop=self.wvplotvalues['Endfrequenz']
		filterorder=self.wvplotvalues['Filterordnung']
		cfgvalues=['Wellenform Konfiguration',['Linienart','cbro',linestyle,'-','--','-.',':','.','None'],['Zeichenmodus','cbro',drawmode,'default' ,'steps' ,'steps-mid','steps-post'],['Filter','c',filteract],['Startfrequenz','e',bandstart],['Endfrequenz','e',bandstop],['Filterordnung','e',filterorder]]
		self.wvplotvalues=cfgdlg(cfgvalues)
		self.fig.clear()
		self.wvplot()
	def welchplotcfg(self):
		nfft=self.welchplotvalues['NFFT']
		window=self.welchplotvalues['window']
		noverlap=self.welchplotvalues['noverlap']
		padto=self.welchplotvalues['padto']
		cfgvalues=['Welch-Periodogramm Konfiguration',['NFFT','e',str(nfft)],['window','cbro',window,'boxcar', 'triang', 'blackman', 'hamming', 'hann', 'bartlett', 'flattop', 'parzen', 'bohman', 'blackmanharris', 'nuttall', 'barthann'],['noverlap','e',str(noverlap)],['padto','e',padto]]
		self.welchplotvalues=cfgdlg(cfgvalues)
		self.fig.clear()
		self.welchplot()
	def chsort(self):
		#get highest channel
		highest=0
		for i in range(self.fileslist.size()):
			stringstart=self.fileslist.get(i).upper().find('.WAVCH')
			if stringstart>-1:
				ch=int(self.fileslist.get(i)[stringstart+6:])
				print(ch)
				if ch>highest:
					highest=ch

		#Put all channels in seperate lists
		chanlist=[[] for k in range(highest)] # generete a list with highest elemts of sublists
		print(chanlist)
		for i in range(self.fileslist.size()):
			stringstart=self.fileslist.get(i).upper().find('.WAVCH')
			if stringstart>-1:
				ch=int(self.fileslist.get(i)[stringstart+6:])
				chanlist[ch-1].append(self.fileslist.get(i))
		# delete all collected itemes
		for i in range(len(chanlist)):
			for j in range(len(chanlist[i])):
				self.fileslist.delete(self.fileslist.get(0,tkinter.END).index(chanlist[i][j]))
		# append all itmes in sorted order
		for i in range(len(chanlist)):
			for j in range(len(chanlist[i])):
				self.fileslist.insert(tkinter.END,chanlist[i][j])
	def seldelclick(self):
		while () != self.selectionlist.curselection():
			element=self.selectionlist.curselection()[0]
			del self.selectiondict[self.selectionlist.get(element)]
			self.selectionlist.delete(element)
	def seladdclick(self):
		self.selectionlist.insert(tkinter.END,'Auswahl '+str(self.selectionlist.size()+1))
	def selrenclick(self):
		newname=spldlg.askstring('Neuer Name','Neuer Name')
		if newname:
			while (newname in self.selectiondict.keys()):
				newname+='_'
			saveslot=self.selectionlist.get(self.selectionlist.curselection()[0])
			selpos=self.selectionlist.get(0,tkinter.END).index(saveslot)
			self.selectionlist.delete(selpos)
			self.selectionlist.insert(selpos, newname)
			self.selectiondict[newname]=self.selectiondict[saveslot]
			del self.selectiondict[saveslot]

	def selchange(self,event):
		if self.selectionstate.get():
			#save selection
			print('save selection')
			saveslot=self.selectionlist.get(self.selectionlist.curselection()[0])
			self.selectiondict[saveslot]=self.fileslist.curselection()
			print(saveslot)
			print(self.selectiondict[saveslot])
		else:
			#recall selection
			print('load selection')
			saveslot=self.selectionlist.get(self.selectionlist.curselection()[0])
			if saveslot in self.selectiondict.keys():
				self.fileslist.selection_clear(0,tkinter.END)
				for i in self.selectiondict[saveslot]:
					self.fileslist.selection_set(i)
				self.plotdata('')
	def shutdown(self):
		print('eva shutdown')
		home=os.path.expanduser('~')
		savepath=home+os.sep+'.pyacousticmeasure'
		if not os.path.exists(savepath):
			os.makedirs(savepath)
		settingsfile=open(savepath+os.sep+'eva.json','w')
		openedfiles=[]
		for i in self.datas.keys():
			openedfiles.append(self.datas[i][2])
		openedfiles=set(openedfiles)
		openedfiles=list(openedfiles)
		settings={
				'openedfiles':openedfiles
			}
		settingsfile.write(json.dumps(settings))
		settingsfile.close()
