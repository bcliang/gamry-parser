# Change Log for gamry-parser
All notable changes to this project will be documented in this file.
This project adheres to [Semantic Versioning](http://semver.org/).

## [1.0.0] - Unreleased

### Changed
- Breaking: `gamry_parser.read(path)` replaces `GamryParser(...).load()`. It returns an immutable `Experiment` subclass
  chosen by the file's TAG. 0.x constructors raise `TypeError`.
- Breaking: curves are polars DataFrames and `Pt` is a column. Install `gamry-parser[pandas]` to use `to_pandas()`.
- Breaking: requires Python 3.12 or newer.
- `to_timestamp` is replaced by `curve(i, timestamps=True)`; `start_time` gives the experiment start.
- Measured columns are Float64, `#` columns (Pt, IERange) are Int64, and `IQUANT`/`SELECTOR` header values are `int`
  when integral.
- Errors are `GamryParseError`, `IndexError` or `FileNotFoundError` instead of `AssertionError`.
- Packaging uses uv and `uv_build`; CI runs ruff and publishes with PyPI trusted publishing.
- Parsing is about 12 times faster on large files (1M-row CV file: 5.0 s with 0.4.6, 0.42 s with 1.0).

### Fixed
- Files written with a decimal comma parse correctly under any process locale.
- VFP600 units line up with their columns.
- Non-UTF-8 characters such as `°` are decoded as cp1252 instead of dropped.

### Added
- Header fields after the curve tables (e.g. `EXPERIMENTABORTED`) and header fields of unknown type are kept.
- An empty curve table is returned as an empty curve instead of ending the file.

## [0.4.6] - 2022-01-01

### Fixed
- [ed0c932](https://github.com/bcliang/gamry-parser/commit/ed0c93208f5a5ce3b62d5c619e3fd6aa34158b35) Fix: Static typing for class methods, resolve pandas futurewarning

### Changed
- 

### Added
- [#45](https://github.com/bcliang/gamry-parser/pull/45) Impl: support for Square Wave Voltammetry experiments

## [0.4.5] - 2021-05-07

### Fixed
- 

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

### Changed
- 

### Added
- [#37](https://github.com/bcliang/gamry-parser/pull/37) Impl: Workflow for automated release deployment

## [0.4.3] - 2020-05-28

### Fixed
- [#30](https://github.com/bcliang/gamry-parser/pull/30) Include missing files in sdist

## [0.4.2] - 2020-05-20

### Added
- [#28](https://github.com/bcliang/gamry-parser/pull/28) Initial changelog file, update README, and rev version
- [#27](https://github.com/bcliang/gamry-parser/pull/27) Add support for VFP600 parsing
