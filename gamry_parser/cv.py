import gamry_parser as parser

class CyclicVoltammetry(parser.GamryParser):
    "Load an EXPLAIN file for a Cyclic Voltammetry experiment."
    def get_v_range(self):
        assert self.loaded,  'DTA file not loaded. Run CyclicVoltammetry.load()'
        assert 'VLIMIT1' in self.header.keys(), 'DTA header file missing VLIMIT1 specification'
        assert 'VLIMIT2' in self.header.keys(), 'DTA header file missing VLIMIT2 specification'
        
        return self.header['VLIMIT1'], self.header['VLIMIT2']

    def get_curve_data(self, curve = 1):
        "Overloaded function returns CV-relevant data to the user"
        assert self.loaded,  'DTA file not loaded. Run CyclicVoltammetry.load()'
        assert curve <= self.curve_count, 'Invalid curve ({}). File contains {} total curves.'.format(curve, self.curve_count)
        df = self.curves[curve-1]
        return df[['Vf', 'Im']]
