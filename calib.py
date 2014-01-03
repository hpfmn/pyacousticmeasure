import numpy as np
import tkinter
import tkinter.ttk as ttk
import pysoundfile
import tkinter.filedialog as filedialog
import os
from numpy.fft import fft, ifft, fftshift, ifftshift


def nextpow2(n):
	return 2**np.ceil(np.log2(n))

class CALIB_GUI:
	def __init__(self, parent):
		self.myparent = parent
		self.calibframe = ttk.Frame(self.myparent)
		self.calibframe.grid(row=0,column=0)
		self.datas = dict()

		self.loadbtn = ttk.Button(self.calibframe, text='Laden', command=self.add_files)
		self.loadbtn.grid(row=0, column=0, columnspan=2)

		self.fileslist = tkinter.Listbox(self.calibframe,exportselection=0)
		self.fileslist.grid(row=1, column=0,rowspan=2, sticky=(tkinter.W))
		self.filescroll = ttk.Scrollbar(self.calibframe,orient=tkinter.VERTICAL, command=self.fileslist.yview)
		self.filescroll.grid(row=1,column=1,rowspan=2, sticky=(tkinter.N,tkinter.S,tkinter.E))
		self.fileslist['yscrollcommand'] = self.filescroll.set


		self.upbtn = ttk.Button(self.calibframe, text='↑', command=self.moveup)
		self.upbtn.grid(row=1,column=2)
		self.downbtn = ttk.Button(self.calibframe, text='↓', command=self.movedown)
		self.downbtn.grid(row=2,column=2)


		self.refbtn = ttk.Button(self.calibframe, text='Referenz wählen', command=self.gen_imp)
		self.refbtn.grid(row=3,column=0)
		self.delbtn = ttk.Button(self.calibframe, text='Auswahl entfernen', command=self.rem_files)
		self.delbtn.grid(row=3,column=2)
	def add_files(self):
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
	def rem_files(self):
		while () != self.fileslist.curselection():
			element=self.fileslist.curselection()[0]
			del self.datas[self.fileslist.get(element)]
			self.fileslist.delete(element)
	def gen_imp(self):
		n = len(self.datas.keys())
		
		# Find longest Data
		lngst = ''
		maximum = 0
		for i in range(0,n):
			#cur_dat=list(self.datas.keys())[i]
			cur_dat=self.fileslist.get(i)
			data_long = len(self.datas[cur_dat][1])
			if i == 0:
				Fs = self.datas[cur_dat][0]
			if Fs != self.datas[cur_dat][0]:
				print('WARNING: Wrong FS detected!')
			if data_long>maximum:
				maximum=data_long
				lngst=cur_dat
		NFFT=int(nextpow2(maximum))
		data_fft=np.zeros((NFFT,n), dtype=np.complex128)
		cur_sel=self.fileslist.curselection()
		for i in range(0,n):
			#cur_dat=list(self.datas.keys())[i]
			cur_dat=self.fileslist.get(i)
			data_fft[:,i]=fft(ifftshift(self.datas[cur_dat][1]),n=NFFT)
			if cur_dat == self.fileslist.get(cur_sel[0]):
				reference=data_fft[:,i]
		data_imp=np.zeros((NFFT,n))
		# Generate IMP-Resp
		for i in range(0,n):
			data_imp[:,i]=np.real(fftshift(ifft(reference/data_fft[:,i])))
				
		wav_write = pysoundfile.SoundFile('ImpulseResonses.wav', sample_rate=Fs, channels=data_imp.shape[1], format=('WAV','FLOAT','FILE'), mode=pysoundfile.write_mode)
		wav_write.write(data_imp)
	def moveup(self):
		sel=int(self.fileslist.curselection()[0])
		if ((sel != ()) & (self.fileslist.size()>=2) & (sel>=1)):
			self.fileslist.insert(sel-1,self.fileslist.get(sel))
			self.fileslist.delete(sel+1)
			self.fileslist.select_set(sel-1)
	def movedown(self):
		sel=int(self.fileslist.curselection()[0])
		if ((sel != ()) & (self.fileslist.size()>=2) & ((sel+1)<self.fileslist.size())):
			self.fileslist.insert(sel+2,self.fileslist.get(sel))
			self.fileslist.delete(sel)
			self.fileslist.select_set(sel+1)





root = tkinter.Tk()
calib_gui = CALIB_GUI(root)
root.mainloop()
