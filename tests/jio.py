import unittest
import sr
from sr.tssric import LockableDev

class JointIOTest(unittest.TestCase):
    "Tests of the JointIO API"

    def setUp(self):
        self.R = sr.Robot( wait_start = False, quiet = True )
        self.io = self.R.io[0]

    def tearDown(self):
        del self.R

    def test_input_num(self):
        "Check input list is the correct length"
        self.assertTrue( len( self.io.input ) == 8 )

    def test_output_num(self):
        "Check output list is the correct length"
        self.assertTrue( len( self.io.output ) == 8 )

    def test_output_set(self):
        "Check we can set the value of an output"
        o = self.io.output[0]

        o.d = 1
        self.assertTrue( o.d == 1 )

        o.d = 0
        self.assertTrue( o.d == 0 )

    def test_dinput_read(self):
        "Check we can read a digital input"
        i = self.io.input[0]
        v = i.d
        self.assertTrue( v in (0,1) )

    def test_ainput_read(self):
        "Check we can read an analogue input"
        i = self.io.input[0]
        v = i.a
        self.assertTrue( isinstance( v, float ) )
        self.assertTrue( v >= 0 )
        self.assertTrue( v <= 3.3 )

    def test_lockabledev(self):
        "Check we are using a lockable device for the jointio board"
        self.assertTrue( isinstance( self.io.dev, LockableDev ) )
