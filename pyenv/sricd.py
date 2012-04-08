# Utility functions for starting/stopping sricd
from subprocess import Popen
import os, signal, time, sys, threading, time

PID_FILE = "/tmp/sricd.pid"

def kill():
    "Kill sricd"
    print "Killing sricd"
    sys.stdout.flush()

    if os.path.exists(PID_FILE):
        f = open(PID_FILE)
        pid = int( f.read() )
        f.close()

        os.kill( pid, signal.SIGKILL )
    else:
        print "sricd file doesn't exist"

def start(logfile):
    out = open( logfile, "a" )
    print >>out, "-" * 80

    p = Popen( "sricd -p /tmp/sricd.pid -di -u /dev/ttyS1 -v",
               stdin = open("/dev/null", "r"),
               stdout = out, stderr = out, shell = True )
    p.wait()

def restart(logfile):
    kill()
    start(logfile)

class EnumWaiter(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

        # Allow things to quit even if this thread persists
        self.daemon = True

        # Hold this lock until we have finished enumerating
        self.waiting = threading.Lock()
        self.waiting.acquire()

    def run(self):
        from sr.pysric import PySric

        ps = PySric()
        self.waiting.release()

def test_bus():
    """Test the bus to see if it works

    Return True if it works."""

    waiter = EnumWaiter()
    start_time = time.time()
    waiter.start()

    while (time.time() - start_time) < 5:
        if waiter.waiting.acquire( False ):
            "Got the lock - enum's done"
            waiter.join()
            return True

        time.sleep(0.1)

    return False
