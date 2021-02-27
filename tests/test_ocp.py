import pandas as pd
import gamry_parser as parser
import unittest
from pandas.testing import assert_frame_equal


class TestOpenCircuit(unittest.TestCase):
    def setUp(self):
        pass

    def test_use_datetime(self):
        gp = parser.OpenCircuitPotential(
            filename="tests/ocp_data.dta", to_timestamp=False
        )
        gp.load()
        curve = gp.get_curve_data()
        # 'T' should return elapsed time in seconds
        self.assertEqual(curve["T"][0], 5.00833)
        self.assertEqual(curve["T"].iloc[-1], 105.175)

        gp = parser.OpenCircuitPotential(
            filename="tests/ocp_data.dta", to_timestamp=True
        )
        gp.load()
        curve = gp.get_curve_data()
        # 'T' should return datetime objects
        self.assertEqual(curve["T"][0], pd.to_datetime("2020-02-10 17:18:05.008330"))
        self.assertEqual(
            curve["T"].iloc[-1], pd.to_datetime("2020-02-10 17:19:45.175000")
        )

    def test_is_loaded(self):
        gp = parser.OpenCircuitPotential(
            filename="tests/ocp_data.dta", to_timestamp=False
        )
        gp.load()
        self.assertEqual(len(gp.curves), 1)

        curve = gp.get_curve_data()
        for key in curve.keys():
            self.assertTrue(key in ["T", "Vf"])
        self.assertEqual(curve.shape, (21, 2))
        self.assertEqual(curve["Vf"][0], 0.0205436)
        self.assertEqual(curve["Vf"].iloc[-1], 0.0345678)

        # no filename at init, only provided at load
        gp = parser.OpenCircuitPotential()
        gp.load(filename="tests/ocp_data.dta")
        self.assertEqual(len(gp.curves), 1)

        curve = gp.get_curve_data()
        for key in curve.keys():
            self.assertTrue(key in ["T", "Vf"])
        self.assertEqual(curve.shape, (21, 2))
        self.assertEqual(curve["Vf"][0], 0.0205436)
        self.assertEqual(curve["Vf"].iloc[-1], 0.0345678)

    def test_getters(self):
        gp = parser.OpenCircuitPotential(
            filename="tests/ocp_data.dta", to_timestamp=False
        )
        self.assertIsNone(gp.get_ocv_curve())
        gp.load()
        curve = gp.get_curve_data()
        self.assertEqual(gp.get_curve_count(), 1)
        self.assertEqual(len(curve), 21)
        self.assertTrue((curve.columns == ["T", "Vf"]).all())

        # pandas equivalence check
        assert_frame_equal(gp.get_ocv_curve(), gp.curves[0])
