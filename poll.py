from time_event import *

class Poll:
    def __init__(self):
        pass

    def eval(self):
        # Returns a list of event objects
        print "WARNING: Evaluating instance of base poll :-("
        return None

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
        return "Nothing Poll" 

class TimePoll(Poll):
    def __init__(self, t):
        self.start = time.time()
        self.t = t
        Poll.__init__(self)

    def eval(self):
        if (time.time() - self.start) > self.t:
            return TimeoutEvent(self.t)
        return None

    def __str__(self):
        return "TimePoll(%s)" % str(self.t)

def convert_polls(polls):
    res = []
    for poll in polls:
        if hasattr( poll, "eval" ):
            res.append(poll)
        elif isinstance( poll, int ) or isinstance( poll, float ):
            res.append( time_event.TimePoll(poll) )
        else:
            print "Failed to convert \"%s\" into poll." % str(poll)
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

