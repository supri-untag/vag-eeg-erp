"""Prepare Qt plugin discovery before QApplication initializes its platform."""

import os
import stat
import sys
from pathlib import Path


def clear_hidden_plugin_flags(plugin_root: Path, environment: Path) -> int:
    """Clear only UF_HIDDEN in a virtual environment's Qt plugin tree on macOS.

    Some local tooling reapplies Finder hidden flags to environment files.
    Qt's plugin directory scan then omits the installed platform libraries.
    Other flags, permissions, binary contents, and external symlinks stay intact.
    """
    if sys.platform != "darwin":
        return 0
    root, boundary = plugin_root.resolve(), environment.resolve()
    if not root.is_relative_to(boundary) or root == boundary:
        raise ValueError("Folder plugin harus berada di dalam virtual environment.")
    candidates = [root, *root.rglob("*")]
    parent = root.parent
    while parent != boundary:
        candidates.append(parent)
        parent = parent.parent
    count = 0
    for path in candidates:
        if path.is_symlink():
            continue
        flags = path.stat().st_flags
        if flags & stat.UF_HIDDEN:
            try:
                os.chflags(path, flags & ~stat.UF_HIDDEN)
            except OSError as error:
                raise RuntimeError(
                    f"Plugin Qt tersembunyi dan atributnya tidak dapat dipulihkan: {path}. "
                    "Periksa izin virtual environment."
                ) from error
            count += 1
    return count


def prepare_qt_plugins() -> None:
    from PySide6.QtCore import QCoreApplication, QLibraryInfo

    root = Path(QLibraryInfo.path(QLibraryInfo.LibraryPath.PluginsPath))
    # Installed/frozen distributions must not modify system or bundle files.
    if (
        sys.platform == "darwin"
        and not getattr(sys, "frozen", False)
        and sys.prefix != sys.base_prefix
        and root.resolve().is_relative_to(Path(sys.prefix).resolve())
    ):
        clear_hidden_plugin_flags(root, Path(sys.prefix))
    if root.is_dir():
        QCoreApplication.addLibraryPath(str(root))
