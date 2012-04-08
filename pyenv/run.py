#!/usr/bin/python
import optparse, sys, os, os.path, time, shutil
import sricd, json, fw, log, squidge, usercode
import addcr
import subprocess
from subprocess import Popen, call

# The length of a match in seconds
MATCH_DURATION = 180

parser = optparse.OptionParser( description = "Run some robot code." )
parser.add_option( "-d", "--debug", dest = "debug", action = "store_true",
                     help = "Send output to terminal, not logfile." )
parser.add_option( "-i", "--immed", dest = "immed_start", action = "store_true",
                     help = "Start user code immediately." )
parser.add_option( "-l", "--log-dir", dest = "log_dir", default = "./",
                   help = "Log into the given directory." )
args, trailing_args = parser.parse_args()

if not os.path.exists( args.log_dir ):
    os.mkdir( args.log_dir )

LOG_DIR = args.log_dir
LOG_FNAME = os.path.join( LOG_DIR, "log.txt" )
ROBOT_RUNNING = "/tmp/robot-running"
PROG_DIR = os.path.abspath( os.path.dirname( __file__ ) )
BIN_DIR = os.path.join( PROG_DIR, "bin" )
LIB_DIR = os.path.join( PROG_DIR, "lib" )
PYLIB_DIR = os.path.join( PROG_DIR, "pylib" )
USER_DIR = os.path.join( PROG_DIR , "user" )
USER_EXEC = os.path.join( USER_DIR, "robot.py" )
VAR_DIR = os.path.join( PROG_DIR, "var")

if not args.debug:
    if os.path.exists( LOG_FNAME ):
        "Move old log file to log.txt.N"
        log.move_old_logfile( LOG_FNAME,
                              old_log_dir = os.path.join( LOG_DIR, "old-logs" ) )

    "Put stdout and stderr into log file"
    sys.stderr = sys.stdout = addcr.AddCRWriter(open( LOG_FNAME, "at", 1))
else:
    "Ensure that the logfile exists, as some things need it"
    if not os.path.exists( LOG_FNAME ):
        open( LOG_FNAME, "w" ).close()

def init_env():
    "Initialise/check environment variables that we want"
    # Environment variables that we want:
    envs = { "PYSRIC_LIBDIR": LIB_DIR,
             "LD_LIBRARY_PATH": LIB_DIR,
             "PYTHONPATH": PYLIB_DIR,
             "DISPLAY": ":0.0" }
    for k,v in envs.iteritems():
        os.environ[k] = v

    if "PATH" not in os.environ:
        "The PATH environment variable doesn't make it through when run from udev"
        os.environ["PATH"] = "/usr/local/bin:/usr/bin:/bin:/usr/local/sbin:/usr/sbin:/sbin"

    # Prefix PATH with our bin directory
    os.environ["PATH"] =  "%s:%s" % ( BIN_DIR, os.environ["PATH"] )

def init_fs():
    "Initialise/reset the filesystem"

    # Hack around zip not supporting file permissions...
    if not os.access( os.path.join( BIN_DIR, "sricd" ), os.X_OK ):
        call( "find %s -type f | xargs chmod u+x" % os.path.dirname(__file__),
              shell = True )

    # Copy ldconfig cache over
    shutil.copyfile( os.path.join( VAR_DIR, "ld.so.cache" ),
                     "/var/volatile/run/ld.so.cache" )

    # Remove files we don't want to be around
    for fname in [ ROBOT_RUNNING ]:
        if os.path.exists( fname ):
            os.unlink( fname )

def start_wm():
    "Start the window manager"
    Popen( "matchbox-window-manager -use_titlebar no -use_cursor no",
           shell = True )

def real_sleep( start_time, duration ):
    "Wait for the given amount of time from start_time"

    # time.sleep() can sleep for less time than specified
    # so loop calling it several times over
    while True:
        runtime = (time.time() - start_time)

        if runtime < duration:
            time.sleep( duration - runtime )
        else:
            break

def end_match( start_time, robot ):
    "End the match when the time comes"

print "Initialising..."

init_env()
init_fs()

if not os.path.exists( USER_EXEC ):
    "No robot code around"
    raise Exception( "No robot code found." )

sricd.start( os.path.join( args.log_dir, "sricd.log" ) )

start_wm()

if fw.update_with_gui( root = PROG_DIR,
                       bin_dir = BIN_DIR,
                       log_dir = LOG_DIR ):
    "Everything could have changed, so restart the bus"
    sricd.restart( os.path.join( args.log_dir, "sricd.log" ) )

user = usercode.UserCode( USER_EXEC, LOG_DIR, USER_DIR )

print "Running user code."

# Start the task-switcher
Popen( ["sr-ts", ROBOT_RUNNING],  shell = True )
# Start the GUI
sq = squidge.Squidge( LOG_FNAME )

# Funnel button presses through to X
Popen( "srinput" )

if not args.immed_start:
    "Wait for the button press to happen"
    call("pyenv_start")

#Tell things that code is being run
open(ROBOT_RUNNING,"w").close()

mode_info = sq.signal_start();

print "Mode: %s\t Zone: %i" % ( mode_info["mode"],
                                mode_info["zone"] )

user.start( mode_info )
start_time = time.time()

if mode_info["mode"] == "comp":
    "Competition mode"
    real_sleep( start_time, MATCH_DURATION )
    user.end_match()

user.wait()
