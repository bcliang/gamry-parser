import gamry_parser as parser
import pandas as pd
import os
import re


class OpenCircuitPotential(parser.GamryParser):
    """Load an Open Circuit Potential (CORPOT) experiment generated in Gamry EXPLAIN format."""

    def curve(self):
        """retrieve OCP data

        Args:
            None

        Returns:
            pandas.DataFrame:
                - T: time, in seconds or Timestamp
                - Vf: potential, in V

        """

        assert self.loaded, "DTA file not loaded. Run OpenCircuitPotential.load()"
        df = self._curves[0]
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
            self._header.get("TAG", "NOTFOUND") == "CORPOT"
        ), "This does not appear to be an Open Circuit Potential \
            Experiment file (looking for CORPOT, received {})".format(
            self.header.get("TAG", None)
        )
        self._ocv = self._curves[0]
        self.loaded = True
