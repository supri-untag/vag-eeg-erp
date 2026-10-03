"""Native OpenGL and cached-fade smoke test with measured presentation intervals."""

import json
import sys
import time
from pathlib import Path

import numpy as np
from PySide6.QtCore import QTimer

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from vard_eeg_erp.app import MainWindow, create_application  # noqa: E402

app = create_application()
window = MainWindow(auto_demo=False)
errors = []
window.show_error = errors.append
window.show()
window.load_demo()
phase = 0
started = time.perf_counter()
frames = []
period_start = 0
output = Path(__file__).resolve().parents[1] / "artifacts"
output.mkdir(exist_ok=True)


def check():
    global phase, period_start
    try:
        if errors:
            raise AssertionError(errors)
        if time.perf_counter() - started > 90:
            raise TimeoutError("Animation test timed out")
        if window.job is not None:
            return
        if phase == 0:
            window.navigate(5)
            period_start = time.perf_counter()
            phase = 1
        elif phase == 1:
            if not window.brain.view or not window.brain.view.isValid():
                if time.perf_counter() - period_start < 5:
                    return
                raise RuntimeError("No valid native OpenGL context")
            window.brain.view.frameSwapped.connect(lambda: frames.append(time.perf_counter()))
            window.brain.speed.setCurrentIndex(0)
            window.brain.reset()
            window.brain.rotate.setChecked(True)
            window.brain.toggle()
            period_start = time.perf_counter()
            phase = 2
        elif phase == 2:
            if time.perf_counter() - period_start < 4:
                return
            window.brain.pause()
            assert window.brain.sample == window.sample_index
            assert window.brain.sample > 0
            assert window.grab().save(str(output / "brain3d-macos.png"))
            # Ignore startup and report rendered swap intervals, not just timer ticks.
            intervals = np.diff(frames[3:]) * 1000
            assert len(intervals) > 20
            report = {
                "qt_platform": app.platformName(),
                "rendered_frames": len(frames),
                "median_frame_ms": float(np.median(intervals)),
                "p95_frame_ms": float(np.percentile(intervals, 95)),
                "mean_render_fps": float(1000 / np.mean(intervals)),
                "sample": window.sample_index,
            }
            (output / "animation-performance.json").write_text(json.dumps(report, indent=2))
            print(json.dumps(report), flush=True)
            window.navigate(4)
            window.prepare_presentation()
            phase = 3
        elif phase == 3:
            if len(window.presentation.cache) != len(window.presentation.results):
                return
            assert len(window.presentation.cache) == 2
            window.presentation.toggle()
            period_start = time.perf_counter()
            phase = 4
        elif phase == 4:
            if time.perf_counter() - period_start < 1.25:
                return
            assert window.presentation.canvas.alpha > 0
            assert window.grab().save(str(output / "erp-fade-macos.png"))
            paint_times = [
                value for value in window.presentation.canvas.paint_times if value > period_start
            ]
            intervals = np.diff(paint_times) * 1000
            report = json.loads((output / "animation-performance.json").read_text())
            report["erp_paint_frames"] = len(paint_times)
            report["erp_mean_paint_fps"] = float(1000 / np.mean(intervals))
            report["erp_p95_paint_ms"] = float(np.percentile(intervals, 95))
            (output / "animation-performance.json").write_text(json.dumps(report, indent=2))
            print(json.dumps(report), flush=True)
            window.presentation.pause()
            window.invalidate_result()
            assert not window.brain.timer.isActive()
            assert not window.presentation.timer.isActive()
            timer.stop()
            window.dirty = False
            window.close()
            print("PASS: OpenGL rendering, playback, sync, cached fade, invalidation", flush=True)
            app.quit()
    except Exception as error:
        print(f"FAIL: {error}", flush=True)
        timer.stop()
        if window.job:
            window.job.wait()
        app.exit(1)


timer = QTimer()
timer.timeout.connect(check)
timer.start(50)
sys.exit(app.exec())
