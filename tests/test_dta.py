from gamry_parser._dta import parse


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
