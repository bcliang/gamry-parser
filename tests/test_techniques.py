from datetime import datetime

import pytest

import gamry_parser as gp

TECHNIQUES = [
    ("cv_data.dta", gp.CyclicVoltammetry),
    ("chronoa_data.dta", gp.ChronoAmperometry),
    ("eispot_data.dta", gp.Impedance),
    ("ocp_data.dta", gp.OpenCircuitPotential),
    ("squarewave_data.dta", gp.SquareWaveVoltammetry),
    ("vfp600_data.dta", gp.VFP600),
    ("ccd_data.dta", gp.CyclicChargeDischarge),
    ("ccd_charge_data.dta", gp.ChargeDischarge),
]


@pytest.mark.parametrize(("name", "cls"), TECHNIQUES)
def test_read_dispatches_on_tag(data_dir, name, cls):
    assert type(gp.read(data_dir / name)) is cls
    assert type(cls.read(data_dir / name)) is cls


def test_subclass_read_rejects_other_tags(data_dir):
    with pytest.raises(gp.GamryParseError, match=r"cv_data\.dta: expected TAG SQUARE_WAVE, found 'CV'"):
        gp.SquareWaveVoltammetry.read(data_dir / "cv_data.dta")


def test_subclass_without_tags_names_the_missing_tags(data_dir):
    class Unregistered(gp.Experiment):
        pass

    with pytest.raises(gp.GamryParseError, match=r"cv_data\.dta: Unregistered has no TAGS; found TAG 'CV'"):
        Unregistered.read(data_dir / "cv_data.dta")


def test_user_subclasses_do_not_replace_dispatch(data_dir):
    class MyCV(gp.CyclicVoltammetry):
        pass

    assert type(gp.read(data_dir / "cv_data.dta")) is gp.CyclicVoltammetry
    assert type(MyCV.read(data_dir / "cv_data.dta")) is MyCV


def test_sample_count_counts_rows_across_curves(data_dir):
    assert gp.read(data_dir / "cv_data.dta").sample_count == 50
    assert gp.read(data_dir / "eispot_data.dta").sample_count == 10


@pytest.mark.parametrize("cls", [cls for _, cls in TECHNIQUES])
def test_0x_constructors_raise(cls):
    with pytest.raises(TypeError, match=rf"{cls.__name__}\(filename=\.\.\.\)\.load\(\) was removed"):
        cls(filename="x.dta")
    with pytest.raises(TypeError, match=r"removed in gamry-parser 1\.0"):
        cls()


def test_cyclic_voltammetry(data_dir):
    cv = gp.read(data_dir / "cv_data.dta")
    assert cv.v_range == (0.1, 0.9)
    assert cv.scan_rate == 1.23456
    assert cv.curve(1).columns == ["Vf", "Im"]
    assert cv.curve_count == 5


def test_cyclic_voltammetry_requires_units(tmp_path):
    path = tmp_path / "cv.dta"
    path.write_text("EXPLAIN\nTAG\tCV\nCURVE1\tTABLE\n\tPt\tVf\tIm\n\t#\tV\tA\n\t0\t0.5\t1e-9\n")
    with pytest.raises(gp.GamryParseError, match=r"column Vf has unit 'V', expected 'V vs\. Ref\.'"):
        gp.read(path)


def test_missing_technique_columns_raise(tmp_path):
    path = tmp_path / "cv.dta"
    path.write_text("EXPLAIN\nTAG\tCV\nCURVE1\tTABLE\n\tPt\tVf\n\t#\tV vs. Ref.\n\t0\t0.5\n")
    with pytest.raises(gp.GamryParseError, match=r"cv\.dta: curve 0 has no Im column"):
        gp.read(path).curve()


def test_chronoamperometry(data_dir):
    ca = gp.read(data_dir / "chronoa_data.dta")
    assert ca.curve().columns == ["T", "Vf", "Im"]
    assert ca.sample_time == 30
    assert ca.sample_count == 10


def test_impedance(data_dir):
    z = gp.read(data_dir / "eispot_data.dta")
    curve = z.curve()
    assert curve.columns == ["Freq", "Zreal", "Zimag", "Zmod", "Zphz"]
    assert curve.height == 10
    assert curve["Freq"][-1] == 0.5
    assert z.units["Zphz"] == "°"


def test_open_circuit_potential(data_dir):
    ocp = gp.read(data_dir / "ocp_data.dta")
    curve = ocp.curve()
    assert curve.columns == ["T", "Vf"]
    assert curve.shape == (21, 2)
    assert curve["T"][0] == 5.00833
    assert curve["T"][-1] == 105.175
    assert curve["Vf"][0] == 0.0205436
    assert curve["Vf"][-1] == 0.0345678
    assert ocp.ocv_curve is not None
    assert ocp.ocv_curve.equals(ocp.curves[0])


def test_square_wave_voltammetry(data_dir):
    swv = gp.read(data_dir / "squarewave_data.dta")
    assert swv.v_range == (0, -0.5)
    assert swv.step_size == 2
    assert swv.frequency == 100
    assert swv.pulse_size == 25
    assert swv.pulse_width == 0.01
    assert swv.cycles == 251
    assert swv.curve_count == 1
    curve = swv.curve()
    assert curve.columns == ["T", "Vfwd", "Vrev", "Vstep", "Ifwd", "Irev", "Idif"]
    assert curve.shape == (10, 7)
    assert curve["T"][0] == 0.01
    assert swv.curve(timestamps=True)["T"][0] == datetime(2021, 12, 31, 12, 0, 0, 10000)


def test_vfp600(data_dir):
    vfp = gp.read(data_dir / "vfp600_data.dta")
    assert vfp.experiment_type == "VFP600"
    assert vfp.sample_time == 1 / 15
    assert vfp.sample_count == 20
    curve = vfp.curve()
    assert curve.columns == ["T", "Voltage", "Current"]
    assert curve["T"][0] == 0
    assert round(curve["T"][-1] * 100) == 127
    assert curve["Voltage"][-1] == 0.033333
    assert round(curve["Current"][-1] * 1e13) == 5125


def test_cyclic_charge_discharge(data_dir):
    ccd = gp.read(data_dir / "ccd_data.dta")
    assert ccd.experiment_type == "PWR800_CYCLICCHARGEDISCHARGE"
    assert ccd.cycles == 50
    assert ccd.capacity == 1
    assert ccd.charge_current == 1.25
    assert ccd.sample_time == 5
    assert ccd.stop_reason == "Cycle Limit"
    assert ccd.curve_count == 1
    curve = ccd.curve()
    assert curve.columns == ["Time", "Type", "Cycle", "Charge", "Duration", "Vstart", "Vend", "Energy"]
    assert curve.shape == (100, 8)
    assert curve.row(0) == (3493, 0, 1, 4362.108, 3492.657, 0.7937095, 1.206959, 3962.024)
    assert curve.row(-1) == (284885, 1, 50, 3114.31, 2488.698, 0.7620814, 0.3999423, -2055.479)
    assert curve["Type"].value_counts(sort=True)["count"].to_list() == [50, 50]
    assert ccd.units["Charge"] == "C"
    assert ccd.units["Energy"] == "J"


def test_charge_discharge(data_dir):
    step = gp.read(data_dir / "ccd_charge_data.dta")
    assert step.experiment_type == "PWR800_CHARGE"
    assert step.capacity == 10
    assert step.sample_time == 0.1
    assert step.start_time_offset == 16.83167
    assert step.header["SEQUENCER"] is True
    curve = step.curve()
    assert curve.columns == ["T", "Vf", "Im"]
    assert curve.shape == (66, 3)
    assert curve.row(0) == (0.1, -0.289835, 0.0200063)
    assert curve["T"][-1] == 6.56833
    assert step.curve(timestamps=True)["T"][0] == datetime(2015, 11, 12, 11, 16, 43, 100000)


def test_vfp600_without_freq_has_null_time(tmp_path):
    path = tmp_path / "vfp.dta"
    path.write_text("VFP600\nTAG\tVFP600\nVFPCURVE\tTABLE\n\tVoltage\tCurrent\n\tV\tA\n\t0.1\t1e-10\n")
    assert gp.read(path).curve()["T"].to_list() == [None]


@pytest.mark.parametrize(
    ("tag", "properties"),
    [
        ("CV", ["v_range", "scan_rate"]),
        ("CHRONOA", ["sample_time"]),
        ("SQUARE_WAVE", ["step_size", "pulse_size", "pulse_width", "frequency", "v_range", "cycles"]),
        ("VFP600", ["sample_time"]),
        ("PWR800_CYCLICCHARGEDISCHARGE", ["cycles", "capacity", "charge_current", "sample_time", "stop_reason"]),
        ("PWR800_CHARGE", ["capacity", "sample_time", "start_time_offset"]),
        ("PWR800_DISCHARGE", ["capacity", "sample_time", "start_time_offset"]),
    ],
)
def test_properties_are_none_when_header_keys_are_missing(tmp_path, tag, properties):
    path = tmp_path / "header_only.dta"
    path.write_text(f"EXPLAIN\nTAG\t{tag}\n")
    exp = gp.read(path)
    assert {name: getattr(exp, name) for name in properties} == dict.fromkeys(properties)
