import os, sys
import addcr

def init( fname, log_dir, debug ):
    "Initialise and use a new log file"

    if not os.path.exists( log_dir ):
        os.mkdir( log_dir )

    if not debug:

        if os.path.exists( fname ):
            "Move the old log file to log.txt.N"
            move_old_logfile( fname,
                              old_log_dir = os.path.join( log_dir, "old-logs" ) )

        "Put stdout and stderr into the log file"
        sys.stderr = sys.stdout = addcr.AddCRWriter(open( fname, "at", 1))

    else:
        if not os.path.exists( fname ):
            "Some utilities rely on the log file existing"
            open( fname, "w" ).close()

def move_old_logfile( log_fname, old_log_dir ):
    "Move an old log file to the right place"

    if not os.path.exists( old_log_dir ):
        os.mkdir( old_log_dir )

    n = 1
    while True:
        "Find a log file that doesn't exist"
        f = os.path.join( old_log_dir, "log-%i.txt" % (n) )

        if not os.path.exists( f ):
            break
        n += 1

    os.rename( log_fname, f )
