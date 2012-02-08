CMD_ENABLE_INPUT_NOTES = 5
CMD_PLAY_PIEZO = 6
CMD_SET_LEDS = 7
CMD_SET_MOTOR_RAIL = 8
CMD_GET_LEDS = 9
CMD_GET_VI = 10

class LedList(object):
    def __init__(self, dev=None):
        self.dev = dev

    def __len__(self):
        return 3

    def __setitem__(self, idx, val):
        if idx > 2 or idx < 0:
            raise IndexError("The powerboard only has 3 LEDs")

        # Fetch current status of led
        r = self._get_leds()
        bit = bool( r & (1 << idx) )

        # Normalise val
        val = bool(val)

        if (bit != val):
            flags = r & (~(1 << idx))
            if val:
                flags |= (1 << idx)
            tx = [ CMD_SET_LEDS, flags ]
            self.dev.txrx( tx )

    def __getitem__(self, idx):
        if idx > 2 or idx < 0:
            raise IndexError("The powerboard only has 3 LEDs")

        r = self._get_leds()
        return bool( r & (1 << idx) )

    def _get_leds(self):
        """Read the state of all the LEDs.
        Return the values in a bitmask."""
        tx = [ CMD_GET_LEDS ]
        rx = self.dev.txrx( tx )
        return rx[0]

class Battery(object):
    def __init__(self, dev=None):
        self.dev = dev

    @property
    def voltage(self):
        return round(self._get_vi()[0], 2)

    @property
    def current(self):
        return round(self._get_vi()[1], 2)

    def _get_vi(self):
        """Read the battery voltage and current from the power board.
	Return the values in a tuple."""
        r = self.dev.txrx( [ CMD_GET_VI ] )

	# Use scaling values stated in monitor.h of power-fw.git
        v = (r[0] | (r[1] << 8)) * 0.0036621
        i = (r[2] | (r[3] << 8)) * 0.012201
        return v, i

class Power:
    def __init__(self, dev):
        self.dev = dev
        self.led = LedList(dev)
        self.battery = Battery(dev)

    def beep( self, freq = 1000, dur = 0.1 ):
        "Beep"

        if hasattr( freq, "__iter__" ):
            beeps = freq
        else:
            "It's just a single note"
            beeps = [(freq, dur)]

        if len(beeps) > 10:
            # TODO: Do something better here
            raise "Too many beeps added"

        tx = [ CMD_PLAY_PIEZO, len(beeps) ]
        for f,d  in beeps:
            d = int(1000 * d)

            # Frequency
            tx.append( (f >> 8) & 0xff )
            tx.append( f & 0xff )
            # Duration
            tx.append( (d >> 8) & 0xff )
            tx.append( d & 0xff )

            # Volume (fixed right now)
            tx.append( 5 )

        self.dev.txrx( tx )

