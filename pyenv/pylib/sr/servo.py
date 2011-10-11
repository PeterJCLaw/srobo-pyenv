"Interface to servo boards"

# Motor controller SRIC commands
CMD_SERVO_SET = 0
CMD_SERVO_GET = 1
CMD_SERVO_SMPS = 7

# The number of servos
SERVO_COUNT = 8
# The maximum angle that the servo board will accept
SERVO_ANGLE = 400
# The maximum angle in the API
SERVO_API_ANGLE = 100.0

class Servo(object):
    "A collection of 8 servos"
    def __init__(self, dev=None):
        self.dev = dev
        self._set_smps(True)

    def __len__(self):
        return SERVO_COUNT

    def __setitem__(self, idx, val):
        if idx > SERVO_COUNT-1 or idx < 0:
            raise IndexError("There are only 8 servo outputs on a servo board")

        if val > SERVO_API_ANGLE:
            val = SERVO_API_ANGLE
        if val < 0:
            val = 0

        self._set_angle(idx, val)

    def __getitem__(self, idx):
        if idx > SERVO_COUNT-1 or idx < 0:
            raise IndexError("there are only 8 servo outputs on a servo board")

        return self._get_angle(idx)

    def _set_angle(self, idx, val):
        """Set the angle of a given servo"""
        tmp = int(val * (SERVO_ANGLE/SERVO_API_ANGLE))
        tx = [CMD_SERVO_SET, idx, tmp & 0xff, (tmp >> 8) & 0xff]
        self.dev.txrx(tx)

    def _get_angle(self, idx):
        """Get the currently set angle for a given servo"""
        tx = [CMD_SERVO_GET, idx]
        rx = self.dev.txrx(tx)
        tmp = (0xff & rx[0]) | ((0xff & rx[1]) << 8)
        return tmp / (SERVO_ANGLE/SERVO_API_ANGLE)

    def _set_smps(self, en):
        """Enable/disable the SMPS on the servo board"""
        tx = [CMD_SERVO_SMPS, bool(en)]
        self.dev.txrx(tx)
