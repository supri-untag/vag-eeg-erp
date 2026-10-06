"""Read-only recursive inventory; companion files are never run or guessed as EEG."""

from pathlib import Path

import numpy as np

from vard_eeg_erp.analysis import read_recording


def scan_folder(folder):
    root = Path(folder).resolve()
    if not root.is_dir():
        raise ValueError('Folder tidak ditemukan.')
    rows = []
    for path in sorted(root.rglob('*')):
        if not path.is_file() or path.is_symlink():
            continue
        row = {'path': str(path), 'name': str(path.relative_to(root)),
               'status': 'Pendukung', 'channels': '', 'sfreq': '', 'duration': '',
               'events': '', 'notes': '', 'readable': False}
        suffix = path.suffix.lower()
        if suffix in ('.bdf', '.edf', '.set'):
            recording = None
            try:
                recording = read_recording(path)
                raw = recording.raw
                eeg = [ch for ch, kind in zip(raw.info['chs'], raw.get_channel_types())
                       if kind == 'eeg']
                notes = []
                if not len(recording.events):
                    notes.append('Tidak ada event; ERP belum tersedia')
                elif len(np.unique(recording.events[:, 2])) == len(recording.events):
                    notes.append('Tiap kode hanya 1 trial; perlu pemetaan kategori')
                if any(not np.isfinite(ch['loc'][:3]).all() or
                       np.linalg.norm(ch['loc'][:3]) == 0 for ch in eeg):
                    notes.append('Posisi elektroda belum lengkap')
                if any(ch['ch_name'].lower().startswith('add_lead') for ch in eeg):
                    notes.append('Identitas Add_lead perlu dikonfirmasi')
                if 'provisional' in path.name.lower():
                    notes.append('PROVISIONAL: konfirmasi timing marker dengan log stimulus')
                row.update(status='Perlu tinjau' if notes else 'Terbaca', readable=True,
                           channels=len(eeg), sfreq=raw.info['sfreq'],
                           duration=round(raw.n_times / raw.info['sfreq'], 2),
                           events=len(recording.events), notes='; '.join(notes))
            except Exception as error:
                row.update(status='Gagal dibaca', notes=str(error))
            finally:
                if recording is not None:
                    recording.raw.close()
        elif suffix == '.fdt':
            row['notes'] = 'Data pendamping SET; bukan rekaman mandiri'
        elif suffix == '.m':
            row['notes'] = 'Script MATLAB dicatat saja, tidak dijalankan'
        elif suffix == '.ced':
            row['notes'] = 'Koordinat channel; belum diterapkan otomatis'
        else:
            row['notes'] = 'File pendukung; tidak digabung otomatis dengan rekaman'
        rows.append(row)
    return rows
