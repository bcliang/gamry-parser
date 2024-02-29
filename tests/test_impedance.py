import os
import gamry_parser as parser
import unittest

FIXTURE_PATH = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    "test_data",
)

class TestImpedance(unittest.TestCase):
    def setUp(self):
        pass

    def test_is_loaded(self):
        gp = parser.Impedance(filename=os.path.join(FIXTURE_PATH, "eispot_data.dta"))
        gp.load()
        self.assertEqual(len(gp.curves), 1)

        curve = gp.curve()
        self.assertTrue(isinstance(curve["Freq"].iloc[-1], float))

    def test_getters(self):
        gp = parser.Impedance(filename=os.path.join(FIXTURE_PATH, "eispot_data.dta"))
        gp.load()
        curve = gp.curve()
        self.assertEqual(len(curve), 10)
        self.assertTrue(
            (curve.columns == ["Freq", "Zreal", "Zimag", "Zmod", "Zphz"]).all()
        )
