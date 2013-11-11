#!/usr/bin/python
# Routines for invoking flashb and thus updating board firmware.
import subprocess, os.path, re

SRIC_VERSION_BUF_CMD = 0x84

power_vbuf = [ 7, 100, 114, 105, 118, 101, 114, 115, 5, 37,
               251, 84, 30, 144, 8, 102, 108, 97, 115, 104,
               52, 51, 48, 5, 87, 171, 113, 171, 124, 7,
               108, 105, 98, 115, 114, 105, 99, 5, 31, 227,
               112, 155, 220, 1, 46, 5, 230, 243, 165, 7,
               161]

def sric_read_vbuf(dev):
    "Read the versionbuf from dev"
    d = []
    off = 0

    while True:
        "Loop until we've received all the buffer"
        r = dev.txrx( [SRIC_VERSION_BUF_CMD, off & 0xff, (off >> 8) & 0xff] )
        d += r
        if len(r) == 0:
            break
        off += len(r)

    return d

def update_with_gui( root, bin_dir, log_dir ):
    if not check_power_update():
        "No update required"
        return False

    p = subprocess.Popen( [ os.path.join( bin_dir, "fwsplash" ) ] )

    res = update_power( root, bin_dir, log_dir )

    p.kill()
    p.wait()
    return res

def check_power_update():
    "Determine if a power board update is necessary using its vbuf"
    import sr.pysric as pysric
    p = pysric.PySric()
    vb = sric_read_vbuf( p.devices[ pysric.SRIC_CLASS_POWER ][0] )
    return vb != power_vbuf

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
