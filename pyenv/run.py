#!/usr/bin/python
import __builtin__
# Let things know that they're running in the trampoline
__builtin__.__sr_trampoline = True
# List of functions to call on abort (can be tuples with args as items after first)
__builtin__.__sr_cleanup_funcs = []

import optparse, sys, logging, os, os.path, traceback
import trampoline, sricd
import subprocess

parser = optparse.OptionParser( description = "Run some robot code." )
parser.add_option( "-d", "--debug", dest = "debug", action = "store_true",
                     help = "Send output to terminal, not logfile." )
parser.add_option( "-i", "--immed", dest = "immed_start", action = "store_true",
                     help = "Start user code immediately, rather than waiting for a button press or radio event." )
args, trailing_args = parser.parse_args()

if not args.debug:
    "Put stdout and stderr into log file"
    sys.stderr = sys.stdout = open("log.txt", "at")

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s %(message)s',
                    stream = sys.stdout)

print "Initialising..."
try:
    # Add libsric location to path
    os.environ["PYSRIC_LIBDIR"] = os.path.join( os.getcwd(), "lib" )
    sricd.start("sricd.log")

#    import fw
#    fw.update_all()

    loc = os.path.join(os.curdir, "robot.zip")
    sys.path.insert(0, loc)
    print "%s added to python path." % loc

    # Hack in launch of display: begins with "Press button to start" message
    os.environ["DISPLAY"] = ":0.0"
    disp = subprocess.Popen(["./bin/squidge", "./log.txt"], stdin=subprocess.PIPE)

    t = trampoline.Trampoline()
    if not args.immed_start:
        os.environ["LD_LIBRARY_PATH"] = os.path.join( os.getcwd(), "lib" )
        subprocess.call("./bin/pyenv_start")

    # Feed display a newline once code it to be launched
    disp.stdin.write("\n")

    import addhack, robot
    addhack.add_queued()
    addhack.add_coroutine( robot.main )

    print "Starting trampoline"
    t.schedule()
except:
    print "Error: "
    traceback.print_exc(file=sys.stderr)

print "Calling %i cleanup functions" % (len(__sr_cleanup_funcs))
for f in __sr_cleanup_funcs:
    if isinstance( f, tuple ):
        f[0](*f[1:])
    else:
        f()
