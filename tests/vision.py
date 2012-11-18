import unittest
import sr, sr.vision

class VisionTest(unittest.TestCase):
    "Tests of the vision API"

    def setUp(self):
        self.R = sr.Robot( wait_start = False, quiet = True )

    def tearDown(self):
        del self.R

    def test_vision(self):
        "Check that we can see"
        markers = self.R.see()

        self.assertTrue( isinstance( markers, list ) )

    def test_res(self):
        "Check that we can set the resolution"
        for res in self.R.vision.camera_focal_length.keys():
            markers = self.R.see( res = res )

            self.assertTrue( isinstance( markers, list ) )

