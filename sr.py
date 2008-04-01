from motor import checkmotor

if checkmotor():
    from motor import setspeed
else:
    setspeed = None

from vis import *
from pwm import setpos
import logging

vision = vispoll()
vision.next()

from jointio import *
if checkjointio():
    io = iopoll()
    io.next()
else:
    logging.error("DIO Failed")
    io = None
