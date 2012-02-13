import unittest
from unittest import TestLoader, TestSuite
import jio, power, environ

jointio_tests = TestLoader().loadTestsFromTestCase(jio.JointIOTest)
power_tests = TestLoader().loadTestsFromTestCase(power.PowerTest)
environ_tests = TestLoader().loadTestsFromTestCase(environ.EnvironTest)

suite = TestSuite( [ jointio_tests,
                     power_tests,
                     environ_tests ] )

unittest.TextTestRunner(verbosity=2).run(suite)
