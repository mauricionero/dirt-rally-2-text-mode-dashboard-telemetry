#!/usr/bin/python3

# reference: https://gist.github.com/adrianjost/7673ca97c15f5b9e05c3af94b660b6c4

# set udp connection as true and extra_params to 3
# ~/.local/share/Steam/steamapps/compatdata/690790/pfx/drive_c/users/steamuser/Documents/My Games/DiRT Rally 2.0/hardwaresettings

##################
## CONFIGURATIONS

HIGH_RPM_PERCENTAGE = 8

SIMULATED_DATA = False # For debugging without real data

# VISUAL OFFSETS
SHIFT_LIGHT_V_OFFSET = 4
RPM_V_OFFSET = SHIFT_LIGHT_V_OFFSET + 2
GEAR_V_OFFSET = RPM_V_OFFSET + 3
DEBUG_V_OFFSET = GEAR_V_OFFSET
BUTTONS_V_OFFSET = GEAR_V_OFFSET

## CONFIGURATIONS
##################

import socket
import time
import struct
import curses
import random
# import evdev

time.sleep(3)

DIRT_IP = ""
DIRT_PORT = 20777

RUN_TIME = 0
LAP_TIME = 1
SPEED_POS = 7
GEAR_POS = 33
RPM_POS = 37
TIRE_PRESSURE_FL = 57
COMPLETED_LAPS = 59
TOTAL_LAPS = 60
MAX_RPM_POS = 63
IDLE_RPM_POS = 64
MAX_GEARS_POS = 65

HLINE = u'\u2500' # ─
VLINE = u'\u2502' # │
TRLINE = u'\u2510' # ┐
TLLINE = u'\u250C' # ┌
BLLINE = u'\u2514' # └
BRLINE = u'\u2518' # ┘
FULLBLOCK = u'\u2588' # █
SHADEBLOCK = u'\u2592' # ▒

# devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
# for device in devices:
# 	print(device.path, device.name, device.phys)
# print("====")

# device = evdev.InputDevice('/dev/input/event22')

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((DIRT_IP, DIRT_PORT))

window = curses.initscr()
window.nodelay(True)
curses.curs_set(0)
window.keypad(1)
curses.mousemask(1)
window.clear()
window.refresh()
window_rows, window_cols = window.getmaxyx()
window_middle = int(window_cols / 2)

gear_window = None
rpm_window = None
shiftlight_window = None
buttons_window = None

rpm_info_size = 0
rpm_idle_size = 0
rpm_max_size = 0
rpm_shift_light = 0
rpm_shift_light_size = 0
shift_light_h_size = 0
shift_light_v_size = 0
shift_light_h_begin = 0
gear_h_size = 0
gear_v_size = 0

curses.start_color()
RPM_LOW_COLOR = 1
curses.init_pair(RPM_LOW_COLOR, curses.COLOR_BLUE, curses.COLOR_BLACK)
RPM_COLOR = 2
curses.init_pair(RPM_COLOR, curses.COLOR_GREEN, curses.COLOR_BLACK)
RPM_HIGH_COLOR = 3
curses.init_pair(RPM_HIGH_COLOR, curses.COLOR_RED, curses.COLOR_BLACK)
RPM_SUPER_HIGH_COLOR = 4
curses.init_pair(RPM_SUPER_HIGH_COLOR, curses.COLOR_YELLOW, curses.COLOR_BLACK)
BACKGROUND_COLOR = 5
curses.init_pair(BACKGROUND_COLOR, curses.COLOR_BLACK, curses.COLOR_BLACK)
RPM_INFO_COLOR = 6
curses.init_pair(RPM_INFO_COLOR, curses.COLOR_WHITE, curses.COLOR_BLUE)
GEAR_COLOR = 7
curses.init_pair(GEAR_COLOR, curses.COLOR_WHITE, curses.COLOR_BLACK)
BUTTON_COLOR = 8
curses.init_pair(BUTTON_COLOR, curses.COLOR_WHITE, curses.COLOR_BLACK)

def bit_stream_to_float32(data, pos):
	pos *= 4
	try:
		value = struct.unpack('f', data[pos:pos+4])[0]
	except struct.error as _:
		value = 0
		# print('Failed to get data item at pos {}'.format(pos))
	except Exception as e:
		value = 0
		# print('Failed to get data item at pos {}. Make sure to set extradata=3 in the hardware settings.'.format(pos))
	return value


def draw_interface():
	try:
		draw_rpm_bar()
		draw_shift_light_bar()
		draw_gear_bar()
		# draw_buttons()
	except curses.error:
		return


def draw_buttons():
	global buttons_window
	global buttons_v_size
	global buttons_h_size
	global buttons_h_begin

	button_h_size = 3
	button_v_size = 1
	button_v_spaces = 1

	buttons_v_size = (button_v_size * 2) + button_v_spaces + 2
	buttons_h_size = button_h_size + 2
	buttons_h_begin = window_cols - buttons_h_size - 1

	buttons_window = window.subwin(buttons_v_size, buttons_h_size, BUTTONS_V_OFFSET, buttons_h_begin)
	buttons_window.box()
	buttons_window.addstr(1, 1, " ⬆️ ", curses.color_pair(BUTTON_COLOR) | curses.A_BOLD)
	buttons_window.addstr(1 + button_v_size + button_v_spaces, 1, " ⬇️ ", curses.color_pair(BUTTON_COLOR) | curses.A_BOLD)
	
	buttons_window.refresh()


def button_interaction(mx, my):
	return ""


def draw_gear_bar():
	global gear_h_size
	global gear_v_size
	global gear_window

	gear_h_begin = 1

	gear_v_size = 7
	gear_h_size = 9

	gear_window = window.subwin(gear_v_size, gear_h_size, GEAR_V_OFFSET, gear_h_begin)
	gear_window.box()
	gear_window.refresh()


def print_gear(gear):
	global gear_window

	h_offset = 2

	if gear == -1:
		gear_window.addstr(1, h_offset, "┏━━━┓ ", curses.color_pair(GEAR_COLOR) | curses.A_BOLD)
		gear_window.addstr(2, h_offset, "┃   ┃ ", curses.color_pair(GEAR_COLOR) | curses.A_BOLD)
		gear_window.addstr(3, h_offset, "┣━━━┛ ", curses.color_pair(GEAR_COLOR) | curses.A_BOLD)
		gear_window.addstr(4, h_offset, "┃  ╲  ", curses.color_pair(GEAR_COLOR) | curses.A_BOLD)
		gear_window.addstr(5, h_offset, "      ", curses.color_pair(GEAR_COLOR) | curses.A_BOLD)
	elif gear == 0:
		gear_window.addstr(1, h_offset, "┏━━━┓ ", curses.color_pair(GEAR_COLOR) | curses.A_BOLD)
		gear_window.addstr(2, h_offset, "┃   ┃ ", curses.color_pair(GEAR_COLOR) | curses.A_BOLD)
		gear_window.addstr(3, h_offset, "┃   ┃ ", curses.color_pair(GEAR_COLOR) | curses.A_BOLD)
		gear_window.addstr(4, h_offset, "┃   ┃ ", curses.color_pair(GEAR_COLOR) | curses.A_BOLD)
		gear_window.addstr(5, h_offset, "┗━━━┛ ", curses.color_pair(GEAR_COLOR) | curses.A_BOLD)
	elif gear == 1:
		gear_window.addstr(1, h_offset, " ━┓   ", curses.color_pair(GEAR_COLOR) | curses.A_BOLD)
		gear_window.addstr(2, h_offset, "  ┃   ", curses.color_pair(GEAR_COLOR) | curses.A_BOLD)
		gear_window.addstr(3, h_offset, "  ┃   ", curses.color_pair(GEAR_COLOR) | curses.A_BOLD)
		gear_window.addstr(4, h_offset, "  ┃   ", curses.color_pair(GEAR_COLOR) | curses.A_BOLD)
		gear_window.addstr(5, h_offset, " ━┻━  ", curses.color_pair(GEAR_COLOR) | curses.A_BOLD)
	elif gear == 2:
		gear_window.addstr(1, h_offset, " ━━━┓ ", curses.color_pair(GEAR_COLOR) | curses.A_BOLD)
		gear_window.addstr(2, h_offset, "    ┃ ", curses.color_pair(GEAR_COLOR) | curses.A_BOLD)
		gear_window.addstr(3, h_offset, "┏━━━┛ ", curses.color_pair(GEAR_COLOR) | curses.A_BOLD)
		gear_window.addstr(4, h_offset, "┃     ", curses.color_pair(GEAR_COLOR) | curses.A_BOLD)
		gear_window.addstr(5, h_offset, "┗━━━  ", curses.color_pair(GEAR_COLOR) | curses.A_BOLD)
	elif gear == 3:
		gear_window.addstr(1, h_offset, " ━━━┓ ", curses.color_pair(GEAR_COLOR) | curses.A_BOLD)
		gear_window.addstr(2, h_offset, "    ┃ ", curses.color_pair(GEAR_COLOR) | curses.A_BOLD)
		gear_window.addstr(3, h_offset, " ━━━┫ ", curses.color_pair(GEAR_COLOR) | curses.A_BOLD)
		gear_window.addstr(4, h_offset, "    ┃ ", curses.color_pair(GEAR_COLOR) | curses.A_BOLD)
		gear_window.addstr(5, h_offset, " ━━━┛ ", curses.color_pair(GEAR_COLOR) | curses.A_BOLD)
	elif gear == 4:
		gear_window.addstr(1, h_offset, "╻   ╻ ", curses.color_pair(GEAR_COLOR) | curses.A_BOLD)
		gear_window.addstr(2, h_offset, "┃   ┃ ", curses.color_pair(GEAR_COLOR) | curses.A_BOLD)
		gear_window.addstr(3, h_offset, "┗━━━┫ ", curses.color_pair(GEAR_COLOR) | curses.A_BOLD)
		gear_window.addstr(4, h_offset, "    ┃ ", curses.color_pair(GEAR_COLOR) | curses.A_BOLD)
		gear_window.addstr(5, h_offset, "    ╹ ", curses.color_pair(GEAR_COLOR) | curses.A_BOLD)
	elif gear == 5:
		gear_window.addstr(1, h_offset, "┏━━━  ", curses.color_pair(GEAR_COLOR) | curses.A_BOLD)
		gear_window.addstr(2, h_offset, "┃     ", curses.color_pair(GEAR_COLOR) | curses.A_BOLD)
		gear_window.addstr(3, h_offset, "┗━━━┓ ", curses.color_pair(GEAR_COLOR) | curses.A_BOLD)
		gear_window.addstr(4, h_offset, "    ┃ ", curses.color_pair(GEAR_COLOR) | curses.A_BOLD)
		gear_window.addstr(5, h_offset, " ━━━┛ ", curses.color_pair(GEAR_COLOR) | curses.A_BOLD)
	elif gear == 6 :
		gear_window.addstr(1, h_offset, "┏━━━  ", curses.color_pair(GEAR_COLOR) | curses.A_BOLD)
		gear_window.addstr(2, h_offset, "┃     ", curses.color_pair(GEAR_COLOR) | curses.A_BOLD)
		gear_window.addstr(3, h_offset, "┣━━━┓ ", curses.color_pair(GEAR_COLOR) | curses.A_BOLD)
		gear_window.addstr(4, h_offset, "┃   ┃ ", curses.color_pair(GEAR_COLOR) | curses.A_BOLD)
		gear_window.addstr(5, h_offset, "┗━━━┛ ", curses.color_pair(GEAR_COLOR) | curses.A_BOLD)
	elif gear == 7:
		gear_window.addstr(1, h_offset, " ━━━┓ ", curses.color_pair(GEAR_COLOR) | curses.A_BOLD)
		gear_window.addstr(2, h_offset, "    ┃ ", curses.color_pair(GEAR_COLOR) | curses.A_BOLD)
		gear_window.addstr(3, h_offset, "    ┃ ", curses.color_pair(GEAR_COLOR) | curses.A_BOLD)
		gear_window.addstr(4, h_offset, "    ┃ ", curses.color_pair(GEAR_COLOR) | curses.A_BOLD)
		gear_window.addstr(5, h_offset, "    ╹ ", curses.color_pair(GEAR_COLOR) | curses.A_BOLD)

def draw_shift_light_bar():
	global window_cols
	global window_middle
	global shift_light_h_size
	global shift_light_v_size
	global shift_light_h_begin
	global shiftlight_window

	shift_light_h_size = int(window_cols / 2)
	shift_light_v_size = 2

	shift_light_h_begin = int(window_middle - (shift_light_h_size / 2))

	shiftlight_window = window.subwin(shift_light_v_size, shift_light_h_size, SHIFT_LIGHT_V_OFFSET, shift_light_h_begin)
	shiftlight_window.refresh()


def print_shift_light(rpm):
	global window_middle
	global rpm_shift_light
	global shift_light_h_size
	global shift_light_v_size
	global shift_light_h_begin
	global shiftlight_window

	if rpm >= rpm_shift_light:
		color = RPM_HIGH_COLOR
		shiftlight_window.bkgdset(curses.COLOR_RED)
	else:
		color = BACKGROUND_COLOR
		shiftlight_window.bkgdset(curses.COLOR_BLACK)

	try:
		for i in range(shift_light_v_size):
			shiftlight_window.addstr(i, 0, FULLBLOCK * (shift_light_h_size - 1), curses.color_pair(color))
	except curses.error:
		return


def draw_rpm_bar():
	global window_cols
	global rpm_info_size
	global rpm_window

	rpm_h_begin = 1

	rpm_v_size = 3
	rpm_h_size = window_cols - 2

	rpm_window = window.subwin(rpm_v_size, rpm_h_size, RPM_V_OFFSET, rpm_h_begin)
	rpm_window.box()

	# rpm_window.addstr(1, 1, "   ", curses.color_pair(RPM_INFO_COLOR) | curses.A_BOLD)

	rpm_window.refresh()

	rpm_info_size = window_cols - 6


def print_rpm(rpm, max_rpm, idle_rpm):
	global rpm_info_size
	global rpm_idle_size
	global rpm_max_size
	global rpm_shift_light_size
	global rpm_window

	if max_rpm == 0:
		max_rpm = 5000

	rpm_size = int((rpm / max_rpm) * rpm_info_size)
	fill_background = True

	rpm_info_v_begin = 1
	rpm_info_h_begin = 2

	try:
		if rpm <= idle_rpm:
			rpm_window.addstr(rpm_info_v_begin, rpm_info_h_begin, FULLBLOCK * rpm_size, curses.color_pair(RPM_LOW_COLOR))
		else:
			rpm_window.addstr(rpm_info_v_begin, rpm_info_h_begin, FULLBLOCK * rpm_idle_size, curses.color_pair(RPM_LOW_COLOR))
			if rpm_size <= rpm_shift_light_size:
				rpm_window.addstr(rpm_info_v_begin, rpm_info_h_begin + rpm_idle_size, FULLBLOCK * (rpm_size - rpm_idle_size), curses.color_pair(RPM_COLOR))
			else:
				rpm_window.addstr(rpm_info_v_begin, rpm_info_h_begin + rpm_idle_size, FULLBLOCK * (rpm_shift_light_size - rpm_idle_size), curses.color_pair(RPM_COLOR))
				if rpm_size <= rpm_max_size:
					rpm_window.addstr(rpm_info_v_begin, rpm_info_h_begin + rpm_shift_light_size, FULLBLOCK * (rpm_size - rpm_shift_light_size), curses.color_pair(RPM_HIGH_COLOR))
				else: # super high RPM
					fill_background = False
					rpm_window.addstr(rpm_info_v_begin, rpm_info_h_begin + rpm_shift_light_size, FULLBLOCK * (rpm_max_size - rpm_shift_light_size + 1), curses.color_pair(RPM_HIGH_COLOR))
					rpm_window.addstr(rpm_info_v_begin, rpm_info_h_begin + rpm_max_size, FULLBLOCK * 1, curses.color_pair(RPM_SUPER_HIGH_COLOR))

		if fill_background:
			rpm_window.addstr(rpm_info_v_begin, rpm_info_h_begin + rpm_size, FULLBLOCK * (rpm_max_size - rpm_size + 1), curses.color_pair(BACKGROUND_COLOR))
	except curses.error:
		return

	# iddle_rpm_h_offset = rpm_info_h_begin + rpm_idle_size - 7
	# if iddle_rpm_h_offset < 0:
	# 	iddle_rpm_h_offset = 1
	
	# rpm_window.addstr(rpm_info_v_begin, iddle_rpm_h_offset, str(rpm) + "  ", curses.color_pair(RPM_INFO_COLOR) | curses.A_BOLD)


def recalculate_values(idle_rpm, max_rpm):
	global window_rows
	global window_cols
	global rpm_info_size
	global rpm_idle_size
	global rpm_max_size
	global rpm_shift_light_size
	global rpm_shift_light

	if max_rpm == 0:
		max_rpm = 5000
	
	# if idle_rpm == 0:
	# 	idle_rpm = 1000

	window_rows, window_cols = window.getmaxyx()
	window_middle = int(window_cols / 2)

	rpm_max_size = int(rpm_info_size)
	rpm_idle_size = int((idle_rpm / max_rpm) * rpm_info_size)
	rpm_shift_light = int(max_rpm - (max_rpm * (HIGH_RPM_PERCENTAGE / 100)))
	rpm_shift_light_size = int(rpm_max_size - (rpm_max_size * (HIGH_RPM_PERCENTAGE / 100)))


start_time = time.time()
max_fake_gears = 7
max_fake_speed = 300
min_fake_speed = (max_fake_speed / 10) * -1
speed_by_gear = max_fake_speed / max_fake_gears
max_rpm_variation = 100
last_data = {
	"run_time": 0.0,
	"lap_time": 0,
	"speed": 0,
	"gear": 0,
	"rpm": 900,
	"max_rpm": 7000,
	"idle_rpm": 900,
	"completed_laps": 0,
	"total_laps": random.choice([0, 1, 2, 3, 4, 5])
}
def generate_fake_data():
	global last_data
	global start_time

	time.sleep(0.05)
	speed = last_data['speed'] + random.choice([-2, -1, 0, 1, 2])
	run_time = time.time() - start_time
	completed_laps = last_data['completed_laps'] + (1 if random.randrange(1, 50, 1) == 1 else 0)

	# speed adjust
	if speed >= max_fake_speed * 2 / 3:
		speed -= 1
	elif speed <= max_fake_speed / 10:
		speed += 1
	if speed > max_fake_speed:
		speed = max_fake_speed
	elif speed < min_fake_speed:
		speed = min_fake_speed
	
	# gear adjust
	if speed < 0:
		gear = 0 if last_data['gear'] >= 1 else -1
	else:
		gear = 0 if last_data['gear'] < 0 else round(speed / speed_by_gear)
	
	# rpm adjust
	rpm = ((speed % speed_by_gear) / speed_by_gear) * (last_data['max_rpm'] - last_data['idle_rpm']) + last_data['idle_rpm']
	if rpm + max_rpm_variation > last_data['rpm']:
		rpm = last_data['rpm'] + max_rpm_variation
	elif rpm - max_rpm_variation < last_data['rpm']: 
		rpm = last_data['rpm'] - max_rpm_variation
	
	# lap adjust
	if completed_laps > last_data['total_laps']:
		completed_laps = 0
	
	last_data =  {
		"run_time": round(run_time, 1),
		"lap_time": round(run_time, 1),
		"speed": speed,
		"gear": gear,
		"rpm": int(rpm),
		"max_rpm": last_data['max_rpm'],
		"idle_rpm": last_data['idle_rpm'],
		"completed_laps": completed_laps,
		"total_laps": last_data['total_laps']
	}

	return last_data


def read_data():
	if SIMULATED_DATA:
		infos = generate_fake_data()
	else:
		data, addr = sock.recvfrom(1024) # buffer size
		infos = {
			"run_time": round(bit_stream_to_float32(data, RUN_TIME), 1),
			"lap_time": round(bit_stream_to_float32(data, LAP_TIME), 1),
			"speed": round(bit_stream_to_float32(data, SPEED_POS) * 3.6),
			"gear": int(bit_stream_to_float32(data, GEAR_POS)),
			"rpm": int(bit_stream_to_float32(data, RPM_POS)),
			"max_rpm": int(bit_stream_to_float32(data, MAX_RPM_POS)),
			"idle_rpm": int(bit_stream_to_float32(data, IDLE_RPM_POS)),
			"completed_laps": int(bit_stream_to_float32(data, COMPLETED_LAPS)),
			"total_laps": int(bit_stream_to_float32(data, TOTAL_LAPS))
		}

	return infos


def main():
	global window_rows
	global window_cols
	
	draw_interface()
	last_gear = None
	last_max_rpm = None

	mx = 0
	my = 0
	mz = 0

	while True:
		infos = read_data()

		event = window.getch()

		# if event == curses.KEY_MOUSE:
		# 	_id, mx, my, _mz, _bstate = curses.getmouse()
		# 	button_interaction(mx, my)

		position = 0

		resized = curses.is_term_resized(window_rows, window_cols)
		if resized:
			recalculate_values(infos['idle_rpm'], infos['max_rpm'])
			draw_interface()

		if last_max_rpm != infos['max_rpm'] or rpm_max_size == 0:
			recalculate_values(infos['idle_rpm'], infos['max_rpm'])
			last_max_rpm = infos['max_rpm']

		print_shift_light(infos['rpm'])

		print_rpm(infos['rpm'], infos['max_rpm'], infos['idle_rpm'])
		rpm_window.refresh()
		shiftlight_window.refresh()
		
		if infos['gear'] != last_gear:
			print_gear(infos['gear'])
			gear_window.refresh()
			last_gear = infos['gear']
		
		debug(infos)

		window.addstr(0, 0, '')
		window.refresh()


def debug(infos):
	global gear_h_size

	lap_info = "  lap: " + str(infos['lap_time']) + "s | " + str(infos['completed_laps']) + " / " + str(infos['total_laps']) + "      "

	try:
		window.addstr(DEBUG_V_OFFSET + 1, gear_h_size + 2, "speed: " + str(infos["speed"]) + " Km/h   ", curses.color_pair(GEAR_COLOR))
		window.addstr(DEBUG_V_OFFSET + 3, gear_h_size + 2, "total: " + str(infos["run_time"]) + "s   ", curses.color_pair(GEAR_COLOR))
		window.addstr(DEBUG_V_OFFSET + 4, gear_h_size + 2, lap_info, curses.color_pair(GEAR_COLOR))
	except curses.error:
		return


if __name__ == '__main__':
  main()
