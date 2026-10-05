"""Source launcher: works without relying on editable-install .pth files."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--smoke-test":
        from vard_eeg_erp.bundle_smoke import run

        raise SystemExit(run(Path(sys.argv[2])))
    else:
        from vard_eeg_erp.app import main

        raise SystemExit(main())
