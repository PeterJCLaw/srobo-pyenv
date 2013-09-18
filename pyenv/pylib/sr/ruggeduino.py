import serial
import time

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
        self.path = path
        self.socket = None
        self.baud = 9600

    def open(self):
        self.socket = serial.Serial(self.path, self.baud)
        # Unfortunately, pin waggling occurs which means the
        # Ruggeduino is reset when we open the connection. Right now
        # the simplest work-around is to delay briefly.
        time.sleep(0.8)

    def close(self):
        self.socket.close()
        self.socket = None

    def _open_on_demand(self):
        if self.socket is None:
            self.open()

    def command(self, data, response = 0):
        self._open_on_demand()
        time.sleep(0.005) # Don't spam the Ruggeduino too much
        self.socket.write(bytes(data))
        self.socket.flush()
        return self.socket.read(response)

    def _encode_pin(self, pin):
        return chr(ord('a') + pin)

    def pin_mode(self, pin, mode):
        MODES = {INPUT: 'i',
                 OUTPUT: 'o',
                 INPUT_PULLUP: 'p'}
        self.command(MODES[mode] + self._encode_pin(pin))

    def digital_read(self, pin):
        response = self.command('r' + self._encode_pin(pin), response = 1)
        return HIGH if response[0] == 'h' else LOW

    def digital_write(self, pin, level):
        self.command(('h' if level == HIGH else 'l') +
                      self._encode_pin(pin))

