# Copyright Robert Spanton 2011
import json, sys, optparse, time, os
import pysric, tssric
import motor, power, servo

class Robot(object):
    """Class for initialising and accessing robot hardware"""

    def __init__(self, wait_start = True):
        self.sricman = tssric.SricCtxMan()

        self._dump_bus()
        self._init_devs()

        self._parse_cmdline()
        if wait_start:
            self._wait_start()

    def _dump_bus(self):
        "Write the contents of the SRIC bus out to stdout"
        print "Found the following devices:"
        ps = self.sricman.get()
        for devclass in ps.devices:
            if devclass in [ pysric.SRIC_CLASS_POWER, pysric.SRIC_CLASS_MOTOR,
                             pysric.SRIC_CLASS_JOINTIO, pysric.SRIC_CLASS_SERVO ]:
                for dev in ps.devices[devclass]:
                    print dev

    def _parse_cmdline(self):
        "Parse the command line arguments"
        parser = optparse.OptionParser()

        parser.add_option( "--usbkey", type="string", dest="usbkey",
                           help="The path of the (non-volatile) user USB key" )

        parser.add_option( "--startfifo", type="string", dest="startfifo",
                           help="The path of the fifo which start information will be received through" )
        (options, args) = parser.parse_args()

        self.usbkey = options.usbkey
        self.startfifo = options.startfifo

    def _wait_start(self):
        "Wait for the start signal to happen"

        os.mkfifo( self.startfifo )
        f = open( self.startfifo, "r" )
        d = f.read()
        f.close()

        j = json.loads(d)

        if "zone" not in j or "mode" not in j:
            raise Exception( "'zone' and 'mode' must be in startup info" )

        self.mode = j["mode"]
        self.zone = j["zone"]

        if self.mode not in ["comp", "dev"]:
            raise Exception( "mode of '%s' is not supported -- must be 'comp' or 'dev'" % self.mode )
        if self.zone < 0 or self.zone > 3:
            raise Exception( "zone must be in range 0-3 inclusive -- value of %i is invalid" % self.zone )

    def _init_devs(self):
        "Initialise the attributes for accessing devices"

        # Motors:
        self.motors = []
        if pysric.SRIC_CLASS_MOTOR in self.sricman.devices:
            for dev in self.sricman.devices[ pysric.SRIC_CLASS_MOTOR ]:
                self.motors.append( motor.Motor( dev ) )

        # Power board
        if pysric.SRIC_CLASS_POWER not in self.sricman.devices:
            raise Exception( "Power board not enumerated -- aborting." )
        self.power = power.Power( self.sricman.devices[pysric.SRIC_CLASS_POWER][0] )

        # Servos:
        self.servos = []
        if pysric.SRIC_CLASS_SERVO in self.sricman.devices:
            for dev in self.sricman.devices[ pysric.SRIC_CLASS_MOTOR ]:
                self.servos.append( servo.Servo(dev) )
