#!/usr/bin/python
import optparse, sys, os, os.path, time, shutil
import sricd, json, fw, log
import addcr
import subprocess
from subprocess import Popen, call

# The length of a match in seconds
MATCH_DURATION = 180

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
PROG_DIR = os.path.abspath( os.path.dirname( __file__ ) )
BIN_DIR = os.path.join( PROG_DIR, "bin" )
LIB_DIR = os.path.join( PROG_DIR, "lib" )
PYLIB_DIR = os.path.join( PROG_DIR, "pylib" )
USER_DIR = os.path.join( PROG_DIR , "user" )
USER_EXEC = os.path.join( USER_DIR, "robot.py" )
START_FIFO = "/tmp/robot-start"
MODE_FILE = "/tmp/robot-mode"
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
    for fname in [ START_FIFO, MODE_FILE, ROBOT_RUNNING ]:
        if os.path.exists( fname ):
            os.unlink( fname )

print "Initialising..."

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

init_fs()

if not os.path.exists( USER_EXEC ):
    "No robot code around"
    raise Exception( "No robot code found." )

sricd.start( os.path.join( args.log_dir, "sricd.log" ) )

Popen( "matchbox-window-manager -use_titlebar no -use_cursor no",
       shell = True )

if fw.update_with_gui( root = PROG_DIR,
                       bin_dir = BIN_DIR,
                       log_dir = LOG_DIR ):
    "Everything could have changed, so restart the bus"
    sricd.restart( os.path.join( args.log_dir, "sricd.log" ) )

print "Running user code."
robot = Popen( ["python", "-m", "sr.loggrok",
                USER_EXEC, "--usbkey", LOG_DIR, "--startfifo", START_FIFO],
               cwd = USER_DIR,
               stdout = sys.stdout,
               stderr = sys.stderr )

# Start the task-switcher
Popen( ["sr-ts", ROBOT_RUNNING],  shell = True )
# Start the GUI
disp = Popen( ["squidge", LOG_FNAME, MODE_FILE] , stdin=subprocess.PIPE)
# Funnel button presses through to X
Popen( "srinput" )

if not args.immed_start:
    "Wait for the button press to happen"
    call("pyenv_start")

#Tell things that code is being run
open(ROBOT_RUNNING,"w").close()

#Feed display a newline now that code is to be run
disp.stdin.write("\n")

# Wait for the GUI to send us the information we want
while not os.path.exists( MODE_FILE ):
    time.sleep(0.1)

mode_info = json.load( open( MODE_FILE, "r" ) )

print "Mode: %s\t Zone: %i" % ( mode_info["mode"],
                                mode_info["zone"] )

# Ready for user code to execute, send it useful info:
while not os.path.exists( START_FIFO ):
    time.sleep(0.1)

print "Starting user code."
with open( START_FIFO, "w" ) as f:
    f.write( json.dumps( mode_info ) )
    start_time = time.time()

if mode_info["mode"] == "comp":
    "Competition mode"

    # time.sleep() can sleep for less time than specified
    # so loop calling it several times over
    while True:
        runtime = (time.time() - start_time)

        if runtime < MATCH_DURATION:
            time.sleep( MATCH_DURATION - runtime )
        else:
            break

    # End the user's code
    robot.kill()

    #### Now kill the motor rail

    # Augment the import path so we can get to the Power class
    sys.path.append( PYLIB_DIR )
    import sr.tssric, sr.power, sr.pysric

    sricman = sr.tssric.SricCtxMan()
    power = sr.power.Power( sricman.devices[sr.pysric.SRIC_CLASS_POWER][0] )
    power._set_motor_rail( False )

    print "Match ended -- User code killed."

r = robot.wait()
print "Robot code exited with code %i" % r
