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

cc = matplotlib.colors.ColorConverter()

def nextpow2(i):
	return 2**np.ceil(np.log2(i))

class EVA_GUI:
	def __init__(self, parent):
		self.plotdata_dict={'wvplot': self.wvplot, 'psd': self.psdplot, 'spec': self.specplot}
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
		self.evatree.insert('','end','spec', text='Plot Spektogram')
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
			p = subpl.plot(data)
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
	def specplot(self):
		subpl = self.fig.add_subplot(111)
		subpl.hold(False)
		for i in self.fileslist.curselection():
			fs=self.datas[self.fileslist.get(i)][0]
			data=self.datas[self.fileslist.get(i)][1]
			subpl.specgram(data,Fs=fs)
			subpl.hold(True)
		self.plotcanvas.show()

root = tkinter.Tk()
root.columnconfigure(0, weight=1)
root.rowconfigure(0, weight=1)
root.columnconfigure(1, weight=10)
root.rowconfigure(1, weight=6)
eva_gui = EVA_GUI(root)
root.mainloop()

