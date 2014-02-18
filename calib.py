# coding=utf8
import numpy as np
import sys
if sys.version_info<(3,0,0):
	import Tkinter as tkinter
	import ttk as ttk
	import tkFileDialog as filedialog
else:
	import tkinter
	import tkinter.ttk as ttk
	import tkinter.filedialog as filedialog
import pysoundfile
import os
import os.path
from numpy.fft import fft, ifft, fftshift, ifftshift


def nextpow2(n):
	return 2**np.ceil(np.log2(n))

class CALIB_GUI:
	def __init__(self, parent):
		self.myparent = parent
		self.myparent.rowconfigure(0,weight=1)
		self.myparent.rowconfigure(1,weight=1)
		self.myparent.columnconfigure(0,weight=1)
		self.calibframe = ttk.LabelFrame(self.myparent, text='Impulsantwort erstellen')
		self.calibframe.grid(row=0,column=0, sticky=tkinter.W+tkinter.E+tkinter.S+tkinter.N)
		self.calibframe.rowconfigure(0,weight=0)
		self.calibframe.rowconfigure(1,weight=1)
		self.calibframe.rowconfigure(2,weight=1)
		self.calibframe.columnconfigure(0,weight=1)
		self.calibframe.columnconfigure(1,weight=0)
		self.calibframe.columnconfigure(2,weight=0)
		self.datas = dict()

		self.loadbtn = ttk.Button(self.calibframe, text='Laden', command=self.add_files)
		self.loadbtn.grid(row=0, column=0, columnspan=3,sticky=tkinter.W+tkinter.E+tkinter.N)

		self.fileslist = tkinter.Listbox(self.calibframe,exportselection=0)
		self.fileslist.grid(row=1, column=0,rowspan=2, sticky=tkinter.W+tkinter.E+tkinter.S+tkinter.N)
		self.filescroll = ttk.Scrollbar(self.calibframe,orient=tkinter.VERTICAL, command=self.fileslist.yview)
		self.filescroll.grid(row=1,column=1,rowspan=2, sticky=(tkinter.N,tkinter.S,tkinter.E))
		self.fileslist['yscrollcommand'] = self.filescroll.set


		self.upbtn = ttk.Button(self.calibframe, text='↑', command=self.moveup)
		self.upbtn.grid(row=1,column=2,sticky=tkinter.N+tkinter.W+tkinter.E)
		self.downbtn = ttk.Button(self.calibframe, text='↓', command=self.movedown)
		self.downbtn.grid(row=2,column=2, sticky=tkinter.S+tkinter.W+tkinter.E)


		self.refbtn = ttk.Button(self.calibframe, text='Referenz wählen', command=self.gen_imp)
		self.refbtn.grid(row=3,column=0,sticky=tkinter.W+tkinter.E+tkinter.S)
		self.delbtn = ttk.Button(self.calibframe, text='Auswahl entfernen', command=self.rem_files)
		self.delbtn.grid(row=3,column=2,sticky=tkinter.E+tkinter.S)


		# Convolution Frame

		self.convframe = ttk.LabelFrame(self.myparent, text='Dateien mit Impulsantwort falten')
		self.convframe.grid(row=1,column=0,sticky=tkinter.W+tkinter.E+tkinter.S+tkinter.N)
		self.convframe.rowconfigure(0,weight=1)
		self.convframe.rowconfigure(1,weight=1)
		self.convframe.rowconfigure(2,weight=1)
		self.convframe.rowconfigure(3,weight=1)
		self.convframe.rowconfigure(4,weight=1)
		self.convframe.rowconfigure(5,weight=1)
		self.convframe.columnconfigure(0,weight=0)
		self.convframe.columnconfigure(1,weight=1)
		self.convframe.columnconfigure(2,weight=0)

		self.multichannellabel= ttk.Label(self.convframe, text='Multichannel Datei')
		self.multichannellabel.grid(row=0,column=0,sticky=tkinter.E+tkinter.W)
		self.multichannel=tkinter.IntVar()
		self.multichannel.set(1)
		self.multichannelcheck=ttk.Checkbutton(self.convframe, variable=self.multichannel, command=self.multichtoggle)
		self.multichannelcheck.grid(row=0,column=1)

		self.fftconvlabel= ttk.Label(self.convframe, text='FFT Faltung')
		self.fftconvlabel.grid(row=1,column=0,sticky=tkinter.E+tkinter.W)
		self.fftconv=tkinter.IntVar()
		self.fftconv.set(1)
		self.fftconvcheck=ttk.Checkbutton(self.convframe, variable=self.multichannel, command=self.multichtoggle)
		self.fftconvcheck.grid(row=1,column=1)

		self.impfile=tkinter.StringVar()
		self.impfilelabel=ttk.Label(self.convframe, text='Impulsantwort:')
		self.impfilee=ttk.Entry(self.convframe, textvariable=self.impfile)
		self.impfilelabel.grid(row=2,column=0,sticky=tkinter.E+tkinter.W)
		self.impfilee.grid(row=2,column=1,sticky=tkinter.E+tkinter.W)
		self.openimpfilebtn=ttk.Button(self.convframe, text='Impulsantwort wählen', command=self.chooseimp)
		self.openimpfilebtn.grid(row=2,column=2,sticky=tkinter.E+tkinter.W)


		self.filespath=tkinter.StringVar()
		self.pathlabel=ttk.Label(self.convframe, text='Pfad:')
		self.pathe=ttk.Entry(self.convframe, textvariable=self.filespath)
		self.openfilespath=ttk.Button(self.convframe, text='Bearbeitungs-Pfad wählen', command=self.choosepath)
		self.pathlabel.grid(row=3, column=0,sticky=tkinter.E+tkinter.W)
		self.pathe.grid(row=3,column=1,sticky=tkinter.E+tkinter.W)
		self.openfilespath.grid(row=3,column=2,sticky=tkinter.E+tkinter.W)

		self.prefixlabel=ttk.Label(self.convframe, text='Dateianfang:')
		self.prefix=tkinter.StringVar()
		self.prefixe=ttk.Entry(self.convframe, textvariable=self.prefix)
		self.prefixlabel.grid(row=4,column=0,sticky=tkinter.E+tkinter.W)
		self.prefixe.grid(row=4,column=1,sticky=tkinter.E+tkinter.W)

		self.channelframe=ttk.Frame(self.convframe)
		self.channeldigits=tkinter.IntVar()
		self.channeldigits.set(2)
		self.channeldigitslabel=ttk.Label(self.channelframe,text='Anzahl Kanalnummernstellen')
		self.channeldigitse=ttk.Entry(self.channelframe,textvariable=self.channeldigits)
		self.channeldigitslabel.grid(row=0,column=0,sticky=tkinter.E+tkinter+W)
		self.channeldigitse.grid(row=0,column=1, columnspan=2,sticky=tkinter.E+tkinter+W)
		self.channelstartlabel.ttk.Label(self.channelframe,text='Erste Kanalnummer')
		self.channelstart=tkinter.IntVar()
		self.channelstart.set(1)
		self.channelstarte=ttk.Entry(self.channelframe,textvariable=self.channelstart)
		self.channelstartlabel.grid(row=1,column=0,sticky=tkinter.E+tkinter+W)
		self.channelstarte.grid(row=1,column=1, columnspan=2,sticky=tkinter.E+tkinter+W)

		self.convbutton=ttk.Button(self.convframe, text='Falten',command=self.convfiles)
		self.convbutton.grid(row=6,column=0,columnspan=3,sticky=tkinter.E+tkinter.W+tkinter.S)
		
		

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
	
	def chooseimp(self):
		impfile = filedialog.askopenfilename(filetypes=[('Wav-Files','*.wav')])
		if impfile!='':
			self.impfile.set(impfile)
	def choosepath(self):
		path=filedialog.askdirectory()
		if path:
			self.filespath.set(path)
	def multichtoggle(self):
		if self.multichannel.get():
			self.channelframe.grid_forget()
		else:
			self.channelframe.grid(row=5,column=0,columnspan=3,sticky=tkinter.E+tkinter.W+tkinter.S+tkiner.N)
	def convfiles(self):
		impfile=self.impfile.get()
		path=self.filespath.get()
		prefix=self.prefix.get()
		if (impfile!='') & (path!='') & (prefix!=''):
			convfiles=[]
			impwav=pysoundfile.Soundfile(impfile)
			impch=impwav.channels
			impfs=impwav.sample_rate
			impdata=impwav.read(impwav.frames)
			savepath=os.path.join(path,'Gefaltet')
			if not os.path.exists(savepath):
				os.makedirs(savepath)
			if self.multichannel.get():
				for files in os.listdir(path):
					if os.path.isfile(files) and (files.find(prefix)!=-1) and (files[-4:].upper == '.WAV'):
						convfiles.append(files)
				for convfile in convfiles:
					convfilepath=os.path.join(path,convfile)
					wav=pysoundfile.Soundfile(convfilepath)
					convfilefs=wav.sample_rate
					convfilech=wav.channels
					convfiledata=wav.read(wav.frames)
					if convfilefs==impfs and convfilech==impch:
						outdata=np.zeros((convfiledata.shape))
						for i in range(imch):
							if fftconv.get():
								outdata[:,i]=scipy.signal.fftconvolve(convfiledata[:,i],impdata[:,i],mode='same')
							else:
								outdata[:,i]=scipy.signal.convolve(convfiledata[:,i],impdata[:,i],mode='same')
						toSave=np.array(outdata,dtype=np.float32)
						scipy.io.wavfile.write(os.path.join(savepath,'CONV'convfile),convfilefs,toSave)
					else:
						print('Wrong FS or CH-Count')
			else:
				for i in range(impch):
					channelstr=int(self.channeldigits.get()-self.len(str(i+self.channelstart.get())))*'0' + str(i+self.channelstart.get())
					chanpref=prefix+channelstr
					for files in os.listdir(path):
						if os.path.isfile(files) and (files.find(chanpref)!=-1) and (files[-4:].upper == '.WAV'):
								convfiles.append(files)
					for convfile in convfiles:
						convfilepath=os.path.join(path,convfile)
						wav=pysoundfile.Soundfile(convfilepath)
						convfilefs=wav.sample_rate
						convfilech=wav.channels
						convfiledata=wav.read(wav.frames)
						if convfilefs==impfs and convfilech==1:
							outdata=np.zeros((convfiledata.shape))
							if fftconv.get():
								outdata=scipy.signal.fftconvolve(convfiledata,impdata[:,i],mode='same')
							else:
								outdata=scipy.signal.convolve(convfiledata,impdata[:,i],mode='same')
							toSave=np.array(outdata,dtype=np.float32)
							scipy.io.wavfile.write(os.path.join(savepath,'CONV'convfile),convfilefs,toSave)
						else:
							print('Wrong FS or CH-Count')

		else:
			print('everything has to be filled out')





#root = tkinter.Tk()
#calib_gui = CALIB_GUI(root)
#root.mainloop()
