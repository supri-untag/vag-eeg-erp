import numpy as np
import pytest
from scipy.io import savemat

from vard_eeg_erp.analysis import read_recording


def test_set_fdt_preserves_samples_units_and_trigger_codes(tmp_path):
    values = np.arange(400, dtype=np.float32).reshape(2, 200)
    values.flatten(order='F').astype('<f4').tofile(tmp_path / 'data.fdt')
    eeg = dict(data='data.fdt', nbchan=2, pnts=200, trials=1, srate=100.,
               xmin=0., xmax=1.99, chanlocs=np.array([{'labels': 'Fp1'}, {'labels': 'Fp2'}],
                                                    dtype=object),
               event=np.array([{'type': '1001', 'latency': 51., 'duration': 1.},
                               {'type': '1002', 'latency': 151., 'duration': 1.}], dtype=object))
    savemat(tmp_path / 'data.set', {'EEG': eeg})
    recording = read_recording(tmp_path / 'data.fdt')
    np.testing.assert_allclose(recording.raw.get_data(), values * 1e-6)
    np.testing.assert_array_equal(recording.events[:, 0], [50, 150])
    np.testing.assert_array_equal(recording.events[:, 2], [1001, 1002])
    assert recording.source.endswith('data.set')
    recording.raw.close()


def test_fdt_requires_set(tmp_path):
    path = tmp_path / 'missing.fdt'
    path.write_bytes(b'')
    with pytest.raises(ValueError, match='SET pendamping'):
        read_recording(path)
