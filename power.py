import c2py
from repeat import *

ADDRESS = 0x3f

# Command
CMD_GET_FIRMWARE = 0x00
CMD_WRITE_LEDS = 0x01
CMD_GET_BATTERY = 0x02
CMD_GET_CURRENT = 0x03
CMD_GET_SWITCHES = 0x04
CMD_SET_RAILS = 0x05
CMD_GET_RAILS = 0x06
CMD_SEND_CHAR = 0x07
CMD_GET_USB = 0x08
CMD_DISABLE_WATCHDOG = 0x09

def checkpower():
    try:
        getfirmware(ADDRESS)
        return True
    except c2py.I2CError:
        return False

def getfirmware():
    return getword(ADDRESS, CMD_GET_FIRMWARE)

def setleds(v):
    setbyte(ADDRESS, CMD_WRITE_LEDS, v & 0x0F)

def getbattery():
    return getword(ADDRESS, CMD_GET_BATTERY) & 0x3FF

def getcurrent():
    return getword(ADDRESS, CMD_GET_CURRENT) & 0x3FF

def getswitches():
    return getbyte(ADDRESS, CMD_GET_SWITCHES)

def setrails(val):
    setbyte(ADDRESS, CMD_SET_RAILS, val)

def getrails():
    return getbyte(ADDRESS, CMD_GET_RAILS)

def sendchar(char):
    setbyte(ADDRESS, CMD_SEND_CHAR, char)

def getusbconnected():
    if getbyte(ADDRESS, CMD_GET_USB) == 1:
        return True
    else:
        return False

def clearwatchdog():
    setbyte(ADDRESS, CMD_DISABLE_WATCHDOG, 1)
