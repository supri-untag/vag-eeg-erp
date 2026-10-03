import os
import tempfile

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("MPLCONFIGDIR", os.path.join(tempfile.gettempdir(), "vard-mpl-test-cache"))

import pytest  # noqa: E402

from vard_eeg_erp.analysis import Settings, analyze, demo_recording  # noqa: E402


@pytest.fixture(scope="session")
def recording():
    return demo_recording()


@pytest.fixture(scope="session")
def result(recording):
    return analyze(recording, Settings(), "Visual A")
