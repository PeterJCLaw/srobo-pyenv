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
            "Output munching doesn't happen when on a terminal"

            # Because of the interesting route that we got into this
            # execution environment, things like isinstance() won't work.
            # So, use string comparison instead!
            self.assertTrue( sys.stdout.__class__.__name__ == "AddCRFlusher" )

    def test_assert_works(self):
        """Check that assert works

        The execfile situation can put us in debug mode.
        This makes assert statements not work."""
        def failfunc():
            assert False

        self.assertRaises( AssertionError, failfunc )
