import serial
import time

SERIAL_BAUD = 115200

# Magic time!
# We do this so that values print nicely, but can also be used in
# the obvious ways
class LogicLevel(object):
    def __init__(self, name, interpretation):
        self.name = name
        self.interpretation = interpretation

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name

    def __nonzero__(self):
        return interpretation

    def __eq__(self, x):
        if isinstance(x, LogicLevel):
            return x.interpretation == self.interpretation
        else:
            return x == self.interpretation

    def __ne__(self, x):
        return not self.__eq__(x)

HIGH = LogicLevel("HIGH", True)
LOW = LogicLevel("LOW", False)

# Strings here so that they print nicely
INPUT = "INPUT"
OUTPUT = "OUTPUT"
INPUT_PULLUP = "INPUT_PULLUP"

class Ruggeduino(object):
    def __init__(self, path):
        self.serial = serial.Serial(path, SERIAL_BAUD, timeout=0.1)
        self._is_srduino()

    def close(self):
        self.serial.close()

    def command(self, data, expected_len = 0):
        res = bytes()
        attempts = 20
        while len(res) != expected_len:
            if len(res) == 0:
                # Not received anything yet, retry the command
                self.serial.write(bytes(data))
            res += self.serial.read(expected_len - len(res))
            attempts -= 1
            if attempts == 0:
                raise Exception("Communications with Ruggeduino failed")
        return res

    def _is_srduino(self):
        response = self.command('a', expected_len=1)
        if response == "a":
            return True
        else:
            return False

    def _encode_pin(self, pin):
        return chr(ord('a') + pin)

    def pin_mode(self, pin, mode):
        MODES = {INPUT: 'i',
                 OUTPUT: 'o',
                 INPUT_PULLUP: 'p'}
        self.command(MODES[mode] + self._encode_pin(pin))

    def digital_read(self, pin):
        response = self.command('r' + self._encode_pin(pin), expected_len = 1)
        return HIGH if response[0] == 'h' else LOW

    def digital_write(self, pin, level):
        self.command(('h' if level == HIGH else 'l') +
                      self._encode_pin(pin))

