import subprocess, sys
import types
from events import TimeoutEvent
import time
import logging
try:
    import robot
except:
    pass

class Trampoline:
    def __init__(self, corner=0, colour=0, game=0):
        self.corner = corner
        self.colour = colour
        self.game = game
        self.lastsync = 0

    def schedule(self):
        """
        Run the main function until it yields, then go through the polling
        functions until one of them yields / returns an event or the yield times
        out.
        """

        stack = []

        robot.event = None
        
        stack.append(robot.main(corner=self.corner,
                                colour=self.colour,
                                game=self.game))

        while True:
            self.do_sync()
            results = [None]
            try:
                results = self.call_generator(stack[-1])
            except StopIteration:
                #Remove the function on the top of the stack
                stack.pop()
                if len(stack) == 0:
                    #Put the main function back in...
                    stack.append(robot.main(corner=0,colour=0,game=0))
                    #Go back to start of while loop
                    continue

            if results == [None]:
                #Function returned or yielded nothing. Go round to top of loop
                continue

            if results[0].__class__ == types.FunctionType:
                #Push the function onto the stack
                #Passing the rest of the yield as arguments
                stack.append(args[0](*args[1:]))
            else:
                polls, timeout = self.filter_results(results)
                #Check we have something to wait on
                if len(polls) > 0 or timeout != None:
                    robot.event = self.poll_polls(polls, timeout)

    def filter_results(self, results):
        polls = []
        timeout = None
        for result in results:
            if result.__class__ == types.GeneratorType:
                polls.append(result)
            elif isinstance(result, int) or isinstance(result, float):
                timeout = time.time() + result
        
        return polls, timeout



    def do_sync(self):
        #Process any background tasks
        if time.time() > self.lastsync + 5:
            sys.stdout.flush()
            subprocess.Popen("sync").wait()
            self.lastsync = time.time()

    def call_generator(self, fn):
        args = None
        try:                    
            args = fn.next() #Advance to the first yield statement
        except AttributeError:
            #A function returned putting a None on the stack
            raise StopIteration
            
        if isinstance(args, types.TupleType):
            args = list(args)
        else:
            args = [args]

        return args

    def poll_polls(self, polls, timeout):
        #Loop waiting for something to happen
        result = None
        while True:
            if timeout != None and timeout < time.time():
                #Timed out
                result = TimeoutEvent(timeout)
            else:
                for poll in polls:
                    try:
                        result = poll.next()
                    except StopIteration:
                        polls.remove(poll)

            #See if anything happened
            if result != None:
                return result

if __name__ == "__main__":
    import sys, os, os.path
    sys.path.insert(0, os.path.join(os.curdir, "robot.zip"))
    import robot
    t = Trampoline()
    t.schedule()
