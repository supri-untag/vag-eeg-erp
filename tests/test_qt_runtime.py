import os
import stat
import sys

import pytest

from vard_eeg_erp.qt_runtime import clear_hidden_plugin_flags

pytestmark = pytest.mark.skipif(sys.platform != "darwin", reason="macOS file flags")


def test_hidden_plugins_repaired_without_changing_contents_or_other_flags(tmp_path):
    environment = tmp_path / "venv"
    root = environment / "lib" / "plugins"
    platforms = root / "platforms"
    platforms.mkdir(parents=True)
    plugin = platforms / "libqcocoa.dylib"
    plugin.write_bytes(b"test plugin")
    os.chflags(platforms, stat.UF_HIDDEN)
    os.chflags(plugin, stat.UF_HIDDEN | stat.UF_NODUMP)
    assert clear_hidden_plugin_flags(root, environment) == 2
    assert not platforms.stat().st_flags & stat.UF_HIDDEN
    assert plugin.stat().st_flags == stat.UF_NODUMP
    assert plugin.read_bytes() == b"test plugin"
    assert clear_hidden_plugin_flags(root, environment) == 0


def test_external_plugin_paths_rejected(tmp_path):
    with pytest.raises(ValueError, match="virtual environment"):
        clear_hidden_plugin_flags(tmp_path / "external", tmp_path / "venv")


def test_external_symlink_untouched(tmp_path):
    root = tmp_path / "venv" / "plugins"
    root.mkdir(parents=True)
    external = tmp_path / "external.dylib"
    external.write_bytes(b"external")
    os.chflags(external, stat.UF_HIDDEN)
    (root / "external.dylib").symlink_to(external)
    assert clear_hidden_plugin_flags(root, tmp_path / "venv") == 0
    assert external.stat().st_flags & stat.UF_HIDDEN
