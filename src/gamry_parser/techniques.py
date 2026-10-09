"""Experiment types with technique-specific columns and header properties."""

from collections.abc import Mapping
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
        ocv_curve = parsed.curves[0] if parsed.curves else None
        return cls(path=path, header=parsed.header, units=parsed.units, curves=parsed.curves, ocv_curve=ocv_curve)


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
    """Data from the Gamry VFP600 LabView front end (TAG VFP600). `curve()` computes T from FREQ."""

    TAGS = frozenset({"VFP600"})
    COLUMNS = ("T", "Voltage", "Current")

    @property
    def sample_time(self) -> float | None:
        """Sample period (1 / FREQ), in s."""
        frequency = self._float("FREQ")
        return 1 / frequency if frequency else None

    def _curve_frame(self, index: int) -> pl.DataFrame:
        frame = self.curves[index]
        sample_time = self.sample_time
        if sample_time is None:
            return frame.with_columns(T=pl.lit(None, dtype=pl.Float64))
        return frame.with_columns(T=pl.int_range(pl.len(), dtype=pl.Int64) * sample_time)


class CyclicChargeDischarge(Experiment):
    """Cyclic charge-discharge summary from the PWR800 software (TAG PWR800_CYCLICCHARGEDISCHARGE).

    The curve has one row per charge or discharge step. Type is 0 for a charge step and 1 for a discharge step.
    Charge is positive for both step types; Energy is negative for discharge steps.
    """

    TAGS = frozenset({"PWR800_CYCLICCHARGEDISCHARGE"})
    COLUMNS = ("Time", "Type", "Cycle", "Charge", "Duration", "Vstart", "Vend", "Energy")

    @property
    def cycles(self) -> int | None:
        """Programmed number of charge-discharge cycles."""
        value = self._float("CYCLES")
        return None if value is None else int(value)

    @property
    def capacity(self) -> float | None:
        """Nominal cell capacity, in A-hr."""
        return self._float("CAPACITY")

    @property
    def charge_current(self) -> float | None:
        """Charge current, in A."""
        return self._float("CHARGECURRENT")

    @property
    def sample_time(self) -> float | None:
        """Sample period, in s."""
        return self._float("SAMPLETIME")

    @property
    def stop_reason(self) -> str | None:
        """Why the run ended (STOPREASON), e.g. "Cycle Limit"."""
        value = self.header.get("STOPREASON")
        return value if isinstance(value, str) else None


class ChargeDischarge(Experiment):
    """One charge or discharge step from the PWR800 software (TAG PWR800_CHARGE or PWR800_DISCHARGE).

    A cyclic charge-discharge run can save each step as its own file alongside the summary.
    """

    TAGS = frozenset({"PWR800_CHARGE", "PWR800_DISCHARGE"})
    COLUMNS = ("T", "Vf", "Im")

    @property
    def capacity(self) -> float | None:
        """Nominal cell capacity, in A-hr."""
        return self._float("CAPACITY")

    @property
    def sample_time(self) -> float | None:
        """Sample period, in s."""
        return self._float("SAMPLETIME")

    @property
    def start_time_offset(self) -> float | None:
        """The STARTTIMEOFFSET field written after the curve, in s."""
        return self._float("STARTTIMEOFFSET")
