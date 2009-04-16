import subprocess, select, os, re, time
import power, poll, events, fcntl
import addhack
from colours import *
from games import *

xbee = "xbee"

# This is a coroutine: 
def xbee_monitor():

    # We have to import the user code here, and catch any new coroutines
    import robot
    newc = list(addhack.get_coroutines())
    print "User robot code import succeeded"

    led_state = 1
    x = XbeePoller()
    while True:
        yield x, 0.5
        if robot.event == xbee:
            break

        if power.getbutton():
            break

        power.setleds(0,led_state)
        led_state ^= 1
        
    power.setbutton()
    power.setservopower(1)
    power.setmotorpower(1)

    addhack.add_queued()
    addhack.add_coroutine( robot.main, color = RED, game = GOLF )

class XbeeEvent(events.Event):
    def __init__(self, s):
        events.Event.__init__(self, xbee)
        self.decode_str(s)

    def add_info(self, ev):
        pass

    def decode_str(self, s):
        r = re.compile("([^= ]+)=([^=, ]+)")
        matches = r.findall(s)

        self.settings = {}

        for match in matches:
            vname = match[0]
            val = match[1]

            self.settings[vname] = val

class XbeePoller(poll.Poll):
    def __init__(self):
        l = os.getenv("LD_LIBRARY_PATH")
        if "/mnt/user/.robotmp" not in l:
            l = l + ":" "/mnt/user/.robotmp"
        if "/usr/local/lib" not in l:
            l = l + ":" "/usr/local/lib"
        os.putenv("LD_LIBRARY_PATH", l)

        # Start the process
        self.xbout = subprocess.Popen(["./xbout"],
                                      stdout = subprocess.PIPE)
        self.fifo = self.xbout.stdout.fileno()
        # Non-blocking please
        fcntl.fcntl(self.fifo, fcntl.F_SETFL, os.O_NONBLOCK)

        self.r = ""
        self.start_found = False

        poll.Poll.__init__(self)

    def eval(self):
        if not os.path.exists("/tmp/xbee"):
            # xbd isn't up yet
            return None

        # Read all the data that's available on the fifo
        while select.select([self.fifo], [], [], 0) != ([],[],[]):

            # Read the output
            c = os.read(self.fifo, 1)
            self.r += c
            print "\tRead '%c'" % c
            print "\tBuffer: '%s'" % self.r

            if self.start_found and len(self.r) > 0 and self.r[-1] == "\n":
                self.r = self.r[6:-1]
                print "Received START:", self.r

                self.start_found = False
                return XbeeEvent(self.r)

            else:
                if self.r[0:6] != "START:"[0:len(self.r)]:
                    self.r = ""
                elif self.r[0:6] == "START:":
                    print "START FOUND"
                    self.start_found = True

        return None
