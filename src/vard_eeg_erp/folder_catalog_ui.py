"""Persistent in-session folder inventory with explicit recording selection."""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QDialog, QHBoxLayout, QTableWidgetItem, QVBoxLayout

from vard_eeg_erp.widgets import button, label, table


class FolderCatalog(QDialog):
    open_requested = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Katalog folder EEG')
        self.resize(1100, 650)
        self.rows = []
        layout = QVBoxLayout(self)
        self.summary = label('Pilih folder untuk memindai data.')
        self.summary.setWordWrap(True)
        layout.addWidget(self.summary)
        note = label('Pemeriksaan awal: header, preview 10 detik, event dan posisi channel. '
                     'Bukan validasi kualitas seluruh sinyal. Data asli tidak diubah; '
                     'rekaman dibuka satu per satu, tidak digabung otomatis.', 'notice')
        note.setWordWrap(True)
        layout.addWidget(note)
        self.grid = table(['File', 'Status', 'EEG', 'Hz', 'Detik', 'Event', 'Catatan'])
        self.grid.setEditTriggers(self.grid.EditTrigger.NoEditTriggers)
        self.grid.setSelectionBehavior(self.grid.SelectionBehavior.SelectRows)
        self.grid.setSelectionMode(self.grid.SelectionMode.SingleSelection)
        self.grid.itemSelectionChanged.connect(self.selection_changed)
        self.grid.cellDoubleClicked.connect(lambda *_: self.open_selected())
        layout.addWidget(self.grid)
        controls = QHBoxLayout()
        self.open_button = button('Buka rekaman terpilih', self.open_selected, True)
        self.open_button.setEnabled(False)
        controls.addWidget(self.open_button)
        controls.addWidget(button('Tutup', self.hide))
        layout.addLayout(controls)

    def populate(self, folder, rows):
        self.rows = rows
        count = sum(row['readable'] for row in rows)
        failed = sum(row['status'] == 'Gagal dibaca' for row in rows)
        self.summary.setText(f'{folder}\n{len(rows)} file · {count} rekaman terbaca · '
                             f'{failed} gagal · katalog disimpan selama aplikasi terbuka')
        self.grid.setRowCount(len(rows))
        for i, row in enumerate(rows):
            for j, key in enumerate(['name', 'status', 'channels', 'sfreq', 'duration', 'events', 'notes']):
                item = QTableWidgetItem(str(row[key]))
                item.setToolTip(str(row[key]))
                self.grid.setItem(i, j, item)
        self.grid.setColumnWidth(0, 280)
        self.grid.setColumnWidth(1, 110)
        self.grid.setColumnWidth(6, 450)
        self.selection_changed()

    def selection_changed(self):
        i = self.grid.currentRow()
        self.open_button.setEnabled(0 <= i < len(self.rows) and self.rows[i]['readable'])

    def open_selected(self):
        i = self.grid.currentRow()
        if 0 <= i < len(self.rows) and self.rows[i]['readable']:
            self.open_requested.emit(self.rows[i]['path'])
