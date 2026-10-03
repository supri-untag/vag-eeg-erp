"""Capture real application screens using only the labelled synthetic demo."""

import sys
import time
from pathlib import Path

from PySide6.QtCore import QTimer

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from vard_eeg_erp.app import MainWindow, create_application  # noqa: E402
from vard_eeg_erp.widgets import SettingsDialog  # noqa: E402

app = create_application()
window = MainWindow(auto_demo=False)
window.resize(1400, 920)
output = Path(__file__).resolve().parents[1] / "docs" / "images"
output.mkdir(parents=True, exist_ok=True)
errors = []
window.show_error = errors.append
window.show()
window.load_demo()
started = time.monotonic()
index = 0
dialog = None
screens = ["01-overview", "02-component", "03-eeg", "04-events", "05-history", "06-parameters"]


def finish(code):
    timer.stop()
    if window.job:
        window.job.wait()
    window.dirty = False
    if dialog:
        dialog.close()
    window.close()
    app.exit(code)


def capture():
    global index
    target = dialog if index == 5 else window
    path = output / f"{screens[index]}.png"
    if not target.grab().save(str(path)):
        print(f"Could not save {path}", file=sys.stderr)
        finish(1)
        return
    print(path.name, flush=True)
    index += 1
    if index == len(screens):
        finish(0)
    else:
        QTimer.singleShot(100, prepare)


def prepare():
    global dialog
    if index == 0:
        window.navigate(0)
        window.select_time(400)
    elif index == 1:
        scroll = window.stack.widget(0)
        scroll.verticalScrollBar().setValue(scroll.verticalScrollBar().maximum())
    elif index in (2, 3, 4):
        window.navigate(index - 1)
    else:
        dialog = SettingsDialog(window.settings, window)
        dialog.show()
    QTimer.singleShot(400, capture)


def ready():
    if errors or time.monotonic() - started > 60:
        print(errors or "Timeout while loading demo", file=sys.stderr)
        finish(1)
    elif window.job is None and window.result is not None:
        timer.stop()
        prepare()


timer = QTimer()
timer.timeout.connect(ready)
timer.start(100)
sys.exit(app.exec())
