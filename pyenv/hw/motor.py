# Interface to motor controllers
import pysric, types, __builtin__

# Motor controller SRIC commands
CMD_MOTOR_SET = 0
CMD_MOTOR_GET = 1

# The maximum value that the motor board will accept
PWM_MAX = 100

class Motor(object):
    "A motor"
    def __init__(self, dev):
        self.dev = dev
        # Private shadow of use_brake
        self._use_brake = True

    @property
    def target(self):
        "Read the target from the motor controller"
        r = self.dev.txrx( [ CMD_MOTOR_GET ] )
        t = r[0]

        if t & 0x80:
            "Sign-extend if negative"
            t = t | -256
        return t

    @target.setter
    def target(self, value):
        "target setter function"
        value = int(value)

        # Limit the value to within the valid range
        if value > PWM_MAX:
            value = PWM_MAX
        elif value < -PWM_MAX:
            value = -PWM_MAX

        brake = 0
        if value == 0 and self.use_brake:
            brake = 1

        self.dev.txrx( [ CMD_MOTOR_SET, value, brake ] )

    @property
    def use_brake(self):
        "Whether to use the brake when at 0 speed"
        return self._use_brake

    @use_brake.setter
    def use_brake(self, value):
        self._use_brake = value

        if self.target == 0:
            "Implement the new braking setting"
            self.target = 0

ps = pysric.PySric()
motor = []

def _stop_motor( dev ):
    dev.target = 0

_exit_registered = hasattr(__builtin__, "__sr_motor_registered")

if pysric.SRIC_CLASS_MOTOR in ps.devices:

    for dev in ps.devices[ pysric.SRIC_CLASS_MOTOR ]:
        motor_dev = Motor(dev)
        motor.append( motor_dev )

        if hasattr(__builtin__, "__sr_trampoline") and not _exit_registered:
            "Register an exit handler to turn off the motor on exit"
            __sr_cleanup_funcs.append( (_stop_motor, motor_dev) )

# The exit handlers have now been registered
__builtin__.__sr_motor_registered = True
