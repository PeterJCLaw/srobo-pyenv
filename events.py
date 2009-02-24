from time import time

class Event:
    def __init__(self, source = None):
        self.source = source
        self.value = None

    def __eq__(self, obj):
        if self.source != None:
            return obj == self.source
        else:
            return NotImplemented

