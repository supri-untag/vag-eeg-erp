import argparse
import logging
import sys
from pathlib import Path

import numpy as np
import pyqtgraph as pg
from PySide6.QtCore import QStandardPaths, Qt, QThread, QTimer, Signal
from PySide6.QtGui import QAction, QColor, QPalette
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QScrollArea,
    QSlider,
    QStackedWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from vard_eeg_erp import __version__
from vard_eeg_erp.analysis import Settings, analyze, demo_recording, read_recording
from vard_eeg_erp.brain3d import Brain3D
from vard_eeg_erp.presentation import Presentation
from vard_eeg_erp.qt_runtime import prepare_qt_plugins
from vard_eeg_erp.scoring_ui import ScoringPage
from vard_eeg_erp.storage import export_csv, load_project, save_project
from vard_eeg_erp.theme import STYLE
from vard_eeg_erp.widgets import (
    ERPPlot,
    SettingsDialog,
    Topomap,
    button,
    card,
    label,
    limit_plot_zoom,
    plot_widget,
    table,
)

LOGGER = logging.getLogger(__name__)


class Job(QThread):
    succeeded = Signal(object)
    failed = Signal(str)

    def __init__(self, work, parent=None):
        super().__init__(parent)
        self.work = work

    def run(self):
        try:
            self.succeeded.emit(self.work())
        except Exception as error:
            LOGGER.exception("Background operation failed")
            self.failed.emit(str(error))


class MainWindow(QMainWindow):
    def __init__(self, auto_demo: bool = True):
        super().__init__()
        self.setWindowTitle("VARD Studio • EEG–ERP Workspace")
        self.resize(1400, 920)
        self.setMinimumSize(1100, 740)
        self.recording = None
        self.result = None
        self.settings = Settings()
        self.history = []
        self.job = None
        self.completion = None
        self.dirty = False
        self.project_path = None
        self.sample_index = 0
        self._build_ui()
        self._build_menu()
        self.topo_timer = QTimer(self)
        self.topo_timer.setSingleShot(True)
        self.topo_timer.setInterval(70)
        self.topo_timer.timeout.connect(self._render_topomap)
        self._set_controls()
        if auto_demo:
            QTimer.singleShot(100, self.load_demo)

    def _build_ui(self):
        root = QWidget()
        outer = QHBoxLayout(root)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        self.setCentralWidget(root)
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(218)
        side = QVBoxLayout(sidebar)
        side.setContentsMargins(22, 28, 22, 22)
        side.setSpacing(10)
        side.addWidget(label("VARD /", "brand"))
        side.addWidget(label("NEUROVISUAL WORKSPACE", "muted"))
        side.addSpacing(30)
        side.addWidget(label("WORKSPACE", "muted"))
        self.nav_buttons = []
        for index, name in enumerate(
            [
                "◈   Overview & ERP",
                "∿   EEG recording",
                "▤   Events",
                "◷   Processing history",
                "▶   ERP presentation",
                "◉   Brain 3D",
                "▦   VARS Scoring",
            ]
        ):
            nav = button(name)
            nav.setObjectName("nav")
            nav.setCheckable(True)
            nav.clicked.connect(lambda checked=False, i=index: self.navigate(i))
            side.addWidget(nav)
            self.nav_buttons.append(nav)
        side.addSpacing(24)
        side.addWidget(label("PROJECT", "muted"))
        self.open_button = button("Buka project", self.open_project)
        self.save_button = button("Simpan project", self.save)
        side.addWidget(self.open_button)
        side.addWidget(self.save_button)
        side.addStretch()
        footer = label(
            f"VARD Studio  {__version__}\nLocal research workspace\n\nVARS scoring: eksperimental", "muted"
        )
        footer.setWordWrap(True)
        side.addWidget(footer)
        outer.addWidget(sidebar)

        workspace = QWidget()
        workspace.setObjectName("workspace")
        body = QVBoxLayout(workspace)
        body.setContentsMargins(26, 24, 26, 16)
        body.setSpacing(18)
        header = QHBoxLayout()
        title_block = QVBoxLayout()
        title_block.addWidget(label("WORKSPACE  /  EEG–ERP", "muted"))
        self.page_title = label("Overview & ERP", "title")
        title_block.addWidget(self.page_title)
        header.addLayout(title_block)
        header.addStretch()
        self.demo_button = button("Muat demo", self.load_demo)
        self.import_button = button("＋  Import EEG", self.import_file, True)
        header.addWidget(self.demo_button)
        header.addWidget(button("Import folder", self.import_folder))
        header.addWidget(button("Katalog folder", self.show_folder_catalog))
        header.addWidget(self.import_button)
        header.addWidget(button("Posisi / kategori", self.configure_import))
        body.addLayout(header)

        banner = QHBoxLayout()
        self.source_label = label("Belum ada rekaman", "subtitle")
        banner.addWidget(self.source_label, 1)
        self.badge = label("LOCAL WORKSPACE", "badge")
        banner.addWidget(self.badge)
        body.addLayout(banner)

        stats = QHBoxLayout()
        self.stats = []
        for name, caption in [
            ("CHANNEL EEG", "Electrode channels"),
            ("SAMPLING RATE", "Recording resolution"),
            ("EVENT", "Detected markers"),
            ("TRIAL DITERIMA", "ERP quality control"),
        ]:
            frame, layout = card()
            layout.addWidget(label(name, "muted"))
            metric = label("—", "metric")
            self.stats.append(metric)
            layout.addWidget(metric)
            layout.addWidget(label(caption, "muted"))
            stats.addWidget(frame)
        body.addLayout(stats)

        self.stack = QStackedWidget()
        body.addWidget(self.stack, 1)
        self._build_analysis()
        eeg_page, eeg_layout = card(
            "EEG recording",
            "Raw signal · preview 10 detik pertama · hingga 16 channel · offset 35 µV",
        )
        self.eeg_plot = plot_widget("Waktu (s)", "Channel / offset")
        eeg_layout.addWidget(self.eeg_plot)
        self.stack.addWidget(eeg_page)
        event_page, event_layout = card(
            "Event markers",
            "Waktu relatif terhadap awal rekaman. Pilih jenis event di halaman Overview untuk ERP.",
        )
        self.event_table = table(["#", "Event", "Kode", "Waktu (s)"])
        event_layout.addWidget(self.event_table)
        self.stack.addWidget(event_page)
        history_page, history_layout = card(
            "Processing history",
            "Parameter, trial, versi engine, dan waktu proses disimpan bersama project.",
        )
        self.history_table = table(
            [
                "#",
                "Waktu (UTC)",
                "Event",
                "Diterima",
                "Ditolak",
                "Filter (Hz)",
                "Epoch (ms)",
                "Baseline (ms)",
                "Referensi",
                "Notch (Hz)",
                "Ambang (µV)",
                "Sumber",
                "Montage",
                "Versi engine",
            ]
        )
        self.history_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.ResizeToContents
        )
        history_layout.addWidget(self.history_table)
        self.stack.addWidget(history_page)
        self.presentation = Presentation(self.prepare_presentation)
        self.stack.addWidget(self.presentation)
        self.brain = Brain3D()
        self.brain.sample_selected.connect(self._sample_changed)
        self.stack.addWidget(self.brain)
        self.scoring = ScoringPage()
        self.stack.addWidget(self.scoring)
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.hide()
        body.addWidget(self.progress)
        self.status = label("Siap. Muat demo atau import rekaman EEG.", "muted")
        self.status.setWordWrap(True)
        body.addWidget(self.status)
        outer.addWidget(workspace, 1)
        self.navigate(0)

    def _build_analysis(self):
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)
        toolbar, toolbar_layout = card()
        row = QHBoxLayout()
        row.addWidget(label("Event", "muted"))
        self.events = QComboBox()
        self.events.setMinimumWidth(130)
        self.events.currentTextChanged.connect(self._event_changed)
        row.addWidget(self.events)
        row.addSpacing(10)
        row.addWidget(label("Channel", "muted"))
        self.channels = QComboBox()
        self.channels.setMinimumWidth(90)
        self.channels.currentTextChanged.connect(self._channel_changed)
        row.addWidget(self.channels)
        row.addStretch()
        self.settings_button = button("Parameter", self.edit_settings)
        self.run_button = button("▶  Generate ERP", self.run_analysis, True)
        row.addWidget(self.settings_button)
        row.addWidget(self.run_button)
        toolbar_layout.addLayout(row)
        self.parameter_label = label("", "muted")
        toolbar_layout.addWidget(self.parameter_label)
        layout.addWidget(toolbar)
        plots = QHBoxLayout()
        erp_card, erp_layout = card(
            "Event-related potential",
            "Klik waveform untuk mengubah waktu · garis hijau = linked cursor",
        )
        self.erp_plot = ERPPlot()
        self.erp_plot.setFixedHeight(230)
        self.erp_plot.time_selected.connect(self.select_time)
        erp_layout.addWidget(self.erp_plot, 1)
        plots.addWidget(erp_card, 3)
        topo_card, topo_layout = card(
            "Scalp topography", "Potensial scalp · skala warna tetap per hasil ERP"
        )
        self.topomap = Topomap()
        self.topomap.setFixedHeight(230)
        topo_layout.addWidget(self.topomap, 1)
        plots.addWidget(topo_card, 2)
        layout.addLayout(plots)

        timeline_card, timeline_layout = card()
        timeline_row = QHBoxLayout()
        timeline_row.addWidget(label("LINKED TIMELINE", "muted"))
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.valueChanged.connect(self._sample_changed)
        timeline_row.addWidget(self.slider, 1)
        self.time_label = label("— ms", "section")
        self.time_label.setMinimumWidth(100)
        timeline_row.addWidget(self.time_label)
        timeline_layout.addLayout(timeline_row)
        layout.addWidget(timeline_card)

        bottom = QHBoxLayout()
        feature_card, feature_layout = card(
            "Component measurements",
            "Peak = amplitudo absolut terbesar, tanda dipertahankan. AUC bertanda.",
        )
        component_row = QHBoxLayout()
        self.component = QComboBox()
        self.component.addItems(["P300", "LPP", "Early visual", "Custom"])
        self.component.currentIndexChanged.connect(self._component_changed)
        component_row.addWidget(self.component)
        self.window_start = QDoubleSpinBox()
        self.window_end = QDoubleSpinBox()
        for widget, value in [(self.window_start, 300), (self.window_end, 500)]:
            widget.setRange(-10000, 10000)
            widget.setDecimals(1)
            widget.setSuffix(" ms")
            widget.setValue(value)
            widget.valueChanged.connect(self._window_changed)
            component_row.addWidget(widget)
        feature_layout.addLayout(component_row)
        self.measurements = label("Jalankan analisis untuk menghitung parameter.")
        self.measurements.setWordWrap(True)
        feature_layout.addWidget(self.measurements)
        feature_layout.addStretch()
        self.export_button = button("↓  Ekspor ERP (.csv)", self.export)
        feature_layout.addWidget(self.export_button)
        bottom.addWidget(feature_card, 3)
        channels_card, channels_layout = card(
            "Channel values", "Sampel waktu yang sama dengan ERP dan topomap"
        )
        self.channel_table = table(["Channel", "Amplitudo (µV)"])
        self.channel_table.setMinimumHeight(150)
        self.channel_table.setMaximumHeight(190)
        channels_layout.addWidget(self.channel_table)
        bottom.addWidget(channels_card, 2)
        layout.addLayout(bottom)
        notice = label(
            "RESEARCH PREVIEW  ·  VARD/VARS belum dihitung. Pengukuran ERP bukan penilaian keindahan.",
            "notice",
        )
        notice.setWordWrap(True)
        layout.addWidget(notice)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(content)
        self.stack.addWidget(scroll)
        self._update_parameter_label()

    def _build_menu(self):
        menu = self.menuBar().addMenu("File")
        for caption, shortcut, callback in [
            ("Import EEG", "Ctrl+I", self.import_file),
            ("Buka project", "Ctrl+O", self.open_project),
            ("Simpan project", "Ctrl+S", self.save),
        ]:
            action = QAction(caption, self)
            action.setShortcut(shortcut)
            action.triggered.connect(callback)
            menu.addAction(action)

    def navigate(self, index):
        if hasattr(self, "brain"):
            self.brain.pause()
            if index == 5:
                QTimer.singleShot(0, self.brain.activate)
        if hasattr(self, "presentation") and index != 4:
            self.presentation.pause()
        self.stack.setCurrentIndex(index)
        if index == 0 and hasattr(self, "topo_timer") and self.result:
            self._sample_changed(self.sample_index)
            self.topo_timer.start()
        self.page_title.setText(
            [
                "Overview & ERP",
                "EEG recording",
                "Event markers",
                "Processing history",
                "ERP presentation",
                "Brain 3D",
                "VARS Scoring",
            ][index]
        )
        for i, nav in enumerate(self.nav_buttons):
            nav.setChecked(i == index)

    def _set_controls(self):
        busy = self.job is not None
        for widget in [
            self.import_button,
            self.demo_button,
            self.open_button,
            self.settings_button,
        ]:
            widget.setEnabled(not busy)
        self.save_button.setEnabled(not busy and self.recording is not None)
        self.run_button.setEnabled(
            not busy and self.recording is not None and self.events.count() > 0
        )
        self.events.setEnabled(not busy and self.recording is not None)
        for widget in [
            self.channels,
            self.slider,
            self.export_button,
            self.component,
            self.window_start,
            self.window_end,
        ]:
            widget.setEnabled(not busy and self.result is not None)
        self.presentation.prepare_button.setEnabled(not busy and self.events.count() > 0)
        self.presentation.setEnabled(not busy)
        self.brain.setEnabled(not busy)
        self.progress.setVisible(busy)

    def start_job(self, work, completion, message):
        if self.job is not None:
            return
        self.presentation.pause()
        self.brain.pause()
        self.status.setText(message)
        self.completion = completion
        self.job = Job(work, self)
        self.job.succeeded.connect(self._job_succeeded)
        self.job.failed.connect(self.show_error)
        self.job.finished.connect(self._job_finished)
        self._set_controls()
        self.job.start()

    def _job_succeeded(self, value):
        try:
            self.completion(value)
        except Exception as error:
            LOGGER.exception("Could not display result")
            self.show_error(str(error))

    def _job_finished(self):
        self.job.deleteLater()
        self.job = None
        self.completion = None
        self._set_controls()

    def show_error(self, message):
        self.status.setText(f"Proses gagal: {message}")
        QMessageBox.warning(self, "Proses belum berhasil", message)

    def confirm_replace(self) -> bool:
        if self.job is not None:
            return False
        if not self.dirty:
            return True
        answer = QMessageBox.question(
            self,
            "Perubahan belum disimpan",
            "Simpan project sebelum melanjutkan?",
            QMessageBox.StandardButton.Save
            | QMessageBox.StandardButton.Discard
            | QMessageBox.StandardButton.Cancel,
        )
        if answer == QMessageBox.StandardButton.Save:
            return self.save()
        return answer == QMessageBox.StandardButton.Discard

    def load_demo(self):
        if not self.confirm_replace():
            return
        settings = Settings()

        def work():
            recording = demo_recording()
            return recording, analyze(recording, settings, "Visual A")

        def complete(value):
            recording, result = value
            self.settings = settings
            self.install_recording(recording)
            self.install_result(result)
            self.dirty = False

        self.start_job(work, complete, "Menyiapkan demo sintetis dan ERP…")

    def configure_import(self):
        if self.recording is None or self.job is not None or self.recording.demo:
            return
        from vard_eeg_erp.import_mapping import apply_setup, ced_setup, read_groups

        choice = QMessageBox.question(
            self, "Pemetaan data", "Impor posisi CED? Pilih No untuk CSV kategori trigger.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No |
            QMessageBox.StandardButton.Cancel)
        if choice == QMessageBox.StandardButton.Cancel:
            return
        setup = dict(self.recording.import_setup)
        try:
            if choice == QMessageBox.StandardButton.Yes:
                ced, _ = QFileDialog.getOpenFileName(self, "CED dengan X Y Z", "", "CED (*.ced)")
                if not ced:
                    return
                mapping, _ = QFileDialog.getOpenFileName(
                    self, "CSV OriginalLabel, ActiveElectrode, UsedForTopoplot", "", "CSV (*.csv)")
                if not mapping:
                    return
                setup.update(ced_setup(ced, mapping))
                message = (f"Pakai {len(setup['positions'])} channel EEG; "
                           f"keluarkan {len(setup['excluded'])} channel dari analisis EEG dan reference. "
                           "Koordinat berupa arah pada kepala ilustratif radius 95 mm. Lanjutkan?")
            else:
                path, _ = QFileDialog.getOpenFileName(
                    self, "CSV event_code, category", "", "CSV (*.csv)")
                if not path:
                    return
                setup['groups'] = read_groups(path)
                message = f"Kelompokkan trigger ke {len(set(setup['groups'].values()))} kategori?"
            if QMessageBox.question(self, "Terapkan pemetaan", message) != QMessageBox.StandardButton.Yes:
                return
            source = self.recording.source
            self.start_job(lambda: apply_setup(read_recording(source), setup),
                           self.install_recording, "Menerapkan pemetaan; hasil ERP perlu dihitung ulang…")
        except (ValueError, KeyError, OSError) as error:
            self.show_error(str(error))

    def import_file(self):
        if not self.confirm_replace():
            return
        path, _ = QFileDialog.getOpenFileName(self, "Import rekaman EEG", "", "EEG (*.bdf *.edf)")
        if path:
            self.start_job(
                lambda: read_recording(path),
                self.install_recording,
                "Membaca metadata dan event EEG…",
            )

    def show_folder_catalog(self):
        if not hasattr(self, "folder_catalog"):
            from vard_eeg_erp.folder_catalog_ui import FolderCatalog

            self.folder_catalog = FolderCatalog(self)
            self.folder_catalog.open_requested.connect(self.open_catalog_recording)
        self.folder_catalog.show()
        self.folder_catalog.raise_()

    def import_folder(self):
        if self.job is not None:
            return
        folder = QFileDialog.getExistingDirectory(self, "Pilih folder subjek / rekaman")
        if not folder:
            return
        from vard_eeg_erp.folder_catalog import scan_folder

        def complete(rows):
            self.show_folder_catalog()
            self.folder_catalog.populate(folder, rows)
            self.status.setText(f"Pemindaian selesai: {len(rows)} file ditemukan.")

        self.start_job(lambda: scan_folder(folder), complete, "Memindai folder dan memeriksa EEG…")

    def open_catalog_recording(self, path):
        if not self.confirm_replace():
            return
        self.folder_catalog.hide()
        self.start_job(lambda: read_recording(path), self.install_recording,
                       "Membuka rekaman dari katalog folder…")

    def install_recording(self, recording):
        self.recording = recording
        self.project_path = None
        self.history = []
        self.history_table.setRowCount(0)
        self.invalidate_result()
        self.events.blockSignals(True)
        self.events.clear()
        self.events.addItems(list(recording.event_id))
        self.events.blockSignals(False)
        self.channels.blockSignals(True)
        self.channels.clear()
        self.channels.addItems(
            [
                name
                for name, kind in zip(
                    recording.raw.ch_names, recording.raw.get_channel_types(), strict=True
                )
                if kind == "eeg"
            ]
        )
        self.channels.setCurrentText(
            "Pz" if "Pz" in recording.raw.ch_names else self.channels.itemText(0)
        )
        self.channels.blockSignals(False)
        source = (
            "Visual response study / Dataset demo"
            if recording.demo
            else Path(recording.source).name
        )
        duration = recording.raw.n_times / recording.raw.info["sfreq"]
        self.source_label.setText(f"{source}   ·   {duration:.1f} s")
        self.source_label.setToolTip(recording.source)
        self.badge.setText("DEMO SINTETIS" if recording.demo else "REKAMAN LOKAL")
        self.stats[0].setText(str(self.channels.count()))
        self.stats[1].setText(f"{recording.raw.info['sfreq']:g} Hz")
        self.stats[2].setText(str(len(recording.events)))
        names = {value: name for name, value in recording.event_id.items()}
        displayed_events = recording.events[:5000]
        self.event_table.setRowCount(len(displayed_events))
        for i, (sample, _, code) in enumerate(displayed_events):
            values = [
                i + 1,
                names.get(int(code), str(code)),
                code,
                f"{(sample - recording.raw.first_samp) / recording.raw.info['sfreq']:.4f}",
            ]
            for column, value in enumerate(values):
                self.event_table.setItem(i, column, QTableWidgetItem(str(value)))
        self.event_table.setToolTip(
            "Tabel menampilkan hingga 5.000 event. Analisis menggunakan seluruh event."
        )
        self.eeg_plot.clear()
        for index, values in enumerate(recording.preview_data):
            self.eeg_plot.plot(
                recording.preview_times,
                values * 1e6 - index * 35,
                pen=pg.mkPen("#1B84FF" if index % 2 == 0 else "#7239EA", width=1),
            )
        self.eeg_plot.getAxis("left").setTicks(
            [[(index * -35, name) for index, name in enumerate(recording.preview_names)]]
        )
        preview = np.asarray(recording.preview_data) * 1e6
        offsets = np.arange(len(preview))[:, None] * 35
        limit_plot_zoom(self.eeg_plot, recording.preview_times, preview - offsets)
        self._update_parameter_label()
        self.dirty = True
        self.status.setText(
            "Rekaman siap. Pilih event dan Generate ERP."
            if recording.event_id
            else "EEG dimuat, tetapi event tidak ditemukan. Analisis ERP memerlukan trigger/annotation."
        )
        self._set_controls()

    def invalidate_result(self):
        self.scoring.set_result(None)
        self.brain.clear()
        self.presentation.clear()
        self.result = None
        if hasattr(self, "topo_timer"):
            self.topo_timer.stop()
        self.erp_plot.curve.clear()
        self.topomap.message("Jalankan analisis untuk melihat topomap")
        self.channel_table.setRowCount(0)
        self.time_label.setText("— ms")
        self.stats[3].setText("—")
        self.measurements.setText("Jalankan analisis untuk menghitung parameter.")
        self._set_controls()

    def _event_changed(self):
        self.invalidate_result()
        self.dirty = True
        self.status.setText("Event berubah. Jalankan Generate ERP untuk memperbarui hasil.")

    def edit_settings(self):
        if self.job is not None:
            return
        dialog = SettingsDialog(self.settings, self)
        if dialog.exec():
            settings = dialog.settings()
            try:
                settings.validate(self.recording.raw.info["sfreq"] if self.recording else 2048)
            except ValueError as error:
                self.show_error(str(error))
                return
            self.settings = settings
            self.invalidate_result()
            self._update_parameter_label()
            self.dirty = True
            self.status.setText("Parameter diperbarui. Jalankan Generate ERP.")

    def _update_parameter_label(self):
        settings = self.settings
        self.parameter_label.setText(
            f"Filter {settings.highpass:g}–{settings.lowpass:g} Hz   ·   "
            f"Epoch {settings.tmin * 1000:g}…{settings.tmax * 1000:g} ms   ·   "
            f"Baseline {settings.baseline_start * 1000:g}…{settings.baseline_end * 1000:g} ms   ·   "
            f"{'Average' if settings.average_reference else 'Original'} reference"
        )

    def prepare_presentation(self):
        if not self.recording or self.job is not None:
            return
        recording, settings = self.recording, self.settings
        if len(recording.event_id) > 64:
            self.show_error("Presentasi mendukung maksimal 64 jenis event per rekaman.")
            return
        self.presentation.clear()

        def work():
            return [analyze(recording, settings, event) for event in recording.event_id]

        def complete(results):
            self.presentation.set_results(results)
            self.history.extend(result.history for result in results)
            self.refresh_history()
            self.dirty = True
            self.status.setText("Presentasi siap. Klik Putar untuk berganti jenis event.")

        self.start_job(work, complete, "Menyiapkan ERP setiap jenis event untuk presentasi…")

    def run_analysis(self):
        if not self.recording or self.job is not None:
            return
        recording, settings, event = self.recording, self.settings, self.events.currentText()
        self.start_job(
            lambda: analyze(recording, settings, event),
            self.install_result,
            "Memproses filter, epoch, baseline, dan ERP…",
        )

    def refresh_history(self):
        self.history_table.setRowCount(len(self.history))
        for row, entry in enumerate(self.history):
            parameters = entry.get("parameters", {})

            def interval(start, end):
                first, last = parameters.get(start), parameters.get(end)
                if first is None or last is None:
                    return "—"
                return f"{first * 1000:g} … {last * 1000:g}"

            source = entry.get("source", "—")
            reference = parameters.get("average_reference")
            values = [
                row + 1,
                entry.get("time_utc", "—").replace("T", " ").split(".")[0],
                entry.get("event", "—"),
                entry.get("accepted", "—"),
                entry.get("rejected", "—"),
                f"{parameters.get('highpass', '—')}–{parameters.get('lowpass', '—')}",
                interval("tmin", "tmax"),
                interval("baseline_start", "baseline_end"),
                "Average" if reference else ("Original" if reference is False else "—"),
                parameters.get("notch") or "Off",
                parameters.get("reject_uv", "—"),
                "Demo sintetis" if entry.get("demo") else Path(source).name,
                entry.get("montage", "—"),
                f"MNE {entry.get('mne_version', '—')} / NumPy {entry.get('numpy_version', '—')}",
            ]
            details = (
                f"Sumber: {source}\nMetode: {entry.get('filter_method', '—')}\n"
                f"Aplikasi: {entry.get('app_version', '—')}\n"
                f"Alasan penolakan: {entry.get('drop_log', [])}"
            )
            for column, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                item.setToolTip(details)
                self.history_table.setItem(row, column, item)

    def install_result(self, result):
        self.scoring.set_result(result)
        self.result = result
        self.presentation.set_results([result])
        self.brain.set_result(result)
        self.history.append(result.history)
        self.refresh_history()
        self.stats[3].setText(f"{result.accepted} / {result.accepted + result.rejected}")
        self.slider.blockSignals(True)
        self.slider.setRange(0, len(result.evoked.times) - 1)
        self.slider.blockSignals(False)
        self._channel_changed()
        self.select_time(400)
        self.dirty = True
        self.status.setText(
            f"ERP siap · {result.event_name} · {result.accepted} trial diterima · {result.rejected} ditolak."
        )
        self._set_controls()

    def _channel_changed(self):
        if self.result and self.channels.currentText() in self.result.evoked.ch_names:
            self.erp_plot.display(self.result, self.channels.currentText())
            self.update_metrics()

    def _component_changed(self, index):
        windows = [(300, 500), (500, 800), (0, 200)]
        if index < len(windows):
            for widget, value in zip(
                [self.window_start, self.window_end], windows[index], strict=True
            ):
                widget.blockSignals(True)
                widget.setValue(value)
                widget.blockSignals(False)
        self.update_metrics()

    def _window_changed(self):
        self.component.blockSignals(True)
        self.component.setCurrentText("Custom")
        self.component.blockSignals(False)
        self.update_metrics()

    def update_metrics(self):
        self.erp_plot.region.setRegion((self.window_start.value(), self.window_end.value()))
        if not self.result:
            return
        try:
            values = self.result.metrics(
                self.channels.currentText(), self.window_start.value(), self.window_end.value()
            )
            self.measurements.setText(
                f"Mean   {values['mean_uv']:.3f} µV      Peak   {values['peak_uv']:.3f} µV\n"
                f"Latency   {values['latency_ms']:.2f} ms      AUC   {values['auc_uv_ms']:.2f} µV·ms"
            )
        except ValueError as error:
            self.measurements.setText(str(error))

    def select_time(self, milliseconds):
        if not self.result:
            return
        sample = self.result.sample(milliseconds)
        self.slider.blockSignals(True)
        self.slider.setValue(sample)
        self.slider.blockSignals(False)
        self._sample_changed(sample)

    def _sample_changed(self, sample):
        if not self.result:
            return
        self.sample_index = sample
        if self.brain.sample != sample:
            self.brain.set_sample(sample)
        self.slider.blockSignals(True)
        self.slider.setValue(sample)
        self.slider.blockSignals(False)
        time = self.result.evoked.times[sample] * 1000
        self.erp_plot.cursor.setValue(time)
        self.time_label.setText(f"{time:.2f} ms")
        if self.stack.currentIndex() == 5 and self.brain.timer.isActive():
            return
        self.channel_table.setRowCount(len(self.result.evoked.ch_names))
        for index, name in enumerate(self.result.evoked.ch_names):
            self.channel_table.setItem(index, 0, QTableWidgetItem(name))
            self.channel_table.setItem(
                index, 1, QTableWidgetItem(f"{self.result.evoked.data[index, sample] * 1e6:.3f}")
            )
        if self.stack.currentIndex() == 0:
            if not self.topo_timer.isActive():
                self.topo_timer.start()

    def _render_topomap(self):
        if self.result:
            self.topomap.display(self.result, self.sample_index)

    def save(self) -> bool:
        if not self.recording or self.job is not None:
            return False
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Simpan project",
            str(self.project_path or "Untitled.vard.json"),
            "VARD project (*.vard.json)",
        )
        if not path:
            return False
        target = Path(path if path.endswith(".vard.json") else path + ".vard.json")
        try:
            save_project(
                target,
                self.recording,
                self.result,
                self.settings,
                self.events.currentText(),
                self.history,
                {
                    "channel": self.channels.currentText(),
                    "time_ms": float(self.result.evoked.times[self.sample_index] * 1000)
                    if self.result
                    else 400,
                    "component": self.component.currentText(),
                    "window_start": self.window_start.value(),
                    "window_end": self.window_end.value(),
                },
            )
            self.project_path = target
            self.dirty = False
            self.status.setText(
                f"Project disimpan: {target.name}. File EEG sumber tetap diperlukan saat membuka project."
            )
            return True
        except Exception as error:
            self.show_error(str(error))
            return False

    def open_project(self):
        if not self.confirm_replace():
            return
        path, _ = QFileDialog.getOpenFileName(
            self, "Buka project", "", "VARD project (*.vard.json)"
        )
        if not path:
            return

        def work():
            payload = load_project(Path(path))
            recording = demo_recording() if payload["demo"] else read_recording(payload["source"])
            if payload.get("import_setup"):
                from vard_eeg_erp.import_mapping import apply_setup

                recording = apply_setup(recording, payload["import_setup"])
            settings = Settings(**payload["settings"])
            result = (
                analyze(recording, settings, payload["event"]) if payload["has_result"] else None
            )
            return payload, recording, settings, result

        def complete(value):
            payload, recording, settings, result = value
            self.settings = settings
            self.install_recording(recording)
            self.events.setCurrentText(payload["event"])
            self.history = payload["history"]
            if result:
                self.install_result(result)
            self.refresh_history()
            view = payload.get("view", {})
            self.channels.setCurrentText(view.get("channel", "Pz"))
            self.window_start.setValue(view.get("window_start", 300))
            self.window_end.setValue(view.get("window_end", 500))
            self.component.setCurrentText(view.get("component", "P300"))
            self.select_time(view.get("time_ms", 400))
            self.project_path = Path(path)
            self.dirty = False
            self.status.setText(
                f"Project dibuka: {Path(path).name}. Hasil dihitung ulang dari sumber dan parameter tersimpan."
            )

        self.start_job(work, complete, "Membuka project dan merekonstruksi analisis…")

    def export(self):
        if not self.result or self.job is not None:
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Ekspor ERP", "ERP-demo.csv" if self.recording.demo else "ERP.csv", "CSV (*.csv)"
        )
        if path:
            target = Path(path if path.endswith(".csv") else path + ".csv")
            result, demo = self.result, self.recording.demo
            self.start_job(
                lambda: export_csv(target, result, demo),
                lambda _: self.status.setText(f"ERP diekspor: {target.name} · ms dan µV."),
                "Mengekspor hasil ERP…",
            )

    def closeEvent(self, event):
        if self.job is not None:
            self.status.setText("Tunggu proses selesai sebelum menutup aplikasi.")
            event.ignore()
        elif self.confirm_replace():
            event.accept()
        else:
            event.ignore()


def create_application() -> QApplication:
    if QApplication.instance() is None:
        prepare_qt_plugins()
    app = QApplication.instance() or QApplication(sys.argv[:1])
    app.setApplicationName("VARD Studio")
    app.setOrganizationName("VARD")
    app.setStyle("Fusion")
    palette = QPalette()
    for role, color in [
        (QPalette.ColorRole.Window, "#F5F7FA"),
        (QPalette.ColorRole.Base, "#FFFFFF"),
        (QPalette.ColorRole.Text, "#252F4A"),
        (QPalette.ColorRole.WindowText, "#252F4A"),
        (QPalette.ColorRole.Button, "#FFFFFF"),
        (QPalette.ColorRole.ButtonText, "#252F4A"),
        (QPalette.ColorRole.Highlight, "#1B84FF"),
        (QPalette.ColorRole.HighlightedText, "#FFFFFF"),
    ]:
        palette.setColor(role, QColor(color))
    app.setPalette(palette)
    app.setStyleSheet(STYLE)
    pg.setConfigOptions(antialias=True)
    return app


def main() -> int:
    parser = argparse.ArgumentParser(description="VARD desktop EEG–ERP workspace")
    parser.add_argument("--empty", action="store_true", help="Start without the synthetic demo")
    args = parser.parse_args()
    app = create_application()
    log_dir = Path(
        QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppLocalDataLocation)
    )
    log_dir.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        filename=log_dir / "vard.log",
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )
    window = MainWindow(auto_demo=not args.empty)
    window.show()
    return app.exec()
