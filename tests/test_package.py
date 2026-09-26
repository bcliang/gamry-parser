import gamry_parser as gp


def test_version_comes_from_package_metadata():
    assert gp.__version__ == "1.0.0"
