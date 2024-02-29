import os
import numpy as np
import pandas as pd
import gamry_parser as parser
import unittest
import locale


FIXTURE_PATH = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    "test_data",
)


class TestGamryParser(unittest.TestCase):
    def setUp(self):
        pass

    def test_is_loaded(self):
        gp = parser.GamryParser()
        # should raise exception if file not loaded
        self.assertEqual(gp.curve_count, 0)
        self.assertRaises(AssertionError, gp.curve, 2)
        self.assertListEqual(gp.curves, [])
        self.assertIsNone(gp.experiment_type)

    def test_read_header(self):
        gp = parser.GamryParser(filename=os.path.join(FIXTURE_PATH, "cv_data.dta"))
        blob, count = gp.read_header()
        self.assertEqual(count, 789)
        self.assertEqual(gp.header, blob)
        self.assertEqual(gp.header["DATE"], "3/6/2019")
        self.assertEqual(gp.header["CHECKPSTAT"], "potentiostat-id")
        self.assertEqual(gp.header["CHECKPOTEN"], 0.5)
        self.assertEqual(gp.header["CHECKQUANT"], 1.2345)
        self.assertEqual(gp.header["CHECKIQUANT"], 5)
        self.assertEqual(gp.header["CHECKSELECTOR"], 0)
        self.assertFalse(gp.header["CHECKTOGGLE"])
        self.assertTrue(isinstance(gp.header["CHECK2PARAM"], dict))
        self.assertTrue(gp.header["CHECK2PARAM"].get("enable", False))
        self.assertEqual(gp.header["CHECK2PARAM"].get("start"), 300)
        self.assertEqual(gp.header["CHECK2PARAM"].get("finish"), 0.5)

        gp = parser.GamryParser(filename=os.path.join(FIXTURE_PATH, "cv_data_incompleteheader.dta"))
        _, count = gp.read_header()
        self.assertEqual(gp.header["DELAY"], dict(enable=False, start=300, finish=0.1))

    def test_load(self):
        locale.setlocale(locale.LC_ALL, "")
        # file not defined
        gp = parser.GamryParser()
        self.assertRaises(AssertionError, gp.load)
        self.assertEqual(gp.fname, None)

        # file defined, make sure data is loaded properly
        gp = parser.GamryParser()
        gp.load(filename=os.path.join(FIXTURE_PATH, "cv_data.dta"))
        self.assertEqual(gp.fname, os.path.join(FIXTURE_PATH, "cv_data.dta"))

        gp = parser.GamryParser(filename=os.path.join(FIXTURE_PATH, "cv_data.dta"))
        gp.load()
        self.assertEqual(gp.curve_count, 5)
        curve1 = gp._curves[0]
        self.assertEqual(curve1["T"].iloc[0], 0.1)
        self.assertEqual(curve1["T"].iloc[-1], 1.0)
        self.assertEqual(curve1["Vf"].iloc[-1], 0.5)
        self.assertEqual(curve1.index.dtype, np.int64)

        curve5 = gp._curves[-1]
        self.assertEqual(curve5.index[-1], 49)
        self.assertEqual(curve5["T"].iloc[-1], 601.1)
        self.assertEqual(curve5["Vf"].iloc[-1], 0.889001)
        self.assertEqual(curve5["Im"].iloc[-1], 2.622720e-07)
        self.assertEqual(curve5["Sig"].iloc[-1], 0.890)
        self.assertEqual(curve5["IERange"].iloc[-1], 5)

    def test_use_datetime(self):
        gp = parser.GamryParser(filename=os.path.join(FIXTURE_PATH, "chronoa_data.dta"), to_timestamp=False)
        gp.load()
        curve = gp.curve()
        # 'T' should return elapsed time in seconds
        self.assertEqual(curve["T"][0], 0)
        self.assertEqual(curve["T"].iloc[-1], 270)

        gp = parser.GamryParser(filename=os.path.join(FIXTURE_PATH, "chronoa_data.dta"), to_timestamp=True)
        gp.load()
        curve = gp.curve()
        # 'T' should return datetime objects
        self.assertEqual(curve["T"][0], pd.to_datetime("3/10/2019 12:00:00"))
        self.assertEqual(curve["T"].iloc[-1], pd.to_datetime("3/10/2019 12:04:30"))

    def test_aborted_experiment(self):
        gp = parser.GamryParser(filename=os.path.join(FIXTURE_PATH, "eispot_data_curveaborted.dta"))
        gp.load()
        self.assertEqual(gp.curve_count, 1)
        self.assertEqual(gp._curves[0].shape, (5, 10))

    def test_getters(self):
        locale.setlocale(locale.LC_ALL, "")
        gp = parser.GamryParser(filename=os.path.join(FIXTURE_PATH, "cv_data.dta"))
        gp.load()
        self.assertEqual(gp.curve_count, 5)
        self.assertTrue(isinstance(gp.header, dict))
        self.assertEqual(gp.experiment_type, gp.header["TAG"])
        self.assertTrue(isinstance(gp.curve(1), pd.DataFrame))
        curves = gp._curves
        self.assertTrue(isinstance(curves, list))
        self.assertTrue(isinstance(curves[-1], pd.DataFrame))

    def test_indices_and_numbers(self):
        locale.setlocale(locale.LC_ALL, "")
        gp = parser.GamryParser(filename=os.path.join(FIXTURE_PATH, "cv_data.dta"))
        gp.load()
        self.assertEqual(gp.curve_indices, (0, 1, 2, 3, 4))
        self.assertEqual(gp.curve_numbers, (1, 2, 3, 4, 5))

    def test_ocvcurve_self(self):
        locale.setlocale(locale.LC_ALL, "")
        gp = parser.GamryParser(filename=os.path.join(FIXTURE_PATH, "cv_data.dta"))
        gp.load()
        self.assertEqual(gp.ocv_curve, None)
        self.assertEqual(gp.ocv, None)
        gp = parser.GamryParser(filename=os.path.join(FIXTURE_PATH, "ocvcurve_data.dta"))
        gp.load()
        self.assertEqual(gp.ocv_curve.iloc[0]["T"], 0.258333)
        self.assertEqual(gp.ocv_curve.iloc[-1]["T"], 10.3333)
        self.assertEqual(gp.ocv_curve.iloc[-1]["Vf"], 0.283437)
        self.assertEqual(gp.ocv, 0.2834373)

    def test_locale(self):
        # confirm that files will load properly with non-US locales
        locale.setlocale(locale.LC_ALL, "de_DE.utf8")

        gp = parser.GamryParser(filename=os.path.join(FIXTURE_PATH, "chronoa_de_data.dta"))
        gp.load()
        curve = gp.curve()
        self.assertEqual(curve["T"].iloc[-1], 270)
        self.assertEqual(curve["Vf"].iloc[0], -5e-004)
        self.assertEqual(curve["Vf"].iloc[-1], 4e-001)
        self.assertEqual(curve["Im"].iloc[0], -2e-008)
        self.assertEqual(curve["Im"].iloc[-1], 3e-009)

        # confirm that files can load with mismatched locales..
        # pandas.read_csv() will handle 1,234,567.890 notation even in the wrong locale.
        gp = parser.GamryParser(filename=os.path.join(FIXTURE_PATH, "chronoa_data.dta"))
        gp.load()
        curve = gp.curve()
        self.assertEqual(curve["T"].iloc[-1], 270)
        self.assertEqual(curve["Vf"].iloc[0], -5.4e-004)
        self.assertEqual(curve["Vf"].iloc[-1], 4e-001)
        self.assertEqual(curve["Im"].iloc[-1], 3e-009)

        # pandas.read_csv() assumes 1,234,567.890 notation by default.
        # If parsed with the wrong locale, we should expect data corruption
        # in the resulting dataframe.
        locale.setlocale(locale.LC_ALL, "en_US.utf8")
        gp = parser.GamryParser(filename=os.path.join(FIXTURE_PATH, "chronoa_de_data.dta"))
        gp.load()
        curve = gp.curve()
        self.assertEqual(curve["Vf"].iloc[0], -50)
        self.assertEqual(curve["Vf"].iloc[-1], 40000)
        self.assertEqual(curve["Im"].iloc[0], -0.002)
