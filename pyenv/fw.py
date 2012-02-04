#!/usr/bin/python
# Routines for invoking flashb and thus updating board firmware.
import subprocess, os.path

def update_power( root, bin_dir, log_dir ):
    fwlog = open( os.path.join( log_dir, "fw-log.txt" ) , "at")

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

if __name__ == "__main__":
    update_power()
