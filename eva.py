import numpy as np
import os
import scipy
import scipy.io.wavfile
import pysoundfile
import scipy.signal
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

def find_nearest(array,value):
	idx = (np.abs(array-value)).argmin()
	return idx

cc = matplotlib.colors.ColorConverter()

def nextpow2(i):
	return 2**np.ceil(np.log2(i))

def phaseunwrap(phase):
	for i in range(1,len(phase)):
			if((phase[i]-phase[i-1]) < -np.pi):
				phase[i]+=2*np.pi
			if((phase[i]-phase[i-1]) > np.pi):
				phase[i]-=2*np.pi
	return phase

class EVA_GUI:
	def __init__(self, parent):
		self.plotdata_dict={'wvplot': self.wvplot, 'psd': self.psdplot, 'spec': self.specplot, 'angle': self.angleplot, 'groupdelay': self.gd_plot, 'polar': self.polarplot}
		self.myParent = parent
		self.filesframe = ttk.Frame(parent)
		self.filesframe.grid(row=0, column=0, columnspan=2, sticky=(tkinter.N, tkinter.S, tkinter.E, tkinter.W))
		self.filesframe.columnconfigure(0, weight=1)
		self.filesframe.columnconfigure(1, weight=0)
		self.filesframe.columnconfigure(2, weight=0)
		self.filesframe.rowconfigure(0, weight=1)
		self.filesframe.rowconfigure(1, weight=1)
		self.treeframe = ttk.Frame(parent)
		self.treeframe.rowconfigure(0, weight=1)
		self.treeframe.columnconfigure(0, weight=1)
		self.treeframe.grid(row=1,column=0, sticky=(tkinter.N, tkinter.S, tkinter.E, tkinter.W))
		self.plotframe = ttk.Frame(parent)
		self.plotframe.grid(row=1,column=1, sticky=(tkinter.N, tkinter.S, tkinter.E, tkinter.W))
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
		self.evatree.insert('','end','psd', text='Plot Periodogram')
		self.evatree.insert('','end','angle', text='Plot Angle')
		self.evatree.insert('','end','groupdelay', text='Plot Group Delay')
		self.evatree.insert('','end','spec', text='Plot Spektogram')
		self.evatree.insert('','end','polar', text='Polar')
		self.evatree.selection_set('wvplot')
		self.fileslist.bind('<<ListboxSelect>>', self.plotdata)
		self.evatree.bind('<<TreeviewSelect>>', self.plotdata)

		# Plot Frame Widgets

		
		self.fig = Figure(figsize=(5,4), dpi=100)
		self.plotcanvas = FigureCanvasTkAgg(self.fig, master=self.plotframe)
		self.plotcanvas.show()
		self.plotcanvas.get_tk_widget().pack(side=tkinter.TOP, fill=tkinter.BOTH, expand=1)#grid(row=0,column=0, sticky=(tkinter.N, tkinter.S, tkinter.W, tkinter.E))
		self.plottoolb = NavigationToolbar2TkAgg(self.plotcanvas, self.plotframe)
		self.plottoolb.update()
		self.plotcanvas._tkcanvas.pack(side=tkinter.TOP, fill=tkinter.BOTH, expand=1)#grid(row=1,column=0)
	def add_measure(self):
		filename = filedialog.askopenfilename(filetypes=[('Wav-Files','*.wav')])
		#fs,data_read = scipy.io.wavfile.read(filename)
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
		self.plotdata_dict[self.evatree.selection()[0]]()
	def wvplot(self):
		subpl = self.fig.add_subplot(111)
		subpl.hold(False)
		for i in self.fileslist.curselection():
			data=self.datas[self.fileslist.get(i)][1]
			p = subpl.plot(data,'.')
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
			psd = 20*np.log10(psd)
			p = subpl.semilogx(f, psd)
			self.fileslist.itemconfig(i,selectforeground=matplotlib.colors.rgb2hex(cc.to_rgb(p[0].get_c())))
			subpl.hold(True)
		self.plotcanvas.show()
	def angleplot(self):
		subpl = self.fig.add_subplot(111)
		subpl.hold(False)
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
			subpl.hold(True)
		self.plotcanvas.show()
	def gd_plot(self):
		subpl = self.fig.add_subplot(111)
		subpl.hold(False)
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
			subpl.hold(True)
		self.plotcanvas.show()
	def specplot(self):
		subpl = self.fig.add_subplot(111)
		subpl.hold(False)
		for i in self.fileslist.curselection():
			fs=self.datas[self.fileslist.get(i)][0]
			data=self.datas[self.fileslist.get(i)][1]
			subpl.specgram(data,Fs=fs)
			subpl.hold(True)
		self.plotcanvas.show()
	def polarplot(self):
		self.fig.clear()
		subpl = self.fig.add_subplot(111, polar=True)
		subpl.hold(False)
		elements=len(self.fileslist.curselection())
		print(elements)
		plot_degree=2*np.pi
		r = np.linspace(0,plot_degree,elements)
		theta = np.zeros(elements)
		x = 0
		for i in self.fileslist.curselection():
			fs=self.datas[self.fileslist.get(i)][0]
			data=self.datas[self.fileslist.get(i)][1]
			nfft=int(nextpow2(len(data)))
			data_fft=fft(data,n=nfft)
			f=np.linspace(0,fs/2,nfft/2)
			theta[x]=np.abs(data_fft[find_nearest(f,1000)+(nfft/2)])
			x+=1
		p = subpl.plot(r,theta)
		self.plotcanvas.show()
	
root = tkinter.Tk()
root.columnconfigure(0, weight=1)
root.rowconfigure(0, weight=1)
root.columnconfigure(1, weight=10)
root.rowconfigure(1, weight=6)
eva_gui = EVA_GUI(root)
root.mainloop()

