import gamry_parser as parser
import unittest


class TestCyclicVoltammetry(unittest.TestCase):
    def setUp(self):
        pass

    def test_is_loaded(self):
        gp = parser.CyclicVoltammetry()
        # should raise exception if file not loaded
        self.assertRaises(AssertionError, gp.get_curve_count)
        self.assertRaises(AssertionError, gp.get_curve_data, 2)
        self.assertRaises(AssertionError, gp.get_curves)
        self.assertRaises(AssertionError, gp.get_scan_rate)
        self.assertRaises(AssertionError, gp.get_experiment_type)

    def test_getters(self):
        gp = parser.CyclicVoltammetry(filename="tests/cv_data.dta")
        gp.load()
        vrange = gp.get_v_range()
        self.assertEqual(vrange[0], 0.1)
        self.assertEqual(vrange[1], 0.9)

        scanrate = gp.get_scan_rate()
        self.assertEqual(scanrate, 1.23456)
        curve = gp.get_curve_data(1)
        self.assertTrue((curve.columns == ["Vf", "Im"]).all())
