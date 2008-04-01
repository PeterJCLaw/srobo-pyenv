import c2py

MAXERR = 10

def getbyte(address, cmd):
    count = 0
    while count < MAXERR:
        try:
            byte = c2py.readbytedata( address, cmd, 1 )
            break
        except c2py.I2CError:
            count = count + 1
    
    if count == MAXERR:
        raise c2py.I2CError

    return byte

def setbyte(address, cmd, val):
    count = 0
    while count < MAXERR:
        try:
            c2py.writebytedata(address, cmd, val, 1)
            break
        except c2py.I2CError:
            count = count + 1

    if count == MAXERR:
        raise c2py.I2CError

def getword(address, cmd):
    count = 0
    while count < MAXERR:
        try:
            val = c2py.readworddata(address, cmd, 1)
            break
        except c2py.I2CError:
            count = count + 1

    if count == MAXERR:
        raise c2py.I2CError
    
    return val

def getblock(address, cmd, bytes):
    count = 0
    while count < MAXERR:
        try:
            val = c2py.readblockdata(address, cmd, bytes)
            break
        except c2py.I2CError:
            count = count + 1

    if count == MAXERR:
        raise c2py.I2CError
    
    return val
