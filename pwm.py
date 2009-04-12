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


def setlcd(*args):
	"""Write up to 32 characters of text to the lcd"""

	if len(args) == 1:
		screen = 0
		text = args[0]
	elif len(args) == 2:
		screen = args[0]
		text = args[1]
	else:
		raise TypeError, "setlcd takes 1 or 2 arguments only. e.g. setlcd(0, \"text\") or setlcd(\"text\")"	

	if screen not in [0, 1, 2, 3]:
		raise TypeError, "Screen out of range. screen must be: 0, 1, 2, 3"


	while True:			#set the screen to write to
		setword(ADDRESS, LCD_CMD_SET_POS, screen)
		if (0x3 & getbyte(ADDRESS, LCD_CMD_GET_POS) == screen):
			break

	vals = [ord(' ')]*32
	i = 0
	text = str(text)				#permit setlcd(54.4)	etc.
	while( i < len(text) and (i < 32) ):		#convert to ascii
		vals[i] = ord(text[i])
		i += 1

	tx_csum = 0;			#generate checksum
	for i in vals:
		tx_csum += i;
	tx_csum &= 0xff
				
	while True:			#write screen contents
		powerwrite(ADDRESS, LCD_CMD_WRITE, list(vals));
		rx_csum = 0xff & getbyte(ADDRESS, LCD_CMD_CSUM)
		if(rx_csum == tx_csum):
			break

class Pwm:
	def __getitem__(self, n):
		"Return the named servo's position"
		return readpos(n)

	def __setitem__(self, n, v):
		setpos(n, v)

pwm = Pwm()
