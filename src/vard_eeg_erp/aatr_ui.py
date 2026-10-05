"""Explicit input of normalized AATR magnitudes; never guesses normalization."""

from pathlib import Path

from PySide6.QtWidgets import (
    QDoubleSpinBox,
    QFileDialog,
    QHBoxLayout,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from vard_eeg_erp.aatr import BOUNDS, classify, read_summary
from vard_eeg_erp.widgets import button, label, table


class AATRPanel(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.addWidget(label('AATR V7B · level respons empiris', 'section'))
        note = label(
            'A0–A4 = besar respons relatif acuan 43 subjek; ± = polaritas ERP. '
            'Bukan keindahan, kesukaan, atau valensi estetika. Masukkan |Z| yang sudah '
            'dinormalisasi sesuai protokol; amplitudo µV tidak otomatis diubah menjadi Z.', 'notice')
        note.setWordWrap(True)
        layout.addWidget(note)
        self.bounds = BOUNDS.copy()
        self.source = label('Acuan: AATR_V7B_EMPIRICAL_ANALYSIS.mat · batas asli lampiran')
        layout.addWidget(self.source)
        self.thresholds = label('')
        layout.addWidget(self.thresholds)
        controls = QHBoxLayout()
        self.magnitude = QDoubleSpinBox()
        self.magnitude.setDecimals(6)
        self.magnitude.setRange(0, 1000000)
        self.amplitude = QDoubleSpinBox()
        self.amplitude.setDecimals(6)
        self.amplitude.setRange(-1000000, 1000000)
        controls.addWidget(label('|Z| / median |Z|'))
        controls.addWidget(self.magnitude)
        controls.addWidget(label('Mean ERP (µV)'))
        controls.addWidget(self.amplitude)
        controls.addWidget(button('Hitung level', self.calculate))
        controls.addWidget(button('Buka hasil MAT', self.open_mat))
        layout.addLayout(controls)
        self.answer = label('Belum dihitung · input manual, tidak terhubung otomatis ke EEG.')
        layout.addWidget(self.answer)
        self.magnitude.valueChanged.connect(self.invalidate)
        self.amplitude.valueChanged.connect(self.invalidate)
        self.grid = table(['Atribut', 'Window', 'Median |Z|', 'Mean µV', 'Kelas', 'Level'])
        self.grid.setMinimumHeight(220)
        self.grid.setEditTriggers(self.grid.EditTrigger.NoEditTriggers)
        layout.addWidget(self.grid)
        self.update_bounds()

    def update_bounds(self):
        self.thresholds.setText('Batas |Z|: ' + ' · '.join(f'{x:.9f}' for x in self.bounds)
                                + ' · tepat di batas masuk kelas berikutnya')

    def invalidate(self):
        self.answer.setText('Input berubah · klik Hitung level.')

    def calculate(self):
        code, level = classify(self.magnitude.value(), self.amplitude.value(), self.bounds)
        self.answer.setText(f'{code} · {level} · input manual, bukan hasil otomatis EEG')

    def open_mat(self):
        path, _ = QFileDialog.getOpenFileName(self, 'Buka hasil AATR V7B', '', 'MATLAB (*.mat)')
        if not path:
            return
        try:
            bounds, rows = read_summary(path)
        except (ValueError, KeyError, OSError, TypeError) as error:
            self.answer.setText(f'File AATR tidak dapat dibaca: {error}')
            return
        self.bounds = bounds
        self.source.setText(f'Hasil penelitian diimpor: {Path(path).name} · bukan rekaman aktif')
        self.update_bounds()
        self.invalidate()
        self.grid.setRowCount(len(rows))
        for row, values in enumerate(rows):
            for column, value in enumerate(values):
                self.grid.setItem(row, column, QTableWidgetItem(value))
        self.grid.resizeColumnsToContents()
