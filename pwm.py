import c2py
from repeat import *

ADDRESS = 0x1E

PWM_CMD_SET = 1

def setpos( s, pos ):
    """Set servo number s to position pos.
    Pos ranges between 0 and 100. """

    pos = int((pos/100.0) * 180)

    v = pos << 8 | s

    setword( ADDRESS, PWM_CMD_SET, v)

