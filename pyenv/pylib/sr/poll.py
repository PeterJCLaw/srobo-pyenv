class Poll:
    def __init__(self):
        pass

    def eval(self):
        """
        (virtual)
        Evaluate this poll.
        Return a tuple: (happened, val)
         - happened: bool: whether the event happened
         - val: The value of the poll that should be passed to the user."""
        # Returns a list of event objects
        raise Exception( "Base class Poll must never be evaluated" )

    def next(self):
        return self.eval()

    def __add__(self, op):
        print "and"
        return And(self,op)

    def __and__(self, op):
        return And(self,op)

    def __or__(self, op):
        return Or(self,op)

    def __str__(self):
        return "Poll base class" 

def convert_polls(polls):
    res = []
    for poll in polls:
        if hasattr( poll, "eval" ):
            res.append(poll)
        else:
            print "\"%s\" is not a valid poll." % str(poll)
    return res

class Or(Poll):
    def __init__(self, *args):
        Poll.__init__(self)
        self.operands = convert_polls(args)

    def eval(self):
        # evaluate until one works...
        for o in self.operands:
            r = o.eval()
            if r != None:
                return r
        return None

    def __str__(self):
        return "OR(%s)" % ", ".join([str(x) for x in self.operands])

class And(Poll):
    def __init__(self, *args):
        Poll.__init__(self)
        self.operands = convert_polls(args)

    def eval(self):
        # evaluate both things...
        res = []
        for o in self.operands:
            r = o.eval()
            if r == None:
                return None
            res.append(r)
        return res

    def __str__(self):
        return "AND(%s)" % ", ".join([str(x) for x in self.operands])

