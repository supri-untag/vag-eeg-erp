"""Check native presentation playback and save a documentation screenshot."""

import sys
import time
from pathlib import Path

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
started = time.monotonic()


def check():
    global phase
    if errors or time.monotonic() - started > 60:
        print(errors or "timeout", flush=True)
        if window.job:
            window.job.wait()
        app.exit(1)
        return
    if window.job is not None:
        return
    if phase == 0:
        window.navigate(4)
        window.prepare_presentation()
        phase = 1
    elif phase == 1:
        if len(window.presentation.cache) < len(window.presentation.results):
            return
        assert len(window.presentation.results) == 2
        window.presentation.toggle()
        window.presentation.advance()
        assert "Visual B" in window.presentation.title.text()
        window.presentation.reset()
        phase = 2
    else:
        path = Path(__file__).resolve().parents[1] / "docs/images/07-presentation.png"
        assert window.grab().save(str(path))
        print("PASS: presentation, two event groups, playback, stop, screenshot", flush=True)
        timer.stop()
        window.dirty = False
        window.close()
        app.quit()


timer = QTimer()
timer.timeout.connect(check)
timer.start(400)
sys.exit(app.exec())
