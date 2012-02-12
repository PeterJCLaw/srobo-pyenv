import unittest
import sr

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


