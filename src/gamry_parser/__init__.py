"""Parse Gamry EXPLAIN (DTA) files into polars DataFrames."""

from importlib.metadata import PackageNotFoundError, version

from ._dta import GamryParseError, HeaderValue, MultiParam, TwoParam, VariableAndUnits
from .experiment import Experiment, GamryParser, read
from .techniques import (
    VFP600,
    ChargeDischarge,
    ChronoAmperometry,
    CyclicChargeDischarge,
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
    "ChargeDischarge",
    "ChronoAmperometry",
    "CyclicChargeDischarge",
    "CyclicVoltammetry",
    "Experiment",
    "GamryParseError",
    "GamryParser",
    "HeaderValue",
    "Impedance",
    "MultiParam",
    "OpenCircuitPotential",
    "SquareWaveVoltammetry",
    "TwoParam",
    "VariableAndUnits",
    "__version__",
    "read",
]
