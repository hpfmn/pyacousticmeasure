# coding=utf8
import numpy as np
import os
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
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
import matplotlib.colors
from numpy.fft import fft,ifft,fftshift,ifftshift
from cfgdlg import cfgdlg

def find_nearest(array,value):
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
    return y

def nextpow2(i):
	return 2**np.ceil(np.log2(i))

class EVA_GUI:
	def __init__(self, parent):
		self.plotdata_dict={'wvplot': self.wvplot, 'psd': self.psdplot, 'spec': self.specplot, 'angle': self.angleplot, 'groupdelay': self.gd_plot, 'polar': self.polarplot,'welchpsd':self.welchplot}
		self.plotcfg_dict={'spec': self.specplotcfg, 'polar': self.polarplotcfg,'wvplot':self.wvplotcfg,'welchpsd':self.welchplotcfg}

		self.specplotvalues={'NFFT': 256,'window':'hann','noverlap':128}
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
		self.fileslist.grid(row=0,column=0, rowspan=2, sticky=(tkinter.N, tkinter.S, tkinter.E, tkinter.W))

		self.fileslistscroll = ttk.Scrollbar(self.filesframe, orient=tkinter.VERTICAL, command=self.fileslist.yview)
		self.fileslistscroll.grid(row=0, column=1, rowspan=2, sticky=(tkinter.N, tkinter.S, tkinter.E))
		self.fileslist['yscrollcommand'] = self.fileslistscroll.set

		self.addbutton = ttk.Button(self.filesframe, text='+', command = self.add_measure)
		self.addbutton.grid(row=0, column=2, sticky=(tkinter.N, tkinter.E, tkinter.S))
		self.rembutton = ttk.Button(self.filesframe, text='-', command = self.rem_selected)
		self.rembutton.grid(row=1, column=2, sticky=(tkinter.S, tkinter.E, tkinter.N))
		
		# Tree Frame Widgets

		self.evatree = ttk.Treeview(self.treeframe)
		self.evatree.grid(row=0,column=0, sticky=(tkinter.N, tkinter.W, tkinter.S, tkinter.E))
		self.evatree.insert('','end','wvplot', text='Plot Wellenform')
		self.evatree.insert('','end','Amplitudengang',text='Amplitudengang',open=True)
		self.evatree.insert('Amplitudengang','end','psd', text='Plot Periodogram')
		self.evatree.insert('Amplitudengang','end','welchpsd', text='Plot Welch Periodogram')
		self.evatree.insert('','end','angle', text='Plot Angle')
		self.evatree.insert('','end','groupdelay', text='Plot Group Delay')
		self.evatree.insert('','end','spec', text='Plot Spektogram')
		self.evatree.insert('','end','polar', text='Polar')
		self.evatree.selection_set('wvplot')
		self.fileslist.bind('<<ListboxSelect>>', self.plotdata)
		self.evatree.bind('<<TreeviewSelect>>', self.plotdata)
		self.cfgbtn=ttk.Button(self.treeframe,text='Konfigurieren',command=self.plotcfg)
		self.cfgbtn.grid(row=1,column=0, sticky=(tkinter.N,tkinter.W,tkinter.S,tkinter.E))

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
				self.datas[name] = (fs, data[:,i])

	def rem_selected(self):
		while () != self.fileslist.curselection():
			element=self.fileslist.curselection()[0]
			del self.datas[self.fileslist.get(element)]
			self.fileslist.delete(element)
	def plotdata(self, event):
		self.fig.clear()
		self.plotdata_dict[self.evatree.selection()[0]]()
	def wvplot(self):
		subpl = self.fig.add_subplot(111)
		subpl.hold(False)
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
			p = subpl.plot(data,ls=drawmode+linestyle)
			self.fileslist.itemconfig(i,selectforeground=matplotlib.colors.rgb2hex(cc.to_rgb(p[0].get_c())))
			subpl.hold(True)
		self.plotcanvas.show()
	def psdplot(self):
		subpl = self.fig.add_subplot(111)
		subpl.hold(False)
		for i in self.fileslist.curselection():
			fs=self.datas[self.fileslist.get(i)][0]
			data=self.datas[self.fileslist.get(i)][1]
			f,psd = scipy.signal.periodogram(data,fs,nfft=nextpow2(len(data)))
			psd = 20*np.log10(psd)#/max(psd))
			p = subpl.semilogx(f, psd)
			self.fileslist.itemconfig(i,selectforeground=matplotlib.colors.rgb2hex(cc.to_rgb(p[0].get_c())))
			subpl.hold(True)
		self.plotcanvas.show()
	def angleplot(self):
		subpl = self.fig.add_subplot(111)
		subpl.hold(True)
		for i in self.fileslist.curselection():
			fs=self.datas[self.fileslist.get(i)][0]
			data=self.datas[self.fileslist.get(i)][1]
			nfft=int(nextpow2(len(data)))
			data_fft=fftshift(fft(data,n=nfft))
			angle_fft=np.angle(data_fft)
			angle_fft=np.unwrap(angle_fft)
			#angle_fft=phaseunwrap(angle_fft)
			angle_fft=angle_fft[nfft/2:]
			f=np.linspace(0,fs/2,nfft/2)
			p = subpl.plot(f, angle_fft)
			self.fileslist.itemconfig(i,selectforeground=matplotlib.colors.rgb2hex(cc.to_rgb(p[0].get_c())))
		self.plotcanvas.show()
	def gd_plot(self):
		subpl = self.fig.add_subplot(111)
		subpl.hold(True)
		for i in self.fileslist.curselection():
			fs=self.datas[self.fileslist.get(i)][0]
			data=self.datas[self.fileslist.get(i)][1]
			nfft=int(nextpow2(len(data)))
			data_fft=fftshift(fft(data,n=nfft))
			f=np.linspace(0,fs/2,nfft/2)
			#gd=-1*(phaseunwrap(np.angle(data_fft[nfft/2:]))/(2*np.pi*f))
			delta_f=fs/nfft
			phase=np.angle(data_fft[nfft/2:])
			phase=np.unwrap(phase)
			gd=np.zeros(len(phase))
			for n in range(1,len(phase)-1):
				gd[n]=-1*((phase[n-1]-phase[n+1])/(f[n-1]-f[n+1]))
			p = subpl.plot(f, gd)
			self.fileslist.itemconfig(i,selectforeground=matplotlib.colors.rgb2hex(cc.to_rgb(p[0].get_c())))
		self.plotcanvas.show()
	def specplot(self):
		elements=len(self.fileslist.curselection())
		#self.fig.clear()
		#subpl = self.fig.add_subplot(elements,1,1)
		#subpl.hold(False)
		print(self.specplotvalues)
		nfft=int(self.specplotvalues['NFFT'])
		window=scipy.signal.get_window(window=self.specplotvalues['window'],Nx=nfft)
		noverlap=int(self.specplotvalues['noverlap'])
		e=1
		for i in self.fileslist.curselection():
			subpl = self.fig.add_subplot(elements,1,e)
			fs=self.datas[self.fileslist.get(i)][0]
			data=self.datas[self.fileslist.get(i)][1]
			subpl.specgram(data,Fs=fs,NFFT=nfft,window=window,noverlap=noverlap)
			e+=1
		self.plotcanvas.show()
	def welchplot(self):
		subpl = self.fig.add_subplot(111)
		subpl.hold(True)
		elements=len(self.fileslist.curselection())
		#subpl = self.fig.add_subplot(elements,1,1)
		#subpl.hold(False)
		print(self.welchplotvalues)
		nfft=int(self.welchplotvalues['NFFT'])
		padto=int(self.welchplotvalues['padto'])
		window=scipy.signal.get_window(window=self.welchplotvalues['window'],Nx=nfft)
		noverlap=int(self.welchplotvalues['noverlap'])
		for i in self.fileslist.curselection():
			fs=self.datas[self.fileslist.get(i)][0]
			data=self.datas[self.fileslist.get(i)][1]
			subpl.psd(data,Fs=fs,NFFT=nfft,window=window,noverlap=noverlap,pad_to=padto)
			p=subpl.get_lines()
			self.fileslist.itemconfig(i,selectforeground=matplotlib.colors.rgb2hex(cc.to_rgb(p[-1].get_c())))
		self.plotcanvas.show()
	def polarplot(self):
		degree=int(self.polarplotvalues['Radius in Grad'])
		freq=int(self.polarplotvalues['Frequenz'])
		#self.fig.clear()
		subpl = self.fig.add_subplot(111, polar=True)
		subpl.hold(False)
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
		#theta=-10*np.log10(theta/np.max(theta))
		#theta=theta+np.abs(np.min(theta))
		#theta=theta+np.abs(np.min(theta))+1
		print(theta)
		p = subpl.plot(r,theta)
	#	subpl.set_rscale('log')
		self.plotcanvas.show()
	def plotcfg(self):
		self.plotcfg_dict[self.evatree.selection()[0]]()
	def specplotcfg(self):
		nfft=self.specplotvalues['NFFT']
		window=self.specplotvalues['window']
		noverlap=self.specplotvalues['noverlap']
		cfgvalues=['Spektrogramm Konfiguration',['NFFT','e',str(nfft)],['window','cbro',window,'boxcar', 'triang', 'blackman', 'hamming', 'hann', 'bartlett', 'flattop', 'parzen', 'bohman', 'blackmanharris', 'nuttall', 'barthann'],['noverlap','e',str(noverlap)]]
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
		cfgvalues=['Wellenform Konfiguration',['Linienart','cbro',linestyle,'-','--','-.',':','None'],['Zeichenmodus','cbro',drawmode,'default' ,'steps' ,'steps-mid','steps-post'],['Filter','c',filteract],['Startfrequenz','e',bandstart],['Endfrequenz','e',bandstop],['Filterordnung','e',filterorder]]
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


