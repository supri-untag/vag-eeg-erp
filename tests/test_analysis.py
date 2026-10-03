from dataclasses import replace

import mne
import numpy as np
import pytest

from vard_eeg_erp.analysis import Result, Settings, analyze, read_recording


def test_pipeline_preserves_raw_and_baseline(recording, result):
    before = recording.raw.get_data().copy()
    second = analyze(recording, Settings(), "Visual B")
    np.testing.assert_array_equal(recording.raw.get_data(), before)
    assert result.accepted == second.accepted == 12
    assert result.rejected == 0
    baseline = (result.evoked.times >= -0.2) & (result.evoked.times <= 0)
    np.testing.assert_allclose(result.evoked.data[:, baseline].mean(axis=1), 0, atol=1e-18)
    np.testing.assert_allclose(result.evoked.data.mean(axis=0), 0, atol=1e-18)
    assert not np.array_equal(result.evoked.data, second.evoked.data)


def test_known_measurements_and_nearest_sample():
    info = mne.create_info(["Cz"], 1000, "eeg")
    evoked = mne.EvokedArray(np.array([[0, 1, -4, 2, 0]]) * 1e-6, info, tmin=0)
    result = Result(evoked, 1, 0, "test", Settings(), {})
    metrics = result.metrics("Cz", 0, 4)
    assert metrics["mean_uv"] == pytest.approx(-0.2)
    assert metrics["peak_uv"] == pytest.approx(-4)
    assert metrics["latency_ms"] == 2
    assert metrics["auc_uv_ms"] == pytest.approx(-1)
    assert result.sample(2.4) == 2
    assert result.sample(9999) == 4
    assert result.sample(-9999) == 0


@pytest.mark.parametrize(
    "changes",
    [
        {"highpass": 40},
        {"lowpass": 128},
        {"baseline_end": 2},
        {"tmin": 2},
        {"reject_uv": 0},
        {"notch": 45},
        {"lowpass": float("nan")},
    ],
)
def test_invalid_parameters(changes):
    with pytest.raises(ValueError):
        replace(Settings(), **changes).validate(256)


def test_absent_event_and_all_rejected(recording):
    with pytest.raises(ValueError, match="event"):
        analyze(recording, Settings(), "missing")
    with pytest.warns(RuntimeWarning), pytest.raises(ValueError, match="Seluruh epoch"):
        analyze(recording, replace(Settings(), reject_uv=0.0001), "Visual A")


def test_invalid_measurement_window(result):
    with pytest.raises(ValueError, match="Window"):
        result.metrics("Pz", 1000, 2000)


def write_test_bdf(path):
    """Small valid 24-bit BDF fixture with two EEG channels and BioSemi Status."""
    sfreq, records, channels = 256, 8, 3

    def field(value, width):
        return str(value).encode("ascii").ljust(width, b" ")

    header = b"\xffBIOSEMI" + field("Synthetic", 80) + field("Test", 80)
    header += field("01.01.24", 8) + field("00.00.00", 8)
    header += field(256 + channels * 256, 8) + field("24BIT", 44)
    header += field(records, 8) + field(1, 8) + field(channels, 4)
    fields = [
        (["Fp1", "Fp2", "Status"], 16),
        (["", "", ""], 80),
        (["uV", "uV", ""], 8),
        ([-100, -100, -8388608], 8),
        ([100, 100, 8388607], 8),
        ([-8388608] * channels, 8),
        ([8388607] * channels, 8),
        ([""] * channels, 80),
        ([sfreq] * channels, 8),
        ([""] * channels, 32),
    ]
    for values, width in fields:
        header += b"".join(field(value, width) for value in values)
    assert len(header) == 1024
    times = np.arange(records * sfreq) / sfreq
    first = (np.sin(2 * np.pi * 10 * times) * 800000).astype(np.int32)
    status = np.zeros(records * sfreq, dtype=np.int32)
    status[512:517] = 1
    status[1024:1029] = 2
    samples = np.array([first, -first, status])
    with path.open("wb") as stream:
        stream.write(header)
        for block in range(records):
            for channel in samples:
                values = channel[block * sfreq : (block + 1) * sfreq].astype(np.uint32)
                encoded = np.column_stack([values & 255, (values >> 8) & 255, (values >> 16) & 255])
                stream.write(encoded.astype(np.uint8).tobytes())


def test_real_bdf_reader_with_synthetic_binary(tmp_path):
    path = tmp_path / "rekaman uji.bdf"
    write_test_bdf(path)
    recording = read_recording(path)
    assert recording.demo is False
    assert recording.raw.info["sfreq"] == 256
    assert recording.preview_names == ["Fp1", "Fp2"]
    np.testing.assert_array_equal(recording.events[:, 0], [512, 1024])
    np.testing.assert_array_equal(recording.events[:, 2], [1, 2])
    result = analyze(recording, Settings(), "Trigger 1")
    assert result.accepted == 1
    assert result.evoked.ch_names == ["Fp1", "Fp2"]
