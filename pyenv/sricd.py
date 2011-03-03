# Utility functions for starting/stopping sricd
from subprocess import Popen

def start(logfile):
    out = open( logfile, "a" )
    print >>out, "-" * 80

    p = Popen( "./bin/sricd -d -u /dev/ttyS1 -v",
               stdout = out, stderr = out, shell = True )
    p.wait()
