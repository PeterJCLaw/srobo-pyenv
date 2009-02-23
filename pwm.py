import c2py
from repeat import *

ADDRESS = 0x2E

PWM_CMD_SET = 1
PWM_CMD_GET_LAST = 2

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

