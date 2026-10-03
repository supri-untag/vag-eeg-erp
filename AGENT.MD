# Panduan Pengembangan VARD EEG–ERP

## 1. Tujuan dan sumber kebutuhan

Bangun aplikasi desktop menggunakan Python untuk analisis dan visualisasi EEG–ERP sesuai [README.MD](README.MD). Target distribusi adalah aplikasi Windows 10/11 64-bit yang dapat dijalankan melalui `.exe` tanpa memasang Python secara terpisah.

Urutan kerja wajib: **kembangkan dan uji di macOS → pastikan aplikasi berjalan baik di Mac → build `.exe` di Windows → uji executable Windows**. macOS menjadi lingkungan utama pengembangan dan pengujian awal. Build distribusi dilakukan setelah alur aplikasi yang akan dirilis lolos pengujian di Mac.

Dokumen ini menjadi panduan kerja pengembang dan agen AI. README.MD merupakan acuan kebutuhan fitur dan batasan ilmiah. Instruksi eksplisit pengguna menjadi acuan utama jika ada perubahan ruang lingkup.

Status implementasi: versi awal aplikasi desktop tersedia di `src/vard_eeg_erp`, dengan demo sintetis, import BDF/EDF, preprocessing, ERP, linked cursor, topomap, project JSON, dan ekspor CSV, serta ERP presentation dengan fade dan Brain 3D ilustratif. Lihat `docs/development.md` untuk menjalankan aplikasi dan `docs/validation.md` untuk bukti pengujian. Struktur modular lengkap dan build Windows di bawah tetap menjadi target pengembangan.

## 2. Keputusan teknis awal

Gunakan rancangan berikut untuk implementasi desktop:

| Bagian | Pilihan awal | Tujuan |
|---|---|---|
| Bahasa | Python; tetapkan versi setelah memeriksa kompatibilitas dependensi | Engine dan aplikasi desktop |
| GUI | PySide6 / Qt Widgets | Window, dialog, panel, dan interaksi |
| Analisis EEG | MNE-Python, NumPy, SciPy | Pembacaan data dan pemrosesan EEG–ERP |
| Grafik | PyQtGraph dan Matplotlib | Waveform interaktif, topomap, dan ekspor ilmiah |
| Data tabular | Pandas | Tabel hasil dan ekspor |
| Metadata lokal | SQLite | Project, konfigurasi, dan processing history |
| Data numerik | File terpisah sesuai format dan ukuran | Menghindari penyimpanan array besar dalam tabel metadata |
| Distribusi | PyInstaller | Bundle executable Windows |
| Pemeriksaan | pytest dan Ruff | Pengujian numerik dan konsistensi kode |

SQLite merupakan penyesuaian awal dari rekomendasi PostgreSQL di README untuk aplikasi desktop mandiri. Pisahkan akses penyimpanan agar PostgreSQL dapat ditambahkan ketika kebutuhan multiuser muncul.

Versi 0.1 memakai manifest `.vard.json` untuk satu rekaman per project agar alur simpan/buka dapat digunakan terlebih dahulu. Manifest menyimpan referensi sumber, parameter, history, serta pilihan tampilan; hasil dihitung ulang ketika dibuka. SQLite tetap menjadi target ketika project mencakup banyak subjek/sesi.

Pilih versi dependensi yang kompatibel, catat dalam `pyproject.toml`, dan simpan versi hasil resolusi untuk build yang dapat diulang. Tambahkan dependensi hanya ketika fitur memerlukannya. Aplikasi inti harus dapat digunakan secara lokal tanpa server atau koneksi internet.

## 3. Struktur kode yang dituju

```text
VAG-EEG-ERP/
├── AGENT.MD
├── README.MD
├── pyproject.toml
├── src/
│   └── vard_eeg_erp/
│       ├── __init__.py
│       ├── __main__.py
│       ├── app.py
│       ├── ui/               # Window, widget, dialog
│       ├── application/      # Workflow, worker, dan shared state
│       ├── domain/           # Model project, komponen, ROI, scoring
│       ├── analysis/         # Preprocessing, epoch, ERP, fitur
│       ├── io/               # Import dan ekspor
│       ├── storage/          # Metadata, konfigurasi, dan history
│       └── resources/        # Ikon, tema, konfigurasi bawaan
├── tests/
│   ├── unit/
│   ├── integration/
│   └── fixtures/             # Data sintetis kecil
├── packaging/
│   ├── launcher.py
│   └── vard.spec
├── scripts/
│   └── build_windows.ps1
└── docs/
    ├── development.md
    ├── build-windows.md
    └── validation.md
```

Buat direktori saat diperlukan. Engine analisis harus dapat dipanggil dan diuji tanpa membuka GUI. UI memanggil workflow aplikasi; operasi file dan database melalui modul penyimpanan atau import/export.

## 4. Aturan implementasi

### Tampilan terang bergaya Metronic

- Terapkan tema terang sebagai tampilan utama, termasuk ketika sistem operasi menggunakan dark mode.
- Gunakan karakter visual Metronic: sidebar putih, workspace abu-abu sangat muda, kartu putih, border lembut, tombol utama biru, badge status, dan tabel rapi. Implementasi memakai widget Qt; aset Metronic tidak disertakan.
- Gunakan token warna: background `#F5F7FA`, surface `#FFFFFF`, primary `#1B84FF`, teks `#252F4A`, teks sekunder `#78829D`, border `#E8EDF3`, success `#17C653`, warning `#FFF8DD`.
- Gunakan spacing konsisten 8–24 px, radius kartu 12 px, radius kontrol 6–8 px, serta hierarki judul/label/nilai yang jelas.
- Grafik memakai latar putih dengan grid tipis dan satuan eksplisit. Warna ilmiah topomap harus mewakili polaritas/amplitudo data, terpisah dari aksen dekoratif UI.
- Sediakan status loading, pesan error, keadaan kosong, tombol disabled, dan label demo sintetis. Gunakan teks bersama warna untuk menyampaikan status.
- Pertahankan keterbacaan pada layar Mac; panel panjang harus dapat di-scroll. Detail desain ada di `docs/design.md`.

### Kode dan data

- Gunakan type hint pada antarmuka modul, nama yang jelas, dan fungsi dengan tanggung jawab terfokus.
- Gunakan `pathlib`; hindari path absolut mesin pengembang dan ketergantungan pada current working directory.
- Pertahankan kompatibilitas macOS dan Windows. Pisahkan kode khusus sistem operasi; hindari ketergantungan pada Windows API untuk fitur inti. Catat versi macOS, arsitektur Mac, Python, dan dependensi yang benar-benar diuji.
- Jalankan pembacaan file besar, filtering, epoching, dan ekspor berat melalui worker. Pembaruan widget tetap di thread GUI.
- Sediakan status proses, penanganan error, dan pembatalan jika operasi mendukungnya.
- Gunakan lazy loading, pembacaan bertahap, atau cache sesuai kebutuhan ukuran data. Cache harus dibatalkan ketika data atau parameter analisis berubah.
- Simpan log diagnostik ke lokasi pengguna; tampilkan pesan error yang dapat dipahami pengguna.
- Gunakan data sintetis berlabel untuk demo dan tes. Jangan menampilkan hasil dummy sebagai analisis rekaman pengguna.
- Jangan memasukkan rekaman subjek, identitas pribadi, kredensial, `venv`, `build`, atau `dist` ke version control.

## 5. Integritas ilmiah dan sinkronisasi

Prinsip utama: **ONE DATA — MULTIPLE SYNCHRONIZED REPRESENTATIONS**.

- File EEG asli tidak boleh ditimpa. Simpan hasil preprocessing sebagai turunan beserta parameter dan asal data.
- Gunakan satu state analisis untuk subject, stimulus, condition, channel/ROI, komponen, dan waktu terpilih.
- ERP, topomap, nilai channel, dan visualisasi lain harus mengambil data dari hasil analisis yang sama.
- Simpan waktu internal dalam detik dan amplitudo dalam volt, dengan konversi eksplisit ke ms dan µV pada tampilan/ekspor. Cantumkan satuan.
- Pemetaan cursor ke indeks sampel harus konsisten. Bila waktu pilihan berada di antara sampel, gunakan kebijakan yang terdokumentasi dan tampilkan waktu sampel aktual.
- Validasi sampling rate, event timing, channel type, montage, reference, batas epoch, baseline, dan parameter filter sebelum proses.
- Jika posisi elektroda belum tersedia, jelaskan data yang diperlukan untuk topomap. Jangan membuat posisi elektroda secara diam-diam.
- Definisikan polaritas peak, window, cara agregasi ROI, dan satuan AUC secara eksplisit.
- Simpan jumlah trial diterima/ditolak, alasan penolakan, parameter, versi aplikasi/dependensi, dan processing history.
- Komponen ERP, rentang waktu, ROI, normalisasi, dan bobot VARS harus dapat dikonfigurasi serta memiliki versi.
- Simpan enam domain VARD secara terpisah dari composite score dan subjective rating.
- Jangan mengarang rumus VARD/VARS yang belum ditentukan. Tandai konfigurasi eksperimental dan dokumentasikan definisi fitur sebelum implementasi scoring.
- VARS merupakan skala eksperimental. Jangan menyajikannya sebagai persentase keindahan atau pengukuran neuron individual.

Untuk neural/network representation, tampilkan keterangan yang diwajibkan README:

> Neural Activity Representation — visualization derived from scalp EEG electrical potentials; not direct imaging of individual neuronal activity.

## 6. Urutan pengembangan

### Tahap 1 — Fondasi dan MVP ilmiah

1. Siapkan package, GUI dasar, project manager, penyimpanan, dan logging.
2. Jalankan GUI dari source di macOS dan pastikan startup, resource, dialog file, serta logging bekerja.
3. Implementasikan import BDF, metadata, dan EEG viewer.
4. Tambahkan event mapping, preprocessing, epoch, baseline, dan ERP averaging.
5. Tambahkan komponen ERP yang dapat diatur, topomap, dan linked cursor.
6. Tambahkan penyimpanan history dan ekspor hasil numerik/gambar dasar.
7. Validasi hasil terhadap pipeline MATLAB/EEGLAB sesuai README.
8. Uji alur MVP secara menyeluruh di macOS. Setelah lulus, lanjutkan build dan pengujian `.exe` di Windows sesuai bagian 7.

Uji penerimaan inti: import BDF → pilih event → buat ERP → pilih 400 ms → cursor ERP, nilai channel, dan topomap menggunakan sampel waktu yang sama. Gunakan waktu sampel terdekat jika 400 ms tidak tepat tersedia.

Format tambahan mengikuti prioritas README: MAT dan EEGLAB SET/FDT, kemudian EDF/CSV. Dokumentasikan struktur MAT/CSV yang didukung dan kebutuhan file pendamping FDT.

### Tahap 2 — VARD dan VARS

Stimulus manager, ROI, ekstraksi fitur, profil enam domain, scoring model berversi, subjective rating, comparison, dan group analysis.

### Tahap 3 — Visualisasi lanjutan

Animated topomap, kepala 3D, representasi aktivitas listrik, dan ekspor video. Pertahankan hubungan waktu dan sumber data dengan visualisasi ilmiah.

### Tahap 4 — Analitik penelitian

Korelasi neural–behavioral, statistik, clustering, predictive model, validasi VARS, dan laporan penelitian.

## 7. Menjalankan di Mac dan build `.exe` Windows

### Pengembangan dan pengujian di macOS

Jalankan aplikasi langsung dari source dalam virtual environment selama pengembangan. Contoh perintah berikut digunakan **setelah** package, entry point, dan extra `dev` tersedia:

```bash
python3 -m venv venv
venv/bin/python -m pip install --upgrade pip
venv/bin/python -m pip install -e ".[dev]"
venv/bin/python run.py
venv/bin/python -m pytest
venv/bin/python -m ruff check .
```

Sebelum melanjutkan build Windows, pastikan pada Mac:

- Aplikasi dapat dibuka dan ditutup tanpa error; resource dan dialog file tampil dengan benar.
- Alur import BDF → preprocessing → ERP → topomap dengan linked cursor berjalan sesuai data uji.
- Project dapat disimpan dan dibuka kembali; hasil dapat diekspor ke folder pilihan pengguna.
- Proses berat tidak membekukan UI dan kesalahan input ditampilkan dengan jelas.
- Tes otomatis yang relevan lulus, pengujian GUI langsung dilakukan, dan hasilnya dicatat.

Build `.app` macOS bersifat opsional bila diminta. Pengujian awal cukup menggunakan aplikasi dari source. Jika data BDF referensi belum tersedia, laporkan batas pengujian dan jangan menyatakan alur BDF sudah terverifikasi hanya berdasarkan data sintetis.

### Build dan pengujian di Windows

Lakukan tahap ini setelah pengujian macOS untuk lingkup rilis lulus. Kelulusan di Mac tetap perlu dilanjutkan dengan pengujian executable pada Windows.

PyInstaller membundel aplikasi, interpreter, dan dependensi. Build Windows harus dijalankan di Windows, misalnya komputer Windows, VM, atau runner CI Windows. Pengembangan di macOS tetap memungkinkan, tetapi menjalankan PyInstaller di macOS tidak menghasilkan executable Windows.

Mulai dengan mode `onedir`; distribusikan seluruh folder hasilnya. Setelah stabil, sediakan `onefile` bila dibutuhkan satu file `.exe`. Mode `onefile` mengekstrak dependensi ke folder sementara saat dijalankan sehingga waktu startup perlu diuji.

Sumber: [Dokumentasi resmi cara kerja PyInstaller](https://pyinstaller.org/en/stable/operating-mode.html).

Ketentuan build:

- Simpan konfigurasi build di `packaging/vard.spec`, termasuk resource, ikon, metadata versi, serta hook/hidden import yang diperlukan.
- Gunakan launcher yang memanggil entry point aplikasi dengan guard `if __name__ == "__main__":`. Bila memakai multiprocessing, siapkan `freeze_support()` dan uji pada bundle Windows.
- Pastikan plugin Qt, library numerik, dan resource MNE yang digunakan ikut terkemas.
- Pisahkan resource bawaan dari data yang dapat diubah. Simpan pengaturan/log di lokasi data pengguna dan project di folder pilihan pengguna.
- Jangan menulis database atau hasil analisis ke folder instalasi maupun folder ekstraksi sementara PyInstaller.
- Gunakan mode console saat mendiagnosis build; aktifkan mode GUI tanpa console setelah logging dan pelaporan error tersedia.
- Uji path dengan spasi/Unicode, pembukaan dari shortcut, dan akun Windows tanpa hak administrator.
- Uji pada Windows bersih tanpa Python terpasang. Catat versi Windows, arsitektur, dependensi, dan hasil pengujian.

Contoh alur PowerShell **setelah** package, extra `dev`/`build`, dan spec diimplementasikan:

```powershell
py -m venv venv
.\venv\Scripts\python.exe -m pip install --upgrade pip
.\venv\Scripts\python.exe -m pip install -e ".[dev,build]"
.\venv\Scripts\python.exe -m pytest
.\venv\Scripts\python.exe -m ruff check .
.\venv\Scripts\python.exe -m PyInstaller --clean --noconfirm packaging/vard.spec
```

Tetapkan nama aplikasi pada spec menjadi `VARD-EEG-ERP`. Target hasil `onedir`: `dist/VARD-EEG-ERP/VARD-EEG-ERP.exe`; target `onefile`: `dist/VARD-EEG-ERP.exe`. Installer dapat ditambahkan sebagai tahap distribusi berikutnya.

## 8. Pengujian dan kriteria selesai

- Jalankan pemeriksaan numerik, integrasi, dan GUI di macOS terlebih dahulu. Catat lingkungan serta hasil aktual sebelum beralih ke build Windows.
- Uji numerik memakai sinyal sintetis dengan event dan hasil yang diketahui: satuan, epoch, baseline, averaging, peak, latency, dan AUC.
- Uji input gagal: file rusak, event tidak tersedia, channel/posisi hilang, window tidak valid, dan seluruh trial ditolak.
- Uji sinkronisasi cursor, perubahan pilihan analisis, pembatalan proses, serta simpan/buka project.
- Uji normalisasi VARS pada nilai konstan, data hilang, bobot tidak valid, dan pergantian versi model ketika scoring dibuat.
- Bandingkan hasil dengan MATLAB/EEGLAB menggunakan parameter yang sama. Dokumentasikan dataset referensi, toleransi numerik, perbedaan, dan hasil aktual.
- Jika dataset atau MATLAB belum tersedia, nyatakan validasi tersebut belum dilakukan. Tes sintetis tidak menggantikan validasi referensi.
- Ukur target refresh topomap ≤100 ms pada perangkat/dataset yang disebutkan; jangan mengklaim target tercapai tanpa pengukuran.
- Untuk rilis Windows, jalankan alur import → ERP → topomap → simpan/buka → ekspor pada executable hasil build.

Perubahan dianggap selesai jika perilakunya sesuai lingkup tugas, pemeriksaan relevan lulus, dokumentasi diperbarui, dan keterbatasan dilaporkan. Bedakan status kode selesai, aplikasi teruji di macOS, validasi ilmiah selesai, dan build Windows teruji.

## 9. Cara kerja agen

1. Baca README.MD dan panduan ini sebelum mengubah implementasi.
2. Periksa kode yang tersedia; lanjutkan pola yang sudah digunakan dan hindari perubahan di luar tugas.
3. Kerjakan dan uji fitur di macOS terlebih dahulu sambil menjaga kompatibilitas Windows. Lanjutkan build `.exe` setelah pengujian Mac lulus.
4. Jalankan pemeriksaan yang relevan. Dokumentasikan perintah yang belum dapat dijalankan dan alasannya.
5. Ringkas hasil dalam Bahasa Indonesia: perubahan, cara menjalankan, hasil uji, dan pekerjaan yang masih diperlukan.

Dokumen ini sengaja memakai nama `AGENT.MD` sesuai permintaan pengguna. Jangan mengasumsikan semua alat akan memuatnya otomatis; rujuk file ini secara eksplisit dalam instruksi pengembangan bila diperlukan.
