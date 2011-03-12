# Utility functions for starting/stopping sricd
from subprocess import Popen
import __builtin__, os, signal
import time, sys
PID_FILE = "/tmp/sricd.pid"

def start(logfile):
    out = open( logfile, "a" )
    print >>out, "-" * 80

    p = Popen( "./bin/sricd -p /tmp/sricd.pid -d -u /dev/ttyS1 -v",
               stdin = open("/dev/null", "r"),
               stdout = out, stderr = out, shell = True )
    p.wait()

    # Wait two seconds for enumeration and stuff to complete
    # (otherwise libsric clients will get no devices listed)
    time.sleep(2)
