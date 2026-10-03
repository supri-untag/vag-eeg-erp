"""Native macOS smoke check for the VARS configuration page."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from PySide6.QtCore import QTimer

from vard_eeg_erp.app import MainWindow, create_application

app = create_application()
window = MainWindow(auto_demo=False)
window.show()


def check():
    window.navigate(6)
    assert window.page_title.text() == "VARS Scoring"
    window.scoring.calculate()
    assert window.scoring.output is None
    assert "Generate ERP" in window.scoring.status.text()
    QTimer.singleShot(300, finish)


def finish():
    path = Path(__file__).resolve().parents[1] / "docs/images/10-vars-scoring.png"
    assert window.grab().save(str(path))
    print("PASS: native VARS page, empty-state validation, screenshot", flush=True)
    window.close()
    app.quit()


QTimer.singleShot(500, check)
sys.exit(app.exec())
