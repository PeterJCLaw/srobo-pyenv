#!/usr/bin/python
# Routines for invoking flashb and thus updating board firmware.
import json
import subprocess, os.path, re
import sr.motor
from sr.power import Power
import sr.pysric as pysric
import stm32loader
import threading
import time

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

def flash_motor(dev_path, serialnum, prog_cb, fw_path, log_fd):
    print >>log_fd, "Flashing motor board", serialnum

    c = stm32loader.CommandInterface( port=dev_path,
                                      baudrate=115200,
                                      prog_cb = prog_cb )
    c.initChip()
    c.cmdEraseMemory()

    # Write
    d = [ord(x) for x in open(fw_path, "r").read()]
    c.writeMemory(0x08000000, d)

    # Verify:
    v = c.readMemory(0x08000000, len(d))
    if d != v:
        raise Exception("Firmware verification error :(")

    print >>log_fd, "Verified OK"

    # Reset/quit bootloader
    c.cmdGo(0x8000000)



class LockableUnsafeDev(object):
    "Lockable SRIC device that does *not* use a threadlocal connection"
    def __init__(self, dev ):
        # A lock for transactions on this device
        self.dev = dev
        self.lock = threading.Lock()

    def __getattr__(self, name):
        "Provide access to the underlying Sric device"
        return getattr( self.dev, name )

    def txrx( self, *args, **kw ):
        return self.dev.txrx( *args, **kw )

class FwUpdater(object):
    def __init__(self, conf, sricd_restart):
        self.conf = conf
        self.sricd_restart = sricd_restart
        self.splash = None

        self.fwdir = os.path.join( self.conf.prog_dir, "firmware" )
        logpath = os.path.join( self.conf.log_dir, "fw-log.txt" )
        self.fwlog = open( logpath , "at")

        # Whether the user has confirmed the update's about to happen yet
        self.user_confirmed = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceba):
        # Close our stuff
        self.stop_splash()
        self.fwlog.close()

    def start_splash(self):
        if self.splash is not None:
            "Splash is already running"
            return

        self.splash = subprocess.Popen( [ os.path.join( self.conf.bin_dir,
                                                        "fwsplash" ) ],
                                        stdin = subprocess.PIPE, stdout = subprocess.PIPE )

    def wait_confirmation(self):
        if self.user_confirmed:
            return

        self.start_splash()
        self.splash.stdout.readline()
        self.user_confirmed = True

    def stop_splash(self):
        if self.splash is not None:
            self.splash.kill()
            self.splash.wait()

    def update(self):
        if self.check_power_update():
            self.wait_confirmation()
            self.update_power()
            # The power board's been adjusted, so restart it
            self.sricd_restart()

        # Now bring up the motor rail so we can talk to the motor boards
        p = pysric.PySric()
        dev = LockableUnsafeDev(p.devices[pysric.SRIC_CLASS_POWER][0])
        # Power's constructor brings up the motor rail
        power = Power(dev)

        # Find motor boards that need updating:
        need_update = []
        for n, mdev in enumerate(sr.motor.find_devs()):
            if self.check_motor_update(mdev.device_node):
                need_update.append((n, mdev))

        if len(need_update):
            self.wait_confirmation()

        for n, mdev in need_update:
            self.update_motor(mdev.device_node, n, mdev["ID_SERIAL_SHORT"],
                              prog_scale = 1.0/len(need_update),
                              prog_offset = float(n)/len(need_update) )

    def check_power_update(self):
        "Determine if a power board update is necessary using its vbuf"

        # Disable power board firmware updates
        # There's some kind of funk involved in the version checking
        # that isn't worth fixing now.  (And never will be.)
        return False

        p = pysric.PySric()
        vb = sric_read_vbuf( p.devices[ pysric.SRIC_CLASS_POWER ][0] )
        return vb != power_vbuf

    def update_power( self):
        p = subprocess.Popen( [ os.path.join( self.conf.bin_dir, "flashb" ),
                                "-c", os.path.join( self.fwdir, "flashb.config" ),
                                "-n", "power", "-f",
                                os.path.join( self.fwdir, "power-top" ),
                                os.path.join( self.fwdir, "power-bottom" ) ],
                              stdout = self.fwlog, stderr = self.fwlog )

        pulsemsg = "{0}\n".format( json.dumps( { "type": "pulse", "msg": "Updating power board firmware." } ) )

        while p.poll() is None:
            self.splash.stdin.write( pulsemsg )
            self.splash.stdin.flush()
            time.sleep(0.25)
        res = p.wait()

        print >>self.fwlog, "flashb returned %i" % (res),

    def check_motor_update(self, dev_path):
        try:
            motor = sr.motor.Motor(dev_path)
        except sr.motor.IncorrectFirmware:
            "Requires update"
            return True

        motor.close()
        return False

    def update_motor(self, dev_path, num, serialnum, prog_scale, prog_offset):
        with sr.motor.Motor(dev_path, check_fwver=False) as motor:
            motor._jump_to_bootloader()

        def prog_cb(mode, prog):

            if mode == "READ":
                msg = "Verifying"
                prog = (0.5 + (prog * 0.5))
            else:
                msg = "Writing to"
                prog *= 0.5

            prog *= prog_scale
            prog += prog_offset
            msg += " motor board {0} ({1}).".format( num, serialnum )

            m = { "type": "prog",
                  "fraction": prog,
                  "msg": msg }
            s = "{0}\n".format(json.dumps(m))
            self.splash.stdin.write(s)
            self.splash.stdin.flush()

            print >>self.fwlog, mode, prog

        flash_motor(dev_path, serialnum, prog_cb,
                    os.path.join( self.fwdir, "mcv4.bin" ),
                    self.fwlog)
