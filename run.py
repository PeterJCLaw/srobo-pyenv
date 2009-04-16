#!/usr/bin/python
import sys, logging, os, os.path, subprocess, select, time
import games, colours
import radio
from addhack import add_coroutine
import power

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
    
    import trampoline
    print "Trampoline imported"

    print "Starting xbd, the radio server"
    # Reset the XBee
    power.xbee_reset(True)
    power.xbee_reset(False)

    # Start xbd
    xblog = open("xbd-log.txt","at")
    subprocess.Popen(["./xbd",
                      "-s", "/dev/ttyS0",
                      "-b","57600",
                      "--init-baud", "9600"],
                     stdout = xblog, stderr = xblog )

    t = trampoline.Trampoline()
    add_coroutine( radio.xbee_monitor )

    print "Starting trampoline"
    t.schedule()
except:
    print "Could not load user code!"
    print "Error: "
    print sys.exc_info()[0]
    print sys.exc_info()[1]
    print "On line", sys.exc_info()[2].tb_lineno
