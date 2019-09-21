import pandas as pd
import gamry_parser as parser
import unittest


class TestChronoAmperometry(unittest.TestCase):
    def setUp(self):
        pass

    def test_use_datetime(self):
        gp = parser.ChronoAmperometry(filename='tests/chronoa_data.dta', to_timestamp=False)
        gp.load()
        curve = gp.get_curve_data()
        # 'T' should return elapsed time in seconds
        self.assertEqual(curve['T'][0], 0)
        self.assertEqual(curve['T'].iloc[-1], 270)

        gp = parser.ChronoAmperometry(filename='tests/chronoa_data.dta', to_timestamp=True)
        gp.load()
        curve = gp.get_curve_data()
        # 'T' should return datetime objects
        self.assertEqual(curve['T'][0], pd.to_datetime('3/10/2019 12:00:00'))
        self.assertEqual(curve['T'].iloc[-1], pd.to_datetime('3/10/2019 12:04:30'))

    def test_getters(self):
        gp = parser.ChronoAmperometry(filename='tests/chronoa_data.dta')
        self.assertRaises(AssertionError, gp.get_sample_time)
        self.assertRaises(AssertionError, gp.get_sample_count)

        gp.load()
        curve = gp.get_curve_data()
        self.assertTrue((curve.columns == ['T', 'Vf', 'Im']).all())

        self.assertEqual(gp.get_sample_time(), 30)
        self.assertEqual(gp.get_sample_count(), 10)
