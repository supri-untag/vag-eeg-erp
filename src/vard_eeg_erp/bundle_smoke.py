"""Exercise the packaged startup and demo pipeline; report even import failures."""

import json
import traceback
from pathlib import Path
from tempfile import TemporaryDirectory


def run(report_path: Path) -> int:
    report = {"status": "failed"}
    window = None
    try:
        from vard_eeg_erp.analysis import Settings, analyze, demo_recording
        from vard_eeg_erp.app import MainWindow, create_application
        from vard_eeg_erp.storage import export_csv, load_project, save_project

        app = create_application()
        window = MainWindow(auto_demo=False)
        recording = demo_recording()
        settings = Settings()
        result = analyze(recording, settings, "Visual A")
        assert result.accepted == 12, result.accepted
        window.install_recording(recording)
        window.install_result(result)
        window.show()
        app.processEvents()
        window._render_topomap()
        assert len(window.topomap.figure.axes) == 2
        with TemporaryDirectory(prefix="VARD smoke ") as temporary:
            folder = Path(temporary)
            project = folder / "demo uji.vard.json"
            save_project(project, recording, result, settings, "Visual A", [], {})
            assert load_project(project)["demo"] is True
            export_csv(folder / "ERP.csv", result, True)
            assert (folder / "ERP.csv").stat().st_size > 100
        report = {"status": "passed", "accepted_trials": result.accepted,
                  "qt_platform": app.platformName(),
                  "checks": ["startup", "demo", "ERP", "topomap", "project", "CSV"]}
    except Exception:
        report["traceback"] = traceback.format_exc()
    finally:
        if window is not None:
            window.dirty = False
            window.close()
        report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return 0 if report["status"] == "passed" else 1
