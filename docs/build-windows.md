# Build Windows dan uninstall

Status: konfigurasi build tersedia. File EXE dan installer belum dibuat atau diuji di Windows dari sesi macOS ini. PyInstaller bukan cross-compiler: build Windows dijalankan pada Windows.

## Build lokal Windows x64

Pasang Python 3.12 x64 beserta Python Launcher dan Inno Setup 6. Buka PowerShell di folder proyek:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/build_windows.ps1
```

Skrip membuat `.venv-build`, memasang dependensi, menjalankan tes, membundel aplikasi dengan PyInstaller, lalu menjalankan EXE hasil build untuk memeriksa startup Qt, demo ERP, topomap, simpan/buka project, dan ekspor CSV. Pemeriksaan berjalan dari folder sementara di luar source dengan timeout 180 detik. Installer Inno Setup hanya dibuat jika EXE keluar dengan kode 0 dan laporan berstatus `passed`. Gunakan `-InnoCompiler "C:\lokasi\ISCC.exe"` bila compiler berada di lokasi lain.

Hasil yang diharapkan:

- `dist/VARD-EEG-ERP/VARD-EEG-ERP.exe`: aplikasi beserta dependensi di folder yang sama. Jangan menyalin EXE ini sendirian.
- `dist/installer/VARD-EEG-ERP-Setup-0.1.0-x64.exe`: installer untuk dibagikan.
- `dist/installer/SHA256.txt`: checksum installer.
- `dist/requirements-windows-built.txt`: snapshot dependensi build Windows; bukan memakai snapshot macOS.
- `dist/bundle-smoke.json`: hasil pemeriksaan EXE, termasuk traceback bila impor atau pipeline gagal.

## Perbaikan `No module named 'mne.utils.config'`

Error ini terjadi pada bundel ketika modul Python MNE yang dimuat melalui `lazy_loader` tidak ikut dikemas. Spec kini menyertakan submodul MNE serta file `.pyi` yang dipakai lazy loader, selain data MNE. Menginstal MNE pada komputer pengguna tidak memperbaiki EXE lama: aplikasi memakai dependensi di dalam bundelnya.

Gunakan source yang sudah diperbaiki, tutup aplikasi lama, lalu jalankan kembali perintah build di atas (sudah memakai `--clean`). Setelah build dan uji EXE berhasil, pasang installer baru dari `dist/installer`. Jangan memakai kembali installer lama atau menyalin EXE tanpa folder dependensinya.

Untuk mengulang pemeriksaan bundel atau aplikasi yang sudah terpasang dari komputer build:

```powershell
.\.venv-build\Scripts\python.exe scripts/check_bundle.py dist/VARD-EEG-ERP/VARD-EEG-ERP.exe dist/bundle-smoke.json
.\.venv-build\Scripts\python.exe scripts/check_bundle.py "$env:LOCALAPPDATA\Programs\VARD-EEG-ERP\VARD-EEG-ERP.exe" dist/installed-smoke.json
```

Verifikasi perbaikan pada 5 Oktober 2026: 37 tes source lulus di macOS; smoke test source dengan Qt offscreen lulus untuk startup, demo ERP (12 trial), topomap, project, dan CSV. Executable dan installer Windows yang diperbaiki belum dijalankan dari sesi macOS ini. Smoke test tidak menggantikan pemeriksaan OpenGL/Brain 3D dan instalasi pada Windows bersih.

## Build melalui GitHub Actions

Setelah proyek berada di repository GitHub, buka **Actions → Windows installer → Run workflow**. Unduh artifact `VARD-EEG-ERP-Windows-x64` setelah workflow berhasil. Workflow dibuat manual agar tidak membangun setiap kali ada perubahan. Belum ada workflow yang dijalankan atau source yang diunggah dari sesi ini.

## Instalasi dan uninstall

Installer memasang aplikasi per pengguna di `%LOCALAPPDATA%\Programs\VARD-EEG-ERP`, menyediakan shortcut Start Menu serta pilihan shortcut Desktop. Pengguna akhir tidak perlu memasang Python.

Uninstall melalui **Settings → Apps → Installed apps → VARD EEG-ERP → Uninstall**, atau **Start Menu → VARD EEG-ERP → Uninstall VARD EEG-ERP**. Uninstaller menghapus file aplikasi dan shortcut. Rekaman EEG, project, model VARS, ekspor, serta log pengguna di luar folder instalasi tidak dihapus.

## Pemeriksaan sebelum distribusi

Pada Windows bersih tanpa Python: install → buka demo → ERP dan topomap → Brain 3D/OpenGL → presentasi → VARS → simpan/buka project → ekspor. Uji BDF/EDF referensi yang tersedia. Tutup aplikasi, uninstall, lalu pastikan aplikasi/shortcut terhapus dan data penelitian tetap ada. Uji juga install ulang dan path dengan spasi. Tes source saat build belum membuktikan bundle/installer berjalan benar.

Installer belum ditandatangani dengan sertifikat code signing. Versi dependensi saat ini memakai rentang dari `pyproject.toml`; snapshot hasil build dicatat untuk evaluasi dan penguncian setelah Windows teruji.

Referensi: [PyInstaller](https://pyinstaller.org/en/stable/), [Inno Setup uninstall](https://jrsoftware.org/ishelp/topic_setup_uninstallable.htm).
