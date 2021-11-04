import gamry_parser as parser
import pandas as pd
import os
import re


class OpenCircuitPotential(parser.GamryParser):
    """Load an Open Circuit Potential (CORPOT) experiment generated in Gamry EXPLAIN format."""

    def get_curve_data(self):
        """retrieve OCP data

        Args:
            None

        Returns:
            pandas.DataFrame:
                - T: time, in seconds or Timestamp
                - Vf: potential, in V

        """

        assert self.loaded, "DTA file not loaded. Run OpenCircuitPotential.load()"
        df = self.curves[0]
        return df[["T", "Vf"]]

    def load(self, filename: str = None, to_timestamp: bool = None):
        """save experiment information to \"header\", then save curve data to \"curves\"

        Args:
            filename (str, optional): file containing EXPLAIN-formatted data. defaults to None.
            to_timestamp (bool, optional): Convert sample times from seconds to datetime.datetime.isoformat(). Defaults to True
        Returns:
            None

        """
        super().load(filename=filename, to_timestamp=to_timestamp)

        assert (
            self.header["TAG"] == "CORPOT"
        ), "This does not appear to be an Open Circuit Potential \
            Experiment file (looking for CORPOT, received {})".format(
            self.header["TAG"]
        )
        self.ocv_exists = True
        self.ocv = self.curves[0]
        self.loaded = True

    def get_ocv_curve(self):
        """return the contents of OCVCURVE (if it exists). Deprecated in Framework version 7"""
        if self.ocv_exists:
            return self.ocv
        else:
            return None
