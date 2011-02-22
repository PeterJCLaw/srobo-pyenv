#!/usr/bin/python
import sys, logging, os, os.path, traceback
import trampoline

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s %(message)s',
                    stream = sys.stdout)

# Debug mode
debug = False
# Whether to wait for a start event
wait_start_event = True

if len(sys.argv) > 1:
    for a in sys.argv[1:]:
        if a == "-d":
            debug = True
        elif a == "--start":
            wait_start_event = False
        elif a == "--help":
            print """Usage: %s ARGS
Where ARGS can be:
 -d		Send stdout and stderr to terminal, not log.txt.
 --start	Start the robot code immediately.
		Don't wait for a button or radio event.""" % os.path.basename(sys.argv[0])
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

    t = trampoline.Trampoline()
    if wait_start_event:
        pass
    else:
        print "Starting code"
        import addhack, robot
        addhack.add_queued()
        addhack.add_coroutine( robot.main )

    print "Starting trampoline"
    t.schedule()
except:
    print "Could not load user code!"
    print "Error: "
    traceback.print_exc(file=sys.stderr)
