# Utility functions for starting/stopping sricd
from subprocess import Popen
import __builtin__, os, signal
import time, sys
PID_FILE = "/tmp/sricd.pid"

def _kill():
    "Kill sricd"
    print "Killing sricd"
    sys.stdout.flush()

    if os.path.exists(PID_FILE):
        f = open(PID_FILE)
        pid = int( f.read() )
        f.close()

        os.kill( pid, signal.SIGTERM )
    else:
        print "sricd file doesn't exist"

def start(logfile):
    out = open( logfile, "a" )
    print >>out, "-" * 80

    p = Popen( "./bin/sricd -p /tmp/sricd.pid -d -u /dev/ttyS1 -v",
               stdin = open("/dev/null", "r"),
               stdout = out, stderr = out, shell = True )
    p.wait()

    if hasattr(__builtin__, "__sr_trampoline"):
        "We're in the trampoline -- kill sricd on exit"
        __sr_cleanup_funcs.append( _kill )

    # Wait two seconds for enumeration and stuff to complete
    # (otherwise libsric clients will get no devices listed)
    time.sleep(2)
