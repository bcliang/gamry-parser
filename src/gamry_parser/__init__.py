"""Parse Gamry EXPLAIN (DTA) files into polars DataFrames."""

from importlib.metadata import version

from ._dta import GamryParseError, HeaderValue, TwoParam
from .experiment import Experiment, GamryParser, read

__version__ = version("gamry-parser")

__all__ = [
    "Experiment",
    "GamryParseError",
    "GamryParser",
    "HeaderValue",
    "TwoParam",
    "__version__",
    "read",
]
