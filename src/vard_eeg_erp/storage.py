"""Atomic project manifests and explicitly labelled numerical exports."""

import csv
import json
import os
import tempfile
from dataclasses import asdict
from pathlib import Path

from vard_eeg_erp.analysis import Recording, Result, Settings


def atomic_json(path: Path, payload: dict) -> None:
    descriptor, temporary = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            json.dump(payload, stream, indent=2, ensure_ascii=False, allow_nan=False)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def save_project(
    path: Path,
    recording: Recording,
    result: Result | None,
    settings: Settings,
    event: str,
    history: list[dict],
    view: dict,
) -> None:
    source = recording.source
    if not recording.demo:
        try:
            source = os.path.relpath(source, path.parent)
        except ValueError:  # Different Windows drives.
            source = recording.source
    atomic_json(
        path,
        {
            "schema_version": 1,
            "source": source,
            "demo": recording.demo,
            "import_setup": recording.import_setup,
            "settings": asdict(settings),
            "event": event,
            "history": history,
            "has_result": result is not None,
            "view": view,
        },
    )


def load_project(path: Path) -> dict:
    with path.open(encoding="utf-8") as stream:
        payload = json.load(stream)
    if payload.get("schema_version") != 1:
        raise ValueError("Versi project tidak didukung.")
    Settings(**payload["settings"])
    if not payload["demo"]:
        source = Path(payload["source"])
        if not source.is_absolute():
            source = path.parent / source
        if not source.is_file():
            raise ValueError(
                f"File sumber tidak ditemukan: {source}. Kembalikan file ke lokasi tersebut."
            )
        payload["source"] = str(source.resolve())
    return payload


def export_csv(path: Path, result: Result, demo: bool) -> None:
    """One row per time point; channel amplitudes in microvolts."""
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(
            ["time_ms", "event", "synthetic_demo", "accepted_trials"]
            + [f"{channel}_uV" for channel in result.evoked.ch_names]
        )
        for time, values in zip(result.evoked.times, result.evoked.data.T, strict=True):
            writer.writerow(
                [time * 1000, result.event_name, demo, result.accepted] + (values * 1e6).tolist()
            )
