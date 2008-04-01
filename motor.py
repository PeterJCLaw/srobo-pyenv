import c2py

ADDRESS = 0x12

# Command
MOTOR_IDENT = 0x00
MOTOR_CMD_CONF = 0x01
MOTOR_GET0 = 0x02
MOTOR_GET1 = 0x03

MAXERR = 10

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

def __set__( channel, speed ):
    
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

    v = speed | (dir << 9) | (channel<<11)
    count = 0

    while count < MAXERR:
        c2py.writeworddata( ADDRESS, MOTOR_CMD_CONF, v, 1 )

        cmd = (MOTOR_GET0, MOTOR_GET1)[channel]

        n = c2py.readworddata( ADDRESS, cmd, 1)

        if (n & 0x1FF) == speed and (n >> 9) == dir:
            break

        count = count + 1
    
    if count == MAXERR:
        raise c2py.I2CError

def setspeed(*args):
    if len(args) == 1:
        __set__( 0, args[0] )
        __set__( 1, args[0] )
    elif len(args) == 2:
        __set__( 0, args[0] )
        __set__( 1, args[1] )
    else:
        raise TypeError, "setspeed takes one or two numeric arguments"
