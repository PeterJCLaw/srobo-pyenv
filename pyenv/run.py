#!/usr/bin/python
import __builtin__
# Let things know that they're running in the trampoline
__builtin__.__sr_trampoline = True
# List of functions to call on abort (can be tuples with args as items after first)
# Tuples with form ( debug, func, [args...] )
#  - if debug is true, then will only be called when in debug mode
__builtin__.__sr_cleanup_funcs = []

import optparse, sys, logging, os, os.path, traceback
import trampoline, sricd
import subprocess

parser = optparse.OptionParser( description = "Run some robot code." )
parser.add_option( "-d", "--debug", dest = "debug", action = "store_true",
                     help = "Send output to terminal, not logfile." )
parser.add_option( "-i", "--immed", dest = "immed_start", action = "store_true",
                     help = "Start user code immediately, rather than waiting for a button press or radio event." )
parser.add_option( "-l", "--log-dir", dest = "log_dir", default = "./",
                   help = "Log into the given directory." )
args, trailing_args = parser.parse_args()

if not os.path.exists( args.log_dir ):
    os.mkdir( args.log_dir )

LOG_FNAME = os.path.join( args.log_dir, "log.txt" )
if not args.debug:
    "Put stdout and stderr into log file"
    sys.stderr = sys.stdout = open( LOG_FNAME, "at", 1)

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s %(message)s',
                    stream = sys.stdout)

print "Initialising..."
try:
    # Environment variables that we want:
    envs = { "PYSRIC_LIBDIR": os.path.join( os.getcwd(), "lib" ),
             "LD_LIBRARY_PATH": os.path.join( os.getcwd(), "lib" ),
             "DISPLAY": ":0.0" }
    for k,v in envs.iteritems():
        os.environ[k] = v

    # Need to start dbus, have to manually remove the pid file due to dbus being
    # killed when the stick is removed
    if os.path.isfile("/var/run/messagebus.pid"):
        os.remove("/var/run/messagebus.pid")
    subprocess.call(["/etc/init.d/dbus-1", "start"])

    sricd.start( os.path.join( args.log_dir, "sricd.log" ) )

#    import fw
#    fw.update_all()

    if os.path.exists( "robot.zip" ):
        "robot.zip exists, everyone's happy"
        sys.path.insert(0, os.path.join(os.curdir, "robot.zip"))
    elif not os.path.exists( "robot.py" ):
        "No robot code around"
        raise Exception( "No robot code found." )

    # Hack in launch of display: begins with "Press button to start" message
    disp = subprocess.Popen(["./bin/squidge", LOG_FNAME], stdin=subprocess.PIPE)

    # Also in this series, the input-grabber
    subprocess.Popen("./bin/srinput")

    if not args.immed_start:
        subprocess.call("./bin/pyenv_start")

    # Feed display a newline once code it to be launched
    disp.stdin.write("\n")

    import addhack, robot
    addhack.add_queued()
    addhack.add_coroutine( robot.main )

    print "Starting robot code"
    t = trampoline.Trampoline()
    t.schedule()
except:
    print "Error: "
    traceback.print_exc(file=sys.stderr)

print "Calling %i cleanup functions" % (len(__sr_cleanup_funcs))
for f in __sr_cleanup_funcs:
    if isinstance( f, tuple ):
        if (not f[0]) or args.debug:
            f[1](*f[2:])
    else:
        f()
