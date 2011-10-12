import poll

CMD_OUTPUT_SET = 0
CMD_OUTPUT_GET = 1
CMD_INPUT_A = 2
CMD_INPUT_D = 3
CMD_SMPS = 4

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
        return self.eval()[0]

class IOEqual(IOOperator):
    def eval(self):
        n = self.operands[0].val()
        vals = [n]
        for op in self.operands[1:]:
            v = op.val()
            if n != v:
                return False, None
            vals.append(v)

        return True, tuple(vals)

    def __str__(self):
        return "IOEqual(%s)" % (" == ".join([str(x) for x in self.operands]))

class IONotEqual(IOOperator):
    def eval(self):
        n = self.operands[0].val()
        m = self.operands[1].val()
        if n == m:
            return False, None
        return True, (n,m)

    def __str__(self):
        return "IONotEqual(%s)" % (" != ".join([str(x) for x in self.operands]))

class IOLessThan(IOOperator):
    def eval(self):
        n = self.operands[0].val()
        m = self.operands[1].val()
        if n < m:
            return True, (n,m)
        return False, None

    def __str__(self):
        return "IOLessThan(%s < %s)" % (self.operands[0], self.operands[1])

class IOGreaterThan(IOOperator):
    def eval(self):
        n = self.operands[0].val()
        m = self.operands[1].val()
        if n > m:
            return True, (n,m)
        return False, None

    def __str__(self):
        return "IOGreaterThan(%s > %s)" % (self.operands[0], self.operands[1])

class IOLessThanOrEqual(IOOperator):
    def eval(self):
        n = self.operands[0].val()
        m = self.operands[1].val()
        if n <= m:
            return True, (n,m)
        return False, None

    def __str__(self):
        return "IOGreaterThan(%s > %s)" % (self.operands[0], self.operands[1])

class IOGreaterThanOrEqual(IOOperator):
    def eval(self):
        n = self.operands[0].val()
        m = self.operands[1].val()
        if n >= m:
            return True, (n,m)
        return False, None

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

class QueryInputPinDigital(IOPoll):
    def __init__(self, ipin):
        "num is the pin number we're dealing with"
        self.ipin = ipin

        # Initial value
        self.ival = self.val()
        IOPoll.__init__(self)

    def eval(self):
        v = self.val()
        if v != self.ival:
            self.ival = v
            return True, v
        return False, None

    def val(self):
        return self.ipin.d

class QueryInputPinAnalogue(IOPoll):
    def __init__(self, ipin):
        "num is the pin number we're dealing with"
        self.ipin = ipin

        self.ival = self.val()
        IOPoll.__init__(self)

    def eval(self):
        v = self.val()
        if v != self.ival:
            return True, v
        return False, v

    def __eq__(self,o):
        raise CannotEquate("Analogue pins don't support the '==' operator.")

    def val(self):
        return self.ipin.a

class QueryInputPin(object):
    def __init__(self, ipin):
        self.ipin = ipin

    @property
    def a(self):
        "Analogue pin query"
        return QueryInputPinAnalogue(self.ipin)

    @property
    def d(self):
        "Digital pin query"
        return QueryInputPinDigital(self.ipin)

class InputPin(object):
    def __init__(self, num, jio):
        self.num = num
        self.jio = jio
        self.query = QueryInputPin(self)

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

class JointIO(object):
    def __init__(self, dev):
        self.dev = dev

        inputs = []
        outputs = []
        for x in range(0, 8):
            inputs.append( InputPin(x, self) )
            outputs.append( OutputPin(x, self) )

        self.input = tuple( inputs )
        self.output = tuple( outputs )

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

