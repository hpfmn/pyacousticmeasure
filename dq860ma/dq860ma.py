import parallel
import time

class turntable:
	def __init__(self,dir,rate):
		self.p=parallel.Parallel()
		self.setdir(dir)
		self.dir=dir
		self.rate=rate
		self.pulsef(self.rate*2000)
		if (dir=='fw')
			self.deg=248.5
		if (dir=='bw')
			self.deg=253
	def pulsef(self,f):
		while self.p.getInBusy():
			self.p.setData(self.p.getData() | 0b00000001)
			time.sleep(1.0/f)
			self.p.setData(self.p.getData() & 0b11111110)
	def pulsec(self,count,f):
		for i in range(count):
			self.p.setData(self.p.getData() | 0b00000001)
			time.sleep(1.0/f)
			self.p.setData(self.p.getData() & 0b11111110)
	def setdir(self,dir):
		if (dir=='fw'):
			self.p.setData(self.p.getData() & 0b11111101)
		elif (dir=='bw'):
			 self.p.setData(self.p.getData() | 0b00000010)
		self.dir=dir

				
