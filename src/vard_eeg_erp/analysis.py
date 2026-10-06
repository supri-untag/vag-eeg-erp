"""GUI-independent EEG pipeline. Internal units: seconds and volts."""

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path

import mne
import numpy as np

from vard_eeg_erp import __version__

CHANNELS = [
    "Fp1",
    "Fp2",
    "F7",
    "F3",
    "Fz",
    "F4",
    "F8",
    "FC5",
    "FC1",
    "FC2",
    "FC6",
    "T7",
    "C3",
    "Cz",
    "C4",
    "T8",
    "CP5",
    "CP1",
    "CP2",
    "CP6",
    "P7",
    "P3",
    "Pz",
    "P4",
    "P8",
    "PO7",
    "PO3",
    "POz",
    "PO4",
    "PO8",
    "O1",
    "O2",
]


@dataclass
class Settings:
    highpass: float = 0.5
    lowpass: float = 30.0
    notch: int = 0
    average_reference: bool = True
    tmin: float = -0.2
    tmax: float = 1.0
    baseline_start: float = -0.2
    baseline_end: float = 0.0
    reject_uv: float = 150.0
    standard_montage: bool = False

    def validate(self, sfreq: float) -> None:
        numeric = [
            self.highpass,
            self.lowpass,
            self.tmin,
            self.tmax,
            self.baseline_start,
            self.baseline_end,
            self.reject_uv,
        ]
        if not np.all(np.isfinite(numeric)):
            raise ValueError("Parameter analisis harus berupa angka finite.")
        if not 0 <= self.highpass < self.lowpass < sfreq / 2:
            raise ValueError(f"Filter harus memenuhi 0 ≤ high-pass < low-pass < {sfreq / 2:g} Hz.")
        if not self.tmin < self.tmax:
            raise ValueError("Awal epoch harus lebih kecil dari akhir epoch.")
        if not self.tmin <= self.baseline_start <= self.baseline_end <= self.tmax:
            raise ValueError("Rentang baseline harus berada di dalam epoch.")
        if self.reject_uv <= 0:
            raise ValueError("Ambang penolakan harus lebih besar dari 0 µV.")
        if self.notch not in (0, 50, 60) or self.notch >= sfreq / 2:
            raise ValueError("Notch harus Off, 50, atau 60 Hz dan di bawah frekuensi Nyquist.")


@dataclass
class Recording:
    raw: mne.io.BaseRaw
    events: np.ndarray
    event_id: dict[str, int]
    source: str
    demo: bool = False
    import_setup: dict = field(default_factory=dict)
    preview_times: np.ndarray = field(default_factory=lambda: np.empty(0))
    preview_data: np.ndarray = field(default_factory=lambda: np.empty((0, 0)))
    preview_names: list[str] = field(default_factory=list)


@dataclass
class Result:
    evoked: mne.Evoked
    accepted: int
    rejected: int
    event_name: str
    settings: Settings
    history: dict

    def sample(self, milliseconds: float) -> int:
        return int(np.argmin(np.abs(self.evoked.times * 1000 - milliseconds)))

    def metrics(self, channel: str, start_ms: float, end_ms: float) -> dict:
        times = self.evoked.times * 1000
        if start_ms >= end_ms or start_ms < times[0] or end_ms > times[-1]:
            raise ValueError(
                "Window komponen harus berada dalam epoch dan memiliki durasi positif."
            )
        mask = (times >= start_ms) & (times <= end_ms)
        if np.count_nonzero(mask) < 2:
            raise ValueError("Window komponen membutuhkan minimal dua sampel.")
        values = self.evoked.data[self.evoked.ch_names.index(channel), mask] * 1e6
        selected_times = times[mask]
        peak = int(np.argmax(np.abs(values)))
        return {
            "mean_uv": float(values.mean()),
            "peak_uv": float(values[peak]),
            "latency_ms": float(selected_times[peak]),
            "auc_uv_ms": float(np.trapezoid(values, selected_times)),
        }


def prepare_preview(recording: Recording) -> Recording:
    picks = mne.pick_types(recording.raw.info, eeg=True, exclude=[])
    if not len(picks):
        raise ValueError("Rekaman tidak memiliki channel EEG.")
    stop = min(recording.raw.n_times, int(recording.raw.info["sfreq"] * 10))
    step = max(1, stop // 2500)
    recording.preview_times = recording.raw.times[:stop:step]
    recording.preview_data = recording.raw.get_data(picks=picks[:16], stop=stop)[:, ::step]
    recording.preview_names = [recording.raw.ch_names[i] for i in picks[:16]]
    return recording


def standard_montage_name() -> str:
    """Use MNE's current name, with compatibility for older supported releases."""
    available = mne.channels.get_builtin_montages()
    return "colin27_1020" if "colin27_1020" in available else "standard_1020"


def demo_recording() -> Recording:
    """Seeded synthetic signal, not participant or normative data."""
    sfreq = 256.0
    times = np.arange(int(sfreq * 66)) / sfreq
    rng = np.random.default_rng(42)
    data = rng.normal(0, 2e-6, (len(CHANNELS), len(times)))
    data += 2e-6 * np.sin(2 * np.pi * 10 * times)[None, :]
    onsets = np.arange(3.0, 63.0, 2.5)
    codes = np.tile([1, 2], len(onsets) // 2)
    weights = np.array([0.35 + 0.65 * (name.startswith(("P", "O", "CP"))) for name in CHANNELS])
    for onset, code in zip(onsets, codes, strict=True):
        relative = times - onset
        response = (
            8 * np.exp(-(((relative - 0.38) / 0.08) ** 2))
            - 3 * np.exp(-(((relative - 0.16) / 0.04) ** 2))
            + 4 * np.exp(-(((relative - 0.65) / 0.14) ** 2))
        ) * 1e-6
        data += weights[:, None] * response * (1 if code == 1 else 0.7)
    info = mne.create_info(CHANNELS, sfreq, "eeg")
    raw = mne.io.RawArray(data, info, verbose=False)
    raw.set_montage(standard_montage_name(), verbose=False)
    events = np.column_stack([(onsets * sfreq).astype(int), np.zeros(len(onsets), int), codes])
    return prepare_preview(
        Recording(
            raw, events, {"Visual A": 1, "Visual B": 2}, "demo://visual-response-v1", demo=True
        )
    )


def read_recording(path: str | Path) -> Recording:
    path = Path(path).resolve()
    if path.suffix.lower() == ".fdt":
        companion = path.with_suffix(".set")
        if not companion.is_file():
            raise ValueError("FDT memerlukan file SET pendamping. Pilih SET yang merujuk FDT ini.")
        path = companion
    readers = {".bdf": mne.io.read_raw_bdf, ".edf": mne.io.read_raw_edf,
               ".set": mne.io.read_raw_eeglab}
    if path.suffix.lower() not in readers:
        raise ValueError("Format yang didukung: BDF, EDF, SET/FDT EEGLAB kontinu.")
    raw = readers[path.suffix.lower()](path, preload=False, verbose=False)
    if len(mne.pick_types(raw.info, stim=True)):
        events = mne.find_events(raw, shortest_event=1, verbose=False)
        event_id = {f"Trigger {code}": int(code) for code in np.unique(events[:, 2])}
    else:
        descriptions = set(raw.annotations.description)
        numeric_ids = ({str(value): int(value) for value in descriptions}
                       if descriptions and all(str(value).isdigit() and int(value) > 0
                                               for value in descriptions) else None)
        events, event_id = mne.events_from_annotations(raw, event_id=numeric_ids, verbose=False)
    if len(events) == 0 and len(raw.annotations):
        descriptions = set(raw.annotations.description)
        numeric_ids = ({str(value): int(value) for value in descriptions}
                       if descriptions and all(str(value).isdigit() and int(value) > 0
                                               for value in descriptions) else None)
        events, event_id = mne.events_from_annotations(raw, event_id=numeric_ids, verbose=False)
    return prepare_preview(Recording(raw, events, event_id, str(path)))


def analyze(recording: Recording, settings: Settings, event_name: str) -> Result:
    settings.validate(recording.raw.info["sfreq"])
    if event_name not in recording.event_id:
        raise ValueError("Pilih event yang tersedia sebelum menjalankan analisis.")
    raw = recording.raw.copy().load_data().pick("eeg")
    if settings.standard_montage and not recording.import_setup.get("positions"):
        raw.set_montage(
            standard_montage_name(), match_case=False, on_missing="raise", verbose=False
        )
    if settings.notch:
        raw.notch_filter([settings.notch], method="iir", verbose=False)
    raw.filter(settings.highpass or None, settings.lowpass, method="iir", verbose=False)
    if settings.average_reference:
        raw.set_eeg_reference("average", projection=False, verbose=False)
    code = recording.event_id[event_name]
    events = recording.events[recording.events[:, 2] == code]
    epochs = mne.Epochs(
        raw,
        events,
        event_id={event_name: code},
        tmin=settings.tmin,
        tmax=settings.tmax,
        baseline=(settings.baseline_start, settings.baseline_end),
        reject={"eeg": settings.reject_uv * 1e-6},
        preload=True,
        verbose=False,
    )
    if not len(epochs):
        raise ValueError("Seluruh epoch ditolak. Periksa ambang artefak dan batas rekaman.")
    evoked = epochs.average()
    history = {
        "time_utc": datetime.now(timezone.utc).isoformat(),
        "source": recording.source,
        "demo": recording.demo,
        "import_setup": recording.import_setup,
        "event": event_name,
        "event_code": code,
        "parameters": asdict(settings),
        "filter_method": "MNE IIR default Butterworth",
        "montage": standard_montage_name()
        if settings.standard_montage or recording.demo
        else "from source",
        "accepted": len(epochs),
        "rejected": len(events) - len(epochs),
        "drop_log": [list(reason) for reason in epochs.drop_log],
        "mne_version": mne.__version__,
        "numpy_version": np.__version__,
        "app_version": __version__,
    }
    return Result(evoked, len(epochs), len(events) - len(epochs), event_name, settings, history)
