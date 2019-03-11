import gamry_parser as parser

class Impedance(parser.GamryParser):
    "Load an EXPLAIN file for a Electrochemical Impedance Spectroscopy (EIS) experiment."
    def get_curve_data(self, curve = 1):
        assert self.loaded,  'DTA file not loaded. Run Impedance.load()'
        df = self.curves[curve-1]
        return df[['Freq', 'Zreal', 'Zimag', 'Zmod', 'Zphz']]
