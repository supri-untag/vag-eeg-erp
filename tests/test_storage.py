import csv
import json

import numpy as np
import pytest

from vard_eeg_erp.analysis import Settings, analyze, demo_recording
from vard_eeg_erp.storage import export_csv, load_project, save_project


def test_project_roundtrip(tmp_path, recording, result):
    path = tmp_path / "Riset üji.vard.json"
    save_project(
        path,
        recording,
        result,
        Settings(),
        "Visual A",
        [result.history],
        {"channel": "Pz", "time_ms": 400},
    )
    payload = load_project(path)
    rebuilt = analyze(demo_recording(), Settings(**payload["settings"]), payload["event"])
    np.testing.assert_array_equal(rebuilt.evoked.data, result.evoked.data)
    assert payload["history"][0]["accepted"] == 12
    assert payload["view"]["time_ms"] == 400


def test_export_units_and_demo_label(tmp_path, result):
    path = tmp_path / "ERP.csv"
    export_csv(path, result, demo=True)
    with path.open() as stream:
        rows = list(csv.DictReader(stream))
    assert len(rows) == result.evoked.data.shape[1]
    assert rows[0]["synthetic_demo"] == "True"
    assert float(rows[0]["time_ms"]) == result.evoked.times[0] * 1000
    assert (
        float(rows[0]["Pz_uV"]) == result.evoked.data[result.evoked.ch_names.index("Pz"), 0] * 1e6
    )


def test_unknown_project_version(tmp_path):
    path = tmp_path / "future.vard.json"
    path.write_text(json.dumps({"schema_version": 99}))
    with pytest.raises(ValueError, match="Versi"):
        load_project(path)
