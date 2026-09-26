import polars as pl
import pytest

from gamry_parser._dta import GamryParseError, parse


def dta(*lines: str) -> bytes:
    return ("\n".join(lines) + "\n").encode()


def test_header_value_types():
    header = parse(
        dta(
            "EXPLAIN",
            "TAG\tCV",
            "TITLE\tLABEL\tCyclic Voltammetry\tTest &Identifier",
            "PSTAT\tPSTAT\tpotentiostat-id\tPotentiostat",
            "",
            "VINIT\tPOTEN\t5.00000E-001\tF\tInitial &E (V)",
            "SCANRATE\tQUANT\t1.2345E+000\t&Scan Rate (mV/s)",
            "CYCLES\tIQUANT\t5\tC&ycles (#)",
            "PSTATMODEL\tIQUANT\t4.00000E+000\tPstat Model",
            "MODE\tSELECTOR\t0\tI/E Range &Mode",
            "FOO\tTABLES\tbar\tLabel",
            "STRIP\tTOGGLE\tF\tUsed for Stripping",
            "RUN\tTOGGLE\tT\tRun",
            "CONDIT\tTWOPARAM\tT\t3.00000E+002\t5.00000E-001\tConditionin&g\tTime(s)\tE(V)",
            "OTHER\tOUTPUT\traw value\tSomething",
        )
    ).header
    assert header == {
        "TAG": "CV",
        "TITLE": "Cyclic Voltammetry",
        "PSTAT": "potentiostat-id",
        "VINIT": 0.5,
        "SCANRATE": 1.2345,
        "CYCLES": 5,
        "PSTATMODEL": 4,
        "MODE": 0,
        "FOO": "bar",
        "STRIP": False,
        "RUN": True,
        "CONDIT": {"enable": True, "start": 300.0, "finish": 0.5},
        "OTHER": "raw value",
    }
    assert isinstance(header["CYCLES"], int)
    assert isinstance(header["PSTATMODEL"], int)


def test_notes_are_the_following_lines_joined():
    header = parse(
        dta(
            "EXPLAIN",
            "TAG\tCV",
            "NOTES\tNOTES\t2\t&Notes...",
            "\tfirst line",
            "\tsecond line",
            "EOC\tQUANT\t0\tOpen Circuit (V)",
        )
    ).header
    assert header["NOTES"] == "first line\nsecond line"
    assert header["EOC"] == 0.0


def test_value_that_does_not_match_its_type_is_kept_as_text():
    header = parse(dta("EXPLAIN", "TAG\tCV", "CYCLES\tIQUANT\tfive\tCycles", "LIMITS\tTWOPARAM\tT\t1.0")).header
    assert header["CYCLES"] == "five"
    assert header["LIMITS"] == "T"


def test_table_rows_are_not_header_fields():
    header = parse(
        dta(
            "EXPLAIN",
            "TAG\tCV",
            "CURVE1\tTABLE",
            "\tPt\tT",
            "\t#\ts",
            "\t0\t0.1",
            "EXPERIMENTABORTED\tTOGGLE\tT\tExperiment Aborted",
        )
    ).header
    assert header == {"TAG": "CV", "EXPERIMENTABORTED": True}


def test_cv_fixture_header(data_dir):
    header = parse((data_dir / "cv_data.dta").read_bytes()).header
    assert header["DATE"] == "3/6/2019"
    assert header["CHECKPSTAT"] == "potentiostat-id"
    assert header["CHECKPOTEN"] == 0.5
    assert header["CHECKQUANT"] == 1.2345
    assert header["CHECKIQUANT"] == 5
    assert header["CHECKSELECTOR"] == 0
    assert header["CHECKTOGGLE"] is False
    assert header["CHECK2PARAM"] == {"enable": True, "start": 300, "finish": 0.5}
    assert header["CHECKNOTES"] == "test-notes-data"


def test_incomplete_header_fixture(data_dir):
    header = parse((data_dir / "cv_data_incompleteheader.dta").read_bytes()).header
    assert header["DELAY"] == {"enable": False, "start": 300, "finish": 0.1}


def test_fields_after_the_curves_are_header_fields(data_dir):
    header = parse((data_dir / "eispot_data_curveaborted.dta").read_bytes()).header
    assert header["EXPERIMENTABORTED"] is True


def test_decimal_comma_detected_from_header():
    header = parse(
        dta(
            "EXPLAIN",
            "TAG\tCHRONOA",
            "EQDELAY\tQUANT\t5,00000E+000\tEquil. &Time (s)",
            "CONDIT\tTWOPARAM\tF\t1,50000E+001\t0,00000E+000\tConditionin&g\tTime(s)\tE(V)",
        )
    ).header
    assert header["EQDELAY"] == 5.0
    assert header["CONDIT"] == {"enable": False, "start": 15.0, "finish": 0.0}


def test_decimal_comma_override():
    data = dta("EXPLAIN", "TAG\tCHRONOA", "EQDELAY\tQUANT\t5,5\tEquil")
    assert parse(data, decimal_comma=True).header["EQDELAY"] == 5.5
    assert parse(data, decimal_comma=False).header["EQDELAY"] == "5,5"


def test_cp1252_file_decodes():
    data = "EXPLAIN\nTAG\tEISPOT\nNOTE\tLABEL\t25 °C\tNote\n".encode("cp1252")
    assert parse(data).header["NOTE"] == "25 °C"


def test_crlf_line_endings():
    data = b"EXPLAIN\r\nTAG\tCV\r\nSCANRATE\tQUANT\t1.5\tRate\r\n"
    assert parse(data).header == {"TAG": "CV", "SCANRATE": 1.5}


CURVE = ("CURVE1\tTABLE", "\tPt\tT\tVf\tIm\tIERange\tOver", "\t#\ts\tV vs. Ref.\tA\t#\tbits")


def test_curve_dtypes_follow_units():
    parsed = parse(
        dta(
            "EXPLAIN",
            "TAG\tCV",
            *CURVE,
            "\t0\t0\t4.9E-001\t7.8E-009\t5\t...........",
            "\t1\t1\t5E-001\t5.3E-009\t5\t..a",
        )
    )
    (curve,) = parsed.curves
    assert dict(curve.schema) == {
        "Pt": pl.Int64,
        "T": pl.Float64,
        "Vf": pl.Float64,
        "Im": pl.Float64,
        "IERange": pl.Int64,
        "Over": pl.String,
    }
    assert curve.rows() == [(0, 0.0, 0.49, 7.8e-9, 5, "..........."), (1, 1.0, 0.5, 5.3e-9, 5, "..a")]
    assert parsed.units == {"Pt": "#", "T": "s", "Vf": "V vs. Ref.", "Im": "A", "IERange": "#", "Over": "bits"}


def test_text_in_a_numeric_column_falls_back_to_inference():
    parsed = parse(
        dta("EXPLAIN", "TAG\tCV", "CURVE\tTABLE", "\tPt\tVf\tNote", "\t#\tV\tV", "\t0\t0.5\tok", "\t1\t0.6\tbad")
    )
    assert parsed.curves[0]["Note"].to_list() == ["ok", "bad"]
    assert parsed.curves[0]["Vf"].to_list() == [0.5, 0.6]


def test_rows_shorter_than_the_header_are_padded_with_nulls():
    parsed = parse(dta("EXPLAIN", "TAG\tCV", *CURVE, "\t0\t0\t0.5\t1e-9\t5\t....", "\t1\t1\t0.6"))
    assert parsed.curves[0].row(1) == (1, 1.0, 0.6, None, None, None)


def test_rows_longer_than_the_header_are_truncated():
    parsed = parse(dta("EXPLAIN", "TAG\tCV", *CURVE, "\t0\t0\t0.5\t1e-9\t5\t....\textra"))
    assert parsed.curves[0].row(0) == (0, 0.0, 0.5, 1e-9, 5, "....")


def test_empty_table_gives_empty_curve():
    parsed = parse(dta("EXPLAIN", "TAG\tCV", *CURVE))
    assert parsed.curves[0].height == 0
    assert parsed.curves[0].columns == ["Pt", "T", "Vf", "Im", "IERange", "Over"]


def test_curves_with_different_units_raise():
    second = ("CURVE2\tTABLE", "\tPt\tT\tVf\tIm\tIERange\tOver", "\t#\ts\tV\tA\t#\tbits")
    data = dta("EXPLAIN", "TAG\tCV", *CURVE, "\t0\t0\t0.5\t1e-9\t5\t..", *second, "\t1\t1\t0.5\t1e-9\t5\t..")
    with pytest.raises(GamryParseError, match="CURVE2"):
        parse(data)


def test_other_tables_are_skipped():
    parsed = parse(
        dta(
            "EXPLAIN",
            "TAG\tCV",
            "EXTRA\tTABLE",
            "\tA\tB",
            "\t#\t#",
            "\t1\t2",
            "EOC\tQUANT\t0.5\tOpen Circuit (V)",
            *CURVE,
            "\t0\t0\t0.5\t1e-9\t5\t..",
        )
    )
    assert len(parsed.curves) == 1
    assert parsed.header["EOC"] == 0.5


def test_cv_fixture_curves(data_dir):
    parsed = parse((data_dir / "cv_data.dta").read_bytes())
    assert [curve.height for curve in parsed.curves] == [10, 10, 10, 10, 10]
    first, last = parsed.curves[0], parsed.curves[-1]
    assert first["T"][0] == 0.1
    assert first["T"][-1] == 1.0
    assert first["Vf"][-1] == 0.5
    assert first["Pt"].dtype == pl.Int64
    assert last["Pt"][-1] == 49
    assert last["T"][-1] == 601.1
    assert last["Vf"][-1] == 0.889001
    assert last["Im"][-1] == 2.622720e-07
    assert last["Sig"][-1] == 0.890
    assert last["IERange"][-1] == 5


def test_aborted_experiment_fixtures(data_dir):
    eis = parse((data_dir / "eispot_data_curveaborted.dta").read_bytes())
    assert [curve.shape for curve in eis.curves] == [(5, 11)]
    assert eis.units["Zphz"] == "°"
    swv = parse((data_dir / "squarewave_data.dta").read_bytes())
    assert [curve.shape for curve in swv.curves] == [(10, 13)]


def test_ocvcurve_table(data_dir):
    parsed = parse((data_dir / "ocvcurve_data.dta").read_bytes())
    assert parsed.ocv_curve is not None
    assert parsed.ocv_curve["T"][0] == 0.258333
    assert parsed.ocv_curve["T"][-1] == 10.3333
    assert parsed.ocv_curve["Vf"][-1] == 0.283437
    assert parsed.header["EOC"] == 0.2834373
    assert len(parsed.curves) == 1


def test_decimal_comma_fixture(data_dir):
    comma = parse((data_dir / "chronoa_de_data.dta").read_bytes()).curves[0]
    assert comma["T"][-1] == 270
    assert comma["Vf"][0] == -5e-4
    assert comma["Vf"][-1] == 0.4
    assert comma["Im"][0] == -2e-8
    assert comma["Im"][-1] == 3e-9
    dot = parse((data_dir / "chronoa_data.dta").read_bytes()).curves[0]
    assert dot["T"][-1] == 270
    assert dot["Vf"][0] == -5.4e-4
    assert dot["Vf"][-1] == 0.4
    assert dot["Im"][-1] == 3e-9


def test_decimal_comma_detected_from_first_row_when_header_has_no_fractions():
    parsed = parse(
        dta("EXPLAIN", "TAG\tCV", "EOC\tQUANT\t0\tOpen Circuit (V)", *CURVE, "\t0\t0\t4,9E-001\t7,8E-009\t5\t..")
    )
    assert parsed.curves[0]["Vf"][0] == 0.49
    assert parsed.curves[0]["Im"][0] == 7.8e-9


def test_vfp600_fixture_has_no_pt_column(data_dir):
    parsed = parse((data_dir / "vfp600_data.dta").read_bytes())
    assert parsed.units == {"Voltage": "V", "Current": "A"}
    assert parsed.curves[0].shape == (20, 2)


def test_quote_characters_are_plain_text():
    parsed = parse(
        dta("EXPLAIN", "TAG\tCV", "CURVE\tTABLE", "\tPt\tVf\tOver", "\t#\tV\tbits", '\t0\t0.5\t"..a', "\t1\t0.6\t..b")
    )
    assert parsed.curves[0]["Over"].to_list() == ['"..a', "..b"]
    assert parsed.curves[0]["Vf"].to_list() == [0.5, 0.6]


def test_curve_table_cut_off_before_its_column_line_is_skipped():
    aborted = ("CURVE2\tTABLE", "EXPERIMENTABORTED\tTOGGLE\tT\tExperiment Aborted")
    parsed = parse(dta("EXPLAIN", "TAG\tCV", *CURVE, "\t0\t0\t0.5\t1e-9\t5\t..", *aborted))
    assert [curve.height for curve in parsed.curves] == [1]
    assert parsed.header["EXPERIMENTABORTED"] is True


def test_curve_table_cut_off_before_its_units_line_is_skipped():
    aborted = ("CURVE2\tTABLE", "\tPt\tT\tVf\tIm\tIERange\tOver", "EXPERIMENTABORTED\tTOGGLE\tT\tExperiment Aborted")
    parsed = parse(dta("EXPLAIN", "TAG\tCV", *CURVE, "\t0\t0\t0.5\t1e-9\t5\t..", *aborted))
    assert [curve.height for curve in parsed.curves] == [1]
    assert parsed.units["Vf"] == "V vs. Ref."
