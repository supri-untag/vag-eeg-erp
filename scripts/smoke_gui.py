"""Exercise the native Qt GUI, capture a preview, and exit. Run on macOS desktop."""

import json
import sys
import time
from pathlib import Path
from unittest.mock import patch

from PySide6.QtCore import QTimer

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from vard_eeg_erp.app import MainWindow, create_application  # noqa: E402

app = create_application()
window = MainWindow(auto_demo=False)
errors = []
window.show_error = errors.append
output = Path(__file__).resolve().parents[1] / "artifacts"
output.mkdir(exist_ok=True)
window.show()
window.load_demo()
started = time.monotonic()
phase = 0


def check():
    global phase
    try:
        if errors:
            raise AssertionError(errors)
        if time.monotonic() - started > 60:
            raise TimeoutError("GUI smoke test exceeded 60 seconds")
        if window.job is not None:
            return
        if phase == 0:
            assert window.result.accepted == 12
            window.select_time(400)
            for index in (1, 2, 3, 0):
                window.navigate(index)
            with patch(
                "vard_eeg_erp.app.QFileDialog.getSaveFileName",
                return_value=(str(output / "smoke.vard.json"), ""),
            ):
                assert window.save()
            with patch(
                "vard_eeg_erp.app.QFileDialog.getOpenFileName",
                return_value=(str(output / "smoke.vard.json"), ""),
            ):
                window.open_project()
            phase = 1
        elif phase == 1:
            assert window.result.accepted == 12
            assert window.project_path.name == "smoke.vard.json"
            with patch(
                "vard_eeg_erp.app.QFileDialog.getSaveFileName",
                return_value=(str(output / "smoke.csv"), ""),
            ):
                window.export()
            phase = 2
        else:
            assert (output / "smoke.csv").is_file()
            assert len(window.topomap.figure.axes) == 2
            assert window.grab().save(str(output / "vard-macos.png"))
            report = {
                "status": "passed",
                "qt_platform": app.platformName(),
                "accepted_trials": window.result.accepted,
                "linked_time_ms": window.erp_plot.cursor.value(),
                "checks": [
                    "demo worker",
                    "ERP",
                    "linked cursor",
                    "topomap",
                    "navigation",
                    "save project",
                    "open project",
                    "CSV export",
                    "screenshot",
                ],
            }
            (output / "smoke-report.json").write_text(json.dumps(report, indent=2))
            print(json.dumps(report), flush=True)
            timer.stop()
            window.dirty = False
            window.close()
            app.exit(0)
    except Exception as error:
        print(f"GUI SMOKE FAILED: {error}", file=sys.stderr, flush=True)
        timer.stop()
        # Wait for background work before destroying its QThread.
        if window.job:
            window.job.wait()
        app.exit(1)


timer = QTimer()
timer.timeout.connect(check)
timer.start(300)
sys.exit(app.exec())
