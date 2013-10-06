import serial

SERIAL_BAUD = 115200

# Strings here so that they print nicely
INPUT = "INPUT"
OUTPUT = "OUTPUT"
INPUT_PULLUP = "INPUT_PULLUP"

class Ruggeduino(object):
    def __init__(self, path):
        self.serial = serial.Serial(path, SERIAL_BAUD, timeout=0.1)
        if not self._is_srduino():
            print "Warning: Ruggeduino is not running the SR firmware"

    def close(self):
        self.serial.close()

    def command(self, data):
        for i in range(10):
            self.serial.write(bytes(data))
            res = self.serial.readline()
            if len(res) > 0 and res[-1] == "\n":
                return res
        raise Exception("Communications with Ruggeduino failed")

    def _is_srduino(self):
        response = self.command('v')
        if response.split(":")[0] == "SRduino":
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
        response = self.command('r' + self._encode_pin(pin))
        return True if response[0] == 'h' else False

    def digital_write(self, pin, level):
        self.command(('h' if level else 'l') + self._encode_pin(pin))

    def analogue_read(self, pin):
        response = self.command('a' + self._encode_pin(pin))
        return (int(response)/1023.0)*5.0
