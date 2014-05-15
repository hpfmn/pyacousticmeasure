import parallel
import time

class turntable:
	def __init__(self):
		self.p=parallel.Parallel()
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
				
