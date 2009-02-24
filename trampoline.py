import subprocess, sys
import types
import logging
try:
    import robot
except:
    pass
import addhack
import time_event

class Coroutine:
    def __init__(self, generator, name = ""):
        self.name = name
        self.first_run = True

        self.polls = []
        self.stack = [generator]
        self.event = None

    def poll(self):
        "Call poll functions."
        for p in xrange(0, len(self.polls)):
            poll = self.polls[p]

            result = None

            try:
                result = poll.next()
            except StopIteration:
                # mark poll for removal
                self.polls[p] = None

            if result != None:
                # We have an event
                self.event = result
                # All polls are now invalid
                self.polls = []
                return
            
        # Remove polls that have chosen to remove themselves
        self.polls = [x for x in self.polls if x != None]

        if len(self.polls) == 0:
            "This is an erroneous situation"
            print "OMG PONIES ERROR: No polls left for coroutine '%s' :-S" % self.name
            print "Forging TimeoutEvent as a hack until someone knows how to handle this condition"
            this.event = TimeoutEvent(1)

    def proc(self):
        "Call the generator and get new polls."

        if self.event == None and (not self.first_run):
            return

        self.first_run = False

        robot.event = self.event
        results = self.stack[-1].next()
        self.event = None

        if isinstance(results, types.TupleType):
            results = list(results)
        else:
            results = [results]

        if results == [None]:
            # Function returned or yielded nothing
            print "WARNING: Coroutine yielded absolutely nothing -- this is kind of strange..."
            return

        if results[0].__class__ == types.FunctionType:
            #Push the function onto the stack
            #Passing the rest of the yield as arguments
            self.stack.append(args[0](*args[1:]))
        else:
            for result in results:
                if result.__class__ == types.GeneratorType:
                    self.polls.append(result)
                elif isinstance(result, int) or isinstance(result, float):
                    self.polls.append( time_event.time_poll(result) )
                else:
                    print "WARNING: Ignoring poll", str(result)

def sync():
    "Sync to disk every 5 seconds"
    while True:
        yield 5
        sys.stdout.flush()
        subprocess.Popen("sync").wait()

class Trampoline:
    def __init__(self, corner=0, colour=0, game=0):
        self.corner = corner
        self.colour = colour
        self.game = game

    def schedule(self):
        """
        Manage coroutines.
        Ask each coroutine to poll, then execute them.
        """
        coroutines = []

        # Call the main function
        coroutines.append( Coroutine( robot.main(corner=self.corner,
                                                 colour=self.colour,
                                                 game=self.game),
                                      name = "main" ) )

        # sync to disk every 5 seconds:
        coroutines.append( Coroutine( sync(), name = "sync" ) )

        # TODO: Find coroutines in the user code (Trac #300)
        robot.event = None

        while True:
            for i in range(0, len(coroutines)): 
                "Call all the coroutines"
                c = coroutines[i]

                try:
                    c.proc()
                except StopIteration:
                    # Mark the coroutine for removal
                    print "Removing coroutine"
                    coroutines[i] = None

            # Remove dead coroutines
            while None in coroutines:
                coroutines.remove(None)

            for c in coroutines:
                "Poll all the coroutines"
                c.poll()

            # Add new coroutines into the mix:
            for c in addhack.new_coroutines:
                coroutines.append( Coroutine(c) )
            addhack.new_coroutines = []

def coroutine(f):
    "Decorator to add a function as a coroutine "
    addhack.add_coroutine(f)

    # Don't modify the function
    return f

if __name__ == "__main__":
    import sys, os, os.path
    sys.path.insert(0, os.path.join(os.curdir, "robot.zip"))
    import robot
    t = Trampoline()
    t.schedule()
