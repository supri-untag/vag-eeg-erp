"""Three component maps and event slideshow inspired by the user's reference video."""

import time
from collections import deque

import mne
import numpy as np
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure
from PySide6.QtCore import QRectF, Qt, QTimer
from PySide6.QtGui import QImage, QPainter
from PySide6.QtWidgets import QComboBox, QHBoxLayout, QSlider, QVBoxLayout, QWidget

from vard_eeg_erp.widgets import button, label

WINDOWS = [("Early", 0, 200), ("P300", 300, 500), ("LPP", 500, 800)]


def component_values(result):
    times = result.evoked.times * 1000
    values = []
    for name, start, end in WINDOWS:
        if start < times[0] or end > times[-1]:
            raise ValueError(f"Window {name} {start}–{end} ms tidak tercakup epoch.")
        mask = (times >= start) & (times <= end)
        if mask.sum() < 2:
            raise ValueError(f"Window {name} membutuhkan minimal dua sampel.")
        values.append(result.evoked.data[:, mask].mean(axis=1) * 1e6)
    return np.array(values)


class CachedCanvas(QWidget):
    """Paint prepared images; no Matplotlib work during playback."""

    def __init__(self):
        super().__init__()
        self.first = self.second = None
        self.alpha = 0.0
        self.paint_times = deque(maxlen=500)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), Qt.GlobalColor.white)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        for image, opacity in [(self.first, 1.0), (self.second, self.alpha)]:
            if image is None or opacity <= 0:
                continue
            size = image.size().scaled(self.size(), Qt.AspectRatioMode.KeepAspectRatio)
            target = QRectF(
                (self.width() - size.width()) / 2,
                (self.height() - size.height()) / 2,
                size.width(),
                size.height(),
            )
            painter.setOpacity(opacity)
            painter.drawImage(target, image)
        self.paint_times.append(time.perf_counter())


class Presentation(QWidget):
    def __init__(self, prepare, parent=None):
        super().__init__(parent)
        self.results = []
        self.values = []
        self.limit = 1.0
        self.timer = QTimer(self)
        self.timer.setInterval(16)
        self.timer.setTimerType(Qt.TimerType.PreciseTimer)
        self.timer.timeout.connect(self.tick)
        self.prepare_timer = QTimer(self)
        self.prepare_timer.setSingleShot(True)
        self.prepare_timer.timeout.connect(self.prepare_next)
        self.cache = []
        self.last_tick = None
        self.elapsed = 0.0
        layout = QVBoxLayout(self)
        controls = QHBoxLayout()
        self.prepare_button = button("Siapkan semua event", prepare, True)
        self.play = button("▶ Putar", self.toggle)
        self.stop = button("■ Stop", self.reset)
        self.speed = QComboBox()
        for text, rate in [("0,1×", 0.1), ("0,25×", 0.25), ("0,5×", 0.5), ("1×", 1.0)]:
            self.speed.addItem(text, rate)
        self.speed.setCurrentIndex(3)
        self.speed.currentIndexChanged.connect(self.restart_clock)
        for widget in [self.play, self.stop, self.speed, self.prepare_button]:
            controls.addWidget(widget)
        controls.addStretch()
        layout.addLayout(controls)
        self.title = label("Belum ada hasil ERP", "section")
        layout.addWidget(self.title)
        self.figure = Figure(figsize=(12, 4), dpi=100, facecolor="white")
        self.agg = FigureCanvasAgg(self.figure)
        self.canvas = CachedCanvas()
        self.canvas.setMinimumHeight(260)
        layout.addWidget(self.canvas, 1)
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.valueChanged.connect(self.seek)
        layout.addWidget(self.slider)
        self.progress = label("0,00 / 0,00 detik", "muted")
        layout.addWidget(self.progress)
        note = label(
            "Mean amplitude per window (µV) · warna simetris dan tetap antar-event.\n"
            "Setiap frame = ERP satu jenis event, bukan satu trial atau sampel waktu.\n"
            "Fade antar-event adalah transisi visual, bukan data EEG perantara.",
            "notice",
        )
        note.setWordWrap(True)
        layout.addWidget(note)
        self.clear()

    def pause(self):
        self.timer.stop()
        self.play.setText("▶ Putar")

    def clear(self):
        self.pause()
        self.results = []
        self.values = []
        self.elapsed = 0.0
        self.slider.setValue(0)
        self.progress.setText("0,00 / 0,00 detik")
        self.prepare_timer.stop()
        self.cache = []
        self.figure.clear()
        axis = self.figure.add_subplot(111)
        axis.axis("off")
        axis.text(
            0.5, 0.5, "Generate ERP atau klik Siapkan semua event", ha="center", color="#78829D"
        )
        self.agg.draw()
        self.canvas.first = self.capture_image()
        self.canvas.second = None
        self.canvas.update()
        self.title.setText("Belum ada hasil ERP")
        for widget in [self.play, self.stop, self.slider]:
            widget.setEnabled(False)

    def set_results(self, results):
        self.clear()
        try:
            values = [component_values(result) for result in results]
        except ValueError as error:
            self.title.setText(str(error))
            return
        if not results:
            return
        if len(results) > 64:
            self.title.setText(
                "Presentasi dibatasi 64 jenis event untuk menjaga penggunaan memori."
            )
            return
        self.results, self.values = results, values
        self.limit = max(max(float(np.max(np.abs(value))) for value in values), 0.1)
        self.slider.blockSignals(True)
        self.slider.setRange(0, len(results) * 1500)
        self.slider.setValue(0)
        self.slider.blockSignals(False)
        self.slider.setEnabled(False)
        self.play.setEnabled(False)
        self.stop.setEnabled(True)
        self.prepare_next()

    def toggle(self):
        if self.timer.isActive():
            self.pause()
        elif len(self.results) > 1 and len(self.cache) == len(self.results):
            if self.slider.value() == self.slider.maximum():
                self.slider.setValue(0)
            self.restart_clock()
            self.timer.start()
            self.play.setText("Ⅱ Pause")

    def reset(self):
        self.pause()
        self.seek(0)

    def advance(self):
        index = int(self.elapsed / 1.5)
        if index >= len(self.results) - 1:
            self.seek(self.slider.maximum())
            self.pause()
        else:
            self.seek((index + 1) * 1500)

    def draw_frame(self, index):
        if not self.results:
            return
        result = self.results[index]
        prefix = "DEMO SINTETIS · " if result.history.get("demo") else ""
        self.title.setText(
            f"{prefix}{result.event_name} · {index + 1}/{len(self.results)} · {result.accepted} trial diterima"
        )
        self.figure.clear()
        positions = np.array([channel["loc"][:3] for channel in result.evoked.info["chs"]])
        valid = (
            len(positions) >= 4
            and np.isfinite(positions).all()
            and np.all(np.linalg.norm(positions, axis=1) > 0)
        )
        for column, (name, start, end) in enumerate(WINDOWS):
            axis = self.figure.add_subplot(1, 3, column + 1)
            axis.set_title(f"{name} ({start}–{end} ms)", fontsize=11, color="#252F4A")
            try:
                if not valid:
                    raise ValueError("Posisi elektroda belum lengkap")
                image, _ = mne.viz.plot_topomap(
                    self.values[index][column],
                    result.evoked.info,
                    axes=axis,
                    show=False,
                    names=result.evoked.ch_names,
                    cmap="RdBu_r",
                    vlim=(-self.limit, self.limit),
                    contours=4,
                    res=64,
                )
                bar = self.figure.colorbar(image, ax=axis, fraction=0.04, pad=0.03)
                bar.set_label("µV", fontsize=9)
                bar.ax.tick_params(labelsize=8)
            except (ValueError, RuntimeError) as error:
                axis.clear()
                axis.axis("off")
                axis.text(
                    0.5, 0.5, f"{name}\n{error}", ha="center", va="center", wrap=True, fontsize=9
                )
        self.figure.subplots_adjust(left=0.02, right=0.91, bottom=0.1, top=0.88, wspace=0.45)
        self.agg.draw()

    def capture_image(self):
        width, height = self.agg.get_width_height()
        return QImage(self.agg.buffer_rgba(), width, height, QImage.Format.Format_RGBA8888).copy()

    def prepare_next(self):
        index = len(self.cache)
        if index >= len(self.results):
            return
        self.draw_frame(index)
        self.cache.append(self.capture_image())
        if index == 0:
            self.render(0)
        if len(self.cache) < len(self.results):
            self.title.setText(f"Menyiapkan gambar {len(self.cache)}/{len(self.results)}…")
            self.prepare_timer.start(1)
        else:
            self.play.setEnabled(len(self.results) > 1)
            self.slider.setEnabled(True)
            self.render_position()

    def restart_clock(self):
        self.last_tick = time.perf_counter()

    def seek(self, milliseconds):
        self.elapsed = milliseconds / 1000
        self.restart_clock()
        self.render_position()

    def render(self, index):
        if index >= len(self.cache):
            return
        result = self.results[index]
        prefix = "DEMO SINTETIS · " if result.history.get("demo") else ""
        self.title.setText(
            f"{prefix}{result.event_name} · {index + 1}/{len(self.results)} · {result.accepted} trial diterima"
        )
        self.canvas.first = self.cache[index]
        self.canvas.second = None
        self.canvas.alpha = 0.0
        self.canvas.update()

    def render_position(self):
        if not self.cache or len(self.cache) != len(self.results):
            return
        self.elapsed = float(np.clip(self.elapsed, 0, len(self.results) * 1.5))
        index = min(int(self.elapsed / 1.5), len(self.results) - 1)
        self.render(index)
        self.slider.blockSignals(True)
        self.slider.setValue(round(self.elapsed * 1000))
        self.slider.blockSignals(False)
        self.progress.setText(f"{self.elapsed:.2f} / {len(self.results) * 1.5:.2f} detik · event {index + 1}/{len(self.results)}")
        if index + 1 < len(self.cache):
            fraction = float(np.clip(((self.elapsed / 1.5 - index) - 0.65) / 0.35, 0, 1))
            self.canvas.second = self.cache[index + 1] if fraction > 0 else None
            self.canvas.alpha = fraction * fraction * (3 - 2 * fraction)
            if fraction > 0:
                self.title.setText(
                    f"Transisi visual: {self.results[index].event_name} → {self.results[index + 1].event_name} (bukan sampel EEG)"
                )
        self.canvas.update()

    def tick(self):
        if not self.results or len(self.cache) != len(self.results):
            self.pause()
            return
        now = time.perf_counter()
        self.elapsed += (now - self.last_tick) * self.speed.currentData()
        self.last_tick = now
        self.render_position()
        if self.elapsed >= len(self.results) * 1.5:
            self.pause()
