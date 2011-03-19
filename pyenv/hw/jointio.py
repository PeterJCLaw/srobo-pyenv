import pysric
from events import Event
import logging
import poll

CMD_OUTPUT_SET = 0
CMD_OUTPUT_GET = 1
CMD_INPUT_A = 2
CMD_INPUT_D = 3
CMD_SMPS = 4

class IOEventInfo:
    def __init__(self):
        self.pins = []
        self.vals = {}

class IOEvent(Event):
    def __init__(self, pvals):
        "pvals is a dict of relevant pins and values"
        Event.__init__(self, io)
        self.pvals = pvals

    def add_info(self, ev):
        if not hasattr(ev, "io"):
            ev.io = IOEventInfo()

        for pin, val in self.pvals.iteritems():
            if pin not in ev.io.pins:
                ev.io.pins.append(pin)
            ev.io.vals[pin] = val

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
        "For when the operation gets cast into a bool"
        return self.eval() != None

    def gen_event(self, vals):
        pvals = {}
        for i in xrange(0, len(vals)):
            p = self.operands[i]

            # TODO :(
            # if isinstance(p, Pin) or isinstance(p, AnaloguePin):
            #     pvals[ p.num ] = vals[i]
        return pvals

class IOEqual(IOOperator):
    def eval(self):
        n = self.operands[0].val()
        vals = [n]
        for op in self.operands[1:]:
            v = op.val()
            if n != v:
                return
            vals.append(v)
        return IOEvent(self.gen_event(vals))

    def __str__(self):
        return "IOEqual(%s)" % (" == ".join([str(x) for x in self.operands]))

class IONotEqual(IOOperator):
    def eval(self):
        n = self.operands[0].val()
        m = self.operands[1].val()
        if n == m:
            return
        return IOEvent(self.gen_event([n,m]))

    def __str__(self):
        return "IONotEqual(%s)" % (" != ".join([str(x) for x in self.operands]))

class IOLessThan(IOOperator):
    def eval(self):
        n = self.operands[0].val()
        m = self.operands[1].val()
        if n < m:
            return IOEvent(self.gen_event([n,m]))
        return

    def __str__(self):
        return "IOLessThan(%s < %s)" % (self.operands[0], self.operands[1])

class IOGreaterThan(IOOperator):
    def eval(self):
        n = self.operands[0].val()
        m = self.operands[1].val()
        if n > m:
            return IOEvent(self.gen_event([n,m]))
        return

    def __str__(self):
        return "IOGreaterThan(%s > %s)" % (self.operands[0], self.operands[1])

class IOLessThanOrEqual(IOOperator):
    def eval(self):
        n = self.operands[0].val()
        m = self.operands[1].val()
        if n <= m:
            return IOEvent(self.gen_event([n,m]))
        return

    def __str__(self):
        return "IOGreaterThan(%s > %s)" % (self.operands[0], self.operands[1])

class IOGreaterThanOrEqual(IOOperator):
    def eval(self):
        n = self.operands[0].val()
        m = self.operands[1].val()
        if n >= m:
            return IOEvent(self.gen_event([n,m]))
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

    def __le__(self,o):
        return IOLessThanOrEqual( self, o )

    def __ge__(self,o):
        return IOGreaterThanOrEqual( self, o )

class InputPin(object):
    def __init__(self, num, jio):
        self.num = num
        self.jio = jio

    @property
    def a(self):
        "Return the analogue reading for this pin"
        v = self.jio._inputs_read_a()
        return v[self.num]
    
    @property
    def d(self):
        "Return the digital reading of this pin"
        v = self.jio._inputs_read_d()
        return v[self.num]

class OutputPin(object):
    def __init__(self, num, jio):
        self.num = num
        self.jio = jio

    @property
    def d(self):
        "Read the current value of the output"
        return self.jio._output_get()[self.num]

    @d.setter
    def d(self, value):
        "Set the value of an output pin"
        # Get current outputs
        v = self.jio._output_get_raw()
        if value:
            v |= (1<<self.num)
        else:
            v &= ~(1<<self.num)
        self.jio._output_set(v)

class OutputPins:
    def __init__(self, jio):
        self.jio = jio
    
    def __getitem__(self, n):
        if n < 0 or n > 8:
            raise InvalidPin("Pin out of range")
        return OutputPin(n, self.jio)

class InputPins(object):
    def __init__(self, jio):
        self.jio = jio

    def __getitem__(self, n):
        if n < 0 or n > 8:
            raise InvalidPin("Pin out of range")
        return InputPin(n, self.jio)

class JointIO(object):
    def __init__(self, dev):
        self.dev = dev
        self.input = InputPins(self)
        self.output = OutputPins(self)

        self._smps_control(True)

    def _output_set(self, vals):
        self.dev.txrx( [ CMD_OUTPUT_SET, vals ] )

    def _output_get(self):
        r = self.dev.txrx( [ CMD_OUTPUT_GET ] ) 
        b = []
        for x in range(0,8):
            if r[0] & (1<<x):
                b.append(1)
            else:
                b.append(0)

        return b

    def _output_get_raw(self):
        r = self.dev.txrx( [ CMD_OUTPUT_GET ] )
        return r[0]

    def _inputs_read_a(self):
        r = self.dev.txrx( [ CMD_INPUT_A ] )
        vals = []
        for i in range(0, 16, 2):
            v = r[i]
            v |= (r[i+1] << 8)

            vals.append(3.3 * (v/1024.0))
        return vals

    def _inputs_read_d(self):
        r = self.dev.txrx( [ CMD_INPUT_D ] )
        vals = []
        for i in range(0,8):
            if (r[0] & (1<<i)):
                vals.append(1)
            else:
                vals.append(0)
        return vals

    def _smps_control(self, on):
        "Turn the smps on/off"
        if on:
            v = 1
        else:
            v = 0
        self.dev.txrx( [ CMD_SMPS, v ] )

class QueryInputPinDigital(IOPoll):
    def __init__(self, num, jio):
        "num is the pin number we're dealing with"
        self.num = num
        self.jio = jio

        # Initial value
        self.ival = self.val()
        IOPoll.__init__(self)

    def eval(self):
        v = self.val()
        if v != self.ival:
            self.ival = v
            return IOEvent({self.num: v})
        return None

    def val(self):
        return self.jio.input[self.num].d

class QueryInputPinAnalogue(IOPoll):
    def __init__(self, num, jio):
        "num is the pin number we're dealing with"
        self.num = num
        self.jio = jio

        self.ival = self.val()
        IOPoll.__init__(self)

    def eval(self):
        v = self.val()
        if v != self.ival:
            return IOEvent({self.num: v})
        return None

    def __eq__(self,o):
        raise CannotEquate("Analogue pins don't support the '==' operator.")

    def val(self):
        return self.jio.input[self.num].a

class QueryInputPin(object):
    def __init__(self, num, jio):
        self.num = num
        self.jio = jio

    @property
    def a(self):
        return QueryInputPinAnalogue(self.num, self.jio)

    @property
    def d(self):
        return QueryInputPinDigital(self.num, self.jio)

class QueryInputPins(object):
    def __init__(self, jio):
        self.jio = jio

    def __getitem__(self, n):
        if n < 0 or n > 8:
            raise InvalidPin("Pin out of range")
        return QueryInputPin(n, self.jio)

class QueryJointIO(object):
    def __init__(self, jio):
        self.jio = jio
        self.input = QueryInputPins(jio)

ps = pysric.PySric()
io = []
queryio = []

if pysric.SRIC_CLASS_JOINTIO in ps.devices:
    for dev in ps.devices[ pysric.SRIC_CLASS_JOINTIO ]:
        jio = JointIO(dev)
        io.append( jio )
        queryio.append( QueryJointIO(jio) )
