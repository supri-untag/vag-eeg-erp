"""Source launcher: works without relying on editable-install .pth files."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from vard_eeg_erp.app import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
