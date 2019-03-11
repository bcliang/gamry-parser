import gamry_parser as parser

class CyclicVoltammetry(parser.GamryParser):
    "Load an EXPLAIN file for a Cyclic Voltammetry experiment."
    def get_v_range(self):
        assert self.loaded,  'DTA file not loaded. Run CyclicVoltammetry.load()'
        vals = self.curves[0]['Vf']
        return min(vals), max(vals)

    def get_curve_data(self, curve = 1):
        "Overloaded function returns CV-relevant data to the user"
        assert self.loaded,  'DTA file not loaded. Run CyclicVoltammetry.load()'
        assert curve <= self.curve_count, 'Invalid curve ({}). File contains {} total curves.'.format(curve, self.curve_count)
        df = self.curves[curve-1]
        return df[['Vf', 'Im']]
