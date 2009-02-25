from events import Event
from repeat import *
import logging
import poll

ADDRESS = 0x24

limits = []

curout = 0

# Get the identity from the board
JOINTIO_IDENTIFY = 0
# Set the outputs of the board
JOINTIO_OUTPUT = 1
# Read the board inputs in analogue form
JOINTIO_INPUT = 2
# Read the current digital output setting from the board.
JOINTIO_OUTPUT_READ = 3
# Read the inputs in digital form
JOINTIO_INPUT_DIG = 4

iosens = [0, 1, 2, 3]

class IOEvent(Event):
    def __init__(self, events):
        Event.__init__(self, io)
        self.pins = events

class InvalidPin(Exception):
    def __init__(self, value):
        self.parameter = value
    def __str__(self):
        return repr(self.parameter)

class CannotEquate(Exception):
    def __init__(self, value):
        self.parameter = value
    def __str__(self):
        return repr(self.parameter)

class ValWrapper:
    def __init__(self, thing):
        self.thing = thing
    
    def val(self):
        return self.thing

    def __str__(self):
        return "ValWrapper(" + str(self.thing) + ")"

class IOOperator(poll.Poll):
    """Base class for IO pin operator classes"""
    def __init__(self, *args):
        al = []
        for o in args:
            if not hasattr(o, "val"):
                al.append(ValWrapper(o))
            else:
                al.append(o)

        self.operands = al

    def __nonzero__(self):
        "For when the operation gets casted into a bool"
        return self.eval() != None

class IOEqual(IOOperator):
    def eval(self):
        n = self.operands[0].val()
        for op in self.operands[1:]:
            if n != op.val():
                return
        return IOEvent(100)

    def __str__(self):
        return "IOEqual(%s)" % (" == ".join([str(x) for x in self.operands]))

class IONotEqual(IOOperator):
    def eval(self):
        n = self.operands[0].val()
        m = self.operands[1].val()
        if n == m:
            return
        return IOEvent(100)

    def __str__(self):
        return "IONotEqual(%s)" % (" != ".join([str(x) for x in self.operands]))

class IOLessThan(IOOperator):
    def eval(self):
        n = self.operands[0].val()
        m = self.operands[1].val()
        if n < m:
            return IOEvent(100)
        return

    def __str__(self):
        return "IOLessThan(%s < %s)" % (self.operands[0], self.operands[1])

class IOGreaterThan(IOOperator):
    def eval(self):
        n = self.operands[0].val()
        m = self.operands[1].val()
        if n > m:
            return IOEvent(100)
        return

    def __str__(self):
        return "IOGreaterThan(%s > %s)" % (self.operands[0], self.operands[1])
    
class IOPoll(poll.Poll):
    def __init__(self):
        poll.Poll.__init__(self)

    def __str__(self):
        return "IOPoll(...)"

    def __eq__(self,o):
        return IOEqual( self, o )

    def __lt__(self,o):
        return IOLessThan( self, o )

    def __gt__(self,o):
        return IOGreaterThan( self, o )

    def __ne__(self,o):
        return IONotEqual( self, o )

class Pin(IOPoll):
    def __init__(self, num):
        "num is the pin number we're dealing with"
        self.num = num
        # Initial value
        self.ival = self.val()
        IOPoll.__init__(self)

    def eval(self):
        v = self.val()
        if v != self.ival:
            self.ival = v
            return IOEvent(self.num)
        return None

    def __repr__(self):
        return "%i" % readpin(self.num)

    def __str__(self):
        return str(readpin(self.num))
#        return "Pin(%i)" % self.num

    def val(self):
        return readpin(self.num)

class OutputPin(IOPoll):
    def __init__(self, num):
        "num is the pin number we're dealing with"
        self.num = num
        # Initial value
        self.ival = self.val()
        IOPoll.__init__(self)

    def eval(self):
        if self.val() != self.ival:
            return IOEvent(self.num)
        return None

    def __repr__(self):
        return "%i" % readpin(self.num)

    def __str__(self):
        return "Pin(%i)" % self.num

    def val(self):
        return readpin(self.num)


class AnaloguePin(IOPoll):
    def __init__(self, num):
        "num is the pin number we're dealing with"
        self.num = num
        self.ival = self.val()
        IOPoll.__init__(self)

    def eval(self):
        if self.val() != self.ival:
            return IOEvent(self.num)
        return None

    def __eq__(self,o):
        raise CannotEquate("Analogue pins don't support the '==' operator.")

    def __repr__(self):
        return "%f" % readapin(self.num)

    def __str__(self):
        return "Pin(%i)" % self.num

    def val(self):
        return readapin(self.num)

class Pins:
    def __init__(self):
        pass
    
    ######## Container Operators ########
    def __getitem__(self, n):
        "Return value of the pin"
        return Pin(n)

    def __setitem__(self, n, v):
        "Set the output"
        setoutput(n,v)

class OutputPins:
    def __init__(self):
        pass
    
    ######## Container Operators ########
    def __getitem__(self, n):
        "Return value of the pin"
        return Pin(n)

    def __setitem__(self, n, v):
        "Set the output"
        setoutput(n,v)

class AnaloguePins:
    def __init__(self):
        pass

    ######## Container Operators ########
    def __getitem__(self, n):
        "Return value of the pin"
        return readapin(n)

    def __setitem__(self, n, v):
        "Set the output"
        raise RuntimeError( "Cannot set value of input pins" )

class Jointio:
    def __init__(self):
        self.pin = Pins()
        self.opin = OutputPins()
        self.apin = AnaloguePins()

io = Jointio()

def setoutput(bit, value):
    global curout
    if bit > 3:
        logging.error("Trying to set an invalid DIO pin.")
    else:
        if value == 0:
            curout &= ~(1<<bit)
        else:
            curout |= (1<<bit)

        while True:
            setbyte(ADDRESS, JOINTIO_OUTPUT, curout)
            if getbyte(ADDRESS, JOINTIO_OUTPUT_READ) == curout:
                break

def readapin(pin):
    if pin >= 0 and pin < 8:
	val = getblock(ADDRESS, JOINTIO_INPUT, 16)
	bytes = [ord(x) for x in val]
	word = (bytes[2*pin] << 8) | (bytes[2*pin+1] & 0xFF)
    else:
	raise InvalidPin("Pin Out of range")
    return (float(word)/1023)*3.3	#return a voltage value

def readpin(pin):
    if pin >= 0 and pin < 8:
        val = getbyte(ADDRESS, JOINTIO_INPUT_DIG)
        if val & (1 << pin):
            return 1
	else:
	    return 0
    else:
	raise InvalidPin("Pin out of range")

