# Copyright Robert Spanton 2011
import json, sys, optparse, time, os, glob
import pysric, tssric
import motor, power, servo, jointio, vision

class Robot(object):
    """Class for initialising and accessing robot hardware"""

    def __init__( self,
                  wait_start = True,
                  init_vision = True,
                  camera_dev = "/dev/video0" ):
        self.sricman = tssric.SricCtxMan()

        self._dump_bus()
        self._init_devs()

        if init_vision:
            self._init_vision(camera_dev)

        self._parse_cmdline()
        if wait_start:
            self._wait_start()
        else:
            self.mode = "dev"
            self.zone = 0

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

        mapping = { pysric.SRIC_CLASS_MOTOR: ( "motors", motor.Motor ),
                    pysric.SRIC_CLASS_SERVO: ( "servos", servo.Servo ),
                    pysric.SRIC_CLASS_JOINTIO: ( "io", jointio.JointIO ) }

        for devtype, info in mapping.iteritems():
            attrname, cls = info
            if devtype in self.sricman.devices:
                l = []
                setattr( self, attrname, l )

                for dev in self.sricman.devices[ devtype ]:
                    l.append( cls( dev ) )

        # Power board
        if pysric.SRIC_CLASS_POWER not in self.sricman.devices:
            raise Exception( "Power board not enumerated -- aborting." )
        self.power = power.Power( self.sricman.devices[pysric.SRIC_CLASS_POWER][0] )

    def _init_vision(self, camdev):
        if not os.path.exists(camdev):
            "Camera isn't connected."
            return

        # Find libsric.so:
        libpath = None
        if "LD_LIBRARY_PATH" in os.environ:
            for d in os.environ["LD_LIBRARY_PATH"].split(":"):
                l = glob.glob( "%s/libkoki.so*" % os.path.abspath( d ) )

                if len(l):
                    libpath = os.path.abspath(d)
                    break

        if libpath == None:
            v = vision.Vision(camdev)
        else:
            v = vision.Vision(camdev, libpath)

        self.vision = v

    def see(self, res = (800,600), stats = False):
        return self.vision.see( res = res,
                                mode = self.mode,
                                stats = stats )
