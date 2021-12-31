import gamry_parser as parser
from pandas import Timestamp
import unittest


class TestCyclicVoltammetry(unittest.TestCase):
    def setUp(self):
        pass

    def test_is_loaded(self):
        gp = parser.SquareWaveVoltammetry()

        # should raise exception if no file specified
        self.assertRaises(AssertionError, gp.load)

        # should raise exception if non-swv data is specified
        self.assertRaises(
            AssertionError, gp.load, filename="test/test_chronoamperometry.dta"
        )

        # should retain nulled values if data is not loaded
        self.assertTupleEqual(gp.v_range, (0, 0))
        self.assertIsNone(gp.step_size)
        self.assertIsNone(gp.frequency)
        self.assertIsNone(gp.pulse_size)
        self.assertIsNone(gp.pulse_width)
        self.assertEqual(gp.cycles, 0)

    def test_getters(self):
        gp = parser.SquareWaveVoltammetry(filename="tests/squarewave_data.dta")
        gp.load()

        self.assertTupleEqual(gp.v_range, (0, -0.5))
        self.assertEqual(gp.step_size, 2)
        self.assertEqual(gp.frequency, 100)
        self.assertEqual(gp.pulse_size, 25)
        self.assertEqual(gp.pulse_width, 0.01)
        self.assertEqual(gp.cycles, 251)
        self.assertEqual(gp.get_curve_count(), 1)

        curve = gp.get_curve_data()
        self.assertTrue(
            (
                curve.columns == ["T", "Vfwd", "Vrev", "Vstep", "Ifwd", "Irev", "Idif"]
            ).all()
        )
        self.assertEqual(curve.shape, (10, 7))
        self.assertEqual(curve["T"].iloc[0], 0.01)

        gp.load(to_timestamp=True)
        curve = gp.get_curve_data()
        self.assertTrue(
            (
                curve.columns == ["T", "Vfwd", "Vrev", "Vstep", "Ifwd", "Irev", "Idif"]
            ).all()
        )
        self.assertEqual(curve.shape, (10, 7))
        self.assertEqual(curve["T"].iloc[0], Timestamp("2021/12/31 12:00:00.01"))
