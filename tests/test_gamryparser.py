import pandas as pd
import gamry_parser as parser
import unittest


class TestGamryParser(unittest.TestCase):
    def setUp(self):
        pass

    def test_is_loaded(self):
        gp = parser.GamryParser()
        # should raise exception if file not loaded
        self.assertRaises(AssertionError, gp.get_curve_count)
        self.assertRaises(AssertionError, gp.get_curve_data, 2)
        self.assertRaises(AssertionError, gp.get_curves)
        self.assertRaises(AssertionError, gp.get_experiment_type)

    def test_read_header(self):
        gp = parser.GamryParser(filename='tests/cv_data.dta')
        blob, count = gp.read_header()
        self.assertEqual(count, 809)
        self.assertEqual(gp.header, blob)
        self.assertEqual(gp.header['DATE'], '3/6/2019')
        self.assertEqual(gp.header['CHECKPSTAT'], 'potentiostat-id')
        self.assertEqual(gp.header['CHECKPOTEN'], 0.5)
        self.assertEqual(gp.header['CHECKQUANT'], 1.2345)
        self.assertEqual(gp.header['CHECKIQUANT'], 5)
        self.assertEqual(gp.header['CHECKSELECTOR'], 0)
        self.assertFalse(gp.header['CHECKTOGGLE'])
        self.assertTrue(isinstance(gp.header['CHECK2PARAM'], dict))
        self.assertTrue(gp.header['CHECK2PARAM']['enable'])
        self.assertEqual(gp.header['CHECK2PARAM']['start'], 300)
        self.assertEqual(gp.header['CHECK2PARAM']['finish'], 0.5)

    def test_load(self):
        # file not defined
        gp = parser.GamryParser()
        self.assertRaises(AssertionError, gp.load)
        self.assertEqual(gp.fname, None)

        # file defined, make sure data is loaded properly
        gp = parser.GamryParser()
        gp.load(filename='tests/cv_data.dta')
        self.assertEqual(gp.fname, 'tests/cv_data.dta')

        gp = parser.GamryParser(filename='tests/cv_data.dta')
        gp.load()
        self.assertEqual(gp.curve_count, 5)
        curve1 = gp.curves[0]
        self.assertEqual(curve1['T'][0], 0.1)
        self.assertEqual(curve1['T'][-1], 1.0)
        curve5 = gp.curves[-1]
        self.assertEqual(curve5.index[-1], '49')
        self.assertEqual(curve5['T'][-1], 601.1)
        self.assertEqual(curve5['Vf'][-1], 0.889001)
        self.assertEqual(curve5['Im'][-1], 2.622720e-07)
        self.assertEqual(curve5['Sig'][-1], 0.890)
        self.assertEqual(curve5['IERange'][-1], 5)

    def test_getters(self):
        gp = parser.GamryParser(filename='tests/cv_data.dta')
        gp.load()
        self.assertEqual(gp.get_curve_count(), 5)
        self.assertTrue(isinstance(gp.get_header(), dict))
        self.assertEqual(len(gp.get_header()), len(gp.header))
        self.assertEqual(gp.get_experiment_type(), gp.header['TAG'])
        self.assertTrue(isinstance(gp.get_curve_data(1), pd.DataFrame))
        curves = gp.get_curves()
        self.assertTrue(isinstance(curves, list))
        self.assertTrue(isinstance(curves[-1], pd.DataFrame))

    def test_indices_and_numbers(self):
        gp = parser.GamryParser(filename='tests/cv_data.dta')
        gp.load()
        indices = gp.get_curve_indices()
        self.assertEqual(indices, (0, 1, 2, 3, 4))
        numbers = gp.get_curve_numbers()
        self.assertEqual(numbers, (1, 2, 3, 4, 5))

    def test_ocvcurve_self(self):
        gp = parser.GamryParser(filename='tests/cv_data.dta')
        gp.load()
        self.assertFalse(gp.ocv_exists)
        self.assertEqual(gp.get_ocv_curve(), None)
        self.assertEqual(gp.get_ocv_value(), None)
        gp = parser.GamryParser(filename='tests/ocvcurve_data.dta')
        gp.load()
        self.assertTrue(gp.ocv_exists)
        self.assertEqual(gp.get_ocv_curve().iloc[0]['T'], 0.258333)
        self.assertEqual(gp.get_ocv_curve().iloc[-1]['T'], 10.3333)
        self.assertEqual(gp.get_ocv_curve().iloc[-1]['Vf'], 0.283437)
        self.assertEqual(gp.get_ocv_value(), 0.2834373)
