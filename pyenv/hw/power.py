from jointio import IOPoll
from events import Event
from array import array
import pysric

CMD_ENABLE_INPUT_NOTES = 5
CMD_PLAY_PIEZO = 6
CMD_SET_LEDS = 7
CMD_SET_MOTOR_RAIL = 8
CMD_GET_LEDS = 9

class Power:
    def __init__(self, dev):
        self.dev = dev
        self.led = Power.LedArray('I', [0, 0, 0], dev)

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

    class LedArray(array):
        def __new__(cls, typeclass, init_values, dev):
            return array.__new__(cls, typeclass, init_values)

        def __init__(self, typeclass, init_values, dev=None):
            # We receive a deprecation warning if the following is enabled
            # array.__init__(self, typeclass, init_values)
            self.dev = dev

        def __setitem__(self, idx, val):
            # Fetch current status of led
            tx = [ CMD_GET_LEDS ]
            rx = self.dev.txrx( tx )
            bit = rx[0] & (1 << idx)
            bit = bit >> idx

            # Normalise the value of val
            if val != 0:
                val = 1

            if (bit != val):
                flags = rx[0] & (~(1 << idx))
                flags |= (val << idx)
                tx = [ CMD_SET_LEDS, flags ]
                self.dev.txrx( tx )

        def __getitem__(self, idx):
            tx = [ CMD_GET_LEDS ]
            rx = self.dev.txrx( tx )
            if rx[0] & (1 << idx):
                return 1
            else:
                return 0


ps = pysric.PySric()
power = None

if pysric.SRIC_CLASS_POWER in ps.devices:
    power = Power( ps.devices[pysric.SRIC_CLASS_POWER][0] )

