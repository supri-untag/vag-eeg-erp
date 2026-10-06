"""AATR workspace: measured ERP features separated from imported reference results."""

from pathlib import Path

import numpy as np
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from PySide6.QtWidgets import QComboBox, QTableWidgetItem, QTabWidget, QVBoxLayout, QWidget

from vard_eeg_erp.aatr_dashboard_ui import AATRDashboard
from vard_eeg_erp.aatr_ui import AATRPanel
from vard_eeg_erp.presentation import WINDOWS
from vard_eeg_erp.widgets import button, label, table


class AATRWorkspace(QWidget):
    def __init__(self, import_callback):
        super().__init__()
        self.result = None
        layout = QVBoxLayout(self)
        tabs = QTabWidget()
        layout.addWidget(tabs)
        page = QWidget()
        content = QVBoxLayout(page)
        content.addWidget(button('Import EEG / SET + FDT', import_callback))
        self.context = label('Import SET (FDT diletakkan pada folder yang sama), lalu pilih '
                             'event dan Generate ERP di Overview. Hasil muncul di sini.', 'notice')
        self.context.setWordWrap(True)
        content.addWidget(self.context)
        self.channel = QComboBox()
        self.channel.currentIndexChanged.connect(self.render)
        content.addWidget(self.channel)
        self.figure = Figure(figsize=(9, 3), tight_layout=True)
        self.canvas = FigureCanvasQTAgg(self.figure)
        content.addWidget(self.canvas, 1)
        self.grid = table(['Window', 'Mean µV', 'Peak µV', 'Latency ms', 'Kelas AATR'])
        self.grid.setRowCount(3)
        self.grid.setMaximumHeight(160)
        self.grid.setEditTriggers(self.grid.EditTrigger.NoEditTriggers)
        content.addWidget(self.grid)
        note = label('Fitur channel terpilih dari ERP aktif, bukan grand-average 43 subjek. '
                     'Kelas A0–A4 belum dihitung otomatis: ROI, normalisasi Z dan '
                     'acuan penelitian harus ditentukan terlebih dahulu.', 'notice')
        note.setWordWrap(True)
        content.addWidget(note)
        tabs.addTab(page, 'Data rekaman')
        tabs.addTab(AATRPanel(), 'Level / MAT acuan')
        tabs.addTab(AATRDashboard(), 'Dashboard FIG acuan')
        self.set_result(None)

    def set_result(self, result):
        self.result = result
        self.channel.blockSignals(True)
        previous = self.channel.currentText()
        self.channel.clear()
        if result is not None:
            self.channel.addItems(result.evoked.ch_names)
            if previous in result.evoked.ch_names:
                self.channel.setCurrentText(previous)
            source = result.history.get('source', '')
            self.context.setText(f'{Path(source).name} · {result.event_name} · '
                                 f'{result.accepted} trial diterima · '
                                 + ('DEMO SINTETIS' if result.history.get('demo') else 'Data rekaman'))
        else:
            self.context.setText('Belum ada ERP aktif. Import data, pilih event dan Generate ERP '
                                 'di Overview. FDT memerlukan SET pendamping.')
        self.channel.blockSignals(False)
        self.render()

    def render(self):
        self.figure.clear()
        self.grid.clearContents()
        ax = self.figure.add_subplot(111)
        if self.result is None:
            ax.text(.5, .5, 'Generate ERP untuk menampilkan hasil rekaman', ha='center')
            ax.axis('off')
        else:
            result = self.result
            index = self.channel.currentIndex()
            ax.plot(result.evoked.times * 1000, result.evoked.data[index] * 1e6,
                    color='#1B84FF', linewidth=1.5)
            ax.axhline(0, color='.6', linewidth=.6)
            ax.set(xlabel='Waktu (ms)', ylabel='µV', title=self.channel.currentText())
            for row, ((name, start, end), color) in enumerate(zip(
                    WINDOWS, ['#dceef8', '#ebe1f9', '#fff0ce'])):
                ax.axvspan(start, end, color=color, alpha=.35)
                try:
                    values = result.metrics(self.channel.currentText(), start, end)
                    data = [name, f"{values['mean_uv']:.4f}", f"{values['peak_uv']:.4f}",
                            f"{values['latency_ms']:.1f}", 'Perlu normalisasi Z']
                except ValueError:
                    data = [name, 'Window di luar epoch', '—', '—', '—']
                for col, value in enumerate(data):
                    self.grid.setItem(row, col, QTableWidgetItem(value))
            ax.set_xlim(np.array([result.evoked.times[0], result.evoked.times[-1]]) * 1000)
        self.canvas.draw_idle()
