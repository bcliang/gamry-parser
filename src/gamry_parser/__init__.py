"""Parse Gamry EXPLAIN (DTA) files into polars DataFrames."""

from importlib.metadata import PackageNotFoundError, version

from ._dta import GamryParseError, HeaderValue, TwoParam
from .experiment import Experiment, GamryParser, read
from .techniques import (
    VFP600,
    ChronoAmperometry,
    CyclicVoltammetry,
    Impedance,
    OpenCircuitPotential,
    SquareWaveVoltammetry,
)

try:
    __version__ = version("gamry-parser")
except PackageNotFoundError:
    __version__ = "0.0.0"

__all__ = [
    "VFP600",
    "ChronoAmperometry",
    "CyclicVoltammetry",
    "Experiment",
    "GamryParseError",
    "GamryParser",
    "HeaderValue",
    "Impedance",
    "OpenCircuitPotential",
    "SquareWaveVoltammetry",
    "TwoParam",
    "__version__",
    "read",
]
