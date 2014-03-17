import logging
import threading
import serial
import math
import usbenum

SERIAL_BAUD = 1000000

CMD_RESET = chr(0)
CMD_VERSION = chr(1)
CMD_SPEED0 = chr(2)
CMD_SPEED1 = chr(3)
CMD_BOOTLOADER = chr(4)

# The maximum value that the motor board will accept
PWM_MAX = 100

# The USB model string:
USB_MODEL = "MCV4B"

logger = logging.getLogger( "sr.motor" )

def find_devs():
    return usbenum.list_usb_devices(USB_MODEL)

class IncorrectFirmware(Exception):
    pass

class Motor(object):
    "A motor"
    def __init__(self, path, serialnum = None, check_fwver = True):
        self.serialnum = serialnum
        self.serial = serial.Serial(path, SERIAL_BAUD, timeout=0.1)
        self.lock = threading.Lock()

        with self.lock:
            self.serial.write(CMD_RESET)

        fw = self._get_fwver()
        if check_fwver and fw != "MCV4B:3\n":
            self.close()
            raise IncorrectFirmware()

        self.output_controller = MotorOutputController(self.serial, self.lock)

        self.m0 = MotorChannel(self.output_controller, 0)
        self.m1 = MotorChannel(self.output_controller, 1)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceba):
        self.close()

    def close(self):
        self.serial.close()

    def _get_fwver(self):
        for x in range(10):
            # We make repeat attempts at reading the firmware version
            # because the motor controller may have only just been powered-up.

            with self.lock:
                self.serial.write(CMD_VERSION)
                r = self.serial.readline()

            if len(r) > 0 and r[-1] == "\n":
                "Successfully read the firmware version"
                return r

        raise Exception( "Failed to read firmware version from motor controller" )

    def __repr__(self):
        return "Motor( serialnum = \"{0}\" )".format( self.serialnum )

    def _jump_to_bootloader(self):
        "Jump to the bootloader"
        MAGIC = "Entering bootloader\n"

        # Up the timeout to ensure bootloader response is received
        self.serial.timeout = 0.5

        with self.lock:
            self.serial.write(CMD_BOOTLOADER)

        # Check the command has been received
        r = self.serial.read( len(MAGIC) )

        if r != MAGIC:
            # There's not much we can do about this at the moment
            logger.warning("Incorrect bootloader entry string received")

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
