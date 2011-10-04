#!/usr/bin/python
import optparse, sys, logging, os, os.path, traceback
import trampoline, sricd, pysric
import addcr
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
ROBOT_RUNNING = "/tmp/robot-running"

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

    # Hack around zip not supporting file permissions...
    subprocess.call( "find %s -type f | xargs chmod u+x" % os.path.dirname(__file__),
                     shell = True )

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
    if not args.debug:
        subprocess.Popen("matchbox-window-manager -use_titlebar no -use_cursor no",
                         shell = True)

        if os.path.isfile(ROBOT_RUNNING):
            "sr-ts uses the ROBOT_RUNNING file to determine if we're running"
            os.remove(ROBOT_RUNNING)

        subprocess.Popen("./bin/sr-ts %s" % ROBOT_RUNNING,
                         shell = True)

        disp = subprocess.Popen(["./bin/squidge", LOG_FNAME], stdin=subprocess.PIPE)

    subprocess.Popen("./bin/srinput")

    if not args.immed_start:
        subprocess.call("./bin/pyenv_start")

    if not args.debug:
        #Tell things that code is being run
        open(ROBOT_RUNNING,"w").close()

        #Feed display a newline now that code is to be run
        disp.stdin.write("\n")

    # List the enumerated boards in the log
    print "Found the following devices:"
    ps = pysric.PySric()
    for devclass in ps.devices:
        if devclass in [pysric.SRIC_CLASS_POWER, pysric.SRIC_CLASS_MOTOR, pysric.SRIC_CLASS_JOINTIO, pysric.SRIC_CLASS_SERVO]:
            for dev in ps.devices[devclass]:
                print dev

    print "Starting robot code"
    print "TODO: Start robot code"
except:
    print "Error: "
    traceback.print_exc(file=sys.stderr)
