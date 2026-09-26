"""Parse the contents of Gamry EXPLAIN (DTA) files."""

import re
from dataclasses import dataclass
from typing import TypedDict

import polars as pl


class GamryParseError(ValueError):
    """Raised when a DTA file cannot be parsed."""


class TwoParam(TypedDict):
    enable: bool
    start: float
    finish: float


type HeaderValue = str | float | int | bool | TwoParam


@dataclass(frozen=True, eq=False)
class ParsedFile:
    header: dict[str, HeaderValue]
    units: dict[str, str]
    curves: tuple[pl.DataFrame, ...]
    ocv_curve: pl.DataFrame | None


_TABLE_LINE = re.compile(r"^([^\t\n]+)\tTABLE(?:\t[^\n]*)?(?:\n|\Z)", re.MULTILINE)
_TABLE_END = re.compile(r"\n(?!\t)")
_CURVE_KEY = re.compile(r"(^|Z|VFP|EFM)CURVE")
_COMMA_NUMBER = re.compile(r"[-+]?\d+,\d+(?:[eE][-+]?\d+)?")


def parse(data: bytes, decimal_comma: bool | None = None) -> ParsedFile:
    """Parse the bytes of a DTA file. `decimal_comma=None` detects the decimal separator."""
    lines, _tables = _split(_decode(data).replace("\r\n", "\n"))
    if decimal_comma is None:
        decimal_comma = _detect_decimal_comma(lines)
    return ParsedFile(header=_parse_header(lines, decimal_comma), units={}, curves=(), ocv_curve=None)


def _decode(data: bytes) -> str:
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return data.decode("cp1252", errors="replace")


def _split(text: str) -> tuple[list[str], list[tuple[str, str]]]:
    """Split text into non-table lines and one (key, body) pair per table."""
    lines: list[str] = []
    tables: list[tuple[str, str]] = []
    pos = 0
    while (match := _TABLE_LINE.search(text, pos)) is not None:
        lines.extend(text[pos : match.start()].splitlines())
        end = _TABLE_END.search(text, match.end())
        pos = end.start() + 1 if end else len(text)
        tables.append((match[1], text[match.end() : pos]))
    lines.extend(text[pos:].splitlines())
    return lines, tables


def _detect_decimal_comma(lines: list[str]) -> bool:
    values: list[str] = []
    for line in lines:
        fields = line.split("\t")
        if len(fields) > 2 and fields[1] in ("QUANT", "POTEN"):
            values.append(fields[2])
        elif len(fields) > 4 and fields[1] == "TWOPARAM":
            values.extend(fields[3:5])
    return any(_COMMA_NUMBER.fullmatch(value) for value in values)


def _parse_header(lines: list[str], decimal_comma: bool) -> dict[str, HeaderValue]:
    def number(value: str) -> float:
        return float(value.replace(",", ".") if decimal_comma else value)

    header: dict[str, HeaderValue] = {}
    rows = iter(lines)
    for line in rows:
        fields = line.split("\t")
        if len(fields) < 2 or not fields[0]:
            continue
        key, kind = fields[0], fields[1]
        if key == "TAG":
            header[key] = kind
            continue
        value = fields[2] if len(fields) > 2 else ""
        try:
            match kind:
                case "QUANT" | "POTEN":
                    header[key] = number(value)
                case "IQUANT" | "SELECTOR":
                    parsed = number(value)
                    header[key] = int(parsed) if parsed.is_integer() else parsed
                case "TOGGLE":
                    header[key] = value == "T"
                case "TWOPARAM":
                    header[key] = TwoParam(enable=value == "T", start=number(fields[3]), finish=number(fields[4]))
                case "NOTES":
                    header[key] = "\n".join(next(rows, "").strip() for _ in range(int(value)))
                case _:
                    header[key] = value
        except (ValueError, IndexError):
            header[key] = value
    return header
