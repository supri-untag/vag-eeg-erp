import numpy as np
import pytest

from vard_eeg_erp.analysis import Settings
from vard_eeg_erp.import_mapping import apply_setup, ced_setup
from vard_eeg_erp.storage import load_project, save_project


def test_group_and_project_roundtrip(recording, tmp_path):
    setup = {'groups': {'1': 'Visual', '2': 'Visual'}}
    mapped = apply_setup(recording, setup)
    assert mapped.event_id == {'Visual': 1}
    np.testing.assert_array_equal(mapped.events[:, 0], recording.events[:, 0])
    assert set(mapped.events[:, 2]) == {1}
    assert set(recording.events[:, 2]) == {1, 2}
    path = tmp_path / 'test.vard.json'
    save_project(path, mapped, None, Settings(), 'Visual', [], {})
    assert load_project(path)['import_setup'] == setup


def test_incomplete_groups_rejected(recording):
    with pytest.raises(ValueError, match='semua kode'):
        apply_setup(recording, {'groups': {'1': 'Visual'}})


def test_ced_axes_and_exclusion(tmp_path):
    ced = tmp_path / 'map.ced'
    ced.write_text('labels\tX\tY\tZ\nF\t1\t0\t0\nL\t0\t1\t0\nR\t0\t-1\t0\nC\t0\t0\t1\n')
    mapping = tmp_path / 'map.csv'
    mapping.write_text('OriginalLabel,ActiveElectrode,UsedForTopoplot\nF-A1,F,YES\nL-A1,L,YES\nR-A2,R,YES\nC-A1,C,YES\nExtra,,NO\n')
    setup = ced_setup(ced, mapping)
    np.testing.assert_allclose(setup['positions']['F-A1'], [0, .095, 0])
    np.testing.assert_allclose(setup['positions']['L-A1'], [-.095, 0, 0])
    assert setup['excluded'] == ['Extra']
