import c2py

ADDRESS = 0x0F

PWM_CMD_SET = 1

def setpos( s, pos ):
    """Set servo number s to position pos.
    Pos ranges between 0 and 100. """

    pos = int((pos/100.0) * 180)

    v = pos << 8 | s

    c2py.writeworddata( ADDRESS, PWM_CMD_SET, v, 1 )

