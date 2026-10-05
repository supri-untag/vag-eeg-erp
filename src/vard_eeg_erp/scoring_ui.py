"""VARS configuration worksheet; no implicit physiological feature definitions."""

import json
from datetime import datetime, timezone
from pathlib import Path

from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QLineEdit,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from vard_eeg_erp.scoring import DOMAINS, score
from vard_eeg_erp.storage import atomic_json
from vard_eeg_erp.widgets import button, label, table


class ScoringPage(QWidget):
    def __init__(self):
        super().__init__()
        self.result = None
        self.output = None
        root = QVBoxLayout(self)
        from vard_eeg_erp.aatr_dashboard_ui import AATRDashboard
        from vard_eeg_erp.aatr_ui import AATRPanel

        self.aatr = AATRPanel()
        tabs = QTabWidget()
        root.addWidget(tabs)
        worksheet = QWidget()
        tabs.addTab(worksheet, "VARS")
        tabs.addTab(self.aatr, "AATR V7B")
        self.aatr_dashboard = AATRDashboard()
        tabs.addTab(self.aatr_dashboard, "Dashboard AATR")
        layout = QVBoxLayout(worksheet)
        note = label(
            "VARS EKSPERIMENTAL · Fitur diisi manual sesuai protokol penelitian. "
            "Skor merupakan respons relatif, bukan persentase keindahan. "
            "Ekstraksi otomatis V1–V6 belum tersedia. Simpan model dan ekspor skor terpisah; project .vard.json belum menyimpan isian halaman ini.",
            "notice",
        )
        note.setWordWrap(True)
        layout.addWidget(note)
        self.context = label("Generate ERP untuk mengaitkan skor dengan hasil analisis.")
        layout.addWidget(self.context)
        self.version = QLineEdit()
        self.version.setPlaceholderText("Versi model (wajib, ubah versi jika definisi berubah)")
        self.reference = QLineEdit()
        self.reference.setPlaceholderText("Sumber/populasi data acuan Min–Max (wajib)")
        for field in (self.version, self.reference):
            layout.addWidget(field)
            field.textChanged.connect(self.invalidate)
        self.grid = table(
            [
                "Domain",
                "Definisi fitur / ROI / window",
                "Satuan",
                "Min acuan",
                "Max acuan",
                "Bobot",
                "Arah higher/lower",
                "Fitur mentah",
                "Skor",
            ]
        )
        self.grid.setEditTriggers(
            self.grid.EditTrigger.DoubleClicked | self.grid.EditTrigger.EditKeyPressed
        )
        self.grid.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.grid.horizontalHeader().setMinimumSectionSize(100)
        self.grid.setRowCount(6)
        from PySide6.QtCore import Qt

        for row, (code, name) in enumerate(DOMAINS):
            for column in range(9):
                item = QTableWidgetItem(f"{code} · {name}" if column == 0 else "")
                if column in (0, 8):
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.grid.setItem(row, column, item)
        self.grid.itemChanged.connect(self.invalidate)
        layout.addWidget(self.grid, 1)
        controls = QHBoxLayout()
        for text, callback in [
            ("Hitung VARS", self.calculate),
            ("Simpan model", self.save_model),
            ("Muat model", self.load_model),
            ("Ekspor hasil JSON", self.export),
        ]:
            controls.addWidget(button(text, callback))
        layout.addLayout(controls)
        self.status = label("Isi keenam domain dan bobot dengan total 1. Arah: higher atau lower.")
        self.status.setWordWrap(True)
        layout.addWidget(self.status)

    def invalidate(self, *_):
        self.output = None
        self.grid.blockSignals(True)
        for row in range(6):
            self.grid.item(row, 8).setText("")
        self.grid.blockSignals(False)
        self.status.setText("Konfigurasi berubah. Hitung ulang setelah semua isian lengkap.")

    def set_result(self, result):
        self.result = result
        self.invalidate()
        self.grid.blockSignals(True)
        for row in range(6):
            self.grid.item(row, 7).setText("")
        self.grid.blockSignals(False)
        self.context.setText(
            f"{'DEMO SINTETIS · ' if result.history.get('demo') else ''}{result.event_name} · {result.accepted} trial diterima"
            if result
            else "Generate ERP untuk mengaitkan skor dengan hasil analisis."
        )

    def model(self):
        domains = {}
        for row, (code, _) in enumerate(DOMAINS):
            cells = [self.grid.item(row, col).text().strip() for col in range(1, 7)]
            domains[code] = dict(
                zip(
                    ["definition", "unit", "minimum", "maximum", "weight", "direction"],
                    cells,
                    strict=True,
                )
            )
        return {
            "version": self.version.text().strip(),
            "reference": self.reference.text().strip(),
            "normalization": "minmax",
            "domains": domains,
        }

    def calculate(self):
        self.invalidate()
        try:
            if self.result is None:
                raise ValueError("Generate ERP terlebih dahulu.")
            raw = {code: self.grid.item(row, 7).text() for row, (code, _) in enumerate(DOMAINS)}
            output = score(self.model(), raw)
            output["analysis"] = self.result.history.copy()
            output["time_utc"] = datetime.now(timezone.utc).isoformat()
            self.grid.blockSignals(True)
            for row, (code, _) in enumerate(DOMAINS):
                item = output["domains"][code]
                self.grid.item(row, 8).setText(
                    f"{item['score']:.2f}" + (" *" if item["outside_reference"] else "")
                )
            self.grid.blockSignals(False)
            self.output = output
            self.status.setText(
                f"VARS Composite: {output['composite']:.2f} / 100 · Eksperimental. "
                "* Di luar acuan: skor dibatasi ke 0–100. Ekspor JSON untuk menyimpan hasil."
            )
        except (ValueError, KeyError, TypeError) as error:
            self.status.setText(f"Belum dapat menghitung: {error}")

    def save_model(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Simpan konfigurasi VARS", "vars-model.json", "JSON (*.json)"
        )
        if path:
            try:
                atomic_json(Path(path), self.model())
                self.status.setText(
                    "Konfigurasi disimpan; isian fitur mentah tidak disimpan dalam model."
                )
            except (OSError, ValueError) as error:
                self.status.setText(str(error))

    def load_model(self):
        path, _ = QFileDialog.getOpenFileName(self, "Muat konfigurasi VARS", "", "JSON (*.json)")
        if not path:
            return
        try:
            model = json.loads(Path(path).read_text(encoding="utf-8"))
            # Validate structure before changing the worksheet; drafts may contain empty values.
            if model["normalization"] != "minmax":
                raise ValueError("Normalisasi yang didukung: minmax.")
            rows = [
                [
                    str(model["domains"][code][key])
                    for key in ("definition", "unit", "minimum", "maximum", "weight", "direction")
                ]
                for code, _ in DOMAINS
            ]
            version, reference = str(model["version"]), str(model["reference"])
            self.version.setText(version)
            self.reference.setText(reference)
            for row, values in enumerate(rows):
                for column, value in enumerate(values, 1):
                    self.grid.item(row, column).setText(value)
            self.set_result(self.result)
        except (OSError, ValueError, KeyError, TypeError) as error:
            self.status.setText(f"Model gagal dimuat: {error}")

    def export(self):
        if self.output is None:
            self.status.setText("Hitung VARS terlebih dahulu.")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Ekspor VARS", "vars-score.json", "JSON (*.json)"
        )
        if path:
            try:
                atomic_json(Path(path), self.output)
                self.status.setText("Hasil, keenam domain, model, dan asal analisis tersimpan.")
            except (OSError, ValueError) as error:
                self.status.setText(str(error))
