import gamry_parser as parser
import pandas as pd

class ChronoAmperometry(parser.GamryParser):
    "Load an EXPLAIN file for a Chronoamperometry experiment."
    def __init__(self, filename=None, to_timestamp=True):
        super().__init__(filename=filename)
        self.to_timestamp = to_timestamp

    def get_curve_data(self, curve = 1):
        assert self.loaded,  'DTA file not loaded. Run ChronoAmperometry.load()'
        df = self.curves[curve-1]
        return df[['T', 'Vf', 'Im']]

    def load(self):
        super().load()
        if self.to_timestamp:
            "we want data returned with timestamps instead of relative time"
            start_time = pd.to_datetime(self.header['DATE'] + ' ' + self.header['TIME']) # start time
            for curve in self.curves:
                curve['T'] = (start_time + pd.to_timedelta(curve['T'],'s'))
