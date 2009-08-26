#!/usr/bin/python
import sys, logging, os, os.path, subprocess, select, time, traceback
import games, colours
import radio
from addhack import add_coroutine
import power

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s %(message)s',
                    stream = sys.stdout)

# Debug mode
debug = False
# Whether to wait for a start event
wait_start_event = True
# Whether to use the xbee
use_xbee = True

if len(sys.argv) > 1:
    for a in sys.argv[1:]:
        if a == "-d":
            debug = True
        elif a == "--start":
            wait_start_event = False
        elif a == "--no-xbee":
            use_xbee = False
        elif a == "--help":
            print """Usage: %s ARGS
Where ARGS can be:
 -d		Send stdout and stderr to terminal, not log.txt.
 --start	Start the robot code immediately.
		Don't wait for a button or radio event.
 --no-xbee	Don't use the xbee.  Don't start xbd.""" % os.path.basename(sys.argv[0])
            sys.exit(0)

if not debug:
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

    if use_xbee:
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
    if wait_start_event:
        add_coroutine( radio.xbee_monitor )
    else:
        print "Starting code"
        import addhack, robot
        addhack.add_queued()
        addhack.add_coroutine( robot.main, games.GOLF, colours.RED )

    print "Starting trampoline"
    t.schedule()
except:
    print "Could not load user code!"
    print "Error: "
    traceback.print_exc(file=sys.stderr)
