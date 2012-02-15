import os

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
