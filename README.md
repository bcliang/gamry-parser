# gamry-parser

[![PyPI](https://img.shields.io/pypi/v/gamry-parser.svg)](https://pypi.org/project/gamry-parser/)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/gamry-parser.svg)
[![PyPI - License](https://img.shields.io/pypi/l/gamry-parser.svg)](./LICENSE)

Python package for parsing the contents of Gamry EXPLAIN data (DTA) files. This package is meant to convert flat-file EXPLAIN data into pandas DataFrames for easy analysis and visualization.

## Getting Started

### Dependencies

* pandas

### Installation

#### Package from PyPi

```bash
$ pip install gamry-parser
```

#### Local Installation

1. Check out the latest code:
```bash
$ git clone git@github.com:bcliang/gamry-parser.git
```
2. Use setuptools to install the package
```bash
$ python setup.py install
```

### Usage

The provided Usage example loads a CV DTA file two ways, and demonstrates the utility of custom functions within the CyclicVoltammetry subclass (`get_v_range`, `get_scan_rate`)

```bash
$ python usage.py
```

#### GamryParser Example

The following snippet loads a DTA file and prints to screen: (1) experiment type, (2) # of curves, and (3) a random curve in the form of a pandas DataFrame.

```python
import gamry_parser as parser
import random

file = '/enter/the/file/path.dta'
gp = parser.GamryParser()
gp.load(filename=file)

print("experiment type: {}".format(gp.get_experiment_type()))
print("loaded curves: {}".format(gp.get_curve_count()))

curve_index = random.randint(1,gp.get_curve_count())
print("showing curve #{}".format(curve_index))
print(gp.get_curve_data(curve_index))
```

#### ChronoAmperometry Example

The `ChronoAmperometry` class is a subclass of `GamryParser`. Executing the method `get_curve_data()` will return a DataFrame with three columns: (1) `T`, (2) `Vf`, and (3) `Im`

In the example, the file is expected to be a simple chronoamperometry experiment (single step, no preconditioning); there will only be a single curve of data contained within the file. In addition, note the use of the `to_timestamp` property, which allows the user to request `get_curve_data` to return a DataFrame with a `T` column containing DateTime objects (as opposed to the default: float seconds since start).

```python
import gamry_parser as parser
import random

file = '/enter/the/file/path.dta'
ca = parser.ChronoAmperometry(to_timestamp=True)
ca.load(filename=file)
print(ca.get_curve_data())
```

#### Demos

ipython notebook demonstration scripts are included in the `demo` folder.

- `notebook_gamry_parser.ipynb`: Simple example loading data from ChronoA experiment output. Instead of `gamry_parser.GamryParser()`, the parser could be instantiated with `gamry_parser.ChronoAmperometry()`
- `notebook_cyclicvoltammetry.ipynb`: Example loading data from a CV (cyclic voltammetry) experiment output. Uses the `gamry_parser.CyclicVoltammetry()` subclass.

#### Additional Examples

Similar procedure should be followed for using the `gamry_parser.CyclicVoltammetry()`, `gamry_parser.Impedance()`, and `gamry_parser.OpenCircuitPotential()` parser subclasses. Take a look at `usage.py` and in `tests/` for some additional usage examples.

## Development

### Project Tree
```
  .
  ├── gamry_parser              # source files
  │   ├── ...          
  │   ├── chronoa.py            # ChronoAmperometry() experiment parser
  │   ├── cv.py                 # CyclicVoltammetry() experiment parser
  │   ├── eispot.py             # Impedance() experiment parser
  │   └── ocp.py                # OpenCircuitPotential() experiment parser
  |   └── gamryparser.py        # GamryParser: generic DTA file parser
  ├── tests                     # unit tests and test data
  |   └── ...
  ├── setup.py                  # setuptools configuration
  └── ...                
```

### Roadmap

Documentation! Loading of data is straightforward, and hopefully the examples provided in this README provide enough context for any of the subclasses to be used/extended.

In the future, it would be nice to add support for things like equivalent circuit modeling, though at the moment there are other projects focused specifically on building out models and fitting EIS data (e.g. [kbknudsen/PyEIS](https://github.com/kbknudsen/PyEIS), [ECSHackWeek/impedance.py](https://github.com/ECSHackWeek/impedance.py)).

### Tests

Tests extending `unittest.TestCase` may be found in `/tests/`.

```bash
$ python setup.py test
$ coverage run --source=gamry_parser/ setup.py test
$ coverage report -m
```

Latest output:

```bash
$ coverage report -m
Name                          Stmts   Miss  Cover   Missing
-----------------------------------------------------------
gamry_parser/__init__.py          6      0   100%
gamry_parser/chronoa.py          23      0   100%
gamry_parser/cv.py               17      0   100%
gamry_parser/eispot.py            6      0   100%
gamry_parser/gamryparser.py     146      3    98%   132, 225-226
gamry_parser/ocp.py              32      0   100%
gamry_parser/version.py           1      0   100%
-----------------------------------------------------------
TOTAL                           231      3    99%
```

### Code Guidelines

* PEP8 via `pylint` or `flake8`
* [GitHub flow](https://guides.github.com/introduction/flow/) for proposing changes (i.e. create a feature branch and submit a PR against the master branch).
* Tests: Maintain > 80% line coverage, per file

### Versioning

[SemVer](http://semver.org/) for versioning.
1. Matching major version numbers are guaranteed to work together.
2. Any change to the public API (breaking change) will increase a major version.

### Publishing

Use setuptools to build, twine to publish to pypi.

```bash
$ rm -rf dist
$ python setup.py build
$ python setup.py sdist bdist_wheel
$ twine upload dist/*
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details
