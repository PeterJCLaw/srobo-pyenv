import c2py
from repeat import *

ADDRESS = 0x12

# Command
MOTOR_IDENT = 0x00
MOTOR_CMD_CONF = 0x01
MOTOR_GET0 = 0x02
MOTOR_GET1 = 0x03

# Directions
OFF = 0
FORWARD = 1
BACKWARD = 2
BRAKE = 3

def checkmotor():
    try:
        id = c2py.readworddata( ADDRESS, MOTOR_GET0, 1 )
    except c2py.I2CError:
        return False

    return True

def setpower_channel(channel, speed):
    speed = float(speed)

    if speed > 100:
        speed = 100
    elif speed < -100:
        speed = -100

    if channel not in [0,1]:
        raise ValueError, "Incorrect channel set"
    
    if speed > 0:
        dir = FORWARD
    else:
        dir = BACKWARD

    speed = abs(int(speed * 3.28))
    setpower_raw( channel, speed, dir )

def setpower_raw( channel, speed, dir ):
    v = speed | (dir << 9) | (channel<<11)
    while True:
        try:
            c2py.writeworddata( ADDRESS, MOTOR_CMD_CONF, v, 1 )
            break
        except c2py.I2CError:
            continue

        _dir, _speed = __getpower_raw( channel )

        if _dir == dir and _speed == speed:
            break

def __getpower_raw( channel ):
    cmd = (MOTOR_GET0, MOTOR_GET1)[channel]
    n = getword( ADDRESS,  cmd )

    speed = n & 0x1FF
    dir = n>>9
    return (dir,speed)

def __getpower(channel):
	if channel not in [0, 1]:
		raise ValueError, "Incorrect channel read"

        dir, speed = __getpower_raw(channel)
	
	if(dir == OFF or dir == BRAKE):
		return 0
	elif dir == FORWARD:
		return speed/3.28
	elif dir == BACKWARD:
		return -1*speed/3.28
	
def setpower(*args):
    if len(args) == 1:
        setpower_channel( 0, args[0] )
        setpower_channel( 1, args[0] )
    elif len(args) == 2:
        setpower_channel( 0, args[0] )
        setpower_channel( 1, args[1] )
    else:
        raise TypeError, "setspeed takes one or two numeric arguments"

def readpower(*args):
	if len(args) == 1:
		return	__getpower(args[0])
	else:
		raise TypeError, "readpower takes only one numeric argument"

class Motors:
    def __init__(self):
        pass

    def __getitem__(self, n):
        "Return the current motor speed"
        return readpower(n)

    def __setitem__(self, n, v):
        setpower_channel(n, v)

motor = Motors()
