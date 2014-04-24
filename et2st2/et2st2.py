import parallel
import time

class turntable:
	def __init__(self,direct):
		self.p=parallel.Parallel()
		self.p.setData(0)
		if direct=='fw':
			self.resetafw()
		if direct=='bw':
			self.resetabw()
		#self.deg=0

	def set2deg(self,degree):
		degree=(degree//2.5)*2.5
		print(degree)
		if degree>self.deg:
			while degree>self.deg:
				self.moveaforward()
				print(self.deg)
		if degree<self.deg:
			while degree<self.deg:
				self.moveabackward()
				print(self.deg)
		return(self.deg)
				
	def resetafw(self):
		while self.p.getInPaperOut():
			self.p.setData(self.p.getData() | 1<<3) # Set Data Bit 4 to Highlevel (or)
		else:
			self.p.setData(self.p.getData() & 0b11110111 ) # Set Data bit 4 to off (and)
			self.deg=0
	def resetabw(self):
		while self.p.getInPaperOut():
			self.p.setData(self.p.getData() | 1<<5) # Set Data Bit 4 to Highlevel (or)
		else:
			self.p.setData(self.p.getData() & 0b11011111 ) # Set Data bit 4 to off (and)
			self.deg=0
	def moveaforward(self):
		self.p.setData(self.p.getData() | 1<<3) # Set Data Bit 4 to Highlevel (or)
		time.sleep(0.1)
		while self.p.getInError():
			pass
			#self.p.setData(self.p.getData() | 1<<3) # Set Data Bit 4 to Highlevel (or)
		else:
			self.p.setData(self.p.getData() & 0b11110111 ) # Set Data bit 4 to off (and)
			self.deg+=1.25
	def moveabackward(self):
		self.p.setData(self.p.getData() | 1<<5) # Set Data Bit 6 to Highlevel (or)
		time.sleep(0.1)
		while self.p.getInError():
			pass		
			#self.p.setData(self.p.getData() | 1<<5) # Set Data Bit 6 to Highlevel (or)
		else:
			self.p.setData(self.p.getData() & 0b11011111 ) # Set Data bit 6 to off (and)
			self.deg-=1.25
	def resetb(self):
		while self.p.getInAcknowledge():
			self.p.setData(self.p.getData() | 1<<4) # Set Data Bit 5 to Highlevel (or)
		else:
			self.p.setData(self.p.getData() & 0b11101111 ) # Set Data bit 5 to off (and)
	def movebforward(self):
		self.p.setData(self.p.getData() | 1<<4) # Set Data Bit 5 to Highlevel (or)
		while self.p.getInSelected():
			self.p.setData(self.p.getData() | 1<<4) # Set Data Bit 5 to Highlevel (or)
		else:
			self.p.setData(self.p.getData() & 0b11101111 ) # Set Data bit 5 to off (and)
	def movebbackward(self):
		self.p.setData(self.p.getData() | 1<<6) # Set Data Bit 7 to Highlevel (or)
		while self.p.getInSelected():
			self.p.setData(self.p.getData() | 1<<6) # Set Data Bit 7 to Highlevel (or)
		else:
			self.p.setData(self.p.getData() & 0b11011111 ) # Set Data bit 5 to off (and)	
