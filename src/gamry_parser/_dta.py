"""Parse the contents of Gamry EXPLAIN (DTA) files."""

import re
from dataclasses import dataclass

import polars as pl


class GamryParseError(ValueError):
    """Raised when a DTA file cannot be parsed."""


@dataclass(frozen=True, slots=True)
class TwoParam:
    """A TWOPARAM header value: an on/off flag with two numbers, e.g. conditioning time and potential."""

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
_DOT_NUMBER = re.compile(r"[-+]?\d+\.\d+(?:[eE][-+]?\d+)?")
_UNIT_DTYPES: dict[str, type[pl.DataType]] = {"#": pl.Int64, "bits": pl.String}


def parse(data: bytes, decimal_comma: bool | None = None) -> ParsedFile:
    """Parse the bytes of a DTA file. `decimal_comma=None` detects the decimal separator."""
    lines, tables = _split(_decode(data).replace("\r\n", "\n").replace("\r", "\n"))
    if decimal_comma is None:
        decimal_comma = _detect_decimal_comma(lines, tables)
    header = _parse_header(lines, decimal_comma)
    units: dict[str, str] = {}
    curves: list[pl.DataFrame] = []
    ocv_curve = None
    for key, body in tables:
        if key != "OCVCURVE" and not _CURVE_KEY.search(key):
            continue
        table, table_units = _read_table(body, decimal_comma)
        if not table_units:
            continue
        if key == "OCVCURVE":
            ocv_curve = table
        elif not curves or table_units == units:
            units = table_units
            curves.append(table)
        else:
            raise GamryParseError(f"{key}: units {table_units} differ from the first curve's units {units}")
    return ParsedFile(header=header, units=units, curves=tuple(curves), ocv_curve=ocv_curve)


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
        lines.extend(text[pos : match.start()].split("\n"))
        end = _TABLE_END.search(text, match.end() - 1)
        pos = end.start() + 1 if end else len(text)
        tables.append((match[1], text[match.end() : pos]))
    lines.extend(text[pos:].split("\n"))
    return lines, tables


def _detect_decimal_comma(lines: list[str], tables: list[tuple[str, str]]) -> bool:
    values: list[str] = []
    for line in lines:
        fields = line.split("\t")
        if len(fields) > 2 and fields[1] in ("QUANT", "POTEN"):
            values.append(fields[2])
        elif len(fields) > 4 and fields[1] == "TWOPARAM":
            values.extend(fields[3:5])
    if any(_COMMA_NUMBER.fullmatch(value) for value in values):
        return True
    if any(_DOT_NUMBER.fullmatch(value) for value in values):
        return False
    return any(_COMMA_NUMBER.fullmatch(value) for value in _first_row(tables).split("\t"))


def _first_row(tables: list[tuple[str, str]]) -> str:
    for key, body in tables:
        if _CURVE_KEY.search(key):
            rows = body.split("\n", 3)
            return rows[2] if len(rows) > 2 else ""
    return ""


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


def _read_table(body: str, decimal_comma: bool) -> tuple[pl.DataFrame, dict[str, str]]:
    """Read a table body (column names, units, rows) into a frame and a column-to-unit map."""
    names_line, units_line, rows = [*body.split("\n", 2), "", ""][:3]
    names = names_line.rstrip("\t").split("\t")[1:]
    if "" in names:
        raise GamryParseError("empty column name in table")
    if len(set(names)) != len(names):
        raise GamryParseError(f"duplicate column {next(name for name in names if names.count(name) > 1)!r}")
    units = dict(zip(names, units_line.split("\t")[1:], strict=False))
    schema = {"": pl.String} | {name: _UNIT_DTYPES.get(units.get(name, ""), pl.Float64) for name in names}
    if not rows.strip():
        return pl.DataFrame(schema=schema).drop(""), units
    frame = pl.read_csv(
        rows.encode(),
        separator="\t",
        has_header=False,
        quote_char=None,
        decimal_comma=decimal_comma,
        truncate_ragged_lines=True,
        schema=schema,
        ignore_errors=True,
    )
    return frame.drop(""), units
