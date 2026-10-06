# Menjalankan dan mengembangkan aplikasi

Untuk langkah penggunaan dengan screenshot, baca [Panduan pengguna VARD Studio](panduan-pengguna.md).

## Mac

Jalankan dari direktori proyek:

```bash
python3 -m venv venv
venv/bin/python -m pip install -e ".[dev]"
venv/bin/python run.py
```

Lingkungan pengembangan awal memakai Python 3.14.5 pada macOS ARM64. Versi minimum deklaratif package adalah Python 3.11; kombinasi versi/platform lain perlu diuji. Snapshot dependensi lingkungan uji disimpan di `requirements-macos-tested.txt` dan tidak dianggap sebagai lock Windows.

Gunakan direktori `venv` seperti perintah di atas. Pada lingkungan ini, file environment bisa kembali mendapat atribut macOS `hidden`, termasuk `.pth` dan plugin Qt. Mengganti nama folder atau membersihkan atribut sekali saja tidak cukup. Launcher `run.py` mengakses source langsung; sebelum membuat `QApplication`, aplikasi otomatis membersihkan atribut hidden pada folder plugin Qt di virtual environment aktif dan mendaftarkan path plugin PySide6.

### Error plugin Qt

Jika muncul `This application failed to start because no Qt platform plugin could be initialized`, tutup proses lama lalu jalankan kode terbaru dari folder proyek:

```bash
venv/bin/python run.py
```

Perbaikan startup khusus macOS hanya mengubah atribut hidden pada tree plugin dan direktori induknya di dalam virtual environment. Isi library, permission, dan flag lainnya dipertahankan; instalasi sistem dan bundle aplikasi tidak diubah.

Untuk pemulihan manual pada versi kode lama, bersihkan flag hidden pada environment lokal:

```bash
chflags -R nohidden venv
```

Perintah tersebut hanya mengubah atribut tampilan file environment. Jalankan dari direktori proyek. Flag `.pth` dapat muncul kembali; karena itu gunakan `run.py`, yang langsung memakai package dari `src`. pytest dan script smoke juga memakai path source eksplisit sehingga tidak bergantung pada editable-install `.pth`.

Jika masih gagal, simpan diagnostik dari perintah berikut untuk melihat plugin yang gagal dimuat:

```bash
QT_DEBUG_PLUGINS=1 venv/bin/python run.py
```

Gunakan Python dari `venv` proyek ini. Path plugin dan versi Qt dari environment lain dapat berbeda. Jangan menetapkan `QT_PLUGIN_PATH` secara global; lihat [panduan resmi deployment plugin Qt](https://doc.qt.io/qt-6/deployment-plugins.html).

## Mencoba aplikasi

1. Aplikasi membuka demo sintetis 32 channel, 256 Hz, dengan dua jenis event.
2. Pilih channel, klik waveform, atau geser timeline. Amati waktu dan nilai channel yang sama pada topomap.
3. Ubah window komponen untuk melihat mean, peak, latency, dan AUC.
4. Pilih event lain lalu Generate ERP. Mengubah parameter juga memerlukan Generate ERP ulang.
5. Gunakan Simpan project, Buka project, dan Ekspor ERP untuk mencoba penyimpanan.
6. Import rekaman `.bdf` atau `.edf` untuk mencoba data sendiri. Trigger atau annotation diperlukan untuk ERP.

Peak menggunakan nilai dengan amplitudo absolut terbesar dalam window, mempertahankan tanda. AUC merupakan integral bertanda dalam µV·ms. Cursor menggunakan sampel terdekat; pada 256 Hz, pilihan 400 ms menjadi 398.4375 ms relatif stimulus onset.

Data demo hanya untuk pengujian fungsi. Tidak digunakan sebagai referensi normatif, penilaian keindahan, atau validasi ilmiah.

## Project dan penyimpanan

Manifest `.vard.json` menyimpan path sumber relatif bila memungkinkan, parameter, event, riwayat, channel, window komponen, dan cursor. File EEG tetap terpisah dan tidak ditimpa. Saat project dibuka, ERP dihitung ulang dari sumber dan parameter tersimpan, lalu proses tersebut ditambahkan ke history. Memindahkan project perlu mempertahankan hubungan path dengan file sumber. Demo direkonstruksi memakai seed tetap.

Versi awal memakai JSON alih-alih SQLite agar satu rekaman dapat disimpan secara portabel. Hasil rekonstruksi dapat berubah jika sumber atau versi engine berubah; history mencatat versi MNE/NumPy/aplikasi. Checksum sumber, migrasi skema, dan database multi-subjek merupakan pekerjaan lanjutan.

Preprocessing memuat salinan channel EEG ke memori melalui worker. Impor awal membaca metadata/event dan preview terbatas. Rekaman sangat besar tetap membutuhkan RAM yang cukup; out-of-core processing dan pembatalan proses aktif belum tersedia. Menutup aplikasi saat worker aktif ditunda sampai proses selesai.

## Struktur implementasi awal

- `analysis.py`: model rekaman, parameter, data demo, pembacaan EEG, dan pipeline numerik tanpa GUI.
- `storage.py`: manifest JSON atomik dan ekspor CSV.
- `app.py`: workflow desktop, worker, navigasi, dan aksi pengguna.
- `widgets.py`: komponen GUI, grafik, topomap, dan dialog parameter.
- `theme.py`: warna serta styling terang.
- `qt_runtime.py`: pemulihan atribut plugin macOS dan pengaturan path sebelum GUI dimulai.
- `run.py`: launcher source yang dapat dipakai dari direktori mana pun menggunakan path absolut file launcher.

Pisahkan modul ini menjadi direktori sesuai AGENT.MD ketika ukuran dan kebutuhan berkembang.

## Pengujian

```bash
venv/bin/python -m pytest -q
venv/bin/python -m ruff check src tests scripts
venv/bin/python -m ruff format --check src tests scripts
venv/bin/python scripts/smoke_gui.py
```

pytest menggunakan Qt offscreen. Script smoke membuka window native, mencoba demo, navigasi, simpan/buka project, dan ekspor CSV, mengambil screenshot ke `artifacts/vard-macos.png`, lalu menutup aplikasi. Dialog pemilihan file dimock pada smoke test agar deterministik; dialog native masih perlu dicoba pengguna.

Log aplikasi disimpan di direktori data pengguna dari `QStandardPaths.AppLocalDataLocation`, dengan nama `vard.log`.

## Sumber teknis

### Memperbarui screenshot panduan

Jalankan pada desktop macOS:

```bash
venv/bin/python scripts/capture_docs.py
```

Script membuka demo sintetis, mengambil enam screenshot Overview, pengukuran komponen, EEG, event, history, dan dialog parameter ke `docs/images/`, lalu menutup window. File dengan nama yang sama akan diperbarui. Periksa gambar setelah perubahan UI dan sesuaikan langkah pada `docs/panduan-pengguna.md`. Screenshot tidak menggunakan data partisipan.

### Referensi implementasi

- [MNE Epochs](https://mne.tools/stable/generated/mne.Epochs.html): epoch, baseline, dan penolakan trial.
- [MNE BDF reader](https://mne.tools/stable/generated/mne.io.read_raw_bdf.html): pembacaan rekaman BDF.
- [Qt QThread](https://doc.qt.io/qtforpython-6/PySide6/QtCore/QThread.html): worker untuk operasi latar belakang.

## Build Windows

Belum dilakukan. Setelah aplikasi dan data penelitian teruji di Mac, siapkan launcher/spec PyInstaller serta lingkungan Windows. Petunjuk dalam AGENT.MD merupakan rencana build; file spec belum tersedia pada versi ini.

## ERP presentation

`presentation.py` menampilkan mean per channel pada window Early/P300/LPP dan slideshow per jenis event. Hasil semua event dihitung melalui worker yang sama dengan pipeline ERP. Skala warna ditetapkan sekali dari seluruh nilai mean presentasi. Frame tidak mewakili stimulus individual jika kode event digunakan untuk beberapa stimulus.

Uji native dan screenshot halaman baru:

```bash
venv/bin/python scripts/smoke_presentation.py
```

Snapshot tersimpan di `docs/images/07-presentation.png`. Pemrosesan semua event saat ini mengulang pipeline per kelompok, sehingga dapat memakan waktu dan memori pada rekaman besar. Presentasi belum mendukung ekspor video atau penyimpanan frame di manifest.


## Animasi 3D dan optimasi playback

- `brain3d.py`: mesh ilustratif dibuat sekali, bobot spasial dihitung per hasil ERP, warna vertex diperbarui dari sampel ERP. Renderer memakai PyQtGraph OpenGL dan PyOpenGL. OpenGL dibuat hanya saat halaman 3D dibuka sehingga tes offscreen dan analisis biasa tidak memerlukan konteks GPU.
- Playback memakai waktu monoton dengan timer presisi 16 ms; kecepatan waktu analisis tetap mengikuti waktu berlalu, bukan jumlah tick. Frame dapat dilewati jika perangkat sibuk.
- Visualisasi 3D memakai sampel aktual, tanpa menambah sampel EEG sintetis. Tidak ada source localization atau model MRI.
- ERP presentation menyiapkan raster 1200×400 secara bertahap sebelum Play aktif. QPainter membaurkan gambar selama 35% akhir durasi event; Matplotlib tidak dipanggil selama playback. Cache dibatasi 64 frame, sekitar 123 MB RGBA maksimum di luar overhead UI dan hasil analisis.
- Pembentukan raster tetap memakai GUI thread per gambar; pada banyak event, tahap persiapan dapat terasa lambat. Worker analisis berjalan terpisah. Cache dibersihkan ketika hasil tidak valid.
- Snapshot parameter kamera, kecepatan, dan frame animasi tidak disimpan dalam manifest project.

Pemeriksaan native GPU dan performa:

```bash
venv/bin/python scripts/smoke_animation.py
```

Laporan ada di `artifacts/animation-performance.json`; screenshot di `artifacts/brain3d-macos.png` dan `artifacts/erp-fade-macos.png`. Tes mengukur interval swap OpenGL dan interval paint Qt pada demo, bukan benchmark seluruh perangkat.

Referensi: [PyQtGraph GLMeshItem](https://pyqtgraph.readthedocs.io/en/latest/api_reference/3dgraphics/glmeshitem.html).

Kontrol ERP Presentation mengikuti Brain 3D: Putar/Pause, Stop, dan kecepatan 0,1×–1×. Timeline memakai milidetik presentasi (1,5 detik/event pada 1×), berbasis elapsed clock. Pause mempertahankan fade; seek dan perubahan kecepatan mempertahankan posisi tanpa menghitung ulang topomap.

## Pembanding alur EEG

Repository pembanding yang ditinjau: https://github.com/alesuarez92/NeuronalDataAnalyzerLab
(README, 5 Oktober 2026). Proyek tersebut memisahkan input EEG, posisi elektroda,
filter/reference, trial rejection, ERP dan pelaporan. VARD menggunakan alur yang
serupa untuk mengarahkan impor SET/FDT, validasi parameter, dan menu AATR mandiri;
tidak menyalin kode atau mengklaim kesetaraan metode/hasil dengan aplikasi tersebut.
