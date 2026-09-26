# Changelog

Notable changes to gamry-parser, newest first. The project follows [Semantic Versioning](https://semver.org/).

## [1.0.0] - 2026-09-26 [#51](https://github.com/bcliang/gamry-parser/pull/51)

### Changed
- Breaking: `gamry_parser.read(path)` replaces `GamryParser(...).load()`. It returns an immutable `Experiment` subclass
  chosen by the file's TAG. 0.x constructors raise `TypeError`.
- Breaking: curves are polars DataFrames and `Pt` is a column. Install `gamry-parser[pandas]` to use `to_pandas()`.
- Breaking: requires Python 3.12 or newer.
- `curve(i, timestamps=True)` replaces `to_timestamp`; `start_time` gives the experiment's start.
- Measured columns are Float64, `#` columns (Pt, IERange) are Int64, and `IQUANT`/`SELECTOR` header values are `int`
  when integral.
- `TWOPARAM` header values are frozen `TwoParam` records (`.enable`, `.start`, `.finish`) instead of dicts.
- Errors are `GamryParseError`, `IndexError` or `FileNotFoundError` instead of `AssertionError`.
- `read()` raises `GamryParseError` for a file without a `TAG` header instead of returning an empty result.
- Column dtypes follow the units line: a cell that does not parse in a numeric column becomes null. A table with a
  repeated or empty column name raises `GamryParseError`.
- `header` and `units` are read-only mappings; use `dataclasses.asdict(exp)` for plain dicts.
- A user subclass replaces the built-in class in `read()` dispatch only if it declares its own `TAGS`.
- Packaging uses uv and `uv_build`; CI runs ruff and publishes with PyPI trusted publishing.
- Parsing is about 12 times faster on large files (1M-row CV file: 5.0 s with 0.4.6, 0.42 s with 1.0).

### Fixed
- Files written with a decimal comma parse correctly under any process locale.
- VFP600 units line up with their columns.
- Files that are not valid UTF-8 are read as cp1252, so characters such as the degree sign are kept instead of dropped.

### Added
- `sample_count` on every experiment type, and `start_time` parsing of day-first and two-digit-year dates.
- Header fields after the curve tables (e.g. `EXPERIMENTABORTED`) and header fields of unknown type are kept.
- An empty curve table becomes an empty curve instead of ending the read.

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
