# coding=utf8
import os
import sys
if sys.version_info<(3,0,0):
	import Tkinter as tkinter
	import tkMessageBox as messagebox
	import tkFileDialog as filedialog
	import ttk as ttk
else:
	import tkinter
	import tkinter.messagebox as messagebox
	import tkinter.ttk as ttk
	import tkinter.filedialog as filedialog
import jack
import time
import pyaudio
import numpy as np
import scipy
import scipy.signal
import scipy.io.wavfile
import wave
from numpy.fft import fft,ifft,fftshift,ifftshift,fftn,ifftn
import pysoundfile
import golay
import mls

jack_running=True
try:
	jack.attach('measure')
except Exception as e:
	print(e)
	jack_running=False

p = pyaudio.PyAudio()

FORMAT=pyaudio.paInt16

hostapis=dict()
for i in range(0,p.get_host_api_count()):
	hostapis[p.get_host_api_info_by_index(i)['name']] = i

def nextpow2(m):
	return 2**np.ceil(np.log2(m))

def listadev(hostapi, iotype):
	"""Returns a dictionary containing name and index of all devices of a specific hostapi"""
	adevs=dict()
	for i in range(0,p.get_host_api_info_by_index(hostapi)['deviceCount']):
		if iotype=='i':
			if p.get_device_info_by_host_api_device_index(hostapi,i)['maxInputChannels'] > 0:
				adevs[p.get_device_info_by_host_api_device_index(hostapi,i)['name']] = p.get_device_info_by_host_api_device_index(hostapi,i)['index']
		else:
			if p.get_device_info_by_host_api_device_index(hostapi,i)['maxOutputChannels'] > 0:
				adevs[p.get_device_info_by_host_api_device_index(hostapi,i)['name']] = p.get_device_info_by_host_api_device_index(hostapi,i)['index']
	return adevs



class MES_GUI:
	"""Class for measurement GUI """
	def __init__(self, parent):
		self.myParent = parent
		self.myParent.columnconfigure(0, weight=1)
		self.myParent.columnconfigure(1, weight=1)
		self.myParent.rowconfigure(0, weight=2)
		self.myParent.rowconfigure(1, weight=1)
		self.ausenb = ttk.Notebook(parent)
		self.pyauseframe = ttk.LabelFrame(parent, text='Audiosetup PyAudio')
		self.pyauseframe.grid(row=0, column=0)
		
		self.raw=[]
		# Items in Audio Setup Frame
		self.adriverlabel = ttk.Label(self.pyauseframe, text='Treibertyp')
		self.adriverlabel.grid(row=1, column=0)
		self.adrvcb = ttk.Combobox(self.pyauseframe, values=(list(hostapis.keys())), state='readonly')
		self.adrvcb.set(p.get_default_host_api_info()['name'])
		self.adrvcb.bind('<<ComboboxSelected>>', self.hostapichange)
		self.adrvcb.grid(row=1, column=1)
		self.aodevlabel= ttk.Label(self.pyauseframe, text='Wiedergabegerät')
		self.aodevlabel.grid(row=2, column=0)
		self.aodevlist = listadev(p.get_default_host_api_info()['index'],'o')
		self.aodevcb = ttk.Combobox(self.pyauseframe, values=(list(self.aodevlist.keys())), state='readonly')
		self.aodevcb.set(p.get_default_output_device_info()['name'])
		self.aodevcb.grid(row=2, column=1)
		self.aidevlabel= ttk.Label(self.pyauseframe, text='Aufnahmegerät')
		self.aidevlabel.grid(row=3, column=0)
		self.aidevlist = listadev(p.get_default_host_api_info()['index'],'i')
		self.aidevcb = ttk.Combobox(self.pyauseframe, values=(list(self.aidevlist.keys())), state='readonly')
		self.aidevcb.set(p.get_default_input_device_info()['name'])
		self.aidevcb.grid(row=3, column=1)

		self.nooclabel = ttk.Label(self.pyauseframe, text='Ausgangskanalanzahl')
		self.nooclabel.grid(row=4,column=0)
		self.ochannels = p.get_device_info_by_index(self.aodevlist[self.aodevcb.get()])['maxOutputChannels']
		self.nooccb = ttk.Combobox(self.pyauseframe, values=list(range(1,self.ochannels+1)), state='readonly')
		self.nooccb.current(0)
		self.nooccb.bind('<<ComboboxSelected>>', self.occhange)
		self.nooccb.grid(row=4,column=1)

		self.noiclabel = ttk.Label(self.pyauseframe, text='Eingangskanalanzahl')
		self.noiclabel.grid(row=5,column=0)
		self.ichannels = p.get_device_info_by_index(self.aidevlist[self.aidevcb.get()])['maxInputChannels']
		self.noiccb = ttk.Combobox(self.pyauseframe, values=list(range(1,self.ichannels+1)), state='readonly')
		self.noiccb.bind('<<ComboboxSelected>>', self.icchange)
		self.noiccb.current(0)
		
		self.noiccb.grid(row=5,column=1)

		self.fslabel = ttk.Label(self.pyauseframe, text='Samplingfrequenz')
		self.fslabel.grid(row=6, column=0)
		self.fscb = ttk.Combobox(self.pyauseframe, values=(44100,48000))
		self.fscb.set(48000)
		self.fs=int(self.fscb.get())
		self.fscb.bind('<<ComboboxSelected>>', self.fschange)
		self.fscb.grid(row=6, column=1) 
		self.ausenb.add(self.pyauseframe, text='PyAudio', underline=0, padding=2)
		self.ausenb.grid(row=0, column=0, sticky=tkinter.W+tkinter.E+tkinter.S+tkinter.N)

		# LabelFrame for PyJack Setup 
		if jack_running:
			self.pyjaseframe = ttk.LabelFrame(self.myParent, text='PyJack Setup') 
			self.pyjaseframe.grid(row=0,column=0) 
			self.jainplabel = ttk.Label(self.pyjaseframe, text='Jack Inputs auswählen:') 
			self.jainplabel.grid(row=1, column=0) 
			self.jaoutplabel = ttk.Label(self.pyjaseframe, text='Jack Outputs auswählen:')
			self.jaoutplabel.grid(row=3, column=0)

			self.jainplist = tkinter.Listbox(self.pyjaseframe, height=5, selectmode=tkinter.MULTIPLE, exportselection=0)
			self.jainplist.grid(row=2, column=0, sticky=(tkinter.W, tkinter.E, tkinter.N, tkinter.S))
			self.jainpscroll = ttk.Scrollbar(self.pyjaseframe, orient=tkinter.VERTICAL, command=self.jainplist.yview)
			self.jainpscroll.grid(row=2, column=1, sticky=(tkinter.N,tkinter.S))
			self.jainplist['yscrollcommand'] = self.jainpscroll.set

			self.jaoutlist = tkinter.Listbox(self.pyjaseframe, height=5, selectmode=tkinter.MULTIPLE, exportselection=0)
			self.jaoutlist.grid(row=4, column=0, sticky=(tkinter.W, tkinter.E))
			self.jaoutscroll = ttk.Scrollbar(self.pyjaseframe, orient=tkinter.VERTICAL, command=self.jaoutlist.yview)
			self.jaoutscroll.grid(row=4, column=1, sticky=(tkinter.N,tkinter.S))
			self.jaoutlist['yscrollcommand'] = self.jaoutscroll.set

			self.jarefbtn = ttk.Button(self.pyjaseframe, text='Aktualisieren', command=self.get_jack_ports)
			self.jarefbtn.grid(row=5,column=0) 
			
			self.get_jack_ports()
			self.ausenb.add(self.pyjaseframe, text='PyJack', underline=0, padding=2)
			self.ausenb.select(1)
		self.ausenb.bind('<<NotebookTabChanged>>', self.tabchange)


		# Widgets in Signal Setup Frame

		self.siseframe = ttk.LabelFrame(parent, text='Signalquelle')
		self.siseframe.grid(row=0, column=1, sticky=(tkinter.N, tkinter.S, tkinter.E, tkinter.W))
		self.siseframe.columnconfigure(0, weight=1)
		self.siseframe.columnconfigure(1, weight=1)
		self.siseframe.rowconfigure(0, weight=1)
		self.siseframe.rowconfigure(1, weight=1)
		self.siseframe.rowconfigure(2, weight=5)
		self.siseframe.rowconfigure(3, weight=1)
		self.siseframe.rowconfigure(4, weight=1)
		self.siseframe.rowconfigure(5, weight=1)
		self.siseframe.rowconfigure(6, weight=1)
		self.siseframe.rowconfigure(7, weight=1)
		self.siseframe.rowconfigure(8, weight=1)

		self.siselabel = ttk.Label(self.siseframe, text='Signal', width=20)
		self.siselabel.grid(row=1, column=0, sticky=(tkinter.W))
		self.sisecb = ttk.Combobox(self.siseframe, values=('Sweep', 'MLS', 'Golay', 'Impuls', 'Rauschen', 'Sinus', 'Rechteck', 'Sägezahn'.decode('utf8','ignore')), state='readonly')
		self.generate_signal={'Sweep' : self.sweepgen, 'Rauschen': self.noisegen, 'MLS': self.mlsgen, 'Golay': self.golaygen,'Sinus': self.singen, 'Rechteck': self.squaregen, 'Sägezahn': self.sawtoothgen, 'Impuls': self.impulsegen}
		self.sisecb.current(newindex=0)
		self.sisecb.bind('<<ComboboxSelected>>', self.signaltypechange)
		self.sisecb.grid(row=1, column=1, sticky=tkinter.E+tkinter.W)

		# Frame with widgets for sweep
		
		self.sweepframe = ttk.Frame(self.siseframe)
		self.f0label = ttk.Label(self.sweepframe, text='Startfrequenz', width=20)
		self.f0label.grid(row=0, column=0, sticky=(tkinter.W))

		self.f0 = tkinter.StringVar()
		self.f0e = ttk.Entry(self.sweepframe, textvariable=self.f0)
		self.f0e.grid(row=0, column=1, sticky=tkinter.E+tkinter.W)
		self.f0.set('20')
		
		self.f1label = ttk.Label(self.sweepframe, text='Endfrequenz')
		self.f1label.grid(row=1, column=0, sticky=(tkinter.W))
		
		self.f1 = tkinter.StringVar() 
		self.f1e = ttk.Entry(self.sweepframe, textvariable=self.f1)
		self.f1.set('20000')
		self.f1e.grid(row=1, column=1, sticky=tkinter.E+tkinter.W)

		self.sweepmethodlabel = ttk.Label(self.sweepframe, text='Methode')
		self.sweepmethodlabel.grid(row=2,column=0, sticky=tkinter.W+tkinter.E)

		self.sweepmethodcb = ttk.Combobox(self.sweepframe, values=('logarithmic', 'linear', 'quadratic'), state='readonly')
		self.sweepmethodcb.current(0)
		self.sweepmethodcb.grid(row=2,column=1, sticky=tkinter.E+tkinter.W)
		self.sweepgenkindlb=ttk.Label(self.sweepframe, text='Generatorart')
		self.sweepgenkindcb=ttk.Combobox(self.sweepframe, state='readonly',values=('Frequenzbereich','Zeitbereich'))
		self.sweepgenkindcb.current(0)
		self.sweepgenkindlb.grid(row=3,column=0, sticky=(tkinter.W))
		self.sweepgenkindcb.grid(row=3,column=1, sticky=tkinter.E+tkinter.W)


		self.sweepframe.grid(row=2, column=0, columnspan=2, sticky=tkinter.N+tkinter.S+tkinter.E+tkinter.W)
		self.sweepframe.columnconfigure(0, weight=1)
		self.sweepframe.columnconfigure(1, weight=1)
		self.sweepframe.rowconfigure(0, weight=1)
		self.sweepframe.rowconfigure(1, weight=1)
		self.sweepframe.rowconfigure(2, weight=1)
		self.sweepframe.rowconfigure(3, weight=1)


		# Frame with widgets for noise
		self.noiseframe = ttk.Frame(self.siseframe)


		# General Settings
		
		self.levellabel= ttk.Label(self.siseframe, text='Pegel')
		self.levellabel.grid(row=3, column=0, sticky=(tkinter.W))
		self.level=tkinter.StringVar()
		self.levele = ttk.Entry(self.siseframe, textvariable=self.level)
		self.level.set('-12')
		self.levele.grid(row=3, column=1, sticky=tkinter.E+tkinter.W)

		self.dur=tkinter.StringVar()
		self.dur.trace('w',self.durchange)
		self.durlabel = ttk.Label(self.siseframe, text='Dauer in Sekunden')
		self.durcb = ttk.Combobox(self.siseframe, values=(),textvariable=self.dur)
		#self.durcb.current(1)
		self.durlabel.grid(row=4, column=0, sticky=tkinter.W+tkinter.E)
		self.durcb.grid(row=4, column=1, sticky=tkinter.E+tkinter.W)

		self.dursp=tkinter.StringVar()
		self.dursp.trace('w',self.durspchange)
		self.dursplabel = ttk.Label(self.siseframe, text='Dauer in Samples')
		self.durspcb = ttk.Combobox(self.siseframe, values=(2**16, 2**17, 2**18, 2**19), textvariable=self.dursp)
		self.durspcb.current(1)
		self.dursplabel.grid(row=5, column=0, sticky=tkinter.W+tkinter.E)
		self.durspcb.grid(row=5, column=1, sticky=tkinter.E+tkinter.W)
		
		self.siavglabel = ttk.Label(self.siseframe, text="Wiederholungen")
		self.siavglabel.grid(row=6, column=0, sticky=(tkinter.W))
		self.siavg = tkinter.StringVar()
		self.siavgent = ttk.Entry(self.siseframe, textvariable=self.siavg)
		self.siavg.set('2')
		self.siavgent.grid(row=6,column=1, sticky=tkinter.E+tkinter.W)

		self.delaylabel = ttk.Label(self.siseframe, text='Verzögerung in Samples')
		self.delay=tkinter.StringVar()
		self.delay.set(str(0))
		self.delaye= ttk.Entry(self.siseframe, textvariable=self.delay)
		self.delaylabel.grid(row=7,column=0, sticky=tkinter.W+tkinter.E)
		self.delaye.grid(row=7,column=1, sticky=tkinter.W+tkinter.E)

		self.testbutton = ttk.Button(self.siseframe, text='Test', command=self.testButtonClick)
		self.testbutton.grid(row=8, column=0)
		self.testbutton = ttk.Button(self.siseframe, text='Verzögerung bestimmen', command=self.delayButtonClick)
		self.testbutton.grid(row=8, column=1)

		#Frame for MLS
		self.mlsframe= ttk.Frame(self.siseframe)
		self.mlsnlabel=ttk.Label(self.mlsframe,text='MLS Ordnung', width=20)
		self.mlsn=tkinter.StringVar()
		self.mlsncb=ttk.Combobox(self.mlsframe,textvariable=self.mlsn,values=str(list(range(2,32)))[1:-1].split(', '))
		self.mlsncb.current(12)
		self.mlsnlabel.grid(row=0,column=0, sticky=tkinter.W)
		self.mlsncb.grid(row=0,column=1, sticky=tkinter.W+tkinter.E)
		self.mlsflag=tkinter.IntVar()
		self.mlsflag.set(1)
		self.mlsflaglabel=ttk.Label(self.mlsframe,text='Register mit 1 initialisieren')
		self.mlsflagcheck=ttk.Checkbutton(self.mlsframe,variable=self.mlsflag)
		self.mlsflaglabel.grid(row=1,column=0, sticky=tkinter.W)
		self.mlsflagcheck.grid(row=1,column=1, sticky=tkinter.W)
		self.mlsframe.rowconfigure(0,weight=1)
		self.mlsframe.rowconfigure(1,weight=1)
		self.mlsframe.columnconfigure(0,weight=1)
		self.mlsframe.columnconfigure(1,weight=1)

		#Frame for Golay
		self.golayframe=ttk.Frame(self.siseframe)
		self.golayframe.rowconfigure(0,weight=1)
		self.golayframe.columnconfigure(0,weight=1)
		self.golaynlabel=ttk.Label(self.golayframe,text='Golay Ordnung', width=20)
		self.golayn=tkinter.StringVar()
		self.golayncb=ttk.Combobox(self.golayframe,textvariable=self.golayn,values=str(list(range(2,32)))[1:-1].split(', '))
		self.golayncb.current(12)
		self.golaynlabel.grid(row=0,column=0, sticky=tkinter.W)
		self.golayncb.grid(row=0,column=1, sticky=tkinter.W+tkinter.E)
		self.golaycount='a'

		# Fileframe
		self.fileframe = ttk.LabelFrame(self.myParent,text="Dateien")
		self.fileframe.grid(row=1, column=0, columnspan=2, sticky=tkinter.N+tkinter.S+tkinter.W+tkinter.E)
		self.fileframe.rowconfigure(0, weight=1)
		self.fileframe.rowconfigure(1, weight=1)
		self.fileframe.rowconfigure(2, weight=1)
		self.fileframe.columnconfigure(0, weight=1)
		self.fileframe.columnconfigure(1, weight=1)
		self.fileframe.columnconfigure(2, weight=1)
		self.savesellabel = ttk.Label(self.fileframe, text="Speichern: ")
		self.savesellabel.grid(row=0,column=0, sticky=tkinter.W)


		self.impcheck = tkinter.IntVar()
		self.rawcheck = tkinter.IntVar()
		self.sigcheck = tkinter.IntVar()
		self.impcheckbtn = ttk.Checkbutton(self.fileframe, text="Impulseantwort",variable=self.impcheck)
		self.rawcheckbtn = ttk.Checkbutton(self.fileframe, text="Rohdaten", variable=self.rawcheck)
		self.sigcheckbtn = ttk.Checkbutton(self.fileframe, text="Anregegungssignal", variable=self.sigcheck)
		self.impcheck.set(1)
		self.rawcheck.set(1)
		self.sigcheck.set(1)
		self.impcheckbtn.grid(row=0,column=1, sticky=tkinter.W)
		self.rawcheckbtn.grid(row=0,column=2, sticky=tkinter.W)
		self.sigcheckbtn.grid(row=0,column=3, sticky=tkinter.W)

		self.prefixlabel=ttk.Label(self.fileframe, text="Prefix")
		self.prefix=tkinter.StringVar()
		self.prefixent = ttk.Entry(self.fileframe,textvariable=self.prefix)
		self.prefix.set('Measure')
		self.prefixlabel.grid(row=1,column=0, sticky=tkinter.W)
		self.prefixent.grid(row=1,column=1, sticky=tkinter.W)

		self.counterlabel=ttk.Label(self.fileframe, text="Counter")
		self.counter=tkinter.StringVar()
		self.counterent  =ttk.Entry(self.fileframe, textvariable=self.counter)
		self.counter.set('000001')
		self.counterlabel.grid(row=1,column=2, sticky=tkinter.W)
		self.counterent.grid(row=1,column=3, sticky=tkinter.W)

		self.filepath=tkinter.StringVar()
		self.pathlabel=ttk.Label(self.fileframe, text="Pfad: ")
		self.pathent  =ttk.Entry(self.fileframe,textvariable=self.filepath)
		self.filepath.set(os.getcwd())
		self.pathlabel.grid(row=2, column=0, sticky=tkinter.W)
		self.pathent.grid(row=2,column=1,columnspan=2,sticky=(tkinter.E,tkinter.W))
		self.openbtn=ttk.Button(self.fileframe, text="Auswählen", command=self.selectpath)
		self.openbtn.grid(row=2,column=3, sticky=tkinter.W)


		self.mesbutton = ttk.Button(self.fileframe, text='Messen', command=self.mesButtonClick)
		self.mesbutton.grid(row=3,column=0, sticky=tkinter.W+tkinter.E)




	def hostapichange(self, event):
		host_api_index=hostapis[self.adrvcb.get()]
		self.aidevlist = listadev(host_api_index,'i')
		self.aidevcb.configure(values=list(self.aidevlist.keys()))
		self.aidevcb.current(newindex=0)
		self.aodevlist = listadev(host_api_index,'o')
		self.aodevcb.configure(values=list(self.aodevlist.keys()))
		self.aodevcb.current(newindex=0)

	def get_jack_ports(self):
		self.jainplist.delete(0,tkinter.END)
		self.jaoutlist.delete(0,tkinter.END)
		#jack.attach('measure')
		for port in jack.get_ports():
			if (jack.get_port_flags(port) & jack.IsOutput) > 0:
				self.jainplist.insert(tkinter.END, port)
			if (jack.get_port_flags(port) & jack.IsInput) > 0:
				self.jaoutlist.insert(tkinter.END, port)
		#jack.detach()

		

	def signaltypechange(self, event):
		self.mlsframe.grid_remove()
		self.golayframe.grid_remove()
		self.noiseframe.grid_remove()
		self.sweepframe.grid_remove()
		self.durcb.grid_remove()
		self.durlabel.grid_remove()
		self.durspcb.grid_remove()
		self.dursplabel.grid_remove()
		if self.sisecb.get() == 'Sweep':
			self.sweepframe.grid(row=2,column=0, columnspan=2)
			self.durlabel.grid(row=4, column=0, sticky=tkinter.W+tkinter.E)
			self.durcb.grid(row=4, column=1, sticky=tkinter.E+tkinter.W)
			self.dursplabel.grid(row=5, column=0, sticky=tkinter.W+tkinter.E)
			self.durspcb.grid(row=5, column=1, sticky=tkinter.E+tkinter.W)
			self.siseframe.rowconfigure(2, weight=5)
		if self.sisecb.get() == 'Rauschen':
			self.noiseframe.grid(row=2,column=0, columnspan=2)
			self.durlabel.grid(row=4, column=0, sticky=tkinter.W+tkinter.E)
			self.durcb.grid(row=4, column=1, sticky=tkinter.E+tkinter.W)
			self.dursplabel.grid(row=5, column=0, sticky=tkinter.W+tkinter.E)
			self.durspcb.grid(row=5, column=1, sticky=tkinter.E+tkinter.W)
		if self.sisecb.get() == 'MLS':
			self.mlsframe.grid(row=2,column=0, columnspan=2, sticky=tkinter.W+tkinter.E+tkinter.N+tkinter.S)
			self.siseframe.rowconfigure(2, weight=3)
		if self.sisecb.get() == 'Golay':
			self.golayframe.grid(row=2,column=0, columnspan=2, sticky=tkinter.W+tkinter.E+tkinter.N+tkinter.S)
			self.siseframe.rowconfigure(2, weight=1)
		if self.sisecb.get() == 'Impuls':
			self.durlabel.grid(row=4, column=0, sticky=tkinter.W+tkinter.E)
			self.durcb.grid(row=4,column=1,sticky=tkinter.E+tkinter.W)
			self.dursplabel.grid(row=5, column=0, sticky=tkinter.W+tkinter.E)
			self.durspcb.grid(row=5,column=1,sticky=tkinter.E+tkinter.W)

	def fschange(self, event):
		fsold=self.fs
		self.fs=int(self.fscb.get())
		self.durcb.set(float(self.durcb.get())*fsold/self.fs)
		self.durcb.configure(values=(2**16/self.fs, 2**17/self.fs, 2**18/self.fs, 2**19/self.fs))
		self.durcb.grid(row=4, column=1)

	def occhange(self, event):
		self.ochannels = p.get_device_info_by_index(self.aodevlist[self.aodevcb.get()])['maxOutputChannels']
		self.nooccb.configure(values=list(range(1,self.ochannels+1)))
		

	def icchange(self, event):
		self.ichannels = p.get_device_info_by_index(self.aidevlist[self.aidevcb.get()])['maxInputChannels']
		self.noiccb.configure(values=list(range(1,self.ochannels+1)))

	def IsPyAudio(self):
		if self.ausenb.tab(self.ausenb.select(), option='text')== 'PyAudio':	
			return True
		else:
			return False

	def IsPyJack(self):
		if self.ausenb.tab(self.ausenb.select(), option='text')== 'PyJack':	
			return True
		else:
			return False

	def tabchange(self, event):
		print(self.ausenb.tab(self.ausenb.select(),option='text'))

	def TestPyAudio(self):
		outputdev = self.aodevlist[self.aodevcb.get()]
		CHANNELS=int(self.nooccb.get())
		stream = p.open(format=FORMAT,
				channels=CHANNELS,
				rate=self.fs,
				output=True,
				output_device_index=outputdev)
		self.outputsignal=np.repeat(self.signal, CHANNELS)*(2**15-1)
		stream.write(self.outputsignal.astype(np.int16).tostring())

		stream.stop_stream()
		stream.close()

	def TestPyJack(self):
		CHANNELS=len(self.jaoutlist.curselection())
		self.fs = float(jack.get_sample_rate())
		print(self.jaoutlist.curselection())
		for i in range(0,len(self.jaoutlist.curselection())):
			print(self.jaoutlist.get(self.jaoutlist.curselection()[i]))
		jack.activate()
		for i in range(0,len(self.jaoutlist.curselection())):
			jack.register_port('output_'+str(i), jack.IsOutput)
			jack.connect('measure:output_'+str(i), self.jaoutlist.get(self.jaoutlist.curselection()[i]))
		# Dummy Input
		jack.register_port('dummy_input', jack.IsInput)
		print(jack.get_ports())

		N = jack.get_buffer_size()

		input  = np.zeros((1,len(self.signal)),'f')
		output = np.array(np.tile(self.signal,(CHANNELS,1)),'f')

		x = 0
		while x < output.shape[1] - N:
			try:
				jack.process(output[:,x:x+N], input[:,x:x+N])
				x += N
			except jack.InputSyncError:
				pass
			except jack.OutputSyncError:
				pass	

		for i in range(0,len(self.jaoutlist.curselection())):
			jack.unregister_port('output_'+str(i))
		jack.unregister_port('dummy_input')
		jack.deactivate()

	def testButtonClick(self):
		self.generate_signal[self.sisecb.get()]()
		time.sleep(0.5)
		for i in range(0,int(self.siavg.get())):
			if(self.IsPyAudio()):
				self.TestPyAudio()
			if(self.IsPyJack()):
				self.TestPyJack()
		
	def getImpFilename(self):
		return self.filepath.get()+os.sep+self.prefix.get()+'_IR_'+self.counter.get()+'.wav'

	def getSigFilename(self):
		if self.sisecb.get()=='Golay':
			return self.filepath.get()+os.sep+self.prefix.get()+'_SIG'+self.golaycount+'_'+self.counter.get()+'.wav'
		else:
			return self.filepath.get()+os.sep+self.prefix.get()+'_SIG_'+self.counter.get()+'.wav'
	def getRawFilename(self, avg):
		if self.sisecb.get()=='Golay':
			return self.filepath.get()+os.sep+self.prefix.get()+'_RAW'+self.golaycount+'_'+self.counter.get()+'_AVG_'+str(avg)+'.wav'
		else:
			return self.filepath.get()+os.sep+self.prefix.get()+'_RAW_'+self.counter.get()+'_AVG_'+str(avg)+'.wav'

	def filenotexistscheck(self):
		filenotexists=True
		if self.impcheck.get():
			impfile=self.getImpFilename()
			if os.path.isfile(impfile):
				messagebox.showerror('Datei existiert bereits', 'Die Datei '+impfile+' existiert Bereits!')
				filenotexists=False
		if self.rawcheck.get():
			print('rawcheck')
			for i in range(0,int(self.siavg.get())):
				rawfile=self.getRawFilename(i)
				print('in loop')
				if os.path.isfile(rawfile):
					messagebox.showerror('Datei existiert bereits', 'Die Datei '+rawfile+' existiert Bereits!')
					print('datei existiert')
					filenotexists=False
					break
		if self.sigcheck.get():
			sigfile=self.getSigFilename()
			if os.path.isfile(sigfile):
				messagebox.showerror('Datei existiert bereits', 'Die Datei '+sigfile+' existiert Bereits!')
				filenotexists=False
		return filenotexists
			
	def mesButtonClick(self):
		self.generate_signal[self.sisecb.get()]()
		self.cursiavg=int(self.siavg.get())
		self.golaycount='a'
		filenotexists=self.filenotexistscheck()
		if filenotexists:
			time.sleep(0.5)
			if self.sisecb.get()=='Golay':
				self.golaycount='b'
				filenotexists=self.filenotexistscheck()
				if filenotexists:
					self.signal=self.golaya
					self.golaycount='a'
					for i in range(int(self.siavg.get())):
						if(self.IsPyAudio()):
							self.MesPyAudio()
						if(self.IsPyJack()):
							self.MesPyJack()
					self.rawgolaya=self.raw
					self.raw=[]
					self.cursiavg=int(selfsiavg.get())
					self.signal=self.golayb
					self.golaycount='b'
					for i in range(int(self.siavg.get())):
						if(self.IsPyAudio()):
							self.MesPyAudio()
						if(self.IsPyJack()):
							self.MesPyJack()
					self.rawgolayb=self.raw
					self.inccounter()
			else:
				for i in range(int(self.siavg.get())):
					if(self.IsPyAudio()):
						self.MesPyAudio()
					if(self.IsPyJack()):
						self.MesPyJack()
				if self.sigcheck.get():
					toSave=np.array(self.signal.transpose(),dtype=('float32'))
					scipy.io.wavfile.write(sigfile,int(self.fs),toSave)
				self.inccounter()
	
	def MesPyJack(self):
		OCHANNELS=len(self.jaoutlist.curselection())
		ICHANNELS=len(self.jainplist.curselection())
		self.fs = float(jack.get_sample_rate())
		jack.activate()

		# Register and Connect Output Ports
		for i in range(0,OCHANNELS):
			jack.register_port('output_'+str(i), jack.IsOutput)
			jack.connect('measure:output_'+str(i), self.jaoutlist.get(self.jaoutlist.curselection()[i]))
		# Register and Connect Input Ports
		for i in range(0,ICHANNELS):
			jack.register_port('input_'+str(i), jack.IsInput)
			jack.connect(self.jainplist.get(self.jaoutlist.curselection()[i]), 'measure:input_'+str(i))

		N = jack.get_buffer_size()

		input  = np.zeros((ICHANNELS,len(self.signal)),'f')
		output = np.array(np.tile(self.signal,(OCHANNELS,1)),'f')

		x = 0
		while x < output.shape[1] - N:
			try:
				jack.process(output[:,x:x+N], input[:,x:x+N])
				x += N
			except jack.InputSyncError:
				pass
			except jack.OutputSyncError:
				pass	

		for i in range(0,OCHANNELS):
			jack.unregister_port('output_'+str(i))
		for i in range(0,ICHANNELS):
			jack.unregister_port('input_'+str(i))
		jack.deactivate()

		if self.rawcheck.get():
			rawfile=self.filepath.get()+os.sep+self.prefix.get()+'_RAW_'+self.counter.get()+'_AVG_'+str(int(self.siavg.get())-self.cursiavg)+'.wav'
			toSave = np.array(input.transpose(),dtype=('float32'))	
			scipy.io.wavfile.write(rawfile,int(self.fs), toSave)
			print(rawfile+' saved')
		self.cursiavg-=1

		if self.impcheck.get():
			self.raw.append(input)
			print('append to raw')

		if (self.cursiavg==0) and (self.impcheck.get()):
			self.generateIR()
		#toSave = np.array(output.transpose(),dtype=('float32'))	
		#scipy.io.wavfile.write('measure_output.wav',int(self.fs), toSave)


	def MesPyAudio(self):
		outputdev = self.aodevlist[self.aodevcb.get()]
		inputdev = self.aidevlist[self.aidevcb.get()]
		OCHANNELS=int(self.nooccb.get())
		ICHANNELS=int(self.noiccb.get())
		BUFFER=1024
		self.outputsignal=np.repeat(self.signal, OCHANNELS)*(2**15-1)
		#self.outputsignal=self.signal*(2**15-1)
		self.plpos = 0
		
		ostream = p.open(format=FORMAT,
				channels=OCHANNELS,
				rate=self.fs,
				output=True,
				output_device_index=outputdev,
				stream_callback=self.get_plcb())
		istream = p.open(format=FORMAT,
				channels=ICHANNELS,
				rate=self.fs,
				input=True,
				input_device_index=inputdev)

		self.record=[]
		#ostream.write(self.outputsignal.astype(np.int16).tostring())
		#for i in np.arange(0,len(self.outputsignal)-BUFFER, BUFFER):
			#record.append(istream.read(BUFFER))
			#istream.write(outputsignal[i:i+BUFFER].astype(np.int16).tostring(), BUFFER)
		ostream.start_stream()

		#while istream.is_active():
		#		time.sleep(0.1)
		while ostream.is_active():
			self.record.append(istream.read(BUFFER))
			#time.sleep(0.1)

		ostream.stop_stream()
		ostream.close()
		
		istream.stop_stream()
		istream.close()

		# If selected save raw data as Wavfile
		if self.rawcheck.get():
			rawfile=self.filepath.get()+os.sep+self.prefix.get()+'_RAW_'+self.counter.get()+'_AVG_'+str(int(self.siavg)-self.cursiavg)+'.wav'
			wf = wave.open(rawfile, 'wb')
			wf.setnchannels(ICHANNELS)
			wf.setsampwidth(p.get_sample_size(FORMAT))
			wf.setframerate(self.fs)
			wf.writeframes(b''.join(self.record))
			wf.close()
		self.cursiavg-=1

		# Convert to Numpy array and add to temp raw list
		if self.imgcheck.get():
			MAX_y = 2.0**(p.get_sample_size(FORMAT) * 8 - 1)
			y = np.array(struct.unpack("%dh" % (BUFFER * ICHANNELS), self.record)) / MAX_y
			x = np.array
			for i in range(0,ICHANNELS):
				x[i,:]=y[i::ICHANNELS]
			self.raw.append(x)
			print('raw appened')

		if (self.cursiavg==0) & self.impcheck.get():
			self.generateIR()

	def get_plcb(self):
		def plcb(in_data, frame_count, time_info, status):
			data = self.outputsignal[self.plpos:self.plpos+frame_count].astype(np.int16).tostring()
			self.plpos += frame_count
			return(data, pyaudio.paContinue)
		return plcb
	def get_recb(self):
		def recb(in_data, frame_count, time_info, status):
			self.record.append(in_data)
			return(in_data, pyaudio.paContinue)
		return recb

	def sweepgen(self):
		step=1.0/self.fs
		t1 = float(self.durcb.get())
		t = np.arange(0,t1+step, step)
		f0 = float(self.f0e.get())
		f1 = float(self.f1e.get())

		self.signal=10**(float(self.level.get())/20)*scipy.signal.chirp(t,f0,t1,f1,method=self.sweepmethodcb.get(),phi=90)

	def noisegen(self):
		print('not implemented yet')
	def singen(self):
		print('not implemented yet')
	def squaregen(self):
		print('not implemented yet')
	def sawtoothgen(self):
		print('not implemented yet')
	def mlsgen(self):
		self.signal=10**(float(self.level.get())/20)*mls.generate_mls(int(self.mlsn.get()),self.mlsflag.get())
	def golaygen(self):
		self.golaya, self.golayb=golay.generategolay(int(self.golayn.get()))
	def impulsegen(self):
		self.signal=np.zeros(int(float(self.durcb.get())*self.fs))
		self.signal[0]=10**(float(self.level.get())/20)
	def selectpath(self):
		filepath=filedialog.askdirectory()
		print(filepath)
		if filepath:
			self.filepath.set(filepath)
	def generateIR(self):
		# Average Data
		self.average=self.raw[0]
		for i in range(1,len(self.raw)):
			self.average=self.average+self.raw[i]
		self.average=self.average/len(self.raw)

		if self.sisecb.get()=='Sweep':
			self.generateSweepIR()
		if self.sisecb.get()=='Impuls':
			self.generateImpulseIR()
	def generateSweepIR(self):
		Lsig=len(self.signal)
		Lraw=len(self.average[0,:])
		NFFTsig=nextpow2(Lsig)
		NFFTavg=nextpow2(Lavg)
		if NFFTsig != NFFTraw:
			raise Exception('NFFTsig != NFFTavg')
		else:
			NFFT=int(NFFTsig)
		sigfft=fft(self.signal,n=NFFT)
		N=self.average.shape[0]
		avgfft=fftn(self.average,s=[NFFT])
		imp=np.array(np.zeros(avgfft.shape))
		for i in range(0,N):
			imp[i,:]=np.real(fftshift(ifft(sigfft/avgfft[i,:])))
		toSave=np.array(imp.transpose(), dtype=np.float32)
		impfile=self.filepath.get()+os.sep+self.prefix.get()+'_IR_'+self.counter.get()+'.wav'
		scipy.io.wavfile.write(impfile,int(self.fs),toSave)
		raw=[]
		imp=[]
	def inccounter(self):
		i=int(self.counter.get())
		i+=1
		self.counter.set('0'*(len(self.counter.get())-len(str(i)))+str(i))
	def generateImpulseIR(self):
		toSave=np.array(self.average,dtype=np.float32)
		scipy.io.wavfile.write(self.getImpFilename(),int(self.fs),toSave.transpose())
	def durspchange(self,name,index,mode):
		sec=int(self.dursp.get())/self.fs
		self.dur.set(str(sec))
	def durchange(self,name,index,mode):
		pass
		#samp=float(self.dur.get())*self.fs
		#self.dursp.set(str(int(samp)))
	def delayButtonClick(self):
		pass

root = tkinter.Tk()
mes_gui = MES_GUI(root)
root.mainloop()
p.terminate()
if jack_running:
	jack.detach()
