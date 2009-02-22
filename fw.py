#!/usr/bin/python
# Routines for invoking flashb and thus updating board firmware.
# **** WARNING: Changing and shipping this file without full testing could result in bricked boards. ****
import subprocess, os.path

# All the devices that receive firmware like this
DEVICES = ["motor", "jointio", "power", "pwm"]

def update_dev(name):
    "Update the given device"
    
    if False in [os.path.exists( "./firmware/%s-%s" % (name,x) ) for x in ["top", "bottom"]]:
        "Check that there is firmware for the device"
        return False

    fwlog = open("fw-log.txt", "at")
    p = subprocess.Popen( [ "./flashb",
                            "-g",   # Give up after a few attempts to talk to the device
                            "-c", "./flashb.config",
                            "-n", name,
                            "./firmware/%s-top" % name,
                            "./firmware/%s-bottom" % name ],
                          stdout = fwlog, stderr = fwlog )
    
    # Let flashb do it's thing
    p.communicate()
    res = p.wait()

    print "%s: flashb returned" % name, res,
    if res == 0:
        print "(success)"
    else:
        print "(fail)"

    fwlog.close()

def update_all():
    "Update the firmware for all devices"
    print "*** Updating device firmwares ***"
    for dev in DEVICES:
        update_dev(dev)
    print "*** Firmware update complete *** "

if __name__ == "__main__":
    import sys, os
    os.putenv("LD_LIBRARY_PATH", "/usr/local/lib")
    
    if len(sys.argv) < 2:
        print "Usage: fw.py DEVICE"
        sys.exit(1)

    dev = sys.argv[1]
    update_dev(dev)
