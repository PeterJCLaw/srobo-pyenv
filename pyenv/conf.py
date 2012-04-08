import os

class Config(object):
    def __init__(self, prog_dir, log_dir):

        self.prog_dir = prog_dir
        self.log_dir = log_dir

        self.bin_dir = os.path.join( prog_dir, "bin" )
        self.lib_dir = os.path.join( prog_dir, "lib" )
        self.pylib_dir = os.path.join( prog_dir, "pylib" )
        self.user_dir = os.path.join( prog_dir , "user" )
        self.var_dir = os.path.join( prog_dir, "var")
        self.usr_dir = os.path.join( prog_dir, "usr")
        
        self.log_fname = os.path.join( log_dir, "log.txt" )

        self.robot_running = "/tmp/robot-running"
