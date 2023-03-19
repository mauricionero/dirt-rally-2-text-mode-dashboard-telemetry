#!/usr/bin/python3

class Mcp23017Driver:
	# positions -> 0 to 7 for the GPIOA0...GPIOA7, 8 to 15 for the GPIOB0...GPIOB7

	address = 0x20
	bus = None
	GPA = 0
	GPB = 1
	mem_inout = {
		GPA: 0,
		GPB: 0
	}
	inout_dirt = {
		GPA: False,
		GPB: False
	}
	mem_values = {
		GPA: 0,
		GPB: 0
	}
	values_dirt = {
		GPA: False,
		GPB: False
	}

	def __init__(self, smBus, address = 0x20):
		self.bus = smBus
		self.address = address
	
	def switch_to_output(self, position, set_output = True, dont_sync = False):
		if position >= 8:
			GP = self.GPB
			pin = position - 8
		else:
			GP = self.GPA
			pin = position
		self.inout_dirt[GP] = True
		
		if set_output:
			self.mem_inout[GP] &= ~(1 << pin)
		else:
			self.mem_inout[GP] |= (1 << pin)
		
		if dont_sync:
			return
		
		self.sync_data()
	
	def set_pin_value(self, position, value, dont_sync = False):
		if position >= 8:
			GP = self.GPB
			pin = position - 8
		else:
			GP = self.GPA
			pin = position
		self.values_dirt[GP] = True
		
		if value:
			self.mem_values[GP] |= (1 << pin)
		else:
			self.mem_values[GP] &= ~(1 << pin)
		
		if dont_sync:
			return
		
		self.sync_data()
	
	def sync_data(self, force = False):
		if self.inout_dirt[self.GPA] or force:
			self.sync_inout(self.GPA)
		if self.inout_dirt[self.GPB] or force:
			self.sync_inout(self.GPB)
		if self.values_dirt[self.GPA] or force:
			self.sync_values(self.GPA)
		if self.values_dirt[self.GPB] or force:
			self.sync_values(self.GPB)
	
	def sync_inout(self, gp):
		command = 0x00 if gp == self.GPA else 0x01
		self.send_data(command, self.mem_inout[gp])
		self.inout_dirt[gp] = False
	
	def sync_values(self, gp):
		command = 0x14 if gp == self.GPA else 0x15
		self.send_data(command, self.mem_values[gp])
		self.values_dirt[gp] = False
	
	def send_data(self, command, value):
		# print(">", self.address, command, value)
		self.bus.write_byte_data(self.address, command, value)