from typing import Optional, Union
import re
import gamry_parser as parser
import pandas as pd


class ChronoAmperometry(parser.GamryParser):
    """Load a ChronoAmperometry experiment generated in Gamry EXPLAIN format."""

    def curve(self, curve: int = 0) -> pd.DataFrame:
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
        df = self._curves[curve]
        return df[["T", "Vf", "Im"]]

    @property
    def sample_time(self) -> Optional[Union[float, int]]:
        """retrieve the programmed sample period

        Args:
            None.

        Returns:
            float: sample period of the potentiostat (in seconds)

        """
        return self._header.get("SAMPLETIME", None)

    @property
    def sample_count(self, curve: int = 0) -> int:
        """compute the number of samples collected for the loaded chronoamperometry experiment

        Args:
            curve (int, optional): curve to return (CHRONOA experiments typically only have 1 curve). Defaults to 1.

        Returns:
            int: number of collected samples for the specified curve

        """

        return len(self._curves[curve - 1].index) if len(self.curves) > 0 else 0
