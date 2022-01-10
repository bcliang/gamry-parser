import gamry_parser as parser


class CyclicVoltammetry(parser.GamryParser):
    """Load a Cyclic Voltammetry experiment generated in Gamry EXPLAIN format."""

    @property
    def v_range(self):
        """retrieve the programmed voltage scan ranges

        Args:
            None

        Returns:
            tuple, containing:
                float: voltage limit 1, in V
                float: voltage limit 2, in V

        """
        assert self.loaded, "DTA file not loaded. Run CyclicVoltammetry.load()"
        assert (
            "VLIMIT1" in self._header.keys()
        ), "DTA header file missing VLIMIT1 specification"
        assert (
            "VLIMIT2" in self._header.keys()
        ), "DTA header file missing VLIMIT2 specification"

        return self._header.get("VLIMIT1", None), self._header.get("VLIMIT2", None)

    @property
    def scan_rate(self):
        """retrieve the programmed scan rate

        Args:
            None

        Returns:
            float: the scan rate, in mV/s (returns None for unknown scan rates)

        """
        return self._header.get("SCANRATE", None)

    def curve(self, curve: int = 0):
        """retrieve relevant cyclic voltammetry experimental data

        Args:
            curve (int, optional): curve number to return. Defaults to 0.

        Returns:
            pandas.DataFrame:
                - Vf: potential, in V
                - Im: current, in A

        """
        assert self.loaded, "DTA file not loaded. Run CyclicVoltammetry.load()"
        assert curve >= 0, "Invalid curve ({}). Indexing starts at 0".format(curve)
        assert (
            curve < self.curve_count
        ), "Invalid curve ({}). File contains {} total curves.".format(
            curve, self.curve_count
        )
        df = self._curves[curve]

        return df[["Vf", "Im"]]
