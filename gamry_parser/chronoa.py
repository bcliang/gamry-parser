import gamry_parser as parser
import pandas as pd
import re


class ChronoAmperometry(parser.GamryParser):
    """Load a ChronoAmperometry experiment generated in Gamry EXPLAIN format."""

    def get_curve_data(self, curve: int = 0):
        """retrieve chronoamperometry experiment data

        Args:
            curve (int, optional): curve to return (CHRONOA experiments typically only have 1 curve). Defaults to 1.

        Returns:
            pandas.DataFrame:
                - T: time, in seconds or Timestamp
                - Vf: potential, in V
                - Im: current, in A
        """

        assert self.loaded, "DTA file not loaded. Run ChronoAmperometry.load()"
        df = self.curves[curve]
        return df[["T", "Vf", "Im"]]

    def get_sample_time(self):
        """retrieve the programmed sample period

        Args:
            None.

        Returns:
            float: sample period of the potentiostat (in seconds)

        """

        assert self.loaded, "DTA file not loaded. Run ChronoAmperometry.load()"
        return self.header["SAMPLETIME"]

    def get_sample_count(self, curve: int = 0):
        """compute the number of samples collected for the loaded chronoamperometry experiment

        Args:
            curve (int, optional): curve to return (CHRONOA experiments typically only have 1 curve). Defaults to 1.

        Returns:
            int: number of collected samples for the specified curve

        """

        assert self.loaded, "DTA file not loaded. Run ChronoAmperometry.load()"
        return len(self.curves[curve - 1].index)
