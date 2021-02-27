import gamry_parser as parser
import pandas as pd
import re


class ChronoAmperometry(parser.GamryParser):
    """Load a ChronoAmperometry experiment generated in Gamry EXPLAIN format."""

    def __init__(self, filename=None, to_timestamp=True):
        """ChronoAmperometry.__init__

        Args:
            filename (str, optional): filepath containing CHRONOA experiment data. Defaults to None
            to_timestamp (bool, optional): Convert sample times from seconds to datetime.datetime.isoformat(). Defaults to True

        Returns:
            None

        """

        super().__init__(filename=filename)
        self.to_timestamp = to_timestamp

    def get_curve_data(self, curve=0):
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

    def get_sample_count(self, curve=0):
        """compute the number of samples collected for the loaded chronoamperometry experiment

        Args:
            curve (int, optional): curve to return (CHRONOA experiments typically only have 1 curve). Defaults to 1.

        Returns:
            int: number of collected samples for the specified curve

        """

        assert self.loaded, "DTA file not loaded. Run ChronoAmperometry.load()"
        return len(self.curves[curve - 1].index)

    def load(self, filename=None):
        """run the parser to load the experimental data from file

        Args:
            None

        Returns:
            None

        """

        super().load(filename)
        if self.to_timestamp:
            "we want data returned with timestamps instead of relative time"
            start_time = pd.to_datetime(
                self.header["DATE"] + " " + self.header["TIME"],
                dayfirst=bool(
                    re.search(r"[0-9]+\-[0-9]+\-[0-2]{1}[0-9]{3}", self.header["DATE"])
                ),
            )
            for curve in self.curves:
                curve["T"] = start_time + pd.to_timedelta(curve["T"], "s")
