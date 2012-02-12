import unittest
from unittest import TestLoader, TestSuite
import jio, power

jointio_tests = TestLoader().loadTestsFromTestCase(jio.JointIOTest)
power_tests = TestLoader().loadTestsFromTestCase(power.PowerTest)

suite = TestSuite( [ jointio_tests,
                     power_tests ] )

unittest.TextTestRunner(verbosity=2).run(suite)
