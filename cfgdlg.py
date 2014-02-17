# coding=utf8
import sys
if sys.version_info<(3,0,0):
	import Tkinter as tkinter
	import ttk as ttk
else:
	import tkinter
	import tkinter.ttk as ttk

def cfgdlg(params):
	cfgroot = tkinter.Toplevel()
	cfgroot.title(params[0])
	labels=dict()
	elements=dict()
	for i in range(1,len(params)):
		labels['label'+params[i][0]]=ttk.Label(cfgroot,text=params[i][0])
		labels['label'+params[i][0]].grid(row=i-1,column=0)
		# If Parameters is an Entry, create an Entry Widget
		if params[i][1]=='e':
			elements[params[i][0]]=ttk.Entry(cfgroot)
			elements[params[i][0]].value=tkinter.StringVar()
			elements[params[i][0]].config(textvariable=elements[params[i][0]].value)
			elements[params[i][0]].grid(row=i-1,column=1)
			if len(params[i])>2:
				elements[params[i][0]].value.set(params[i][2])

		# Combobox Read Only
		if params[i][1]=='cbro':
			elements[params[i][0]]=ttk.Combobox(cfgroot, exportselection=0,state='readonly')
			elements[params[i][0]].value=tkinter.StringVar()
			elements[params[i][0]].config(textvariable=elements[params[i][0]].value)
			elements[params[i][0]].grid(row=i-1,column=1)
			if len(params[i])>3:
				elements[params[i][0]].configure(values=params[i][3:])
				elements[params[i][0]].set(params[i][2])
		
		# Comboxbox normal State
		if params[i][1]=='cb':
			elements[params[i][0]]=ttk.Combobox(cfgroot, exportselection=0)
			elements[params[i][0]].value=tkinter.StringVar()
			elements[params[i][0]].config(textvariable=elements[params[i][0]].value)
			elements[params[i][0]].grid(row=i-1,column=1)
			if len(params[i])>2:
				elements[params[i][0]].configure(values=params[i][2:])
				elements[params[i][0]].current(0)

		# Checkbutton
		if params[i][1]=='c':
			elements[params[i][0]]=ttk.Checkbutton(cfgroot)
			elements[params[i][0]].value=tkinter.IntVar()
			elements[params[i][0]].config(variable=elements[params[i][0]].value)
			elements[params[i][0]].grid(row=i-1,column=1)
			if len(params[i])>2:
				elements[params[i][0]].value.set(int(params[i][2]))
	
			
	btn=ttk.Button(cfgroot,text='OK',command=cfgroot.destroy)
	btn.grid(row=i,column=0,columnspan=2)
	#cfgroot.mainloop()
	#while run==True:
	#	pass
	cfgroot.wait_window()
	values=dict()
	for i in elements.keys():
		values[i]=elements[i].value.get()
	return values
