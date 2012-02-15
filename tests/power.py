import unittest
import sr
from sr.tssric import LockableDev

class PowerTest(unittest.TestCase):
    "Tests of the power board API"

    def setUp(self):
        self.R = sr.Robot( wait_start = False, quiet = True )
        self.power = self.R.power

    def test_led_set(self):
        "Check we can set an LED"
        self.power.led[0] = 1
        self.assertTrue( self.power.led[0] == 1 )

        self.power.led[0] = 0
        self.assertTrue( self.power.led[0] == 0 )

    def test_led_len(self):
        "Check we have the right number of LEDs"
        self.assertTrue( len(self.power.led) == 3 )

    def test_beep(self):
        "Check we can beep"
        self.power.beep( 1000, 0.1 )

    def test_beep_multi(self):
        "Check we can enqueue more than one beep"
        self.power.beep( [ (1000, 0.1), (1500, 0.2) ] )

    def test_lockabledev(self):
        "Check we are using a lockable device for the power board"
        self.assertTrue( isinstance( self.power.dev, LockableDev ) )

    def test_lock_use(self):
        "Check that the device must get locked before use"

        self.assertRaises( AssertionError,
                           self.power.led._get_leds_nolock )

    def test_battery_voltage(self):
        "Check that battery voltage reading works"
        v = self.power.battery.voltage

        self.assertTrue( isinstance( v, float ) )

        # The voltage can't be negative
        self.assertTrue( v >= 0 )

        # Make sure it's reasonably under max
        # (this is not the true maximum)
        self.assertTrue( v <= 20 )

    def test_battery_current(self):
        "Check that battery current reading works"
        i = self.power.battery.current

        self.assertTrue( isinstance( i, float ) )
