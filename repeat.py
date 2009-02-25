import c2py

def getbyte(address, cmd):
    while True:
        try:
            byte = c2py.readbytedata( address, cmd, 1 )
            break
        except c2py.I2CError:
            pass
    return byte

def setword(address, cmd, val):
    while True:
        try:
            c2py.writeworddata(address, cmd, val, 1)
            break
        except c2py.I2CError:
            pass

def setbyte(address, cmd, val):
    while True:
        try:
            c2py.writebytedata(address, cmd, val, 1)
            break
        except c2py.I2CError:
            pass

def getword(address, cmd):
    while True:
        try:
            val = c2py.readworddata(address, cmd, 1)
            break
        except c2py.I2CError:
            pass

    return val

def getblock(address, cmd, bytes):
    while True:
        try:
            val = c2py.readblockdata(address, cmd, bytes)
            break
        except c2py.I2CError:
            pass

    return val

# following two functions to read and write to power board only
def powerread(address, cmd):
    while True:
        try:
            val = c2py.powerread(address, cmd)
            break
        except c2py.I2CError:
            pass

    return val

def powerwrite(address, cmd, val):
    while True:
        try:
            c2py.powerwrite(address, cmd, val)
            break
        except c2py.I2CError:
            pass
