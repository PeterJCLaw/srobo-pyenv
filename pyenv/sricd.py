# Utility functions for starting/stopping sricd
from subprocess import Popen
import time

def start(logfile):
    out = open( logfile, "a" )
    print >>out, "-" * 80

    p = Popen( "./bin/sricd -d -u /dev/ttyS1 -v",
               stdout = out, stderr = out, shell = True )
    p.wait()

    # Wait two seconds for enumeration and stuff to complete
    # (otherwise libsric clients will get no devices listed)
    time.sleep(2)
