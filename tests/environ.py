import sr
import unittest
import sys
import sr.loggrok

class EnvironTest(unittest.TestCase):
    "Tests of the execution environment in general"

    def test_stdout_munger(self):
        "Check that stdout newlines will be munged"
        # Note that this test has to behave differently 
        # when stdout is a tty, as the munging isn't done on that

        if not sys.stdout.isatty():
            self.assertTrue( isinstance( sys.stdout,
                                         sr.loggrok.AddCRFlusher ) )

    def test_assert_works(self):
        """Check that assert works

        The execfile situation can put us in debug mode.
        This makes assert statements not work."""
        def failfunc():
            assert False

        self.assertRaises( AssertionError, failfunc )
