import importlib
import importlib.metadata

import gamry_parser as gp


def test_version_comes_from_package_metadata():
    assert gp.__version__ == "1.1.0"


def test_version_falls_back_when_the_package_is_not_installed(monkeypatch):
    def missing(name):
        raise importlib.metadata.PackageNotFoundError(name)

    monkeypatch.setattr(importlib.metadata, "version", missing)
    assert importlib.reload(gp).__version__ == "0.0.0"
    monkeypatch.undo()
    assert importlib.reload(gp).__version__ == "1.1.0"
