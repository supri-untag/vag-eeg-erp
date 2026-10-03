# Hasil pengujian versi 0.1

Tanggal: 3 Oktober 2026, zona waktu Asia/Jakarta.

## Lingkungan

- macOS 26.5.1, ARM64.
- Python 3.14.5.
- PySide6 6.11.2, MNE 1.13.2, NumPy 2.5.3, SciPy 1.18.1.
- Matplotlib 3.11.2, PyQtGraph 0.14.0.
- Dependensi lengkap: `requirements-macos-tested.txt`.

## Pemeriksaan yang dilakukan

| Pemeriksaan | Hasil |
|---|---|
| Unit/integration test melalui pytest | 27 tes lulus |
| Pemulihan plugin Qt macOS | Hidden flag dipulihkan, isi/flag lain tetap, path eksternal dilindungi |
| Ruff lint | Lulus |
| Ruff format | Lulus |
| Qt GUI offscreen | Cursor, nilai channel, topomap, invalidasi hasil, dan worker lulus |
| Window native macOS | Lulus, platform Qt `cocoa` |
| Demo sintetis | 32 channel, 256 Hz, 24 event; 12 trial diterima untuk Visual A |
| Import BDF | Lulus memakai fixture BDF biner 24-bit sintetis dengan trigger diketahui |
| Project | Simpan/buka, rekonstruksi hasil, dan history lulus |
| Ekspor CSV | Jumlah baris, konversi ms/µV, dan penanda demo lulus |

Perintah untuk mengulangi pemeriksaan tersedia pada [development.md](development.md).

## Bukti GUI

Script `scripts/smoke_gui.py` membuka window native, menjalankan worker demo, mencoba navigasi, menyimpan dan membuka project, mengekspor CSV, serta menangkap screenshot. Pemilihan path file diganti secara otomatis pada script; dialog pemilihan file native belum diuji melalui interaksi manusia.

Artefak lokal hasil pengujian:

- `artifacts/vard-macos.png`: screenshot antarmuka native yang diperiksa secara visual.
- `artifacts/smoke-report.json`: laporan otomatis.
- `artifacts/smoke.vard.json`: manifest demo.
- `artifacts/smoke.csv`: hasil numerik demo.

Memilih 400 ms menghasilkan sampel 398.4375 ms pada 256 Hz. Nilai cursor ERP, slider, tabel channel, dan topomap mengacu pada indeks sampel yang sama. Grafik mempertahankan satuan ms dan µV tanpa penambahan prefiks SI otomatis.

## Batas hasil pengujian

- Data EEG penelitian pengguna dan pembandingan MATLAB/EEGLAB belum tersedia; validasi ilmiah belum selesai.
- Pembaca EDF tersedia melalui MNE, tetapi pengujian fixture biner khusus saat ini menggunakan BDF.
- Respons UI untuk rekaman besar, 128 channel/2048 Hz, dan target refresh ≤100 ms belum diukur.
- Screenshot dan smoke test dilakukan pada Mac ARM64 ini; Intel Mac serta versi macOS lain belum diuji.
- Windows dan executable `.exe` belum dibangun atau diuji.
- Pipeline ini belum menerapkan ICA, penolakan epoch manual, VARS, atau analisis multi-subjek.

Hasil ini menunjukkan fungsi versi awal berjalan pada lingkungan uji; belum merupakan validasi metode ilmiah atau kelulusan seluruh requirement README.

## Pembaruan 4 Oktober 2026

Pengujian presentasi mencakup mean numerik tiap window, penolakan epoch yang tidak mencakup LPP, pergantian frame, penghentian playback, dan invalidasi data. Screenshot halaman baru tersedia pada `docs/images/07-presentation.png`.


## Animasi 3D dan ERP — 4 Oktober 2026

Pengujian native `scripts/smoke_animation.py` berhasil: konteks OpenGL, pemutaran,
sinkronisasi sampel dengan Overview, fade dari cache, penghentian, dan invalidasi.
Model 3D menggunakan mesh ilustratif, bukan anatomi dari MRI.

Hasil pengukuran singkat pada demo 32 channel di Mac ARM64 ini:

| Metrik | Hasil |
|---|---:|
| Rata-rata swap frame OpenGL | 62,75 fps |
| Median interval frame 3D | 15,83 ms |
| Persentil 95 interval frame 3D | 23,04 ms |
| Rata-rata paint ERP presentation | 62,42 fps |
| Persentil 95 interval paint ERP | 17,89 ms |

Swap OpenGL diukur selama sekitar 4 detik; paint ERP sekitar 1,25 detik. Ini adalah
pengukuran singkat rendering UI, bukan jaminan 60 fps pada semua perangkat atau
rekaman besar. Data mentah pengukuran: `artifacts/animation-performance.json`.
27 tes otomatis mencakup bobot spasial, penolakan posisi hilang, sinkronisasi
3D–ERP, pemakaian cache saat fade, dan pemulihan frame aktual saat Pause.

## Konfigurasi VARS — 4 Oktober 2026

37 tes lulus (`venv/bin/python -m pytest -q`): termasuk bobot, normalisasi, clipping, arah skor, data nonfinite, dan invalidasi worksheet. Ruff lulus. `scripts/smoke_vars.py` lulus pada GUI native macOS: navigasi halaman, validasi tanpa ERP, dan screenshot. Pengujian ini memverifikasi implementasi; belum memvalidasi VARS sebagai skala penelitian.
