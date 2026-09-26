"""Experiment types with technique-specific columns and header properties."""

from collections.abc import Mapping
from dataclasses import replace
from pathlib import Path
from typing import ClassVar, Self

import polars as pl

from ._dta import ParsedFile
from .experiment import Experiment


class CyclicVoltammetry(Experiment):
    """Cyclic voltammetry (TAG CV)."""

    TAGS = frozenset({"CV"})
    COLUMNS = ("Vf", "Im")
    REQUIRED_UNITS: ClassVar[Mapping[str, str]] = {"Vf": "V vs. Ref.", "Im": "A"}

    @property
    def v_range(self) -> tuple[float, float] | None:
        """Programmed scan limits (VLIMIT1, VLIMIT2), in V."""
        return self._float_pair("VLIMIT1", "VLIMIT2")

    @property
    def scan_rate(self) -> float | None:
        """Programmed scan rate, in mV/s."""
        return self._float("SCANRATE")


class ChronoAmperometry(Experiment):
    """Chronoamperometry (TAG CHRONOA)."""

    TAGS = frozenset({"CHRONOA"})
    COLUMNS = ("T", "Vf", "Im")

    @property
    def sample_time(self) -> float | None:
        """Programmed sample period, in s."""
        return self._float("SAMPLETIME")

    @property
    def sample_count(self) -> int:
        """Number of samples across all curves."""
        return sum(curve.height for curve in self.curves)


class Impedance(Experiment):
    """Potentiostatic EIS (TAG EISPOT)."""

    TAGS = frozenset({"EISPOT"})
    COLUMNS = ("Freq", "Zreal", "Zimag", "Zmod", "Zphz")


class OpenCircuitPotential(Experiment):
    """Open circuit potential (TAG CORPOT). `ocv_curve` is the measured curve."""

    TAGS = frozenset({"CORPOT"})
    COLUMNS = ("T", "Vf")

    @classmethod
    def _from_parsed(cls, path: Path, parsed: ParsedFile) -> Self:
        return replace(super()._from_parsed(path, parsed), ocv_curve=parsed.curves[0] if parsed.curves else None)


class SquareWaveVoltammetry(Experiment):
    """Square wave voltammetry (TAG SQUARE_WAVE)."""

    TAGS = frozenset({"SQUARE_WAVE"})
    COLUMNS = ("T", "Vfwd", "Vrev", "Vstep", "Ifwd", "Irev", "Idif")

    @property
    def step_size(self) -> float | None:
        """Step size, in mV."""
        return self._float("STEPSIZE")

    @property
    def pulse_size(self) -> float | None:
        """Pulse size, in mV."""
        return self._float("PULSESIZE")

    @property
    def pulse_width(self) -> float | None:
        """Pulse on time, in s."""
        return self._float("PULSEON")

    @property
    def frequency(self) -> float | None:
        """Step frequency, in Hz."""
        return self._float("FREQUENCY")

    @property
    def v_range(self) -> tuple[float, float] | None:
        """Sweep limits (VINIT, VFINAL), in V."""
        return self._float_pair("VINIT", "VFINAL")

    @property
    def cycles(self) -> int | None:
        """Number of voltammetry cycles."""
        value = self._float("CYCLES")
        return None if value is None else int(value)


class VFP600(Experiment):
    """Data from the Gamry VFP600 LabView front end (TAG VFP600). T is computed from FREQ."""

    TAGS = frozenset({"VFP600"})
    COLUMNS = ("T", "Voltage", "Current")

    @property
    def sample_time(self) -> float | None:
        """Sample period (1 / FREQ), in s."""
        frequency = self._float("FREQ")
        return 1 / frequency if frequency else None

    @property
    def sample_count(self) -> int:
        """Number of samples across all curves."""
        return sum(curve.height for curve in self.curves)

    def _curve_frame(self, index: int) -> pl.DataFrame:
        frame = self.curves[index]
        sample_time = self.sample_time
        if sample_time is None:
            return frame.with_columns(T=pl.lit(None, dtype=pl.Float64))
        return frame.with_columns(T=pl.int_range(pl.len(), dtype=pl.Int64) * sample_time)
