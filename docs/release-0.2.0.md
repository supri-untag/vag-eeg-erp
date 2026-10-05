# VARD Studio 0.2.0 — fitur eksperimen

Ruang lingkup versi ini dibekukan pada fitur yang sudah tersedia. Finalisasi
source bukan pernyataan bahwa validasi ilmiah atau penerimaan Windows selesai.

## Fitur

- Analisis EEG/ERP, linked cursor, topomap, project, ekspor CSV, dan presentasi.
- Brain 3D ilustratif: mode cyan–ungu transparan serta mode potensial biru–merah.
- VARS manual: model Min–Max, bobot enam domain, simpan model dan ekspor hasil.
- Dashboard AATR: impor FIG asli dengan enam kurva ERP, panel temporal, kartu klasifikasi, zoom, dan ekspor PNG/PDF.
- Tab AATR V7B: klasifikasi |Z| yang sudah dinormalisasi dan impor ringkasan MAT.
- Versi pada sidebar dan provenance analisis mengikuti versi package.

## Batas versi

VARS tetap eksperimental. Pengguna mengisi fitur sesuai protokol dan wajib
menentukan versi model serta sumber acuan. Skor bukan persentase keindahan.
Worksheet VARS dan AATR belum disimpan dalam project EEG. Simpan model dan
hasil VARS secara terpisah; pertahankan file MAT sumber untuk AATR.

Belum tersedia: ekstraksi V1–V6 otomatis, normalisasi Z EEG otomatis, source localization atau anatomi MRI.
Partikel Brain 3D merepresentasikan potensial scalp secara ilustratif.

## Verifikasi dan distribusi

Tes source: 48 tes lulus pada macOS. Impor AATR dan perhitungan UI teruji.
774 kelas subjek dan 18 kode ringkasan cocok dengan lampiran. Uji native OpenGL,
playback dan sinkronisasi berhasil sekitar 63 FPS pada mesin pengembangan.

Setelah source terbaru di-push, jalankan Actions → Windows installer →
Run workflow → main. Bagikan `VARD-EEG-ERP-Setup-0.2.0-x64.exe` hanya setelah
build berhasil dan hasil instalasi diuji di Windows. Jangan menjalankan ulang
run lama untuk mengambil perubahan baru. Installer 0.2.0 belum diverifikasi.

Uji penerimaan: instalasi → demo → ERP/topomap → Brain 3D kedua mode →
VARS simpan/buka model dan ekspor → AATR impor MAT → simpan/buka project EEG →
uninstall. Periksa shortcut menjalankan lokasi instalasi yang baru.

Tambahan: Import folder dan katalog rekaman rekursif. BDF/EDF dapat diperiksa
serta dibuka dari katalog; format pendukung diinventarisasi tanpa dieksekusi
atau digabung otomatis. Verifikasi pada folder lokal SUBJEK 101 menemukan
356 file, termasuk satu BDF terbaca (32 EEG, 200 Hz, 71 trigger) dengan status
Perlu tinjau. Data penelitian tidak disalin ke repository.
