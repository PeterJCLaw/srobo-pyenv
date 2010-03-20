import c2py
from repeat import *

ADDRESS = 0x2E

PWM_CMD_SET = 1
PWM_CMD_GET_LAST = 2
LCD_CMD_SET_POS = 6
LCD_CMD_GET_POS = 7
LCD_CMD_WRITE = 8
LCD_CMD_CSUM = 9
status = [-1, -1, -1, -1, -1, -1]

LINE_LEN = 16
NUM_LINES = 2

def readpos( s ):                                                                              
        #Read the position of the specified servo                                            
        #this reads from global array 'status'                                               
                                                                                             
        if s not in [0, 1, 2, 3, 4, 5]:                                                      
                raise InvalidPin("Servo number out of range")                                
                                                                                             
        return status[s] 


def setpos( s, pos ):
	"""Set servo number s to position pos.
	Pos ranges between 0 and 100. """

	if s not in [0, 1, 2, 3, 4, 5]:	
		raise InvalidPin("Servo number out of range")

	if pos > 100:
		pos = 100
		print "Warning: Servo pos out of range, reduced to 100"
	if pos < 0:
		pos = 0
		print "Warning: Servo pos out of range, increased to 0"

	position = int((pos/100.0) * 255)

	v = position << 8 | s

	while True:
		setword( ADDRESS, PWM_CMD_SET, v)
		r = getword(ADDRESS, PWM_CMD_GET_LAST)
		if r == v:
			status[s] = pos
			break	

def lcd_set_screen(n):
	"""Set the LCD screen to write to"""
	while True:
		setword(ADDRESS, LCD_CMD_SET_POS, n)
		if (0x3 & getbyte(ADDRESS, LCD_CMD_GET_POS)) == n:
			break

def lcd_set_text(text):
	""" """
	# Generate the checksum
	tx_csum = 0
	for c in text:
		tx_csum += ord(c)
	tx_csum &= 0xff

	while True:			#write screen contents
		"Write screen contents"
		powerwrite(ADDRESS, LCD_CMD_WRITE, [ord(x) for x in text]);
		rx_csum = 0xff & getbyte(ADDRESS, LCD_CMD_CSUM)
		if(rx_csum == tx_csum):
			break

def clean_text(t):
	"""Clean up some text ready for sending to the LCD"""
	text = str(t)

	# Replace newlines
	nt = ""
	for c in text:
		if c == '\n':
			nt += " " * ( LINE_LEN - (len(nt) % LINE_LEN) )
		else:
			nt += c

		if len(nt) >= (LINE_LEN * NUM_LINES):
			break

	# Pad out to fill the screen
	nt = nt + " " * ((LINE_LEN * NUM_LINES) - len(nt))
	return nt

def setlcd( *args ):
	"""Write up to 32 characters of text to the lcd"""

	if len(args) == 1:
		screen = 0
		text = args[0]
	elif len(args) == 2:
		screen = args[0]
		text = args[1]
	else:
		raise ValueError, "setlcd takes 1 or 2 arguments only. e.g. setlcd(0, \"text\") or setlcd(\"text\")"	

	if screen not in [0, 1, 2, 3]:
		raise ValueError, "Screen out of range. screen must be: 0, 1, 2, 3"

	lcd_set_screen( screen )
	text = clean_text(text)
	lcd_set_text(text)

class Pwm:
	def __getitem__(self, n):
		"Return the named servo's position"
		return readpos(n)

	def __setitem__(self, n, v):
		setpos(n, v)

class Lcd:
	def __setitem__(self, n, v):
		setlcd( n, v )

pwm = Pwm()
lcd = Lcd()

