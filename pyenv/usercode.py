import subprocess, sys, os, json, time, tempfile
from subprocess import Popen, call

class UserCode(object):
    "Object for managing the user's code"

    def __init__(self, user_exec, log_dir, user_dir):

        self.start_fifo = tempfile.mktemp()

        print "Running user code."
        self.proc = Popen( [ "python", "-m", "sr.loggrok",
                             user_exec,
                             "--usbkey", log_dir,
                             "--startfifo", self.start_fifo ],
                           cwd = user_dir,
                           stdout = sys.stdout,
                           stderr = sys.stderr )

    def start(self, match_info):
        """Send the start signal to the user's code, along with the match info"""

        # Ready for user code to execute, send it useful info:
        while not os.path.exists( self.start_fifo ):
            time.sleep(0.1)

        print "Starting user code."
        with open( self.start_fifo, "w" ) as f:
            f.write( json.dumps( match_info ) )
        
    def end_match(self):
        "End the match by killing the user's code, and dropping the motor rail"
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


    def wait(self):
        r = self.proc.wait()
        print "Robot code exited with code %i" % r
