# Run on Windows from scripts/build_windows.ps1.
import sys
from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

if sys.platform != "win32":
    raise SystemExit("Build executable Windows harus dijalankan di Windows.")

root = Path(SPECPATH).parent
analysis = Analysis(
    [str(root / "run.py")],
    pathex=[str(root / "src")],
    datas=collect_data_files("mne") + [(str(root / "docs"), "docs")],
    hiddenimports=collect_submodules("pyqtgraph.opengl") + collect_submodules("OpenGL"),
    excludes=["PyQt5", "PyQt6", "PySide2"],
    hooksconfig={"matplotlib": {"backends": ["QtAgg", "Agg"]}},
)
pyz = PYZ(analysis.pure)
exe = EXE(
    pyz, analysis.scripts, [], exclude_binaries=True,
    name="VARD-EEG-ERP", console=False, debug=False, upx=False,
)
collection = COLLECT(
    exe, analysis.binaries, analysis.datas,
    name="VARD-EEG-ERP", upx=False,
)
