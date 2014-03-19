#!/usr/bin/python
import optparse, signal, sys, os, time, shutil
from subprocess import Popen, call
import sricd, log, squidge, usercode, conf

# The length of a match in seconds
MATCH_DURATION = 180

class RobotRunner(object):
    def __init__(self, config, debug):
        self.config = config
        self.debug = debug

        print "Initialising..."
        self.init_env()
        self.init_fs()

        user_exec = os.path.join( config.user_dir, "robot.py" )
        if not os.path.exists( user_exec ):
            "No robot code around"
            raise Exception( "No robot code found." )

        sricd.start( os.path.join( config.log_dir, "sricd.log" ) )

        self.start_wm()

        self._test_sric()

        # The firmware updater requires input
        self.start_sr_input()
        self.firmware_update()

        self.user = usercode.UserCode( user_exec, config.log_dir, config.user_dir )
        self.start_gui()

    def _test_sric(self):
        "Check the SRIC bus works, and display an error if it doesn't."
        if sricd.test_bus():
           return

        # Bus is faulty -- show the fail message
        call( [ "imgshow",
                os.path.join( self.config.usr_dir,
                              "share", "sr", "sric-fail.png" ) ] )

    def start_sr_input(self):
        "Funnel button presses through to X"

        # First, tell the power board to enable button notifications
        import sr.pysric as pysric
        p = pysric.PySric()
        pdev = p.devices[pysric.SRIC_CLASS_POWER][0]
        pdev.txrx([5, 1])

        self.sr_input = Popen( "srinput" )

    def restart_sr_input(self):
        self.sr_input.kill()
        self.sr_input.wait()
        self.start_sr_input()

    def firmware_update(self):
        "Update firmware as necessary"

        def sricd_restart():
            sricd.restart( os.path.join( args.log_dir, "sricd.log" ) )
            self.restart_sr_input()

        # We import this here, because it depends on the sr module
        # which is only available at this point in time
        # (Our import path was extended after this file was imported)
        import fw

        with fw.FwUpdater(config, sricd_restart) as u:
            u.update()

    def start_gui(self):
        "Start all interactive GUI things"

        # Start the task-switcher
        Popen( ["sr-ts", self.config.robot_running],  shell = True )

        # Start the GUI
        self.squidge = squidge.Squidge( self.config.log_fname )

    def sigterm_handler(self, signum, frame):
        "Handle TERM signal"
        self.user.end_match()
        sys.exit(0)

    def run(self):
        #Tell things that code is being run
        open(self.config.robot_running,"w").close()

        mode_info = self.squidge.signal_start();

        print "Mode: %s\t Zone: %i" % ( mode_info["mode"],
                                        mode_info["zone"] )

        self.user.start( mode_info )
        start_time = time.time()

        if mode_info["mode"] == "comp":
            "Competition mode"
            self.real_sleep( start_time, MATCH_DURATION )
            self.user.end_match()

        signal.signal(signal.SIGTERM, self.sigterm_handler)

        self.user.wait()

    def init_env(self):
        "Initialise/check environment variables that we want"
        # Environment variables that we want:
        envs = { "PYSRIC_LIBDIR": self.config.lib_dir,
                 "LD_LIBRARY_PATH": self.config.lib_dir,
                 "PYTHONPATH": self.config.pylib_dir,
                 "DISPLAY": ":0.0" }
        for k,v in envs.iteritems():
            os.environ[k] = v

        if "PATH" not in os.environ:
            "The PATH environment variable doesn't make it through when run from udev"
            os.environ["PATH"] = "/usr/local/bin:/usr/bin:/bin:/usr/local/sbin:/usr/sbin:/sbin"

        # Prefix PATH with our bin directory
        os.environ["PATH"] =  "%s:%s" % ( self.config.bin_dir, os.environ["PATH"] )

        # Extend our import path to include pylib
        sys.path.append( self.config.pylib_dir )

    def init_fs(self):
        "Initialise/reset the filesystem"

        # Hack around zip not supporting file permissions...
        if not os.access( os.path.join( self.config.bin_dir, "sricd" ), os.X_OK ):
            call( "find %s -type f | xargs chmod u+x" % os.path.dirname(__file__),
                  shell = True )

        # Copy ldconfig cache over
        shutil.copyfile( os.path.join( self.config.var_dir, "ld.so.cache" ),
                         "/var/volatile/run/ld.so.cache" )

        # Remove files we don't want to be around
        for fname in [ self.config.robot_running,
                       "/tmp/robot-object-lock" ]:
            if os.path.exists( fname ):
                os.unlink( fname )

    def start_wm( self ):
        "Start the window manager"
        Popen( "matchbox-window-manager -use_titlebar no -use_cursor no",
               shell = True )

    def real_sleep( self, start_time, duration ):
        "Wait for the given amount of time from start_time"

        # time.sleep() can sleep for less time than specified
        # so loop calling it several times over
        while True:
            runtime = (time.time() - start_time)

            if runtime < duration:
                time.sleep( duration - runtime )
            else:
                break

def parse_args():
    parser = optparse.OptionParser( description = "Run some robot code." )
    parser.add_option( "-d", "--debug",
                       dest = "debug", action = "store_true",
                       help = "Send output to terminal, not logfile." )

    parser.add_option( "-i", "--immed",
                       dest = "immed_start", action = "store_true",
                       help = "Start user code immediately." )

    parser.add_option( "-l", "--log-dir",
                       dest = "log_dir", default = "./",
                       help = "Log into the given directory." )

    args, trailing_args = parser.parse_args()
    return args

if __name__ == "__main__":
    args = parse_args()
    config = conf.Config( prog_dir = os.path.abspath( os.path.dirname( __file__ ) ),
                          log_dir = args.log_dir )

    log.init( config.log_fname, config.log_dir, debug = args.debug )

    runner = RobotRunner( config,
                          debug = args.debug )

    if not args.immed_start:
        "Wait for the button press to happen"
        call( "pyenv_start" )

    runner.run()
