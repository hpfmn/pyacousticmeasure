import tkinter
import tkinter.ttk as ttk
import mes
import eva
import calib

root = tkinter.Tk()

master = ttk.Notebook(root)
master.pack(fill=tkinter.BOTH)

mesframe=ttk.Frame(master)
evaframe=ttk.Frame(master)
calibframe=ttk.Frame(master)

mesgui=mes.MES_GUI(mesframe)
evagui=eva.EVA_GUI(evaframe)
calibgui=calib.CALIB_GUI(calibframe)

master.add(mesframe, text='Messen')
master.add(evaframe, text='Auswerten')
master.add(calibframe, text='Kalibrieren')

root.mainloop()
