import subprocess, sys
import types
import logging
from time_event import TimeoutEvent
from poll import Poll, TimePoll

class EventInfo:
    def __init__(self, evtree):
        self.evtree = evtree
        self.pop_tree()

    def was(self, obj):
        def ev_cmp(e):
            if isinstance(e, list):
                for x in e:
                    if ev_cmp(x):
                        return True
                return False
            else:
                return e == obj

        return ev_cmp(self.evtree)

    def pop_tree(self):
        def add_events(ev):
            if isinstance(ev, list):
                for e in ev:
                    add_events(e)
            else:
                ev.add_info(self)

        # Recusively add events :-O
        if self.evtree != None:
            add_events(self.evtree)

class Trampoline:
    def __init__(self):
        raise Exception("The springs on the trampoline have rusted.  It's not safe to use any more")
