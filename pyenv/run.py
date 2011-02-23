#!/usr/bin/python
import argparse, sys, logging, os, os.path, traceback
import trampoline

parser = argparse.ArgumentParser( description = "Run some robot code." )
parser.add_argument( "-d", "--debug", dest = "debug", action = "store_true",
                     help = "Send output to terminal, not logfile." )
parser.add_argument( "-i", "--immed", dest = "immed_start", action = "store_true",
                     help = "Start user code immediately, rather than waiting for a button press or radio event." )
args = parser.parse_args()

if not args.debug:
    "Put stdout and stderr into log file"
    sys.stderr = sys.stdout = open("log.txt", "at")

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s %(message)s',
                    stream = sys.stdout)

print "Initialising trampoline..."
try:
    import fw
    fw.update_all()    

    loc = os.path.join(os.curdir, "robot.zip")
    sys.path.insert(0, loc)
    print "%s added to python path." % loc

    t = trampoline.Trampoline()
    if not args.immed_start:
        print "TODO: Wait for button press etc!"
    else:
        print "Starting code"
        import addhack, robot
        addhack.add_queued()
        addhack.add_coroutine( robot.main )

    print "Starting trampoline"
    t.schedule()
except:
    print "Error: "
    traceback.print_exc(file=sys.stderr)
