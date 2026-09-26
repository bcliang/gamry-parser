import copy
import dataclasses
import locale
import pickle
from datetime import datetime
from pathlib import Path

import pandas as pd
import polars as pl
import pytest

import gamry_parser as gp


def write(tmp_path: Path, text: str) -> Path:
    path = tmp_path / "experiment.dta"
    path.write_text(text)
    return path


def test_unknown_tag_returns_experiment(tmp_path):
    exp = gp.read(write(tmp_path, "EXPLAIN\nTAG\tMYSTERY\n"))
    assert type(exp) is gp.Experiment
    assert exp.experiment_type == "MYSTERY"
    assert exp.curves == ()
    assert exp.curve_count == 0


def test_read_accepts_str_paths(data_dir):
    exp = gp.read(str(data_dir / "cv_data.dta"))
    assert exp.path == data_dir / "cv_data.dta"
    assert exp.curve_count == 5


def test_missing_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        gp.read(tmp_path / "missing.dta")


@pytest.mark.parametrize("text", ["", "MIT License\n\nCopyright (c) 2019\n", "a,b\n1,2\n"])
def test_file_without_a_tag_raises(tmp_path, text):
    with pytest.raises(gp.GamryParseError, match=r"experiment\.dta: no TAG header; not a Gamry DTA file"):
        gp.read(write(tmp_path, text))


def test_base_experiment_curve_returns_all_columns(tmp_path):
    exp = gp.read(write(tmp_path, "EXPLAIN\nTAG\tMYSTERY\nCURVE\tTABLE\n\tPt\tT\tVf\n\t#\ts\tV\n\t0\t0.5\t1.5\n"))
    assert exp.curve().columns == ["Pt", "T", "Vf"]
    assert exp.curve().equals(exp.curves[0])


def test_curve_index_out_of_range(data_dir):
    exp = gp.read(data_dir / "cv_data.dta")
    assert exp.curve(-1).equals(exp.curve(4))
    with pytest.raises(IndexError, match=r"curve 5 out of range; cv_data\.dta has 5 curves"):
        exp.curve(5)


def test_header_only_file_has_no_curves(data_dir):
    exp = gp.read(data_dir / "cv_data_incompleteheader.dta")
    assert exp.curve_count == 0
    with pytest.raises(IndexError, match=r"cv_data_incompleteheader\.dta has 0 curves"):
        exp.curve()


def test_ocv_and_ocv_curve(data_dir):
    exp = gp.read(data_dir / "cv_data.dta")
    assert exp.ocv is None
    assert exp.ocv_curve is None
    exp = gp.read(data_dir / "ocvcurve_data.dta")
    assert exp.ocv == 0.2834373
    assert exp.ocv_curve is not None
    assert exp.ocv_curve["T"][-1] == 10.3333


def test_timestamps(data_dir):
    exp = gp.read(data_dir / "chronoa_data.dta")
    assert exp.curve()["T"][0] == 0
    assert exp.curve()["T"][-1] == 270
    stamped = exp.curve(timestamps=True)
    assert stamped["T"].dtype == pl.Datetime("us")
    assert stamped["T"][0] == datetime(2019, 3, 10, 12, 0, 0)
    assert stamped["T"][-1] == datetime(2019, 3, 10, 12, 4, 30)


def test_timestamps_keep_fractional_seconds(data_dir):
    stamped = gp.read(data_dir / "ocp_data.dta").curve(timestamps=True)
    assert stamped["T"][0] == datetime(2020, 2, 10, 17, 18, 5, 8330)
    assert stamped["T"][-1] == datetime(2020, 2, 10, 17, 19, 45, 175000)


def test_timestamps_need_date_and_time(tmp_path):
    exp = gp.read(write(tmp_path, "EXPLAIN\nTAG\tMYSTERY\nCURVE\tTABLE\n\tPt\tT\n\t#\ts\n\t0\t0.5\n"))
    assert exp.start_time is None
    with pytest.raises(gp.GamryParseError, match="no DATE/TIME"):
        exp.curve(timestamps=True)


def test_timestamps_need_a_t_column(data_dir):
    with pytest.raises(gp.GamryParseError, match="no T column"):
        gp.read(data_dir / "eispot_data.dta").curve(timestamps=True)


def test_timestamps_need_a_numeric_t_column(tmp_path):
    text = "EXPLAIN\nTAG\tMYSTERY\nDATE\tLABEL\t3/6/2019\tDate\nTIME\tLABEL\t12:00:00\tTime\n"
    exp = gp.read(write(tmp_path, text + "CURVE\tTABLE\n\tPt\tT\n\t#\ts\n\t0\tabc\n"))
    with pytest.raises(gp.GamryParseError, match="T column is not numeric"):
        exp.curve(timestamps=True)


@pytest.mark.parametrize(
    ("date", "time", "expected"),
    [
        ("3/6/2019", "16:35:22", datetime(2019, 3, 6, 16, 35, 22)),
        ("10-2-2020", "17:18:00", datetime(2020, 2, 10, 17, 18)),
        ("10.2.2020", "17:18:00", datetime(2020, 2, 10, 17, 18)),
        ("2021-12-31", "12:00:00", datetime(2021, 12, 31, 12)),
        ("2021/12/31", "12:00:00", datetime(2021, 12, 31, 12)),
        ("3/6/2019", "4:35:22 PM", datetime(2019, 3, 6, 16, 35, 22)),
        ("25/3/2019", "17:18:00", datetime(2019, 3, 25, 17, 18)),
        ("3-25-2019", "17:18:00", datetime(2019, 3, 25, 17, 18)),
        ("3/6/19", "12:00:00", datetime(2019, 3, 6, 12)),
        ("3/6/99", "12:00:00", datetime(1999, 3, 6, 12)),
    ],
)
def test_start_time_formats(tmp_path, date, time, expected):
    exp = gp.read(write(tmp_path, f"EXPLAIN\nTAG\tMYSTERY\nDATE\tLABEL\t{date}\tDate\nTIME\tLABEL\t{time}\tTime\n"))
    assert exp.start_time == expected


@pytest.mark.parametrize("name", ["de_DE.UTF-8", "zh_CN.UTF-8"])
def test_12_hour_time_ignores_the_process_locale(tmp_path, name):
    path = write(tmp_path, "EXPLAIN\nTAG\tMYSTERY\nDATE\tLABEL\t3/6/2019\tDate\nTIME\tLABEL\t4:35:22 PM\tTime\n")
    previous = locale.setlocale(locale.LC_ALL)
    try:
        locale.setlocale(locale.LC_ALL, name)
    except locale.Error:
        pytest.skip(f"locale {name} is not installed")
    try:
        start = gp.read(path).start_time
    finally:
        locale.setlocale(locale.LC_ALL, previous)
    assert start == datetime(2019, 3, 6, 16, 35, 22)


def test_unparseable_date_raises_on_access(tmp_path):
    exp = gp.read(
        write(tmp_path, "EXPLAIN\nTAG\tMYSTERY\nDATE\tLABEL\t31/31/2019\tDate\nTIME\tLABEL\t12:00:00\tTime\n")
    )
    with pytest.raises(gp.GamryParseError, match="cannot parse DATE '31/31/2019'"):
        _ = exp.start_time


def test_decimal_comma_override(data_dir):
    exp = gp.read(data_dir / "chronoa_de_data.dta", decimal_comma=True)
    assert exp.curves[0]["Vf"][0] == -5e-4


@pytest.mark.parametrize("name", ["de_DE.UTF-8", "en_US.UTF-8"])
def test_parsing_ignores_the_process_locale(data_dir, name):
    previous = locale.setlocale(locale.LC_ALL)
    try:
        locale.setlocale(locale.LC_ALL, name)
    except locale.Error:
        pytest.skip(f"locale {name} is not installed")
    try:
        curve = gp.read(data_dir / "chronoa_de_data.dta").curves[0]
    finally:
        locale.setlocale(locale.LC_ALL, previous)
    assert curve["Vf"][0] == -5e-4
    assert curve["Vf"][-1] == 0.4
    assert curve["Im"][0] == -2e-8


def test_experiment_is_immutable(data_dir):
    exp = gp.read(data_dir / "cv_data.dta")
    with pytest.raises(dataclasses.FrozenInstanceError):
        exp.header = {}


def test_header_and_units_are_read_only(data_dir):
    exp = gp.read(data_dir / "cv_data.dta")
    with pytest.raises(TypeError):
        exp.header["TAG"] = "EISPOT"
    with pytest.raises(TypeError):
        exp.units["Vf"] = "mV"
    assert exp.header["TAG"] == "CV"
    assert exp.units["Vf"] == "V vs. Ref."


def test_replace_keeps_header_read_only(data_dir):
    exp = dataclasses.replace(gp.read(data_dir / "cv_data.dta"), header={"TAG": "CV", "SCANRATE": 2.0})
    assert exp.scan_rate == 2.0
    with pytest.raises(TypeError):
        exp.header["SCANRATE"] = 3.0


def test_experiment_survives_pickle_and_copy(data_dir):
    exp = gp.read(data_dir / "ocvcurve_data.dta")
    for clone in (pickle.loads(pickle.dumps(exp)), copy.deepcopy(exp), copy.copy(exp)):
        assert type(clone) is type(exp)
        assert clone.header == exp.header
        assert clone.curves[0].equals(exp.curves[0])
        with pytest.raises(TypeError):
            clone.header["TAG"] = "EISPOT"


def test_curves_convert_to_pandas(data_dir):
    frame = gp.read(data_dir / "cv_data.dta").curves[0].to_pandas()
    assert isinstance(frame, pd.DataFrame)
    assert frame["Pt"].tolist() == list(range(10))


@pytest.mark.parametrize(
    "call",
    [
        lambda: gp.GamryParser(),
        lambda: gp.GamryParser(filename="x.dta", to_timestamp=True),
        lambda: gp.Experiment(),
        lambda: gp.Experiment("x.dta"),
        lambda: gp.Experiment(filename="x.dta"),
    ],
)
def test_removed_api_raises(call):
    with pytest.raises(TypeError, match=r"removed in gamry-parser 1\.0; use gamry_parser\.read\(path\)"):
        call()


def test_unrecognised_time_raises_on_access(tmp_path):
    exp = gp.read(write(tmp_path, "EXPLAIN\nTAG\tMYSTERY\nDATE\tLABEL\t3/6/2019\tDate\nTIME\tLABEL\tnoon\tTime\n"))
    with pytest.raises(gp.GamryParseError, match="TIME 'noon'"):
        _ = exp.start_time
