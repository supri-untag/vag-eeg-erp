"""Run the actual executable outside the source tree, with a hard timeout."""

import json
import ntpath
import os
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory


def bundle_environment(source: dict[str, str], platform: str) -> dict[str, str]:
    # Windows os.environ is case-insensitive, but its dict copy is not.
    environment = (
        {key.upper(): value for key, value in source.items()}
        if platform == "win32" else source.copy()
    )
    for key in ("PYTHONPATH", "PYTHONHOME", "QT_PLUGIN_PATH", "QT_QPA_PLATFORM_PLUGIN_PATH"):
        environment.pop(key, None)
    if platform == "win32":
        # Do not let the build machine's Python/Qt DLLs mask incomplete packaging.
        windows = environment.get("SYSTEMROOT") or environment.get("WINDIR")
        if not windows:
            raise RuntimeError("Environment Windows tidak memiliki SYSTEMROOT atau WINDIR.")
        environment["PATH"] = ntpath.join(windows, "System32") + ";" + windows
    return environment


def main() -> None:
    executable, report = (Path(arg).resolve() for arg in sys.argv[1:])
    report.unlink(missing_ok=True)
    environment = bundle_environment(dict(os.environ), sys.platform)
    with TemporaryDirectory(prefix="VARD bundle ") as temporary:
        completed = subprocess.run(
            [str(executable), "--smoke-test", str(report)],
            cwd=temporary, env=environment, timeout=180, check=False,
        )
    if not report.is_file():
        raise RuntimeError(f"EXE tidak menghasilkan laporan; exit={completed.returncode}")
    payload = json.loads(report.read_text(encoding="utf-8"))
    if completed.returncode != 0 or payload.get("status") != "passed":
        raise RuntimeError(f"Uji EXE gagal: {payload}")
    if payload.get("frozen") is not True:
        raise RuntimeError("Uji harus dijalankan pada executable hasil bundling.")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
