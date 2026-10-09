# gamry-parser

Parse Gamry EXPLAIN (DTA) files into [polars](https://pola.rs) DataFrames.

Version 1.0 replaces the 0.x API: `gp.read(path)` replaces `GamryParser(...).load()`, and curves are polars
DataFrames instead of pandas. See [Migrating from 0.x](#migrating-from-0x), or pin `gamry-parser<1` to keep the old API.

[![PyPI](https://img.shields.io/pypi/v/gamry-parser.svg)](https://pypi.org/project/gamry-parser/)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/gamry-parser.svg)
[![PyPI - License](https://img.shields.io/pypi/l/gamry-parser.svg)](./LICENSE)
[![Tests](https://github.com/bcliang/gamry-parser/actions/workflows/test.yml/badge.svg)](https://github.com/bcliang/gamry-parser/actions/workflows/test.yml)
[![Lint](https://github.com/bcliang/gamry-parser/actions/workflows/lint.yml/badge.svg)](https://github.com/bcliang/gamry-parser/actions/workflows/lint.yml)

## Installation

```bash
pip install gamry-parser
# or
uv add gamry-parser
```

gamry-parser 1.x requires Python 3.12 or newer. To convert curves to pandas, install the `pandas` extra:
`pip install "gamry-parser[pandas]"`.

## Usage

```python
import gamry_parser as gp

exp = gp.read("path/to/experiment.dta")
exp.experiment_type  # header TAG, e.g. "CV"
exp.header["DATE"]  # every header field, typed
exp.start_time  # datetime from DATE and TIME
exp.curve_count
exp.curve(0)  # polars DataFrame
exp.curves  # every curve with every column, including Pt
```

Header values are typed from the file's field types: `str`, `float`, `int`, `bool`, or a frozen dataclass for field types that hold several values. `TWOPARAM` fields such as `CONDIT` load as `TwoParam` (`enable`, `start`, `finish`), `VARIABLEANDUNITS` fields as `VariableAndUnits` (`value`, `unit`) and `MULTIPARAM` fields as `MultiParam` (`selection`, `value`, `option`, `unit`). `header` and `units` are read-only mappings; `json.dumps(exp.header, default=dataclasses.asdict)` serializes a header, and `TwoParam(**value)` rebuilds a field from the loaded JSON.

`read()` returns the class registered for the file's TAG:

| TAG | Class | `curve()` columns | Properties |
|---|---|---|---|
| `CV` | `CyclicVoltammetry` | Vf, Im | `v_range`, `scan_rate` |
| `CHRONOA` | `ChronoAmperometry` | T, Vf, Im | `sample_time` |
| `EISPOT` | `Impedance` | Freq, Zreal, Zimag, Zmod, Zphz | |
| `CORPOT` | `OpenCircuitPotential` | T, Vf | |
| `SQUARE_WAVE` | `SquareWaveVoltammetry` | T, Vfwd, Vrev, Vstep, Ifwd, Irev, Idif | `step_size`, `pulse_size`, `pulse_width`, `frequency`, `v_range`, `cycles` |
| `VFP600` | `VFP600` | T, Voltage, Current | `sample_time` |
| `PWR800_CYCLICCHARGEDISCHARGE` | `CyclicChargeDischarge` | Time, Type, Cycle, Charge, Duration, Vstart, Vend, Energy | `cycles`, `capacity`, `charge_current`, `sample_time`, `stop_reason`, `efficiency()` |
| `PWR800_CHARGE`, `PWR800_DISCHARGE` | `ChargeDischarge` | T, Vf, Im | `capacity`, `sample_time`, `start_time_offset` |
| anything else | `Experiment` | all columns | |

Every class also has `ocv` (the EOC header field), `ocv_curve` (the OCVCURVE table, if the file has one) and
`sample_count` (rows across all curves).
Properties return `None` when the header field is missing.

A cyclic charge-discharge (CCD) run in Gamry's PWR800 software writes a summary file with one row per step. In it, Type is `0` for a charge step and `1` for a discharge step. `efficiency()` pairs the two steps of each cycle by Cycle number and returns coulombic and energy efficiency as fractions, null for a cycle that lacks either step. The run can also save each step's raw curve as its own file, which loads as `ChargeDischarge`.

To require one experiment type, call `read` on its class. It raises `GamryParseError` for any other TAG:

```python
cv = gp.CyclicVoltammetry.read("cv.dta")
cv.scan_rate, cv.v_range
```

### Timestamps

`T` is seconds since the start of the experiment. `timestamps=True` converts it to datetimes using the DATE and TIME header fields. In a `CyclicChargeDischarge` summary the converted column is `Time`, the end of each step:

```python
gp.read("chronoa.dta").curve(timestamps=True)
```

### Decimal commas

`read()` detects files written with a decimal comma (`5,00000E-001`), whatever the locale of the machine reading them. To override detection, pass `decimal_comma=True` or `decimal_comma=False`.

### pandas

```python
df = exp.curve(0).to_pandas()  # needs gamry-parser[pandas]
```

### Errors

`read()` raises `FileNotFoundError` for a missing file and `GamryParseError` (a `ValueError`) for a file it cannot parse, including any file without a `TAG` header line. `curve(i)` raises `IndexError` when `i` is out of range.

## Migrating from 0.x

| 0.x | 1.x |
|---|---|
| `p = GamryParser(filename=f); p.load()` | `exp = gp.read(f)` |
| `CyclicVoltammetry(filename=f).load()` | `gp.CyclicVoltammetry.read(f)` |
| `to_timestamp=True` | `exp.curve(i, timestamps=True)` |
| `p.curve(i)` returns pandas with `Pt` as the index | `exp.curve(i)` returns polars; `Pt` is a column of `exp.curves[i]` |
| `p.curves` (list) | `exp.curves` (tuple) |
| `p.curve_indices`, `p.curve_numbers` | `range(exp.curve_count)` |
| `p.fname`, `p.loaded` | `exp.path` |
| `AssertionError` | `GamryParseError`, `IndexError`, `FileNotFoundError` |

Calling a 0.x constructor raises a `TypeError` that names `read()` as the replacement.

## Examples

`python usage.py` reads a cyclic voltammetry file. The notebooks in `demo/` cover chronoamperometry, cyclic voltammetry, CV peak detection, and EIS with an equivalent-circuit fit. They run in Jupyter or Google Colab:

```bash
uv run --group demo --with jupyterlab jupyter lab demo/
```

## Development

```bash
git clone git@github.com:bcliang/gamry-parser.git
cd gamry-parser
uv sync                  # create .venv with the dev dependencies
uv run pytest --cov
uvx ruff check
uvx ruff format
uv build                 # sdist and wheel in dist/
```

```
src/gamry_parser/
  _dta.py          file bytes -> header, units, curves
  experiment.py    Experiment and read()
  techniques.py    technique subclasses
tests/             pytest suite; fixtures in tests/data/
demo/              example notebooks
```

Propose changes as pull requests against `master`. CI runs ruff and the tests on Python 3.12 to 3.14, and the test run fails if total branch coverage drops below 90%.

## Related projects

For equivalent-circuit modeling of EIS data, see [impedance.py](https://github.com/ECSHackWeek/impedance.py) and [PyEIS](https://github.com/kbknudsen/PyEIS).

## Changelog

See [CHANGELOG.md](CHANGELOG.md).
