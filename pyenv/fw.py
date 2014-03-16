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

class FwUpdater(object):
    def __init__(self, conf):
        self.conf = conf
        self.splash = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceba):
        # Close our stuff
        self.stop_splash()

    def start_splash(self):
        self.splash = subprocess.Popen( [ os.path.join( self.conf.bin_dir,
                                                        "fwsplash" ) ] )

    def stop_splash(self):
        if self.splash is not None:
            self.splash.kill()
            self.splash.wait()

    def update(self):
        sric_restart = False

        # First, check if a power board update is required:
        if self.check_power_update():
            self.start_splash()
            sric_restart = self.update_power()

        return sric_restart

    def check_power_update(self):
        "Determine if a power board update is necessary using its vbuf"
        import sr.pysric as pysric
        p = pysric.PySric()
        vb = sric_read_vbuf( p.devices[ pysric.SRIC_CLASS_POWER ][0] )
        return vb != power_vbuf

    def update_power( self):
        logpath = os.path.join( self.conf.log_dir, "fw-log.txt" )
        fwlog = open( logpath , "at")
        fwdir = os.path.join( self.conf.prog_dir, "firmware" )

        p = subprocess.Popen( [ os.path.join( self.conf.bin_dir, "flashb" ),
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
