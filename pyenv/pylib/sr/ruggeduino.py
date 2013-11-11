import threading
import serial

SERIAL_BAUD = 115200

# Strings here so that they print nicely
INPUT = "INPUT"
OUTPUT = "OUTPUT"
INPUT_PULLUP = "INPUT_PULLUP"

class Ruggeduino(object):
    """Class for talking to a Ruggeduino flashed with the SR firmware"""

    def __init__(self, path, serialnum = None):
        self.serialnum = serialnum
        self.serial = serial.Serial(path, SERIAL_BAUD, timeout=0.1)

        # Lock that must be acquired for use of the serial device
        self.lock = threading.Lock()

        if not self._is_srduino():
            print "Warning: Ruggeduino is not running the SR firmware"


    def close(self):
        self.serial.close()

    def command(self, data):
        """Send a command to the Ruggeduino

        Returns the response from the device."""

        # The lock must have been acquired to talk to the device
        assert self.lock.locked()

        for i in range(10):
            self.serial.write(bytes(data))
            res = self.serial.readline()
            if len(res) > 0 and res[-1] == "\n":
                return res
        raise Exception("Communications with Ruggeduino failed")

    def _is_srduino(self):
        "Determine if the board is flashed with the SR firmware"
        with self.lock:
            response = self.command('v')
            if response.split(":")[0] == "SRduino":
                return True
            else:
                return False

    def _encode_pin(self, pin):
        "Encode a pin number in ascii"
        return chr(ord('a') + pin)

    def pin_mode(self, pin, mode):
        "Set the mode of a pin"
        MODES = {INPUT: 'i',
                 OUTPUT: 'o',
                 INPUT_PULLUP: 'p'}
        with self.lock:
            self.command(MODES[mode] + self._encode_pin(pin))

    def digital_read(self, pin):
        "Read a digital input"
        with self.lock:
            response = self.command('r' + self._encode_pin(pin))
            return True if response[0] == 'h' else False

    def digital_write(self, pin, level):
        "Write to an output"
        with self.lock:
            self.command(('h' if level else 'l') + self._encode_pin(pin))

    def analogue_read(self, pin):
        "Read an analogue input"
        with self.lock:
            response = self.command('a' + self._encode_pin(pin))
        return (int(response)/1023.0)*5.0

    def __repr__(self):
        return "Ruggeduino( serialnum = \"{0}\" )".format( self.serialnum )
