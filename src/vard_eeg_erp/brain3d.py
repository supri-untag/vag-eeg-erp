"""Illustrative 3D brain; scalp potentials projected for presentation, not sources."""

import time

import numpy as np
from matplotlib import colormaps
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtWidgets import QCheckBox, QComboBox, QHBoxLayout, QSlider, QVBoxLayout, QWidget

from vard_eeg_erp.widgets import button, label


def brain_mesh(rows=64, columns=96):
    """Closed parametric ellipsoid with illustrative folds and midline groove."""
    theta = np.linspace(0.001, np.pi - 0.001, rows)
    phi = np.linspace(0, 2 * np.pi, columns, endpoint=False)
    t, p = np.meshgrid(theta, phi, indexing="ij")
    unit = np.stack([np.sin(t) * np.cos(p), np.sin(t) * np.sin(p), np.cos(t)], axis=-1)
    folds = 1 + 0.045 * np.sin(t) ** 2 * np.sin(14 * t + 3 * np.sin(5 * p)) * np.sin(
        11 * p + 2 * np.cos(4 * t)
    )
    vertices = unit * np.array([0.82, 1.08, 0.78]) * folds[..., None]
    vertices[..., 2] -= 0.09 * np.exp(-((unit[..., 0] / 0.08) ** 2)) * np.maximum(unit[..., 2], 0)
    faces = []
    for row in range(rows - 1):
        for col in range(columns):
            a, b = row * columns + col, row * columns + (col + 1) % columns
            faces.extend([[a, b, a + columns], [b, b + columns, a + columns]])
    vertices = vertices.reshape(-1, 3)
    faces = np.array(faces, dtype=np.uint32)
    # Close polar caps.
    for start in [0, (rows - 1) * columns]:
        cap = np.array([[start, start + i, start + i + 1] for i in range(1, columns - 1)])
        faces = np.vstack([faces, cap])
    return vertices.astype(np.float32), faces[:, [0, 2, 1]].astype(np.uint32)


def spatial_weights(vertices, positions):
    positions = np.asarray(positions, dtype=float)
    if (
        len(positions) < 4
        or not np.isfinite(positions).all()
        or np.any(np.linalg.norm(positions, axis=1) == 0)
    ):
        raise ValueError("Posisi elektroda belum lengkap. Atur montage sebelum animasi 3D.")
    directions = positions / np.linalg.norm(positions, axis=1, keepdims=True)
    surface = vertices / np.linalg.norm(vertices, axis=1, keepdims=True)
    weights = np.exp(14 * (surface @ directions.T - 1))
    return (weights / weights.sum(axis=1, keepdims=True)).astype(np.float32), directions


class Brain3D(QWidget):
    sample_selected = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.result = None
        self.view = None
        self.mesh = None
        self.weights = None
        self.sample = 0
        self.vertices, self.faces = brain_mesh()
        self.timer = QTimer(self)
        self.timer.setTimerType(Qt.TimerType.PreciseTimer)
        self.timer.setInterval(16)
        self.timer.timeout.connect(self.tick)
        self.last_tick = None
        layout = QVBoxLayout(self)
        controls = QHBoxLayout()
        self.play = button("▶ Putar", self.toggle)
        self.stop = button("■ Stop", self.reset)
        self.speed = QComboBox()
        for name, value in [("0,1×", 0.1), ("0,25×", 0.25), ("0,5×", 0.5), ("1×", 1.0)]:
            self.speed.addItem(name, value)
        self.speed.setCurrentIndex(1)
        self.rotate = QCheckBox("Putar kamera")
        self.electrodes = QCheckBox("Elektroda")
        self.electrodes.setChecked(True)
        self.electrodes.toggled.connect(self.show_electrodes)
        for widget in [
            self.play,
            self.stop,
            self.speed,
            self.rotate,
            self.electrodes,
            button("Reset kamera", self.reset_camera),
        ]:
            controls.addWidget(widget)
        controls.addStretch()
        layout.addLayout(controls)
        self.title = label("Generate ERP untuk melihat aktivitas 3D", "section")
        layout.addWidget(self.title)
        self.scene_layout = QVBoxLayout()
        layout.addLayout(self.scene_layout, 1)
        self.placeholder = label(
            "Model otak ilustratif · drag untuk orbit · scroll untuk zoom", "notice"
        )
        self.placeholder.setWordWrap(True)
        self.scene_layout.addWidget(self.placeholder)
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.valueChanged.connect(self.seek)
        layout.addWidget(self.slider)
        self.legend = label("Biru = negatif · putih = nol · merah = positif (µV)", "muted")
        layout.addWidget(self.legend)
        note = label(
            "Neural Activity Representation — visualization derived from scalp EEG electrical potentials; "
            "not direct imaging of individual neuronal activity.\n"
            "Bentuk ilustratif, bukan MRI atau source localization. Warna = proyeksi spasial potensial scalp.",
            "notice",
        )
        note.setWordWrap(True)
        layout.addWidget(note)
        self.clear()

    def ensure_view(self):
        if self.view is not None:
            return True
        try:
            import pyqtgraph.opengl as gl
            from pyqtgraph.opengl import shaders

            lighting = shaders.ShaderProgram(
                "vard-soft-light",
                [
                    shaders.VertexShader("""
                    uniform mat4 u_mvp;
                    uniform mat3 u_normal;
                    attribute vec4 a_position;
                    attribute vec3 a_normal;
                    attribute vec4 a_color;
                    varying vec4 color;
                    varying vec3 normal;
                    void main() {
                        normal = normalize(u_normal * a_normal);
                        color = a_color;
                        gl_Position = u_mvp * a_position;
                    }
                """),
                    shaders.FragmentShader("""
                    varying vec4 color;
                    varying vec3 normal;
                    void main() {
                        float diffuse = abs(dot(normalize(normal), normalize(vec3(.3,.4,1.))));
                        gl_FragColor = vec4(color.rgb * (.65 + .35 * diffuse), color.a);
                    }
                """),
                ],
            )

            self.view = gl.GLViewWidget()
            self.view.setBackgroundColor("#F5F7FA")
            self.scene_layout.addWidget(self.view, 1)
            self.placeholder.hide()
            self.mesh = gl.GLMeshItem(
                vertexes=self.vertices,
                faces=self.faces,
                smooth=True,
                shader=lighting,
                drawEdges=False,
                color=(0.85, 0.87, 0.91, 1),
            )
            self.view.addItem(self.mesh)
            self.points = gl.GLScatterPlotItem(
                pos=np.empty((0, 3)), size=6, color=(0.15, 0.18, 0.3, 1), glOptions="opaque"
            )
            self.view.addItem(self.points)
            axes = gl.GLAxisItem(size=None)
            axes.setSize(0.3, 0.3, 0.3)
            self.view.addItem(axes)
            self.reset_camera()
            for text, position in [
                ("A", (0, 1.3, 0)),
                ("P", (0, -1.3, 0)),
                ("L", (-1.1, 0, 0)),
                ("R", (1.1, 0, 0)),
            ]:
                self.view.addItem(
                    gl.GLTextItem(
                        pos=position, text=text, color=(65, 80, 110, 255), glOptions="opaque"
                    )
                )
            QTimer.singleShot(2500, self.check_context)
            return True
        except (ImportError, RuntimeError) as error:
            self.placeholder.setText(
                f"3D belum tersedia: {error}. Pasang dependensi proyek dan gunakan desktop dengan OpenGL."
            )
            self.placeholder.show()
            return False

    def check_context(self):
        if self.view and self.isVisible() and not self.view.isValid():
            self.pause()
            self.title.setText("OpenGL tidak tersedia: gunakan desktop dengan dukungan OpenGL.")
            self.play.setEnabled(False)
            self.placeholder.setText(
                "Konteks OpenGL gagal dibuat. Analisis EEG/ERP tetap tersedia di Overview."
            )
            self.placeholder.show()
            self.view.hide()

    def reset_camera(self):
        if self.view:
            self.view.setCameraPosition(distance=5.2, elevation=28, azimuth=35)

    def show_electrodes(self, checked):
        if self.view:
            self.points.setVisible(checked)

    def clear(self):
        self.pause()
        self.result = None
        self.weights = None
        self.title.setText("Generate ERP untuk melihat aktivitas 3D")
        for widget in [self.play, self.stop, self.slider]:
            widget.setEnabled(False)
        if self.mesh:
            self.mesh.setColor((0.85, 0.87, 0.91, 1))
            self.mesh.setMeshData(vertexes=self.vertices, faces=self.faces)
            self.points.setData(pos=np.empty((0, 3)))

    def set_result(self, result):
        self.clear()
        try:
            self.weights, self.directions = spatial_weights(
                self.vertices, [channel["loc"][:3] for channel in result.evoked.info["chs"]]
            )
        except ValueError as error:
            self.title.setText(str(error))
            return
        self.result = result
        self.limit = max(float(np.abs(result.evoked.data).max()) * 1e6, 0.1)
        self.legend.setText(
            f"−{self.limit:.2f} µV (biru)     0 (putih)     +{self.limit:.2f} µV (merah) · skala tetap sepanjang epoch"
        )
        self.slider.setRange(0, len(result.evoked.times) - 1)
        for widget in [self.play, self.stop, self.slider]:
            widget.setEnabled(True)
        self.set_sample(result.sample(400))

    def activate(self):
        if self.ensure_view() and self.result:
            self.points.setData(
                pos=self.directions * np.array([0.91, 1.2, 0.92]),
                size=7,
                color=(0.15, 0.18, 0.3, 1),
            )
            self.set_sample(self.sample)

    def set_sample(self, sample):
        if self.result is None:
            return
        self.sample = int(np.clip(sample, 0, len(self.result.evoked.times) - 1))
        self.slider.blockSignals(True)
        self.slider.setValue(self.sample)
        self.slider.blockSignals(False)
        prefix = "DEMO SINTETIS · " if self.result.history.get("demo") else ""
        self.title.setText(
            f"{prefix}{self.result.event_name} · {self.result.evoked.times[self.sample] * 1000:.2f} ms · potensial scalp pada bentuk ilustratif"
        )
        if self.mesh and self.isVisible():
            values = self.weights @ (self.result.evoked.data[:, self.sample] * 1e6)
            colors = colormaps["RdBu_r"](np.clip((values / self.limit + 1) / 2, 0, 1)).astype(
                np.float32
            )
            self.mesh.opts["meshdata"].setVertexColors(colors)
            self.mesh.meshDataChanged()
            self.view.update()

    def seek(self, sample):
        self.set_sample(sample)
        self.sample_selected.emit(sample)
        self.position = float(sample)
        self.last_tick = time.perf_counter()

    def pause(self):
        self.timer.stop()
        self.play.setText("▶ Putar")

    def toggle(self):
        if self.timer.isActive():
            self.pause()
        elif self.result and self.ensure_view():
            if self.sample == len(self.result.evoked.times) - 1:
                self.seek(0)
            self.position = float(self.sample)
            self.last_tick = time.perf_counter()
            self.timer.start()
            self.play.setText("Ⅱ Pause")

    def reset(self):
        self.pause()
        self.seek(0)

    def tick(self):
        if self.result is None:
            self.pause()
            return
        now = time.perf_counter()
        elapsed = now - self.last_tick
        self.last_tick = now
        self.position += elapsed * self.speed.currentData() * self.result.evoked.info["sfreq"]
        sample = min(round(self.position), len(self.result.evoked.times) - 1)
        self.set_sample(sample)
        self.sample_selected.emit(sample)
        if self.rotate.isChecked() and self.view:
            self.view.orbit(elapsed * 12, 0)
        if sample == len(self.result.evoked.times) - 1:
            self.pause()
