import gamry_parser as parser
import unittest


class TestImpedance(unittest.TestCase):
    def setUp(self):
        pass

    def test_is_loaded(self):
        gp = parser.Impedance(filename="tests/eispot_data.dta")
        gp.load()
        self.assertEqual(len(gp.curves), 1)

        curve = gp.get_curve_data()
        self.assertTrue(isinstance(curve["Freq"].iloc[-1], float))

    def test_getters(self):
        gp = parser.Impedance(filename="tests/eispot_data.dta")
        gp.load()
        curve = gp.get_curve_data()
        self.assertEqual(len(curve), 10)
        self.assertTrue(
            (curve.columns == ["Freq", "Zreal", "Zimag", "Zmod", "Zphz"]).all()
        )
