import pandas as pd
import gamry_parser as parser
import unittest


class TestChronoAmperometry(unittest.TestCase):
    def setUp(self):
        pass

    def test_getters(self):
        gp = parser.ChronoAmperometry(filename="tests/chronoa_data.dta")
        self.assertIsNone(gp.sample_time)
        self.assertEqual(gp.sample_count, 0)

        gp.load()
        curve = gp.curve()
        self.assertTrue((curve.columns == ["T", "Vf", "Im"]).all())

        self.assertEqual(gp.sample_time, 30)
        self.assertEqual(gp.sample_count, 10)
