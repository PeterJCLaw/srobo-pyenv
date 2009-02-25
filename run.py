#!/usr/bin/python
import sys, logging, os, os.path, subprocess, select

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s %(message)s',
                    stream = sys.stdout)

sys.stderr = sys.stdout = open("log.txt", "at")

os.putenv("LD_LIBRARY_PATH", "/usr/local/lib")

print "Initialising trampoline..."
try:
    import fw
    fw.update_all()    

    loc = os.path.join(os.curdir, "robot.zip")
    sys.path.insert(0, loc)
    print "%s added to python path." % loc

    import jointio, motor, pwm, vis, c2py, power
    print "Peripheral libraries imported"
    #power.setleds(1)
    #power.clearwatchdog()
    
    import robot
    print "User robot code import succeeded"

    import trampoline
    print "Trampoline imported"
    #power.setleds(2)

    #print "Watchdog cleared"
    #power.setleds(4)

    corner = 0
    colour = 0
    game = 0

    while not power.getbutton()
    

    t = trampoline.Trampoline( corner = corner,
                               colour = colour,
                               game = game )
    print "Trampoline initialised"
    #power.setleds(0)
    
    print "Starting trampoline"
    t.schedule()
except:
    print "Could not load user code!"
    print "Error: "
    print sys.exc_info()[0]
    print sys.exc_info()[1]
    print "On line", sys.exc_info()[2].tb_lineno
