import gamry_parser as parser


class Impedance(parser.GamryParser):
    """Load a Potentiostatic EIS experiment generated in Gamry EXPLAIN format."""

    def get_curve_data(self, curve=0):
        """ retrieve potentiostatic eis-relevant data

        Args:
            curve (int, optional): curve number to return. Defaults to 1.

        Returns:
            pandas.DataFrame:
                - Freq (float): frequency, in Hz
                - Zreal (float): Real Impedance, in ohms
                - Zimag (float): Imaginary Impedance, in ohms
                - Zmod (float): Impedance magnitude, in ohms
                - Zmod (float): Impedance phase angle, in degrees

        """

        assert self.loaded, 'DTA file not loaded. Run Impedance.load()'
        df = self.curves[curve]
        return df[['Freq', 'Zreal', 'Zimag', 'Zmod', 'Zphz']]
