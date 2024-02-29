import pandas as pd
from pandas.api.types import is_numeric_dtype
from typing import Optional, Dict, Any, List, Union, Tuple
import re
import os
import locale
from io import StringIO, TextIOWrapper


class GamryParser:
    """Load experiment data generated in Gamry EXPLAIN format."""

    fname: Optional[str] = None
    to_timestamp: bool = False
    loaded: bool = False
    curve_count: int = 0
    header_length: int = 0

    _header: Dict[str, Any] = dict()
    _curves: List[pd.DataFrame] = []
    _curve_units: Dict[str, str] = dict()
    _ocv: pd.DataFrame = None

    REQUIRED_UNITS: Dict[str, Dict[str, str]] = dict(CV=dict(Vf="V vs. Ref.", Im="A"))

    def __init__(
        self, filename: Optional[str] = None, to_timestamp: Optional[bool] = None
    ):
        """GamryParser.__init__

        Args:
            filename (str, optional): filepath to experiment data. Defaults to None
            to_timestamp (bool, optional): Convert sample times from elapsed seconds to pandas.Timestamp(). Defaults to False

        Returns:
            None

        """
        self._reset_props()
        self.fname = filename if filename is not None else self.fname
        self.to_timestamp = (
            to_timestamp if to_timestamp is not None else self.to_timestamp
        )

    def _reset_props(self):
        "re-initialize parser properties"

        self.fname = None
        self.to_timestamp = False
        self.loaded = False
        self.curve_count = 0
        self.header_length = 0

        self._header = dict()
        self._curves = []
        self._curve_units = dict()
        self._ocv = None

    def load(self, filename: Optional[str] = None, to_timestamp: Optional[bool] = None):
        """save experiment information to \"header\", then save curve data to \"curves\"

        Args:
            filename (str, optional): file containing EXPLAIN-formatted data. defaults to None.
        Returns:
            None

        """

        self.__init__(
            filename=filename if filename else self.fname,
            to_timestamp=to_timestamp if to_timestamp else self.to_timestamp,
        )
        self.loaded = False
        assert self.fname is not None, "GamryParser needs to know what file to parse."
        assert os.path.exists(self.fname), "The file '{}' was not found.".format(
            self.fname
        )

        self.read_header()
        self.read_curves()
        if self.to_timestamp:
            self._convert_T_to_Timestamp()

        self.loaded = True

    def _convert_T_to_Timestamp(self):
        """convert experiment sample elapsed time to absolute time (pd.Timestamp)"

        Args:
            None
        Returns:
            None
        """

        start_time = pd.to_datetime(
            self._header["DATE"] + " " + self._header["TIME"],
            dayfirst=bool(
                re.search(r"[0-9]+\-[0-9]+\-[0-2]{1}[0-9]{3}", self._header["DATE"])
            ),
        )
        for curve in self._curves:
            curve["T"] = start_time + pd.to_timedelta(curve["T"], "s")

    @property
    def curve_indices(self) -> Union[Tuple[int, ...], None]:
        """return indices of curves (zero-based indexing)"""
        return tuple(range(self.curve_count)) if self.curve_count else None

    @property
    def curve_numbers(self) -> Union[Tuple[int, ...], None]:
        """return Gamry curve numbers (one-based indexing, as in Gamry software)"""
        return tuple(range(1, self.curve_count + 1)) if self.curve_count else None

    def curve(self, curve: int = 0) -> pd.DataFrame:
        """retrieve relevant experimental data

        Args:
            curve (int, optional): curve number to return. Defaults to 0.

        Returns:
            pandas.DataFrame: (multiple columns)

        """
        assert self.loaded, "DTA file not loaded. Run GamryParser.load()"
        assert (
            curve < self.curve_count
        ), "Invalid curve ({}). File contains {} total curves.".format(
            curve, self.curve_count
        )
        return self._curves[curve]

    @property
    def curves(self) -> List[pd.DataFrame]:
        """return all loaded curves as a list of pandas DataFrames"""
        # assert self.loaded, "DTA file not loaded. Run GamryParser.load()"
        return self._curves

    @curves.setter
    def curves(self, val: List[pd.DataFrame]):
        self._curves = val

    @property
    def header(self) -> Dict[str, Any]:
        """return the experiment configuration dictionary"""
        # assert self.loaded, "DTA file not loaded. Run GamryParser.load()"
        return self._header if self._header else dict()

    @property
    def experiment_type(self) -> Optional[str]:
        """retrieve the type of experiment that was loaded (TAG)

        Args:
            None
        Returns:
            str: Experiment Type (EXPLAIN-TAG)

        """
        return self._header.get("TAG", None)

    @property
    def ocv(self) -> Optional[Union[float, int]]:
        """return the final OCV measurement of the experiment (if it exists)"""
        return self._header.get("EOC", None)

    @property
    def ocv_curve(self) -> pd.DataFrame:
        """return the contents of OCVCURVE (if it exists). Deprecated in Framework version 7"""
        return self._ocv

    def read_header(self) -> Tuple[Dict[str, Any], int]:
        """helper function to grab data from the EXPLAIN file header, which contains the loaded experiment's configuration

        Args:
            None
        Returns:
            header (dict): experimental header data in key-value pairs.
            length (int): length of header text, in # of bytes

        """

        assert self.fname, "No filename specified (fname)"

        pos = 0
        with open(file=self.fname, mode="r", encoding="utf8", errors="ignore") as f:
            cur_line = f.readline().split("\t")
            while not re.search(r"(^|Z|VFP|EFM)CURVE", cur_line[0]):
                if f.tell() == pos:
                    break

                pos = f.tell()
                cur_line = f.readline().strip().split("\t")
                if len(cur_line[0]) == 0:
                    pass

                if len(cur_line) > 1:
                    # data format: key, type, value
                    if cur_line[1] in ["LABEL", "PSTAT"]:
                        self._header[cur_line[0]] = cur_line[2]
                    elif cur_line[1] in ["QUANT", "IQUANT", "POTEN"]:
                        # locale-friendly alternative to float
                        self._header[cur_line[0]] = locale.atof(cur_line[2])
                    elif cur_line[1] in ["IQUANT", "SELECTOR"]:
                        self._header[cur_line[0]] = int(cur_line[2])
                    elif cur_line[1] in ["TOGGLE"]:
                        self._header[cur_line[0]] = cur_line[2] == "T"
                    elif cur_line[1] == "TWOPARAM":
                        self._header[cur_line[0]] = {
                            "enable": cur_line[2] == "T",
                            # locale-friendly alternative to float
                            "start": locale.atof(cur_line[3]),
                            # locale-friendly alternative to float
                            "finish": locale.atof(cur_line[4]),
                        }
                    elif cur_line[0] == "TAG":
                        self._header["TAG"] = cur_line[1]
                    elif cur_line[0] == "NOTES":
                        n_notes: int = int(cur_line[2])
                        note: str = ""
                        for _ in range(n_notes):
                            note += f.readline().strip() + "\n"
                        self._header[cur_line[0]] = note
                    elif cur_line[0] == "OCVCURVE":
                        n_points = int(cur_line[2])
                        ocv = f.readline().strip() + "\n"  # grab header data
                        f.readline()  # skip second line of header
                        for _ in range(n_points):
                            ocv += f.readline().strip() + "\n"
                        ocv = pd.read_csv(
                            StringIO(ocv), delimiter="\t", header=0, index_col=0
                        )
                        self._ocv: str = ocv

            self.header_length = f.tell()

        return self._header, self.header_length

    def _read_curve_data(self, fid: TextIOWrapper) -> Tuple[List[str], List[str], pd.DataFrame]:
        """helper function to process an EXPLAIN Table

        Args:
            fid (int): a file handle pointer to the table position in the data files
        Returns:
            keys (list): column identifier (e.g. Vf)
            units (list): column unit type (e.g. V)
            curve (DataFrame): Table data saved as a pandas Dataframe

        """
        pos = 0
        curve = fid.readline().strip() + "\n"  # grab header data
        if len(curve) <= 1:
            return [], [], pd.DataFrame()

        units = fid.readline().strip().split("\t")
        cur_line = fid.readline().strip()
        while not re.search(r"(CURVE|EXPERIMENTABORTED)", cur_line):
            curve += cur_line + "\n"
            pos = fid.tell()
            cur_line = fid.readline().strip()
            if fid.tell() == pos:
                break

        curve = pd.read_csv(StringIO(curve), delimiter="\t", header=0, index_col=0)
        keys = curve.columns.values.tolist()
        units = units[1:]

        return keys, units, curve

    def read_curves(self) -> List[pd.DataFrame]:
        """helper function to iterate through curves in a dta file and save as individual dataframes

        Args:
            None
        Returns:
            curves (list): list of DataFrames, each element representing an individual curve of experimental data.

        """

        assert (
            len(self._header) > 0
        ), "Must read file header before curves can be extracted."
        assert self.fname, "No filename specified (fname)"

        self._curves = []
        self.curve_count = 0

        with open(file=self.fname, mode="r", encoding="utf8", errors="ignore") as f:
            f.seek(self.header_length)  # skip to end of header

            while True:
                curve_keys, curve_units, curve = self._read_curve_data(f)
                if curve.empty:
                    break

                for key in curve_keys:
                    nonnumeric_keys = [
                        "Over",
                    ]
                    if key in nonnumeric_keys:
                        continue
                    elif key == "Pt":
                        if not is_numeric_dtype(curve.index):
                            curve.index = curve.index.map(int)
                    else:
                        if not is_numeric_dtype(curve[key]):
                            curve[key] = curve[key].map(locale.atof)

                if not bool(self._curve_units.items()):
                    exp_type = self._header["TAG"]
                    for key, unit in zip(curve_keys, curve_units):
                        if exp_type in self.REQUIRED_UNITS.keys():
                            if key in self.REQUIRED_UNITS[exp_type].keys():
                                assert (
                                    unit == self.REQUIRED_UNITS[exp_type][key]
                                ), "Unit error for '{}': Expected '{}', found '{}'!".format(
                                    key, self.REQUIRED_UNITS[exp_type][key], unit
                                )
                        self._curve_units[key] = unit
                else:
                    for key, unit in zip(curve_keys, curve_units):
                        assert self._curve_units[key] == unit, "Unit mismatch found!"

                self._curves.append(curve)
                self.curve_count += 1

        return self._curves
