#!/usr/bin/python
import sys, logging, os, os.path

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
    
    import robot
    print "User robot code import succeeded"

    import trampoline
    print "Trampoline imported"

    power.clearwatchdog()
    print "Watchdog cleared"
    
    t = trampoline.Trampoline()
    print "Trampoline initialised"
    
    print "Starting trampoline"
    t.schedule()
except:
    print "Could not load user code!"
    print "Error: "
    print sys.exc_info()[0]
    print sys.exc_info()[1]
    print sys.exc_info()[2]
