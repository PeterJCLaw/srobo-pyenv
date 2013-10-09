import serial

SERIAL_BAUD = 1000000

CMD_RESET = chr(0)
CMD_VERSION = chr(1)
CMD_SPEED0 = chr(2)
CMD_SPEED1 = chr(3)

SPEED_BRAKE = chr(2)

# The maximum value that the motor board will accept
PWM_MAX = 100

class Motor(object):
    "A motor"
    def __init__(self, path):
        self.serial = serial.Serial(path, SERIAL_BAUD, timeout=0.1)
        self.serial.write(CMD_RESET)
        if not self._is_mcv4b():
            print "Warning: Motor board is not running the expected firmware"

        self.m0 = MotorChannel(self.serial, 0)
        self.m1 = MotorChannel(self.serial, 1)

    def close(self):
        self.serial.close()

    def _is_mcv4b(self):
        self.serial.write(CMD_VERSION)
        return self.serial.readline().split(":")[0] == "MCV4B"

class MotorChannel(object):
    def __init__(self, serial, channel):
        self.serial = serial
        self.channel = channel

        # Private shadow of use_brake
        self._use_brake = True

        # There is currently no method for reading the power from a motor board
        self._power = 0

    def _encode_speed(self, speed):
        return chr(speed + 128)

    @property
    def power(self):
        return self._power

    @power.setter
    def power(self, value):
        "target setter function"
        value = int(value)
        self._power = value

        # Limit the value to within the valid range
        if value > PWM_MAX:
            value = PWM_MAX
        elif value < -PWM_MAX:
            value = -PWM_MAX

        if self.channel == 0:
            self.serial.write(CMD_SPEED0)
        else:
            self.serial.write(CMD_SPEED1)

        if value == 0 and self.use_brake:
            self.serial.write(SPEED_BRAKE)
        else:
            self.serial.write(self._encode_speed(value))

    @property
    def use_brake(self):
        "Whether to use the brake when at 0 speed"
        return self._use_brake

    @use_brake.setter
    def use_brake(self, value):
        self._use_brake = value

        if self.power == 0:
            "Implement the new braking setting"
            self.power = 0

    def __del__(self):
        self.power = 0
