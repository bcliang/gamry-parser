import pandas as pd
from pandas.api.types import is_numeric_dtype
import datetime
import re
import os
import locale
from io import StringIO


class GamryParser:
    """Load experiment data generated in Gamry EXPLAIN format."""

    def __init__(self, filename=None):
        self.fname = filename
        self.header = dict()
        self.header_length = 0
        self.loaded = False
        self.curves = []
        self.curve_count = 0
        self.curve_units = dict()
        self.ocv = None
        self.ocv_exists = False
        self.REQUIRED_UNITS = {
            'CV': {
                'Vf': 'V vs. Ref.',
                'Im': 'A'
            }, }

    def load(self, filename=None):
        """save experiment information to \"header\", then save curve data to \"curves\"

        Args:
            filename (str, optional): file containing EXPLAIN-formatted data. defaults to None.
        Returns:
            None

        """

        if filename is not None:
            # reset
            self.__init__(filename)

        self.loaded = False
        assert self.fname is not None, "GamryParser needs to know what file to parse."
        assert os.path.exists(self.fname), "The file \'{}\' was not found.".format(self.fname)

        self.read_header()
        self.read_curves()
        self.loaded = True

    def get_curve_count(self):
        """return the number of loaded curves"""
        assert self.loaded, 'DTA file not loaded. Run GamryParser.load()'
        return self.curve_count

    def get_curve_indices(self):
        """return indices of curves (zero-based indexing)"""
        assert self.loaded, 'DTA file not loaded. Run GamryParser.load()'
        return tuple(range(self.curve_count))

    def get_curve_numbers(self):
        """return Gamry curve numbers (one-based indexing, as in Gamry software)"""
        assert self.loaded, 'DTA file not loaded. Run GamryParser.load()'
        return tuple(range(1, self.curve_count + 1))

    def get_curve_data(self, curve=0):
        """retrieve relevant experimental data

        Args:
            curve (int, optional): curve number to return. Defaults to 0.

        Returns:
            pandas.DataFrame: (multiple columns)

        """
        assert self.loaded, 'DTA file not loaded. Run GamryParser.load()'
        assert curve < self.curve_count, 'Invalid curve ({}). File contains {} total curves.'.format(curve, self.curve_count)
        return self.curves[curve]

    def get_curves(self):
        """return all loaded curves as a list of pandas DataFrames"""
        assert self.loaded, 'DTA file not loaded. Run GamryParser.load()'
        return self.curves

    def get_header(self):
        """return the experiment configuration dictionary"""
        assert self.loaded, 'DTA file not loaded. Run GamryParser.load()'
        return self.header

    def get_experiment_type(self):
        """retrieve the type of experiment that was loaded (TAG)

        Args:
            None
        Returns:
            str: Experiment Type (EXPLAIN-TAG)

        """
        assert self.loaded, 'DTA file not loaded. Run GamryParser.load()'
        return self.header['TAG']

    def get_ocv_curve(self):
        """return the contents of OCVCURVE (if it exists). Deprecated in Framework version 7"""
        if self.ocv_exists:
            return self.ocv
        else:
            return None

    def get_ocv_value(self):
        """return the final OCV measurement of the experiment (if it exists)"""
        if 'EOC' in self.header.keys():
            return self.header['EOC']
        else:
            return None

    def read_header(self):
        """helper function to grab data from the EXPLAIN file header, which contains the loaded experiment's configuration

        Args:
            None
        Returns:
            header (dict): experimental header data in key-value pairs.
            length (int): length of header text, in # of bytes

        """

        pos = 0
        with open(self.fname, 'r', encoding='utf8', errors='ignore') as f:
            cur_line = f.readline().split('\t')
            while not re.search(r'(^|Z)CURVE', cur_line[0]):
                if f.tell() == pos:
                    break

                pos = f.tell()
                cur_line = f.readline().strip().split('\t')
                if len(cur_line[0]) == 0:
                    pass

                if len(cur_line) > 1:
                    # data format: key, type, value
                    if cur_line[1] in ['LABEL', 'PSTAT']:
                        self.header[cur_line[0]] = cur_line[2]
                    elif cur_line[1] in ['QUANT', 'IQUANT', 'POTEN']:
                        self.header[cur_line[0]] = locale.atof(cur_line[2])  # locale-friendly alternative to float
                    elif cur_line[1] in ['IQUANT', 'SELECTOR']:
                        self.header[cur_line[0]] = int(cur_line[2])
                    elif cur_line[1] in ['TOGGLE']:
                        self.header[cur_line[0]] = cur_line[2] == 'T'
                    elif cur_line[1] == 'TWOPARAM':
                        self.header[cur_line[0]] = {
                            'enable': cur_line[2] == 'T',
                            'start': locale.atof(cur_line[3]),  # locale-friendly alternative to float
                            'finish': locale.atof(cur_line[4])  # locale-friendly alternative to float
                        }
                    elif cur_line[0] == 'TAG':
                        self.header['TAG'] = cur_line[1]
                    elif cur_line[0] == 'NOTES':
                        n_notes = int(cur_line[2])
                        note = ''
                        for i in range(n_notes):
                            note += f.readline().strip() + '\n'
                        self.header[cur_line[0]] = note
                    elif cur_line[0] == 'OCVCURVE':
                        n_points = int(cur_line[2])
                        ocv = f.readline().strip() + '\n'  # grab header data
                        f.readline()  # skip second line of header
                        for i in range(n_points):
                            ocv += f.readline().strip() + '\n'
                        ocv = pd.read_csv(StringIO(ocv), '\t', header=0, index_col=0)
                        self.ocv = ocv
                        self.ocv_exists = True

            self.header_length = f.tell()

        return self.header, self.header_length

    def read_curves(self):
        """helper function to iterate through curves in a dta file and save as individual dataframes

        Args:
            None
        Returns:
            curves (list): list of DataFrames, each element representing an individual curve of experimental data.

        """

        assert len(self.header) > 0, "Must read file header before curves can be extracted."
        self.curves = []
        self.curve_count = 0

        with open(self.fname, 'r', encoding='utf8', errors='ignore') as f:
            f.seek(self.header_length)  # skip to end of header

            def read_curve_data(fid):
                pos = 0
                curve = f.readline().strip() + '\n'  # grab header data
                if len(curve) <= 1:
                    return [], [], pd.DataFrame()

                units = f.readline().strip().split('\t')
                cur_line = fid.readline().strip()
                while not re.search(r'CURVE', cur_line):
                    curve += cur_line + '\n'
                    pos = fid.tell()
                    cur_line = fid.readline().strip()
                    if fid.tell() == pos:
                        break

                curve = pd.read_csv(StringIO(curve), '\t', header=0, index_col=0)
                keys = curve.columns.values.tolist()
                units = units[1:]

                return keys, units, curve

            while True:
                curve_keys, curve_units, curve = read_curve_data(f)
                if curve.empty:
                    break

                for key in curve_keys:
                    nonnumeric_keys = ['Over', ]
                    if key in nonnumeric_keys:
                        continue
                    elif key == 'Pt':
                        if not is_numeric_dtype(curve.index):
                            curve.index = curve.index.map(int)
                    else:
                        if not is_numeric_dtype(curve[key]):
                            curve[key] = curve[key].map(locale.atof)

                if not bool(self.curve_units.items()):
                    exp_type = self.header['TAG']
                    for key, unit in zip(curve_keys, curve_units):
                        if exp_type in self.REQUIRED_UNITS.keys():
                            if key in self.REQUIRED_UNITS[exp_type].keys():
                                assert unit == self.REQUIRED_UNITS[exp_type][key], 'Unit error for \'{}\': Expected \'{}\', found \'{}\'!'.format(key, self.REQUIRED_UNITS[exp_type][key], unit)
                        self.curve_units[key] = unit
                else:
                    for key, unit in zip(curve_keys, curve_units):
                        assert self.curve_units[key] == unit, 'Unit mismatch found!'

                self.curves.append(curve)
                self.curve_count += 1

        return self.curves
