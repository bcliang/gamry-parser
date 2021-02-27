import gamry_parser as parser


class CyclicVoltammetry(parser.GamryParser):
    """Load a Cyclic Voltammetry experiment generated in Gamry EXPLAIN format."""

    def get_v_range(self):
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
            "VLIMIT1" in self.header.keys()
        ), "DTA header file missing VLIMIT1 specification"
        assert (
            "VLIMIT2" in self.header.keys()
        ), "DTA header file missing VLIMIT2 specification"

        return self.header["VLIMIT1"], self.header["VLIMIT2"]

    def get_scan_rate(self):
        """retrieve the programmed scan rate

        Args:
            None

        Returns:
            float: the scan rate, in mV/s

        """
        assert self.loaded, "DTA file not loaded. Run CyclicVoltammetry.load()"
        assert (
            "SCANRATE" in self.header.keys()
        ), "DTA header file missing SCANRATE specification"
        return self.header["SCANRATE"]

    def get_curve_data(self, curve=0):
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
        df = self.curves[curve]

        return df[["Vf", "Im"]]
