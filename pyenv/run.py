#!/usr/bin/python
import optparse, sys, os, os.path, traceback
import sricd, pysric, json
import addcr
import subprocess
from subprocess import Popen, call

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

LOG_DIR = args.log_dir
LOG_FNAME = os.path.join( LOG_DIR, "log.txt" )
ROBOT_RUNNING = "/tmp/robot-running"
PROG_DIR = os.path.dirname( __file__ )
BIN_DIR = os.path.join( PROG_DIR, "bin" )
LIB_DIR = os.path.join( PROG_DIR, "lib" )
PYLIB_DIR = os.path.join( PROG_DIR, "pylib" )
USER_DIR = os.path.join( PROG_DIR , "user" )
USER_EXEC = os.path.join( USER_DIR, "robot.py" )
START_FIFO = "/tmp/robot-start"

if not args.debug:
    if os.path.exists( LOG_FNAME ):
        "Move old log file to log.txt.N"
        n = 1
        while True:
            "Find a log file that doesn't exist"
            f = "%s.old.%i" % (LOG_FNAME, n)
            if not os.path.exists( f ):
                break
            n += 1
        os.rename( LOG_FNAME, f )

    "Put stdout and stderr into log file"
    sys.stderr = sys.stdout = addcr.AddCRWriter(open( LOG_FNAME, "at", 1))

print "Initialising..."
try:
    # Environment variables that we want:
    envs = { "PYSRIC_LIBDIR": LIB_DIR,
             "LD_LIBRARY_PATH": LIB_DIR,
             "PYTHONPATH": PYLIB_DIR,
             "DISPLAY": ":0.0" }
    for k,v in envs.iteritems():
        os.environ[k] = v

    # Extend PATH to include our bin directory
    os.environ["PATH"] += ":" + BIN_DIR

    # Hack around zip not supporting file permissions...
    call( "find %s -type f | xargs chmod u+x" % os.path.dirname(__file__),
          shell = True )

    if not os.path.exists( USER_EXEC ):
        "No robot code around"
        raise Exception( "No robot code found." )

    sricd.start( os.path.join( args.log_dir, "sricd.log" ) )

    robot = Popen( [USER_EXEC, "--usbkey", LOG_DIR, "--startfifo", START_FIFO],
                   executable = USER_EXEC,
                   cwd = USER_DIR,
                   stdout = sys.stdout,
                   stderr = sys.stderr )

    Popen( "matchbox-window-manager -use_titlebar no -use_cursor no",
           shell = True )

    if os.path.isfile(ROBOT_RUNNING):
        "sr-ts uses the ROBOT_RUNNING file to determine if we're running"
        os.remove(ROBOT_RUNNING)

    # Start the task-switcher
    Popen( "sr-ts %s" % ROBOT_RUNNING,  shell = True )
    # Start the GUI
    disp = Popen( ["squidge", LOG_FNAME] , stdin=subprocess.PIPE)
    # Funnel button presses through to X
    Popen( "srinput" )

    if not args.immed_start:
        "Wait for the button press to happen"
        call("pyenv_start")

    #Tell things that code is being run
    open(ROBOT_RUNNING,"w").close()

    #Feed display a newline now that code is to be run
    disp.stdin.write("\n")

    # TODO: Move this into Robot constructor
    # List the enumerated boards in the log
    print "Found the following devices:"
    ps = pysric.PySric()
    for devclass in ps.devices:
        if devclass in [pysric.SRIC_CLASS_POWER, pysric.SRIC_CLASS_MOTOR, pysric.SRIC_CLASS_JOINTIO, pysric.SRIC_CLASS_SERVO]:
            for dev in ps.devices[devclass]:
                print dev

    # Ready for user code to execute, send it useful info:
    if not os.path.exists( START_FIFO ):
        os.mkfifo( START_FIFO )
    f = open( START_FIFO, "w" )
    # Hard-coded data for the moment
    f.write( json.dumps( { "zone": 0, "mode": "dev" } ) )
    f.close()

    r = robot.wait()
    print "Robot code exited with code %i" % r

except:
    print "Error: "
    traceback.print_exc(file=sys.stderr)
