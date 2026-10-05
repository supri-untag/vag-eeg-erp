"""Run the actual executable outside the source tree, with a hard timeout."""

import json
import os
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory


def main() -> None:
    executable, report = (Path(arg).resolve() for arg in sys.argv[1:])
    report.unlink(missing_ok=True)
    environment = os.environ.copy()
    for key in ("PYTHONPATH", "PYTHONHOME", "QT_PLUGIN_PATH", "QT_QPA_PLATFORM_PLUGIN_PATH"):
        environment.pop(key, None)
    if sys.platform == "win32":
        # Do not let the build machine's Python/Qt DLLs mask incomplete packaging.
        windows = Path(environment["SystemRoot"])
        environment["PATH"] = os.pathsep.join([str(windows / "System32"), str(windows)])
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
