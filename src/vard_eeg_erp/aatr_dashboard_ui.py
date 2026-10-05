"""AATR reference dashboard with zoom and publication export."""

from pathlib import Path

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg, NavigationToolbar2QT
from PySide6.QtWidgets import QFileDialog, QHBoxLayout, QScrollArea, QVBoxLayout, QWidget

from vard_eeg_erp.aatr_dashboard import read_figure, render_figure
from vard_eeg_erp.widgets import button, label


class AATRDashboard(QWidget):
    def __init__(self):
        super().__init__()
        self.figure = None
        self.canvas = None
        self.toolbar = None
        layout = QVBoxLayout(self)
        controls = QHBoxLayout()
        controls.addWidget(button('Buka dashboard FIG', self.open_figure))
        self.export_button = button('Ekspor PNG / PDF', self.export)
        self.export_button.setEnabled(False)
        controls.addWidget(self.export_button)
        controls.addStretch()
        layout.addLayout(controls)
        self.status = label('Buka AATR_V7B_EMPIRICAL_NO_TOOLBOX.fig untuk menampilkan '
                            'enam grafik ERP, temporal prominence, klasifikasi, dan legenda.', 'notice')
        self.status.setWordWrap(True)
        layout.addWidget(self.status)
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        layout.addWidget(self.scroll, 1)
        self.content = QWidget()
        self.content_layout = QVBoxLayout(self.content)
        self.scroll.setWidget(self.content)

    def load(self, path):
        figure = render_figure(read_figure(path))
        canvas = FigureCanvasQTAgg(figure)
        canvas.setMinimumSize(1280, 800)
        toolbar = NavigationToolbar2QT(canvas, self.content)
        for widget in [self.toolbar, self.canvas]:
            if widget is not None:
                self.content_layout.removeWidget(widget)
                widget.deleteLater()
        self.figure, self.canvas, self.toolbar = figure, canvas, toolbar
        self.content_layout.addWidget(toolbar)
        self.content_layout.addWidget(canvas)
        canvas.draw()
        self.status.setText(f'Hasil penelitian dari {Path(path).name} · '
                            'bukan analisis rekaman EEG aktif. Kurva dan label mengikuti file FIG.')
        self.export_button.setEnabled(True)

    def open_figure(self):
        path, _ = QFileDialog.getOpenFileName(self, 'Buka dashboard AATR', '', 'MATLAB figure (*.fig)')
        if path:
            try:
                self.load(path)
            except (ValueError, TypeError, KeyError, OSError, NotImplementedError) as error:
                self.status.setText(f'FIG tidak dapat dibuka: {error}')

    def export(self):
        if self.figure is None:
            return
        path, selected = QFileDialog.getSaveFileName(self, 'Ekspor dashboard', 'AATR-dashboard.png',
                                                     'PNG (*.png);;PDF (*.pdf)')
        if path:
            target = Path(path)
            if target.suffix.lower() not in ('.png', '.pdf'):
                target = target.with_suffix('.pdf' if selected.startswith('PDF') else '.png')
            try:
                self.figure.savefig(target, dpi=200)
            except (OSError, ValueError) as error:
                self.status.setText(f'Ekspor gagal: {error}')
