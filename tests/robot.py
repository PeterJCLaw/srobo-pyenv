import unittest
from unittest import TestLoader, TestSuite
import jio, power, environ, vision
import sr

FORCE_ALL_DEVS = False

jointio_tests = TestLoader().loadTestsFromTestCase(jio.JointIOTest)
power_tests = TestLoader().loadTestsFromTestCase(power.PowerTest)
environ_tests = TestLoader().loadTestsFromTestCase(environ.EnvironTest)
vision_tests = TestLoader().loadTestsFromTestCase(vision.VisionTest)

R = sr.Robot()

suite = TestSuite( [ environ_tests,
                     power_tests,
                     vision_tests ] )

if len( R.io ) or FORCE_ALL_DEVS:
    suite.addTests( [ jointio_tests ] )

# We don't actually want this robot...
del R

unittest.TextTestRunner(verbosity=2).run(suite)
