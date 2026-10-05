"""Windows environment handling can be checked without a Windows runner."""

import runpy
from pathlib import Path

import pytest

bundle_environment = runpy.run_path(
    str(Path(__file__).resolve().parents[1] / "scripts" / "check_bundle.py")
)["bundle_environment"]


@pytest.mark.parametrize("root_key", ["SYSTEMROOT", "SystemRoot", "systemroot", "WINDIR"])
def test_windows_environment_removes_build_paths(root_key):
    source = {root_key: r"C:\Windows", "Path": r"D:\Python;D:\Qt",
              "PythonPath": "source", "PYTHONHOME": "python",
              "Qt_Plugin_Path": "qt", "QT_QPA_PLATFORM_PLUGIN_PATH": "plugins",
              "TEMP": r"C:\Temp"}
    result = bundle_environment(source, "win32")
    assert result["PATH"] == r"C:\Windows\System32;C:\Windows"
    assert result["TEMP"] == r"C:\Temp"
    assert not any(key in result for key in (
        "PYTHONPATH", "PYTHONHOME", "QT_PLUGIN_PATH", "QT_QPA_PLATFORM_PLUGIN_PATH",
    ))
    assert source["Path"] == r"D:\Python;D:\Qt"


def test_missing_windows_root_has_clear_error():
    with pytest.raises(RuntimeError, match="SYSTEMROOT atau WINDIR"):
        bundle_environment({}, "win32")


def test_non_windows_preserves_case_and_path():
    result = bundle_environment({"PATH": "/usr/bin", "mixedCase": "value",
                                 "PYTHONPATH": "source"}, "darwin")
    assert result == {"PATH": "/usr/bin", "mixedCase": "value"}
