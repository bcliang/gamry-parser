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
    assert z.units["Zphz"] == "\N{DEGREE SIGN}"


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
    ],
)
def test_properties_are_none_when_header_keys_are_missing(tmp_path, tag, properties):
    path = tmp_path / "header_only.dta"
    path.write_text(f"EXPLAIN\nTAG\t{tag}\n")
    exp = gp.read(path)
    assert {name: getattr(exp, name) for name in properties} == dict.fromkeys(properties)
