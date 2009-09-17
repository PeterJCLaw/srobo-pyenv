import c2py
from events import Event
import poll
# Whether to display i2c debug info
DEBUG_I2C = False

ADDRESS = 0x12

# Identify command
IDENTIFY = 0x00

INTEGER = 1
BOOL = 2
ARRAY = 3

TYPE_U8 = { "type": INTEGER, "len": 1, "signed": False }
TYPE_U16 = { "type": INTEGER, "len": 2, "signed": False }
TYPE_U32 = { "type": INTEGER, "len": 4, "signed": False }
TYPE_I8 = { "type": INTEGER, "len": 1, "signed": True }
TYPE_I16 = { "type": INTEGER, "len": 2, "signed": True }
TYPE_I32 = { "type": INTEGER, "len": 4, "signed": True }
TYPE_BOOL = { "type": BOOL }
# Array of things
TYPE_ARR = { "type": ARRAY }

# Types of sensors:
SENSOR_NULL = 0
SENSOR_ADS5030 = 1
# Types of controllers:
CONTROLLER_UNITY = 0
CONTROLLER_PID = 1

class Command:
    def __init__(self, reg, rtype, rlen = None, ro = False):
        self.reg = reg
        self.rtype = rtype
        self.len = rlen
        self.ro = ro

    def read(self):
        if self.rtype["type"] == INTEGER:
            d = self._reg_read( self.rtype["len"] )
            assert len(d) == self.rtype["len"]

            val = 0
            # Switch to most significant byte first
            d.reverse()
            for x in d:
                val <<= 8
                val |= x

            if self.rtype["signed"]:
                "Sign extend"
                if val & (1 << (len(d)*8-1)):
                    "Most significant bit set -- needs sign extending"
                    # In python, -1 is an infinite string of '1' bits
                    val |= -1 << (len(d)*8)

            return val

        elif self.rtype["type"] == BOOL:
            d = self._reg_read( 1 )
            if d[0]:
                return True
            return False

    def write(self, v):
        if self.rtype["type"] == INTEGER:
            d = []
            for p in range(0,self.rtype["len"]):
                d.append( v & 0xff )
                v >>= 8

            self._reg_write(d)

        elif self.rtype["type"] == BOOL:
            if v:
                self._reg_write([1])
            else:
                self._reg_write([0])

    def _reg_read( self, l ):
        """Read a motor controller register.
        reg is the register number.
        l is the length of the register in byte.
        Returns array of received bytes."""
        while True:
            try:
                r = c2py.motor_reg_read( ADDRESS, self.reg, l )
                break
            except c2py.I2CError:
                pass
        self._debug("Read", r)
        return r

    def _reg_write( self, data ):
        self._debug("Write", data)
        while True:
            try:
                c2py.motor_reg_write( ADDRESS, self.reg, data )

                if self._reg_read( len(data) ) == data:
                    break
            except c2py.I2CError:
                pass

    def _debug(self, s, data):
        if not DEBUG_I2C:
            return
        print "%s(%i):" % (s, self.reg),
        for b in data:
            print "%x" % b, 
        print

class CommandSet:
    def __init__(self, channel):
        if channel == 0:
            controller = 16
            sensor = 32
            control = 48
        else:
            controller = 64
            sensor = 80
            control = 96

        # Identity
        self.IDENTITY = Command( 0, TYPE_U32 )

        # PID controller
        self.PID_KP = Command( controller+0, TYPE_I16 )
        self.PID_KI = Command( controller+1, TYPE_I16 )
        self.PID_KD = Command( controller+2, TYPE_I16 )

        # ADS5030 sensor
        self.ADS5030_CLK = Command( sensor+0, TYPE_U8 )
        self.ADS5030_DIO = Command( sensor+1, TYPE_U8 )
        self.ADS5030_SHR = Command( sensor+2, TYPE_U8 )

        ## Control loop:
        self.CONTROL_ENABLED = Command( control+0, TYPE_BOOL )
        self.CONTROL_TARGET = Command( control+1, TYPE_I32 )
        self.CONTROL_LAST_POS = Command( control+2, TYPE_I32 )
        # Speed
        self.CONTROL_SPEED_ENABLED = Command( control+3, TYPE_BOOL )
        self.CONTROL_SPEED_INC = Command( control+4, TYPE_I16 )
        self.CONTROL_SPEED_PERIOD = Command( control+5, TYPE_I16 )
        # Controller and sensor selection
        self.CONTROL_CONTROLLER = Command( control+6, TYPE_U8 )
        self.CONTROL_SENSOR = Command( control+7, TYPE_U8 )

CMD = [ CommandSet(0), CommandSet(1) ]

class ADS5030Sensor:
    def __init__(self, channel):
        self.channel = channel
        self.cmds = CMD[channel]

    def set_pins(self, clk, dio):
        if clk not in [0,1,2,3] or dio not in [0,1,2,3]:
            raise "clk and dio must be between 0 and 3 inclusive"

        self.cmds.ADS5030_CLK.write( 1 << clk )
        self.cmds.ADS5030_DIO.write( 1 << dio )

    def set_shr(self, shr):
        self.cmds.ADS5030_SHR.write(shr)

class PIDController:
    def __init__(self, channel):
        self.channel = channel
        self.cmds = CMD[channel]

    def set_coeff( self, kp, ki, kd ):
        self.cmds.PID_KP.write( kp )
        self.cmds.PID_KI.write( ki )
        self.cmds.PID_KD.write( kd )

class MotorEventInfo:
    def __init__(self):
        self.channels = []

class MotorEvent(Event):
    def __init__(self, channel):
        Event.__init__(self, motor)
        self.channel = channel

    def add_info(self, ev):
        if not hasattr(ev, "motor"):
            ev.motor = MotorEventInfo()
        if self.channel not in ev.motor.channels:
            ev.motor.channels.append( self.channel )

class Motor(poll.Poll):
    def __init__(self, channel):
        poll.Poll.__init__(self)

        self.channel = channel
        self.cmds = CMD[channel]

        self._state_loaded = False
        self._cur_sensor_attr = None
        self._cur_controller_attr = None
        self._sensor = None
        self._controller = None

    def enable(self):
        self.cmds.CONTROL_ENABLED.write(True)

    def disable(self):
        self.cmds.CONTROL_ENABLED.write(False)

    def getpos(self):
        return self.cmds.CONTROL_LAST_POS.read()

    def eval(self):
        "The poll eval function"
        if self.getpos() == self.target:
            return MotorEvent(self.channel)

    def __setattr__(self, n, v):
        if n == "sensor":
            self._switch_sensor(v)
        elif n == "controller":
            self._switch_controller(v)
        elif n == "target":
            self._set_target(v)
        else:
            self.__dict__[n] = v

    def _load_state(self):
        if self._state_loaded:
            return

        self._switch_sensor_n( self.cmds.CONTROL_SENSOR.read(), False )
        self._switch_controller_n( self.cmds.CONTROL_CONTROLLER.read(), False )
        self._state_loaded = True
        self._target = self.cmds.CONTROL_TARGET.read()

    def __getattr__(self, n):
        if n in ["PID", "ads5030", "sensor", "controller","target"]:
            # Time to discover what mode the motor controller is in:
            self._load_state()

        if n == "sensor":
            return self._sensor
        if n == "controller":
            return self._controller
        if n == "target":
            t = self._target
            if self._sensor == Motors.NULL:
                t = t / 3.28
            return t

        if self.__dict__.has_key( n ):
            return self.__dict__[n]

        raise AttributeError

    def _switch_sensor_n(self, n, command = True):
        # Called by __setattr__ -- careful.
        prev = self._cur_sensor_attr

        if n == SENSOR_NULL:
            self._sensor = Motors.NULL
            self.NULL = None
            self._cur_sensor_attr = "NULL"

        elif n == SENSOR_ADS5030:
            self._sensor = Motors.ADS5030
            self.ads5030 = ADS5030Sensor(self.channel)
            self._cur_sensor_attr = "ads5030"

        else:
            raise "Invalid sensor requested"

        if command:
            self.cmds.CONTROL_SENSOR.write(n)

        if prev != None and self._cur_sensor_attr != prev :
            "Get rid of the old sensor's properties"
            delattr(self, prev)

    def _set_target(self, t):
        # Called by __setattr__ -- careful.
        self._load_state()

        if self._cur_controller_attr == "UNITY":
            # Scale -100 to 100 to -328 to 328
            t = t * 3.28
            if t > 328:
                t = 328
            elif t < -328:
                t = -328
        
        t = int(t)

        self.cmds.CONTROL_TARGET.write(t)
        self._target = t

    def _switch_sensor(self, v):
        if v == Motors.NULL:
            self._switch_sensor_n( SENSOR_NULL )
        elif v == Motors.ADS5030:
            self._switch_sensor_n( SENSOR_ADS5030 )
        else:
            raise "Invalid sensor requested"

    def _switch_controller_n(self, n, command = True):
        # Called by __setattr__ -- careful.
        prev = self._cur_controller_attr

        if n == CONTROLLER_UNITY:
            self._controller = Motors.UNITY
            self.UNITY = None
            self._cur_controller_attr = "UNITY"

        elif n == CONTROLLER_PID:
            self._controller = Motors.PID
            self.PID = PIDController(self.channel)
            self._cur_controller_attr = "PID"

        else:
            raise "Invalid controller requested"

        if command:
            self.cmds.CONTROL_CONTROLLER.write(n)

        if prev != None and self._cur_controller_attr != prev:
            "Get rid of the old controller's properties"
            delattr(self, prev)

    def _switch_controller(self, v):
        # Called by __setattr__ -- careful.

        if v == Motors.UNITY:
            self._switch_controller_n( CONTROLLER_UNITY )
        elif v == Motors.PID:
            self._switch_controller_n( CONTROLLER_PID )

class Motors(list):
    # Sensor types
    NULL = "null sensor"
    ADS5030 = "ads5030 sensor"

    # Controller types:
    UNITY = "unity controller"
    PID = "pid controller"

    def __init__(self):
        list.__init__(self)
        self.append( Motor(0) )
        self.append( Motor(1) )

motor = Motors()
