#!/usr/bin/python3

# import time
import math
import numpy as np

class Ssd1306Driver:
	DEFAULT_ADDRESS = 0x3C

	ADDRESS_MODE_HORIZONTAL = 0x20 # next page and reset column
	ADDRESS_MODE_VERTICAL = 0x21 # goes vertical in pages and then next column
	ADDRESS_MODE_PAGE = 0x22 # when column ends, go to begin. of same page
	ADDRESS_COL_START = 0x00
	ADDRESS_COL_END = 0x7F
	ADDRESS_PAGE_START = 0x00
	ADDRESS_PAGE_END = 0x07

	bus = None
	address = None

	addr_col_start = ADDRESS_COL_START
	addr_col_end = ADDRESS_COL_END
	addr_page_start = ADDRESS_PAGE_START
	addr_page_end = ADDRESS_PAGE_END

	COLUMN_HIGHT = 8

	char_byte_map = {} # will be filled at initialization time

	def __init__(self, smBus, address = DEFAULT_ADDRESS):
		if address == None:
			address = self.DEFAULT_ADDRESS
		self.bus = smBus
		self.address = address
		self.char_byte_map = {
			'6': self.generate_fonts('4x6')
		}
	
	def calculate_full_byte(self):
		return 2 ** self.COLUMN_HIGHT - 1
	
	def draw_current_column(self, byte = 0x00):
		self.send_data(0x40, byte)

	def fill_current_column(self):
		byte = self.calculate_full_byte()
		self.draw_current_column(byte)

	def fill_current_page(self, byte = None):
		if byte == None:
			byte = self.calculate_full_byte()
		self.set_column_address()
		for _ in range(self.addr_col_start, self.addr_col_end + 1):
			self.draw_current_column(byte)
	
	def clear_screen(self):
		self.fill_screen(0x00)
	
	def fill_screen(self, byte = None):
		if byte == None:
			byte = self.calculate_full_byte()
		self.set_page_address()
		for page_address in range(self.addr_page_start, self.addr_page_end + 1):
			self.fill_current_page(byte)

	def display_on(self):
		self.send_data(0x00, 0xAF)
	
	def display_off(self):
		self.send_data(0x00, 0xAE)
	
	def reset_cursor(self):
		self.set_column_address()
		self.set_page_address()
	
	# 127 max
	def set_column_address(self, start_address = ADDRESS_COL_START, end_address = ADDRESS_COL_END):
		self.addr_col_start = start_address
		self.addr_col_end = end_address

		self.send_data(0x00, 0x21)
		self.send_data(0x00, start_address)
		self.send_data(0x00, end_address)
	
	last_start_address = None
	last_end_address = None
	# 7 max
	def set_page_address(self, start_address = ADDRESS_PAGE_START, end_address = ADDRESS_PAGE_END):
		if start_address == self.last_start_address and end_address == self.last_end_address:
			return
		
		self.addr_page_start = start_address
		self.addr_page_end = end_address

		self.send_data(0x00, 0x22)
		self.send_data(0x00, start_address)
		self.send_data(0x00, end_address)

		self.last_start_address = start_address
		self.last_start_address = end_address
	
	def simple_setup(self):
		self.set_multiplex_ratio()
		self.set_display_offset()
		self.set_start_line()
		self.set_left_right()
		self.set_top_bottom()
		self.set_com_pin_conf()
		self.set_contrast()
		self.set_display_ram_content()
		self.set_display_mode()
		self.set_clock()
		self.set_page_addr_mode()
	
	# 0x10 to 0x3F
	def set_multiplex_ratio(self, ratio = 0x3F):
		self.send_data(0x00, 0xA8)
		self.send_data(0x00, ratio)
	
	def set_display_offset(self, offset = 0x00):
		self.send_data(0x00, 0xD3)
		self.send_data(0x00, offset)
	
	# 0 to 63
	def set_start_line(self, start_line = 0):
		self.send_data(0x00, 0x40 + start_line)
	
	def set_left_right(self, left_right = True):
		if left_right:
			self.send_data(0x00, 0xA1)
		else:
			self.send_data(0x00, 0xA0)
	
	def set_top_bottom(self, top_bottom = True):
		if top_bottom:
			self.send_data(0x00, 0xC8)
		else:
			self.send_data(0x00, 0xC0)
	
	def set_com_pin_conf(self):
		self.send_data(0x00, 0xDA)
		self.send_data(0x00, 0x12)
	
	# from 00 to 7f (127)
	def set_contrast(self, contrast = 0x60):
		self.send_data(0x00, 0x81)
		self.send_data(0x00, contrast)
	
	def set_display_ram_content(self):
		self.send_data(0x00, 0xA4)
	
	def set_disable_ram_content():
		self.send_data(0x00, 0xA5)
	
	# Set Normal/Inverse Display (0xA6 / 0xA7):
	def set_display_mode(self, inverse = False):
		if inverse:
			self.send_data(0x00, 0xA7)
		else:
			self.send_data(0x00, 0xA6)
	
	def set_clock(self):
		self.send_data(0x00, 0xD5)
		self.send_data(0x00, 0x80)
	
	# ??
	def set_charge_pump(self, enable = False):
		self.send_data(0x00, 0x8D)
		if enable:
			self.send_data(0x00, 0x14)
		else:
			self.send_data(0x00, 0x0B)
	
	last_addr_mode = None
	def set_page_addr_mode(self, addr_mode = ADDRESS_MODE_HORIZONTAL):
		if addr_mode == self.last_addr_mode:
			return
		
		self.send_data(0x00, 0x20)
		self.send_data(0x00, addr_mode)

	def send_data(self, command, value):
		self.bus.write_byte_data(self.address, command, value)
	
	###

	def write_screen(self, page, text, begin_addr, size, font_height = 6):
		addr_mode = self.ADDRESS_MODE_HORIZONTAL
		end_page = page
		if font_height > 8:
			addr_mode = self.ADDRESS_MODE_VERTICAL
			end_page += 1
		
		font_height = str(font_height)
		
		self.set_page_addr_mode(addr_mode)
		self.set_page_address(page, end_page)
		self.set_column_address(begin_addr, begin_addr + size)
		for _i, c in enumerate(text):
			
			for b in self.char_byte_map[font_height][c]:
				self.send_data(0x40, b)
			self.send_data(0x40, 0x00) # 1px space
	
	def icon_screen(self, page, icon, begin_addr, font_height = 6):
		self.set_page_addr_mode(self.ADDRESS_MODE_HORIZONTAL)
		self.set_page_address(page, page)
		self.set_column_address(begin_addr, begin_addr + 8)
		for b in self.CHAR_MAP[icon][font_height]:
			self.send_data(0x40, b)

	last_objective_address = None
	def horizontal_bar(self, page, begin_addr, size, percent_fill = 0.0):
		self.set_page_addr_mode(self.ADDRESS_MODE_HORIZONTAL)
		self.set_page_address(page, page)
		max_address = begin_addr + size - 1
		if percent_fill > 1:
			percent_fill = 1
		objective_address = int((max_address - begin_addr) * percent_fill + begin_addr)

		vertical_border = 0xFF
		horizontal_border = 0x81

		if self.last_objective_address == None:
			start_scan = begin_addr
			finish_scan = objective_address
		else:
			start_scan = self.last_objective_address
			finish_scan = objective_address
		
		if start_scan <= finish_scan:
			self.set_column_address(start_scan, finish_scan)
			for _ in range(start_scan, finish_scan):
				self.draw_current_column(vertical_border)
		else:
			self.set_column_address(finish_scan, start_scan)
			for _ in range(finish_scan, start_scan):
				self.draw_current_column(horizontal_border)
		
		# complete first time drawing
		if self.last_objective_address == None:
			self.set_column_address(finish_scan, max_address + 1)
			for _ in range(finish_scan, max_address - 3, 1):
				self.draw_current_column(horizontal_border)
			self.draw_current_column(vertical_border)
		
		self.last_objective_address = objective_address

	def generate_fonts(self, font_name):
		font_map = self.FONT_MAP[font_name]
		char_c = font_map['char_size'][0]
		char_l = font_map['char_size'][1]

		c = -1
		l = 0
		matrixx = {}
		for i, b in enumerate(font_map['data']):
			c += 1
			if c >= font_map['data_size'][0]:
				c = 0
				l += 1
			char_c_current_pos = c % char_c
			current_char = font_map['chars'][math.floor(l/char_l)][math.floor(c/char_c)]
			if not current_char in matrixx:
				matrixx[current_char] = []
			if char_c_current_pos == 0:
				try:
					matrixx[current_char][l%char_l] = []
				except:
					matrixx[current_char].append([])
			elif char_c_current_pos == char_c - 1:
				continue
			matrixx[current_char][l%char_l].append(int(b))
		
		trans_matrix = {}
		for char_m in matrixx:
			trans_matrix[char_m] = np.array(matrixx[char_m]).transpose()
		
		bin_matrix = {}
		for char_m in trans_matrix:
			bin_matrix[char_m] = []
			line = -1
			for char_col in trans_matrix[char_m]:
				line += 1
				bin_matrix[char_m].append(0)
				pos = -1
				for val_pixel in char_col:
					pos += 1
					bin_matrix[char_m][line] += val_pixel * 2 ** pos

		return bin_matrix
	
	# pseudo pixel images to generate the bytes for char_byte_map
	FONT_MAP = {
		'3x6': {
			'char_size': [4, 8],
			'chars': [
				'abcdefghijklmnopqrstuvwxyz',
				'ABCDEFGHIJKLMNOPQRSTUVWXYZ',
				"0123456789.:,;(*!?')/-    "
			],
			'data_size': [104, 24],
			'data': '000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000100000000010000000100000100001000010100011000000000000000000000000000000010000000000000000000000000001101100011001100100010001101100000000001010010010101100010011000110101001101110101010101010101010101110101010101000101010101110101010101100001011000100111010101010101010101100110001001010101010100100101000101010101010001010110001000110101001000010101001001010101010101100101010000010010010101010111001000110010001101100011001100110010000101010111000101010111010101010010010000110100011000010011001001010101000101110000000000000000000000000110000000000110000000000000000000000100000100000000000000000000000000000110000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000010011000100110011101110011010101110001010101000101000100100110001001100011011101010101010101010101011101010101010101010100010001000101001000010101010001110101010101010101010101000010010101010101010101010001011101100100010101100110010101110010000101100100011101110101011001010110001000100101010101110010001000100101010101010101010001000101010100100101010101000101010101010100010101010001001001010111011101010010010001010110001001100111010000110101011100100101011101010100001001000010010101100010011100100101010100100111000000000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000001000100010011101010111001101110011001000000000000000000001010100100110001001000001000000000000000000000101011001010001010101000100000101010101000000100000001000100010001000010010001000010000000000000000000001110010000100100111011001100010001000110000000000000000001001110010001000000010001000000000000000000000010100100010000100010001010101000101000100000000000000000010001000000000000000100010011100000000000000000010011101110110000101100010010001100110001000100010001000100101001000100000001001000000000000000000000000000000000000000000000000000000000000000000000001000100000100000000000000000100010000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000'
		},
		'4x6': {
			'char_size': [5, 8],
			'chars': [
				'abcdefghijklmnopqrstuvwxyz',
				'ABCDEFGHIJKLMNOPQRSTUVWXYZ',
				"0123456789.:,;(*!?')/-    "
			],
			'data_size': [130, 24],
			'data': '000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000100000000000010000000010000000100000010000010100000110000000000000000000000000000000000000010000000000000000000000000000000000000010000000000001000000010100000010000000000000010000001000000000000000000000000000000000000001000000000000000000000000000000000011101110001100011100110001000011101110001100000101010000100101001110001100111000111011100011101110010010010101001010010100101111010010100101000010010101101110010010100100010000010110000010011110100101001010010100101001011000010001001001010100100110010010001001011010010100001001011000010000110010010001000001010100001001001010010100101001010010100000011001000100100101011110011000101001000010101110001100011100110001000100001001001110010101001001110100101001001100111000111010000111000011001110001001111010010001001111000000000000000000000000000000001110000000000000100000000000000000000000000010000000100000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000011001110001100111001111011110011001001001110000101001010000100101001001100111000110011100011000111010010100101001010010010101111010010100101001010010100001000010010100100010000010101001000011110110101001010010100101001010010001001001010010100101001001010000101001011100100001001011100111001000011110001000001011000100001111011010100101001010010100100100000100100101001010010011000101000100111101001010000100101000010000101101001000100000101100010000100101011010010111001001011100001000010010010100101111001100001000100010010100101001010010100001000010010100100010010010101001000010010101101001010000110101010010010001001001001100111101001000100100001001011100011001110011110100000111010010011100110010010111101001010010011001000001100100100110000100011000110010010100100010011110000000000000000000000000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000010000100011001111000100111100110011110011000110000000000000000000000001000000000100001000010001000001000000000000000000000000000010100110010010000100110010000100000001010010100100000001100000000110001000010100010001010001000010000100000000000000000000000000001010001000001001100101001110011100001000110010010000000110000000011000100000100001000001000100001000100000000000000000000000000000101000100001000001011110000101001000100100100111000000000000000000000010000111000100001000000000100010001110000000000000000000000010100010001000100100010010010100100100010010000100110001100001100110001000001000000000000000000010010000000000000000000000000000000100011101111001100001000110001100010000110001100011000110000100010000010001010001000010000000010001000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000100010000000000000000000000000000000000000000000000000000000000000000'
		}
	}

	# mapping the binary for the icons
	CHAR_MAP = {
		'speed': {
			6: [0b00111000, 0b01000100, 0b01001010, 0b01010010, 0b01000010, 0b01000100, 0b00111000]
		},
		'maxspeed': {
			6: [0b00111000, 0b01000100, 0b01000010, 0b01010010, 0b01010010, 0b01010100, 0b00111000]
		}
	}