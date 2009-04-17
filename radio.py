import subprocess, select, os, re, time
import power, poll, events, fcntl
import addhack
from colours import *
from games import *

xbee = "xbee"

# This is a coroutine: 
def xbee_monitor():
    print "Button and Radio monitor started"
    # We have to import the user code here, and catch any new coroutines
    import robot
    newc = list(addhack.get_coroutines())
    print "User robot code import succeeded"

    colour = RED
    game = GOLF

    led_state = 1
    x = XbeePoller()
    while True:
        yield x, 0.5
        if robot.event == xbee:
            colour = robot.event.xbee.colour
            game = robot.event.xbee.game
            break

        if power.getbutton():
            break

        power.setleds(0,led_state)
        led_state ^= 1
        
    power.setbutton()
    power.setservopower(1)
    power.setmotorpower(1)

    addhack.add_queued()
    addhack.add_coroutine( robot.main, game, colour )

class XbeeStruct:
    pass

class XbeeEvent(events.Event):
    def __init__(self, s):
        events.Event.__init__(self, xbee)
        self.decode_str(s)

    def add_info(self, ev):
        if not hasattr(ev, "xbee"):
            ev.xbee = XbeeStruct()
        ev.xbee.colour = self.settings["colour"]
        ev.xbee.game = self.settings["game"]
        ev.xbee.settings = self.settings

    def decode_str(self, s):
        r = re.compile("([^= ]+)=([^=, ]+)")
        matches = r.findall(s)

        self.settings = {}

        for match in matches:
            vname = match[0]
            val = match[1]

            if vname == "colour":
                if "BLUE" in val:
                    val = BLUE
                elif "RED" in val:
                    val = RED
                elif "YELLOW" in val:
                    val = YELLOW
                else:
                    # Default to green... for some reason
                    val = GREEN

            if vname == "game":
                if "SQUIRREL" in val:
                    val = SQUIRREL
                else:
                    # Default to golf... for some other reason
                    val = GOLF

            self.settings[vname] = val

class XbeePoller(poll.Poll):
    def __init__(self):
        l = os.getenv("LD_LIBRARY_PATH")
        if l == None:
            l = ""
        if "/mnt/user/.robotmp" not in l:
            l = l + ":" "/mnt/user/.robotmp"
        if "/usr/local/lib" not in l:
            l = l + ":" "/usr/local/lib"
        os.putenv("LD_LIBRARY_PATH", l)

        self.xbout = None
        self.r = ""
        self.start_found = False

        poll.Poll.__init__(self)

    def eval(self):
        if not os.path.exists("/tmp/xbee"):
            # xbd isn't up yet
            return None

        if self.xbout == None:
            # Start the process
            self.xbout = subprocess.Popen(["./xbout"],
                                          stdout = subprocess.PIPE)
            self.fifo = self.xbout.stdout.fileno()
            # Non-blocking please
            fcntl.fcntl(self.fifo, fcntl.F_SETFL, os.O_NONBLOCK)

        # Read all the data that's available on the fifo
        while select.select([self.fifo], [], [], 0) != ([],[],[]):

            # Read the output
            c = os.read(self.fifo, 1)
            self.r += c

            if self.start_found and len(self.r) > 0 and self.r[-1] == "\n":
                self.r = self.r[6:-1]
                print "Received START:", self.r

                self.start_found = False
                return XbeeEvent(self.r)

            else:
                if self.r[0:6] != "START:"[0:len(self.r)]:
                    self.r = ""
                    self.start_found = False
                elif self.r[0:6] == "START:":
                    self.start_found = True

        return None
