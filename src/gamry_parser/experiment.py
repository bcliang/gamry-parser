"""Experiment results returned by `read`."""

import os
import re
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import ClassVar, NoReturn, Self

import polars as pl

from ._dta import GamryParseError, HeaderValue, ParsedFile, ReadOnlyDict, parse

_REMOVED = "{name} was removed in gamry-parser 1.0; use gamry_parser.read(path)"
_DATE = re.compile(r"(\d{4}|\d{1,2})([/.-])(\d{1,2})\2(\d{4}|\d{2})")
_TIME = re.compile(r"(\d{1,2}):(\d{2}):(\d{2})(?:\s*([AaPp])\.?[Mm]\.?)?")


@dataclass(frozen=True, kw_only=True, eq=False)
class Experiment:
    """A parsed DTA file. Subclasses select technique-specific columns and header properties."""

    TAGS: ClassVar[frozenset[str]] = frozenset()
    COLUMNS: ClassVar[tuple[str, ...] | None] = None
    REQUIRED_UNITS: ClassVar[Mapping[str, str]] = {}

    path: Path
    header: Mapping[str, HeaderValue]
    units: Mapping[str, str]
    curves: tuple[pl.DataFrame, ...]
    ocv_curve: pl.DataFrame | None

    def __new__(cls, *args: object, **kwargs: object) -> Self:
        if args or not kwargs or kwargs.keys() & {"filename", "to_timestamp"}:
            raise TypeError(_REMOVED.format(name=f"{cls.__name__}(filename=...).load()"))
        return super().__new__(cls)

    def __post_init__(self) -> None:
        object.__setattr__(self, "header", ReadOnlyDict(self.header))
        object.__setattr__(self, "units", ReadOnlyDict(self.units))

    def __getnewargs_ex__(self) -> tuple[tuple[()], dict[str, object]]:
        """Arguments pickle and copy pass to `__new__`."""
        return (), {"path": self.path}

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for tag in cls.__dict__.get("TAGS", ()):
            _REGISTRY[tag] = cls

    @classmethod
    def read(cls, path: str | os.PathLike[str], *, decimal_comma: bool | None = None) -> Self:
        """Parse a DTA file. On a subclass, raise `GamryParseError` unless the file's TAG is one it handles."""
        path = Path(path)
        parsed = parse(path.read_bytes(), decimal_comma)
        tag = parsed.header.get("TAG")
        if not isinstance(tag, str):
            raise GamryParseError(f"{path.name}: no TAG header; not a Gamry DTA file")
        if cls is Experiment:
            target = _REGISTRY.get(tag, Experiment)
        elif tag in cls.TAGS:
            target = cls
        elif not cls.TAGS:
            raise GamryParseError(f"{path.name}: {cls.__name__} has no TAGS; found TAG {tag!r}")
        else:
            raise GamryParseError(f"{path.name}: expected TAG {' or '.join(sorted(cls.TAGS))}, found {tag!r}")
        for column, unit in target.REQUIRED_UNITS.items():
            if column in parsed.units and parsed.units[column] != unit:
                raise GamryParseError(
                    f"{path.name}: column {column} has unit {parsed.units[column]!r}, expected {unit!r}"
                )
        return target._from_parsed(path, parsed)

    @classmethod
    def _from_parsed(cls, path: Path, parsed: ParsedFile) -> Self:
        return cls(
            path=path, header=parsed.header, units=parsed.units, curves=parsed.curves, ocv_curve=parsed.ocv_curve
        )

    @property
    def experiment_type(self) -> str | None:
        """The header TAG, e.g. CV."""
        tag = self.header.get("TAG")
        return tag if isinstance(tag, str) else None

    @property
    def curve_count(self) -> int:
        return len(self.curves)

    @property
    def sample_count(self) -> int:
        """Number of rows across all curves."""
        return sum(curve.height for curve in self.curves)

    @property
    def ocv(self) -> float | None:
        """Open circuit potential recorded in the header (EOC), in V."""
        return self._float("EOC")

    @property
    def start_time(self) -> datetime | None:
        """Start of the experiment from the DATE and TIME header fields, or None if either is missing."""
        date, time = self.header.get("DATE"), self.header.get("TIME")
        if not isinstance(date, str) or not isinstance(time, str):
            return None
        return _parse_datetime(date, time)

    def curve(self, index: int = 0, *, timestamps: bool = False) -> pl.DataFrame:
        """Return one curve. With `timestamps`, T holds datetimes instead of seconds since the start."""
        if not -self.curve_count <= index < self.curve_count:
            raise IndexError(f"curve {index} out of range; {self.path.name} has {self.curve_count} curves")
        frame = self._curve_frame(index)
        if self.COLUMNS is not None:
            missing = [column for column in self.COLUMNS if column not in frame.columns]
            if missing:
                raise GamryParseError(f"{self.path.name}: curve {index} has no {', '.join(missing)} column")
            frame = frame.select(self.COLUMNS)
        if timestamps:
            frame = self._with_timestamps(frame)
        return frame

    def _curve_frame(self, index: int) -> pl.DataFrame:
        return self.curves[index]

    def _with_timestamps(self, frame: pl.DataFrame) -> pl.DataFrame:
        start = self.start_time
        if start is None:
            raise GamryParseError(f"{self.path.name} has no DATE/TIME header; cannot compute timestamps")
        if "T" not in frame.columns:
            raise GamryParseError(f"{self.path.name}: curve has no T column; cannot compute timestamps")
        if not frame.schema["T"].is_numeric():
            raise GamryParseError(f"{self.path.name}: T column is not numeric; cannot compute timestamps")
        elapsed = pl.duration(microseconds=(pl.col("T") * 1_000_000).round().cast(pl.Int64))
        return frame.with_columns(T=pl.lit(start) + elapsed)

    def _float(self, key: str) -> float | None:
        value = self.header.get(key)
        return float(value) if isinstance(value, int | float) and not isinstance(value, bool) else None

    def _float_pair(self, first: str, second: str) -> tuple[float, float] | None:
        a, b = self._float(first), self._float(second)
        return None if a is None or b is None else (a, b)


_REGISTRY: dict[str, type[Experiment]] = {}


def read(path: str | os.PathLike[str], *, decimal_comma: bool | None = None) -> Experiment:
    """Parse a DTA file into the `Experiment` subclass registered for its TAG."""
    return Experiment.read(path, decimal_comma=decimal_comma)


def GamryParser(*args: object, **kwargs: object) -> NoReturn:
    """Removed in 1.0; raises TypeError."""
    raise TypeError(_REMOVED.format(name="GamryParser"))


def _parse_datetime(date: str, time: str) -> datetime:
    date_match = _DATE.fullmatch(date.strip())
    time_match = _TIME.fullmatch(time.strip())
    if date_match is None or time_match is None:
        raise GamryParseError(f"cannot parse DATE {date!r} and TIME {time!r}")
    hour, minute, second = (int(part) for part in time_match.group(1, 2, 3))
    if time_match[4]:
        hour = hour % 12 + (12 if time_match[4] in "Pp" else 0)
    try:
        year, month, day = _date_parts(date_match)
        return datetime(year, month, day, hour, minute, second)
    except ValueError as error:
        raise GamryParseError(f"cannot parse DATE {date!r} and TIME {time!r}") from error


def _date_parts(match: re.Match[str]) -> tuple[int, int, int]:
    """Year, month and day. Slash dates are month first, dash and dot dates day first, unless the month exceeds 12.

    A two-digit year is accepted only in the M/D/YY form, with no swap, so it cannot be mistaken for a day.
    """
    first, separator, middle, last = match.groups()
    if len(first) == 4:
        return int(first), int(middle), int(last)
    month, day = (int(first), int(middle)) if separator == "/" else (int(middle), int(first))
    if len(last) == 2:
        if separator != "/" or month > 12:
            raise ValueError("ambiguous two-digit year")
        year = int(last)
        return year + (2000 if year < 69 else 1900), month, day
    if month > 12 >= day:
        month, day = day, month
    return int(last), month, day
