from dataclasses import asdict

import mne
import numpy as np
import pyqtgraph as pg
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QFrame,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QVBoxLayout,
)

from vard_eeg_erp.analysis import Result, Settings


def label(text: str, role: str = "") -> QLabel:
    widget = QLabel(text)
    widget.setObjectName(role)
    widget.setTextFormat(Qt.TextFormat.PlainText)
    return widget


def button(text: str, callback=None, primary: bool = False) -> QPushButton:
    widget = QPushButton(text.replace("&", "&&"))
    if primary:
        widget.setObjectName("primary")
    if callback:
        widget.clicked.connect(callback)
    widget.setCursor(Qt.CursorShape.PointingHandCursor)
    return widget


def card(title: str = "", subtitle: str = "") -> tuple[QFrame, QVBoxLayout]:
    frame = QFrame()
    frame.setObjectName("card")
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(20, 18, 20, 18)
    layout.setSpacing(10)
    if title:
        layout.addWidget(label(title, "section"))
    if subtitle:
        text = label(subtitle, "muted")
        text.setWordWrap(True)
        layout.addWidget(text)
    return frame, layout


def table(headers: list[str]) -> QTableWidget:
    widget = QTableWidget(0, len(headers))
    widget.setHorizontalHeaderLabels(headers)
    widget.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
    widget.verticalHeader().hide()
    widget.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
    widget.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
    widget.setAlternatingRowColors(True)
    widget.setShowGrid(False)
    return widget


def plot_widget(x_label: str, y_label: str) -> pg.PlotWidget:
    plot = pg.PlotWidget(background="w")
    plot.setLabel("bottom", x_label)
    plot.setLabel("left", y_label)
    plot.showGrid(x=True, y=True, alpha=0.12)
    plot.getPlotItem().hideButtons()
    plot.setMenuEnabled(False)
    for side in ("bottom", "left"):
        plot.getAxis(side).setPen(pg.mkPen("#CBD5E1"))
        plot.getAxis(side).setTextPen(pg.mkPen("#78829D"))
    return plot


def limit_plot_zoom(plot, x_values, y_values):
    """Fit data and bound zoom/pan to its padded extent on both axes."""
    ranges = []
    for values, padding, minimum in [(x_values, 0.02, 1e-3), (y_values, 0.1, 1.0)]:
        values = np.asarray(values)
        finite = values[np.isfinite(values)]
        if not finite.size:
            return
        low, high = float(finite.min()), float(finite.max())
        margin = max(high - low, minimum) * padding
        ranges.append((low - margin, high + margin))
    (xmin, xmax), (ymin, ymax) = ranges
    view = plot.getViewBox()
    view.setLimits(
        xMin=xmin, xMax=xmax, yMin=ymin, yMax=ymax,
        maxXRange=xmax - xmin, maxYRange=ymax - ymin,
    )
    view.setRange(xRange=ranges[0], yRange=ranges[1], padding=0)


class ERPPlot(pg.PlotWidget):
    time_selected = Signal(float)

    def __init__(self):
        super().__init__(background="w")
        self.setLabel("bottom", "Waktu", units="ms")
        self.setLabel("left", "Amplitudo", units="µV")
        self.getAxis("bottom").enableAutoSIPrefix(False)
        self.getAxis("left").enableAutoSIPrefix(False)
        self.showGrid(x=True, y=True, alpha=0.12)
        self.setMenuEnabled(False)
        self.getPlotItem().hideButtons()
        self.curve = self.plot(pen=pg.mkPen("#1B84FF", width=2.5))
        self.onset = pg.InfiniteLine(0, pen=pg.mkPen("#99A1B7", style=Qt.PenStyle.DashLine))
        self.addItem(self.onset)
        self.region = pg.LinearRegionItem(
            (300, 500), movable=False, brush=pg.mkBrush(27, 132, 255, 15), pen=pg.mkPen(None)
        )
        self.region.setZValue(-10)
        self.addItem(self.region)
        self.cursor = pg.InfiniteLine(400, movable=True, pen=pg.mkPen("#17C653", width=2))
        self.addItem(self.cursor)
        self.cursor.sigPositionChangeFinished.connect(
            lambda: self.time_selected.emit(float(self.cursor.value()))
        )
        self.scene().sigMouseClicked.connect(self._clicked)
        self.setToolTip(
            "Klik grafik atau geser garis hijau untuk menyinkronkan topomap dan channel."
        )

    def _clicked(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.sceneBoundingRect().contains(
            event.scenePos()
        ):
            point = self.getPlotItem().vb.mapSceneToView(event.scenePos())
            self.time_selected.emit(point.x())

    def display(self, result: Result, channel: str):
        times = result.evoked.times * 1000
        values = result.evoked.data[result.evoked.ch_names.index(channel)] * 1e6
        self.curve.setData(times, values)
        self.cursor.setBounds((float(times[0]), float(times[-1])))
        limit_plot_zoom(self, times, values)


class Topomap(FigureCanvasQTAgg):
    def __init__(self):
        self.figure = Figure(figsize=(3.6, 2.9), facecolor="white")
        super().__init__(self.figure)
        self.setMinimumSize(250, 235)
        self.message("Jalankan analisis untuk melihat topomap")

    def message(self, message: str):
        self.figure.clear()
        axis = self.figure.add_subplot(111)
        axis.axis("off")
        axis.text(
            0.5,
            0.5,
            message,
            ha="center",
            va="center",
            wrap=True,
            color="#78829D",
            fontsize=10,
            transform=axis.transAxes,
        )
        self.draw_idle()

    def display(self, result: Result, sample: int):
        info = result.evoked.info
        positions = np.array([channel["loc"][:3] for channel in info["chs"]])
        if (
            len(positions) < 4
            or not np.isfinite(positions).all()
            or np.any(np.linalg.norm(positions, axis=1) == 0)
        ):
            self.message("Posisi elektroda belum lengkap.\nAtur montage di parameter analisis.")
            return
        self.figure.clear()
        axis = self.figure.add_axes((0.03, 0.08, 0.76, 0.86))
        limit = max(float(np.max(np.abs(result.evoked.data))) * 1e6, 0.1)
        try:
            image, _ = mne.viz.plot_topomap(
                result.evoked.data[:, sample] * 1e6,
                info,
                axes=axis,
                show=False,
                cmap="RdBu_r",
                vlim=(-limit, limit),
                contours=4,
                res=64,
            )
            color_axis = self.figure.add_axes((0.85, 0.23, 0.035, 0.54))
            colorbar = self.figure.colorbar(image, cax=color_axis)
            colorbar.ax.tick_params(labelsize=8, colors="#78829D")
            colorbar.set_label("µV", fontsize=9, color="#78829D")
            colorbar.outline.set_visible(False)
            self.draw_idle()
        except (ValueError, RuntimeError) as error:
            self.message(f"Topomap belum tersedia:\n{error}")


class SettingsDialog(QDialog):
    def __init__(self, settings: Settings, parent=None, sfreq=200):
        super().__init__(parent)
        self.sfreq = sfreq
        self.setWindowTitle("Parameter analisis")
        self.setMinimumWidth(460)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.addWidget(label("Preprocessing & epoch", "title"))
        note = label("Parameter diterapkan pada salinan data. File asli tetap utuh.", "muted")
        note.setWordWrap(True)
        layout.addWidget(note)
        form = QFormLayout()
        form.setVerticalSpacing(10)
        layout.addLayout(form)
        self.fields = {}
        definitions = [
            ("highpass", "Batas bawah / high-pass (Hz; 0 = off)", 0, 10, 1),
            ("lowpass", "Batas atas / low-pass (Hz)", 0.1, min(50, sfreq / 2 - .01), 1),
            ("tmin", "Awal epoch (ms)", -10000, 10000, 1000),
            ("tmax", "Akhir epoch (ms)", -10000, 10000, 1000),
            ("baseline_start", "Awal baseline (ms)", -10000, 10000, 1000),
            ("baseline_end", "Akhir baseline (ms)", -10000, 10000, 1000),
            ("reject_uv", "Ambang peak-to-peak (µV)", 0.1, 100000, 1),
        ]
        self.scales = {}
        for name, caption, minimum, maximum, scale in definitions:
            field = QDoubleSpinBox()
            field.setRange(minimum, maximum)
            field.setDecimals(2)
            field.setValue(getattr(settings, name) * scale)
            form.addRow(caption, field)
            self.fields[name] = field
            self.scales[name] = scale
        self.notch = QComboBox()
        self.notch.addItems(["Off", "50 Hz", "60 Hz"])
        self.notch.setCurrentIndex([0, 50, 60].index(settings.notch))
        form.addRow("Notch", self.notch)
        self.reference = QCheckBox("Average reference")
        self.reference.setChecked(settings.average_reference)
        form.addRow("Referensi", self.reference)
        self.montage = QCheckBox("Gunakan standard 10–20 dari nama channel")
        self.montage.setChecked(settings.standard_montage)
        self.montage.setToolTip(
            "Aktifkan hanya jika nama dan susunan elektroda sesuai standard 10–20."
        )
        form.addRow("Montage", self.montage)
        self.original = asdict(settings)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def validate_and_accept(self):
        try:
            self.settings().validate(self.sfreq)
        except ValueError as error:
            QMessageBox.warning(self, "Parameter belum valid", str(error))
            return
        self.accept()

    def settings(self) -> Settings:
        values = self.original.copy()
        for name, field in self.fields.items():
            values[name] = field.value() / self.scales[name]
        values.update(
            notch=[0, 50, 60][self.notch.currentIndex()],
            average_reference=self.reference.isChecked(),
            standard_montage=self.montage.isChecked(),
        )
        return Settings(**values)
