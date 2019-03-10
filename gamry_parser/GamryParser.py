import pandas as pd
import datetime
import re
import os

class GamryParser:
    "Generic Parser for data files in Gamry EXPLAIN format (*.dta)."
    def __init__(self, filename=None):
        self.fname = filename
        self.header = dict()
        self.header_length = 0
        self.loaded = False
        self.curves = []
        self.curve_count = 0

    def load(self, filename=None):
        "save experiment information to \"header\", then save curve data to \"curves\""
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
        "return the number of loaded curves"
        assert self.loaded, 'DTA file not loaded. Run GamryParser.load()'
        return self.curve_count

    def get_curve_data(self, curve = 1):
        "return the data from a specific curve in the form of a pandas.DataFrame()"
        assert self.loaded,  'DTA file not loaded. Run GamryParser.load()'
        assert curve <= self.curve_count, 'Invalid curve ({}). File contains {} total curves.'.format(curve, self.curve_count)
        return self.curves[curve - 1]

    def get_curves(self):
        "return all loaded curves as a list of pandas DataFrames"
        assert self.loaded,  'DTA file not loaded. Run GamryParser.load()'
        return self.curves

    def get_header(self):
        "return the experiment configuration dictionary"
        assert self.loaded,  'DTA file not loaded. Run GamryParser.load()'
        return self.header

    def get_experiment_type(self):
        "return the type of experiment that was loaded (TAG)"
        assert self.loaded,  'DTA file not loaded. Run GamryParser.load()'
        return self.header['TAG']

    def read_header(self):
        "helper function to grab data from the EXPLAIN file header, which contains the loaded experiment's configuration"
        pos = 0
        with open(self.fname, 'r', encoding='utf8', errors='ignore') as f:
            cur_line = f.readline().split('\t')
            #while not cur_line[0].startswith('CURVE'):
            while not re.search(r'CURVE', cur_line[0]):
                if f.tell() == pos:
                    break

                pos = f.tell()
                cur_line = f.readline().split('\t')
                if len(cur_line[0]) == 0:
                    pass

                if len(cur_line) > 1:
                    # data format: key, type, value
                    if cur_line[1] in ['LABEL', 'PSTAT']:
                        self.header[cur_line[0]] = cur_line[2]
                    elif cur_line[1] in ['QUANT', 'IQUANT', 'POTEN']:
                        self.header[cur_line[0]] = float(cur_line[2])
                    elif cur_line[1] in ['IQUANT', 'SELECTOR']:
                        self.header[cur_line[0]] = int(cur_line[2])
                    elif cur_line[1] in ['TOGGLE']:
                        self.header[cur_line[0]] = cur_line[2] == 'T'
                    elif cur_line[1] == 'TWOPARAM':
                        self.header[cur_line[0]] = {
                            'enable': cur_line[2] == 'T',
                            'start': float(cur_line[3]),
                            'finish': float(cur_line[4])
                        }
                    elif cur_line[0] == 'TAG':
                        self.header['TAG'] = cur_line[1]

            self.header_length = f.tell()

        return self.header, self.header_length

    def read_curves(self):
        "helper function to iterate through curves in a dta file and save as individual dataframes"
        assert len(self.header) > 0, "Must read file header before curves can be extracted."
        self.curves = []
        self.curve_count = 0

        with open(self.fname, 'r', encoding='utf8', errors='ignore') as f:
            f.seek(self.header_length) # skip to end of header

            def read_curve_data(fid):
                pos = 0
                keys = fid.readline().strip().split('\t')
                if len(keys) <= 1:
                    return [], ''

                fid.readline()
                curve = ''
                cur_line = fid.readline().strip().split()
                #while not cur_line[0].startswith('CURVE'):
                while not re.search(r'CURVE', cur_line[0]):
                    curve += '\t'.join(cur_line)
                    curve += '\n'
                    pos = fid.tell()
                    cur_line = fid.readline().strip().split()
                    if fid.tell() == pos:
                        break

                curve = curve[:-1] # remove trailing newline
                return keys, curve

            while True:
                curve_keys, curve_vals = read_curve_data(f)
                if len(curve_vals) == 0:
                    break

                temp = pd.DataFrame([x.split('\t') for x in curve_vals.split('\n')])
                temp.columns = curve_keys
                temp.set_index(curve_keys[0], inplace=True)
                temp = temp.apply(pd.to_numeric, errors='ignore')
                self.curves.append(temp)
                self.curve_count += 1

        return self.curves
