import os
import pandas as pd
import gamry_parser as parser
import unittest


FIXTURE_PATH = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    "test_data",
)


class TestChronoAmperometry(unittest.TestCase):
    def setUp(self):
        pass

    def test_getters(self):
        gp = parser.ChronoAmperometry(
            filename=os.path.join(FIXTURE_PATH, "chronoa_data.dta")
        )
        self.assertIsNone(gp.sample_time)
        self.assertEqual(gp.sample_count, 0)

        gp.load()
        curve = gp.curve()
        self.assertTrue((curve.columns == ["T", "Vf", "Im"]).all())

        self.assertEqual(gp.sample_time, 30)
        self.assertEqual(gp.sample_count, 10)
