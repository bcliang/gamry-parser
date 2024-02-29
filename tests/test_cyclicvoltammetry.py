import os
import gamry_parser as parser
import unittest

FIXTURE_PATH = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    "test_data",
)


class TestCyclicVoltammetry(unittest.TestCase):
    def setUp(self):
        pass

    def test_is_loaded(self):
        gp = parser.CyclicVoltammetry()
        # should raise exception if file not loaded
        self.assertEqual(gp.curve_count, 0)
        self.assertRaises(AssertionError, gp.curve, 2)
        self.assertListEqual(gp.curves, [])
        self.assertIsNone(gp.scan_rate)
        self.assertIsNone(gp.experiment_type)

    def test_getters(self):
        gp = parser.CyclicVoltammetry(
            filename=os.path.join(FIXTURE_PATH, "cv_data.dta")
        )
        gp.load()
        vrange = gp.v_range
        self.assertEqual(vrange[0], 0.1)
        self.assertEqual(vrange[1], 0.9)

        self.assertEqual(gp.scan_rate, 1.23456)
        curve = gp.curve(curve=1)
        self.assertTrue((curve.columns == ["Vf", "Im"]).all())
