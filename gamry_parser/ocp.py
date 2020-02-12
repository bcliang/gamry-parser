import gamry_parser as parser
import pandas as pd
import os

class OpenCircuitPotential(parser.GamryParser):
    """Load an Open Circuit Potential (CORPOT) experiment generated in Gamry EXPLAIN format."""
    def __init__(self, filename=None, to_timestamp=True):
        """ OpenCircuitPotential.__init__

        Args:
            filename (str, optional): filepath containing CORPOT experiment data. Defaults to None
            to_timestamp (bool, optional): Convert sample times from seconds to datetime.datetime.isoformat(). Defaults to True

        Returns:
            None

        """

        super().__init__(filename=filename)
        self.to_timestamp = to_timestamp

    def get_curve_data(self):
        """ retrieve OCP data

        Args:
            None

        Returns:
            pandas.DataFrame:
                - T: time, in seconds or Timestamp
                - Vf: potential, in V

        """

        assert self.loaded, 'DTA file not loaded. Run OpenCircuitPotential.load()'
        df = self.curves[0]
        return df[['T', 'Vf']]

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
        assert self.header['TAG'] == "CORPOT", \
            "This does not appear to be an Open Circuit Potential \
                Experiment file (looking for CORPOT, received {})".format(
                    self.get_experiment_type())
        # assert len(re.findall(r"Open Circuit Potential", header)) > 0, "This does not appear to be an Open Circuit Potential Experiment file"
        self.read_curves()
        if self.to_timestamp:
            "we want data returned with timestamps instead of relative time"
            start_time = pd.to_datetime(self.header['DATE'] + ' ' + self.header['TIME'])  # start time
            for curve in self.curves:
                curve['T'] = (start_time + pd.to_timedelta(curve['T'], 's'))

        self.ocv_exists =  True
        self.ocv = self.curves[0]
        self.loaded = True

    def get_ocv_curve(self):
        """return the contents of OCVCURVE (if it exists). Deprecated in Framework version 7"""
        if self.ocv_exists:
            return self.ocv
        else:
            return None