# Run on Windows from scripts/build_windows.ps1.
import sys
from pathlib import Path

from PyInstaller.utils.hooks import collect_all, collect_data_files, collect_submodules

if sys.platform != "win32":
    raise SystemExit("Build executable Windows harus dijalankan di Windows.")

root = Path(SPECPATH).parent
# Include MNE's source, data, metadata and binaries as well as dynamic imports.
mne_datas, mne_binaries, mne_imports = collect_all(
    "mne", filter_submodules=lambda name: "tests" not in name.split("."),
)
required_mne = {"mne.utils.config", "mne.io.edf.edf", "mne.channels", "mne.epochs"}
analysis = Analysis(
    [str(root / "run.py")],
    pathex=[str(root / "src")],
    # MNE resolves Python modules dynamically through lazy_loader and .pyi stubs.
    datas=(mne_datas
           + collect_data_files("mne", includes=["**/*.pyi"])
           + [(str(root / "docs"), "docs")]),
    binaries=mne_binaries,
    hiddenimports=(sorted(set(mne_imports) | required_mne)
                   + collect_submodules("pyqtgraph.opengl") + collect_submodules("OpenGL")),
    excludes=["PyQt5", "PyQt6", "PySide2"],
    hooksconfig={"matplotlib": {"backends": ["QtAgg", "Agg"]}},
)
# Missing hidden imports are otherwise only warnings. Never release that bundle.
missing_mne = required_mne - {entry[0] for entry in analysis.pure}
if missing_mne:
    raise SystemExit(f"Build gagal: modul MNE tidak terkemas: {sorted(missing_mne)}")
pyz = PYZ(analysis.pure)
exe = EXE(
    pyz, analysis.scripts, [], exclude_binaries=True,
    name="VARD-EEG-ERP", console=False, debug=False, upx=False,
)
collection = COLLECT(
    exe, analysis.binaries, analysis.datas,
    name="VARD-EEG-ERP", upx=False,
)
