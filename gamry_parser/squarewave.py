from typing import Optional, Tuple, Union
import pandas as pd
import gamry_parser as parser


class SquareWaveVoltammetry(parser.GamryParser):
    """Load a Square Wave Voltammetry (SWV) experiment generated in Gamry EXPLAIN format."""

    def load(self, filename: Optional[str] = None, to_timestamp: Optional[bool] = None):
        """save experiment information to \"header\", then save curve data to \"curves\"

        Args:
            filename (str, optional): file containing VFP600 data. defaults to None.
        Returns:
            None

        """
        super(SquareWaveVoltammetry, self).load(
            filename=filename, to_timestamp=to_timestamp
        )
        typecheck = self.header.get("TAG", None)
        assert (
            typecheck == "SQUARE_WAVE"
        ), f"The input file does not contain data from a square wave voltammetry experiment (expected type SQUARE_WAVE, found {typecheck})."

    @property
    def step_size(self) -> Optional[Union[float, int]]:
        """returns the experimental step size, in mV"""
        return self.header.get("STEPSIZE", None)

    @property
    def pulse_size(self) -> Optional[Union[float, int]]:
        """returns the experimental pulse size, in mV"""
        return self.header.get("PULSESIZE", None)

    @property
    def pulse_width(self) -> Optional[Union[float, int]]:
        """returns the experimental pulse "on" time, in seconds"""
        return self.header.get("PULSEON", None)

    @property
    def frequency(self) -> Optional[Union[float, int]]:
        """returns the experimental step frequency, in Hz"""
        return self.header.get("FREQUENCY", None)

    @property
    def v_range(self) -> Tuple[Union[float, int], Union[float, int]]:
        """returns the potential sweep range of a single voltammetry cycle (tuple, in V)"""
        return (self.header.get("VINIT", 0), self.header.get("VFINAL", 0))

    @property
    def cycles(self) -> int:
        """returns the number of voltammetry cycles (#)"""
        return self.header.get("CYCLES", 0)

    def curve(self, curve: int = 0) -> pd.DataFrame:
        """retrieve relevant SWV experimental data

        Args:
            curve (int, optional): curve number to return. Defaults to 0.

        Returns:
            pandas.DataFrame:
                - T: time, in seconds or Timestamp
                - Vfwd: forward potential, in V
                - Vrev: reverse potential, in V
                - Vstep: step potential, in V
                - Ifwd: peak forward current measurement, in A
                - Irev: peak reverse current measurement, in A
                - Idif: differential current measurement (pulse), in A

        """
        assert self.loaded, "DTA file not loaded. Run CyclicVoltammetry.load()"
        assert curve >= 0, "Invalid curve ({}). Indexing starts at 0".format(curve)
        assert (
            curve < self.curve_count
        ), "Invalid curve ({}). File contains {} total curves.".format(
            curve, self.curve_count
        )
        df = self._curves[curve]

        return df[["T", "Vfwd", "Vrev", "Vstep", "Ifwd", "Irev", "Idif"]]
