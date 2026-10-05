"""Explicit CED channel mapping and trigger grouping; raw files remain unchanged."""
import csv
from dataclasses import replace

import mne
import numpy as np

from vard_eeg_erp.analysis import prepare_preview


def ced_setup(ced, mapping):
    with open(ced, encoding='utf-8-sig') as stream:
        coordinates = {row['labels']: np.array([float(row[k]) for k in ('X', 'Y', 'Z')])
                       for row in csv.DictReader(stream, delimiter='\t')}
    with open(mapping, encoding='utf-8-sig') as stream:
        rows = list(csv.DictReader(stream))
    selected, excluded = {}, []
    for row in rows:
        name = row['OriginalLabel']
        if name in selected or name in excluded:
            raise ValueError('Channel duplikat pada mapping.')
        if row['UsedForTopoplot'].upper() == 'YES':
            xyz = coordinates[row['ActiveElectrode']]
            if not np.isfinite(xyz).all() or np.linalg.norm(xyz) == 0:
                raise ValueError('Koordinat CED tidak valid.')
            # EEGLAB: X anterior, Y left. MNE: X right, Y anterior.
            selected[name] = (np.array([-xyz[1], xyz[0], xyz[2]]) /
                              np.linalg.norm(xyz) * .095).tolist()
        elif row['UsedForTopoplot'].upper() == 'NO':
            excluded.append(name)
        else:
            raise ValueError('UsedForTopoplot harus YES atau NO.')
    if len(selected) < 4:
        raise ValueError('Minimal 4 channel berposisi diperlukan.')
    return {'positions': selected, 'excluded': excluded,
            'coordinate_model': 'EEGLAB XYZ directions → MNE head; sphere radius 0.095 m'}


def read_groups(path):
    with open(path, encoding='utf-8-sig') as stream:
        rows = list(csv.DictReader(stream))
    result = {}
    for row in rows:
        code, category = str(int(row['event_code'])), row['category'].strip()
        if not category or code in result:
            raise ValueError('Kategori kosong atau kode trigger duplikat.')
        result[code] = category
    if not result:
        raise ValueError('Mapping kategori kosong.')
    return result


def apply_setup(recording, setup):
    raw = recording.raw.copy()
    if setup.get('positions'):
        positions = setup['positions']
        excluded = setup.get('excluded', [])
        eeg = {n for n, t in zip(raw.ch_names, raw.get_channel_types()) if t == 'eeg'}
        if set(positions) & set(excluded) or set(positions) | set(excluded) != eeg:
            raise ValueError('Mapping harus mencakup seluruh channel EEG tepat satu kali.')
        raw.set_channel_types({n: 'misc' for n in excluded})
        raw.set_montage(mne.channels.make_dig_montage(ch_pos=positions, coord_frame='head'))
    events = recording.events.copy()
    event_id = dict(recording.event_id)
    if setup.get('groups'):
        groups = setup['groups']
        codes = set(events[:, 2].tolist())
        if {int(c) for c in groups} != codes:
            raise ValueError('CSV kategori harus mencakup semua kode trigger rekaman.')
        event_id = {name: i + 1 for i, name in enumerate(dict.fromkeys(groups.values()))}
        events[:, 2] = [event_id[groups[str(int(code))]] for code in events[:, 2]]
    return prepare_preview(replace(recording, raw=raw, events=events,
                                   event_id=event_id, import_setup=setup))
