from events import Event
import time
from poll import Poll

timeout = "timeout"

class TimeoutEvent(Event):
    def __init__(self, when):
        Event.__init__(self, timeout)
        self.when = when
    def __str__(self):
        return "TimeoutEvent"

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
