# Changelog

Notable changes to gamry-parser, newest first. The project follows [Semantic Versioning](https://semver.org/).

## [1.1.0] - 2026-10-09

### Added
- `CyclicChargeDischarge` reads the summary file of a PWR800 cyclic charge-discharge run, whose data sit in a
  `CAPACITYCURVE` table. Based on [#52](https://github.com/bcliang/gamry-parser/pull/52) by @bpbrown.
- `ChargeDischarge` reads the raw charge and discharge step files from the same run.
- `CyclicChargeDischarge.efficiency()` returns the coulombic and energy efficiency of each cycle as fractions.

### Fixed
- `TOGGLE` header fields written as `TRUE` or `FALSE` load as booleans; `TRUE` used to load as `False`.
- `VARIABLEANDUNITS` and `MULTIPARAM` header fields load as `VariableAndUnits` and `MultiParam` dataclasses. They
  used to load as a string holding only their first value.
- `curve(timestamps=True)` works on `CyclicChargeDischarge` summaries, converting their `Time` column.

## [1.0.0] - 2026-09-26 [#51](https://github.com/bcliang/gamry-parser/pull/51)

A rewrite. The 0.x API is gone; see the README's migration table.

### Changed
- Breaking: `gamry_parser.read(path)` replaces `GamryParser(...).load()` and returns a read-only `Experiment`
  subclass chosen by the file's TAG. 0.x constructors raise `TypeError`.
- Breaking: curves are polars DataFrames instead of pandas, with `Pt` as a column. Install `gamry-parser[pandas]`
  for `to_pandas()`.
- Breaking: requires Python 3.12 or newer.
- Column dtypes follow the units line, and header values are typed (`TWOPARAM` fields are `TwoParam` dataclasses).
- Malformed files raise `GamryParseError` instead of `AssertionError` or loading silently.
- Parsing is about 12 times faster on large files.
- Packaging uses uv; CI runs ruff and the tests, and releases publish through PyPI trusted publishing.

### Fixed
- Decimal-comma files parse correctly under any process locale.
- VFP600 units line up with their columns.

## [0.4.6] - 2022-01-01

### Fixed
- [ed0c932](https://github.com/bcliang/gamry-parser/commit/ed0c93208f5a5ce3b62d5c619e3fd6aa34158b35) Fix: Static typing for class methods, resolve pandas futurewarning

### Added
- [#45](https://github.com/bcliang/gamry-parser/pull/45) Impl: support for Square Wave Voltammetry experiments

## [0.4.5] - 2021-05-07

### Changed
- [#40](https://github.com/bcliang/gamry-parser/pull/40) Change: GamryParser to_timestamp param
- [#41](https://github.com/bcliang/gamry-parser/pull/41) Use tox as test runner

### Added
- [#42](https://github.com/bcliang/gamry-parser/pull/42) Update read_header function to support EFM140 data Files
- [#43](https://github.com/bcliang/gamry-parser/pull/43) Add Examples: Peak Finding, Impedance

## [0.4.4] - 2021-02-28

### Fixed
- [#33](https://github.com/bcliang/gamry-parser/pull/33) Fix pycodestyle errors, make flake8 strict in CI workflow
- [#35](https://github.com/bcliang/gamry-parser/pull/35) Fix loading data from aborted experiments

### Added
- [#37](https://github.com/bcliang/gamry-parser/pull/37) Impl: Workflow for automated release deployment

## [0.4.3] - 2020-05-28

### Fixed
- [#30](https://github.com/bcliang/gamry-parser/pull/30) Include missing files in sdist

## [0.4.2] - 2020-05-20

### Added
- [#28](https://github.com/bcliang/gamry-parser/pull/28) Initial changelog file, update README, and rev version
- [#27](https://github.com/bcliang/gamry-parser/pull/27) Add support for VFP600 parsing
