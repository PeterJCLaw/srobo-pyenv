#!/usr/bin/python
import sys, logging, os, os.path, subprocess, select

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s %(message)s',
                    stream = sys.stdout)

sys.stderr = sys.stdout = open("log.txt", "at")

os.putenv("LD_LIBRARY_PATH", "/usr/local/lib")

print "Initialising trampoline..."
try:
    loc = os.path.join(os.curdir, "robot.zip")
    sys.path.insert(0, loc)
    print "%s added to python path." % loc

    import jointio, motor, pwm, vis, c2py, power
    print "Peripheral libraries imported"
    power.setleds(1)
    
    import robot
    print "User robot code import succeeded"

    import trampoline
    print "Trampoline imported"
    power.setleds(2)

    power.clearwatchdog()
    print "Watchdog cleared"
    power.setleds(4)

    corner = 0
    colour = 0
    game = 0

    # Are we in competition mode?
    if (power.getswitches() & 1) == 0:
        print "In competition mode"
        print "Starting xbd, the radio server"
        xblog = open("xbd-log.txt","at")
        subprocess.Popen(["./xbd",
                          "-s", "/dev/ttyS0",
                          "-b","57600",
                          "--init-baud", "9600"],
                         stdout = xblog, stderr = xblog )
        
        import radio
        settings = radio.wait_start()
        corner,colour,game = settings["corner"], settings["colour"], settings["game"]

    t = trampoline.Trampoline( corner = corner,
                               colour = colour,
                               game = game )
    print "Trampoline initialised"
    power.setleds(0)
    
    print "Starting trampoline"
    t.schedule()
except:
    print "Could not load user code!"
    print "Error: "
    print sys.exc_info()[0]
    print sys.exc_info()[1]
    print sys.exc_info()[2]
