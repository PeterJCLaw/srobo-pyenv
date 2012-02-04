#!/usr/bin/python
# Routines for invoking flashb and thus updating board firmware.
import subprocess, os.path, re

def update_with_gui( root, bin_dir, log_dir ):
    p = subprocess.Popen( [ os.path.join( bin_dir, "fwsplash" ) ] )

    res = update_power( root, bin_dir, log_dir )

    p.kill()
    p.wait()
    return res

def update_power( root, bin_dir, log_dir ):
    logpath = os.path.join( log_dir, "fw-log.txt" )
    fwlog = open( logpath , "at")

    fwdir = os.path.join( root, "firmware" )

    p = subprocess.Popen( [ os.path.join( bin_dir, "flashb" ),
                            "-c", os.path.join( fwdir, "flashb.config" ),
                            "-n", "power",
                            os.path.join( fwdir, "power-top" ),
                            os.path.join( fwdir, "power-bottom" ) ],
                          stdout = fwlog, stderr = fwlog )
    
    # Let flashb do it's thing
    p.communicate()
    res = p.wait()

    print >>fwlog, "flashb returned %i" % (res),
    fwlog.close()

    log = open( logpath, "r" ).read()
    # See if an update actually occurred
    res = re.search( "Sending firmware version", log )

    if res != None:
        "An update did indeed occur"
        return True
    return False

if __name__ == "__main__":
    update_power()
