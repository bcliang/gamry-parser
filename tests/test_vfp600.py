import gamry_parser as parser
import unittest


class TestVFP600(unittest.TestCase):
    def setUp(self):
        pass

    def test_load(self):
        gp = parser.VFP600()
        self.assertFalse(gp.loaded)

        gp.load("tests/vfp600_data.dta")
        self.assertEqual(gp.fname, "tests/vfp600_data.dta")
        self.assertTrue("VFP600" in gp.get_header()["TAG"])
        # data file acq frequency = 15hz
        self.assertEqual(gp.get_sample_time(), 1 / 15)
        self.assertEqual(gp.get_curve_count(), 1)
        self.assertEqual(gp.get_sample_count(), 20)
        self.assertTrue(gp.loaded)

    def test_getters(self):
        gp = parser.VFP600()
        gp.load("tests/vfp600_data.dta")

        curve = gp.get_curve_data()
        self.assertTrue((curve.columns == ["T", "Voltage", "Current"]).all())

        self.assertEqual(curve["T"][0], 0)
        self.assertEqual(round(curve["T"].iloc[-1] * 100), 127)
        self.assertEqual(curve["Voltage"].iloc[-1], 0.033333)
        self.assertEqual(round(curve["Current"].iloc[-1] * 1e13), 5125)
