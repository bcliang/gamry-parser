import pandas as pd
import gamry_parser as parser
import unittest


class TestChronoAmperometry(unittest.TestCase):
    def setUp(self):
        pass

    def test_getters(self):
        gp = parser.ChronoAmperometry(filename="tests/chronoa_data.dta")
        self.assertRaises(AssertionError, gp.get_sample_time)
        self.assertRaises(AssertionError, gp.get_sample_count)

        gp.load()
        curve = gp.get_curve_data()
        self.assertTrue((curve.columns == ["T", "Vf", "Im"]).all())

        self.assertEqual(gp.get_sample_time(), 30)
        self.assertEqual(gp.get_sample_count(), 10)
