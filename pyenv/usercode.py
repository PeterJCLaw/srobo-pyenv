import subprocess, sys, os, json, time, tempfile
from subprocess import Popen, call

class UserCode(object):
    "Object for managing the user's code"

    def __init__(self, user_exec, log_dir, user_dir):

        self.start_fifo = tempfile.mktemp()

        user_rev = self._get_user_revision(user_dir)

        print "Running user code", user_rev
        self.proc = Popen( [ "python", "-m", "sr.loggrok",
                             user_exec,
                             "--usbkey", log_dir,
                             "--startfifo", self.start_fifo ],
                           cwd = user_dir,
                           stdout = sys.stdout,
                           stderr = sys.stderr )

    def _get_user_revision(self, user_dir):
        user_rev_path = os.path.join(user_dir, '.user-rev')
        user_rev = 'unknown @ unknown'
        if os.path.exists(user_rev_path):
            with open(user_rev_path) as f:
                user_rev = f.read().strip()
        return user_rev

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
        self.proc.kill()

        #### Now kill the motor rail

        # Augment the import path so we can get to the Power class
        import sr.tssric, sr.power, sr.pysric

        sricman = sr.tssric.SricCtxMan()
        power = sr.power.Power( sricman.devices[sr.pysric.SRIC_CLASS_POWER][0] )
        power._set_motor_rail( False )

        print "Match ended -- User code killed."


    def wait(self):
        r = self.proc.wait()
        print "Robot code exited with code %i" % r
