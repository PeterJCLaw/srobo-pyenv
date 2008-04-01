from time import time

class Event:
    def __init__(self, source = None):
        self.source = None
        self.value = None

    def __eq__(self, obj):
        if self.source != None:
            return obj == self.source
        else:
            return NotImplemented

class TimeoutEvent(Event):
    def __init__(self, when):
        Event.__init__(self)
        self.when = when
