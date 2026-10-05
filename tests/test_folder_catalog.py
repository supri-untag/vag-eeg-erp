from unittest.mock import patch

from vard_eeg_erp.folder_catalog import scan_folder
from vard_eeg_erp.folder_catalog_ui import FolderCatalog


def test_recursive_scan_keeps_bad_and_companion_files(tmp_path, recording):
    child = tmp_path / 'SUBJEK 101'
    child.mkdir()
    (child / 'good.BDF').write_bytes(b'placeholder')
    (child / 'bad.edf').write_bytes(b'broken')
    (child / 'analysis.m').write_text('error("must never execute")')
    (child / 'record.set').write_bytes(b'placeholder')
    (child / 'record.fdt').write_bytes(b'placeholder')

    def read(path):
        if path.suffix.lower() == '.edf':
            raise ValueError('invalid header')
        return recording

    with patch('vard_eeg_erp.folder_catalog.read_recording', side_effect=read):
        rows = scan_folder(tmp_path)
    assert len(rows) == 5
    assert sum(r['readable'] for r in rows) == 1
    assert next(r for r in rows if r['name'].endswith('bad.edf'))['status'] == 'Gagal dibaca'
    assert 'FDT senama tersedia' in next(r for r in rows if r['name'].endswith('.set'))['notes']
    assert (child / 'analysis.m').read_text() == 'error("must never execute")'


def test_empty_folder(tmp_path):
    assert scan_folder(tmp_path) == []


def test_catalog_opens_only_readable_recording(tmp_path):
    from vard_eeg_erp.app import create_application

    app = create_application()
    dialog = FolderCatalog()
    rows = [{'name': 'sample.bdf', 'path': '/sample.bdf', 'status': 'Terbaca',
             'readable': True, 'channels': 16, 'sfreq': 200, 'duration': 60,
             'events': 2, 'notes': ''},
            {'name': 'notes.m', 'path': '/notes.m', 'status': 'Pendukung',
             'readable': False, 'channels': '', 'sfreq': '', 'duration': '',
             'events': '', 'notes': ''}]
    dialog.populate(str(tmp_path), rows)
    opened = []
    dialog.open_requested.connect(opened.append)
    dialog.grid.selectRow(1)
    dialog.open_selected()
    assert opened == []
    dialog.grid.selectRow(0)
    dialog.open_selected()
    assert opened == ['/sample.bdf']
    dialog.close()
    app.processEvents()
