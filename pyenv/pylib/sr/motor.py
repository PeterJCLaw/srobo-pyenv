import threading
import serial
import math

SERIAL_BAUD = 1000000

CMD_RESET = chr(0)
CMD_VERSION = chr(1)
CMD_SPEED0 = chr(2)
CMD_SPEED1 = chr(3)

# The maximum value that the motor board will accept
PWM_MAX = 100

class Motor(object):
    "A motor"
    def __init__(self, path):
        self.serial = serial.Serial(path, SERIAL_BAUD, timeout=0.1)
        self.lock = threading.Lock()

        with self.lock:
            self.serial.write(CMD_RESET)

        if not self._is_mcv4b():
            print "Warning: Motor board is not running the expected firmware"

        self.output_controller = MotorOutputController(self.serial, self.lock)

        self.m0 = MotorChannel(self.output_controller, 0)
        self.m1 = MotorChannel(self.output_controller, 1)

    def close(self):
        self.serial.close()

    def _is_mcv4b(self):
        with self.lock:
            self.serial.write(CMD_VERSION)
            return self.serial.readline().split(":")[0] == "MCV4B"


class MotorOutputController(object):
    def __init__(self, serial, lock):
        self.serial = serial
        self.lock = lock
        self.power = [0, 0]

    def _encode_speed(self, speed):
        return chr(int(speed) + 128)

    def update(self):
        power0 = self.power[0] if self.power[0] != 0 else 1
        power1 = self.power[1] if self.power[1] != 0 else 1
        with self.lock:
            self.serial.write(CMD_SPEED0)
            self.serial.write(self._encode_speed(math.copysign(power1,
                                                               power0)))
            self.serial.write(CMD_SPEED1)
            self.serial.write(self._encode_speed(math.copysign(power0,
                                                               power1)))


class MotorChannel(object):
    def __init__(self, output_controller, channel):
        self.output_controller = output_controller
        self.channel = channel

    @property
    def power(self):
        return self.output_controller.power[self.channel]

    @power.setter
    def power(self, value):
        "target setter function"
        value = int(value)

        # Limit the value to within the valid range
        if value > PWM_MAX:
            value = PWM_MAX
        elif value < -PWM_MAX:
            value = -PWM_MAX

        self.output_controller.power[self.channel] = value
        self.output_controller.update()

    def __del__(self):
        self.power = 0
