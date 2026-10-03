# Konfigurasi VARS Scoring

Status: eksperimental, konfigurasi model tahap awal. Belum ada model penelitian bawaan atau ekstraksi otomatis enam domain dari EEG.

![Halaman konfigurasi VARS](images/10-vars-scoring.png)

## Alur penggunaan

1. Generate ERP untuk event yang ingin dikaitkan dengan hasil.
2. Buka **VARS Scoring** di sidebar.
3. Isi versi model dan sumber data acuan (populasi, dataset, atau protokol normalisasi).
4. Klik dua kali sel untuk mengisi keenam domain V1–V6: definisi fitur beserta ROI/window, satuan, minimum dan maksimum acuan, bobot, serta arah `higher` atau `lower`.
5. Jumlah bobot harus 1; maksimum acuan harus lebih besar dari minimum. Fitur konstan dalam acuan tidak dapat dinormalisasi Min–Max.
6. **Simpan model** untuk menyimpan konfigurasi JSON. Konfigurasi yang belum lengkap boleh disimpan sebagai draft; perhitungan akan menolaknya sampai lengkap.
7. Isi **Fitur mentah** sesuai definisi dan satuan model, lalu **Hitung VARS**.
8. **Ekspor hasil JSON** menyimpan enam skor domain, fitur mentah, komposit, konfigurasi model lengkap, timestamp, dan provenance analisis. Data sintetis tetap ditandai melalui metadata analisis.

## Perhitungan

Untuk setiap domain: `r = clip((fitur − min) / (max − min), 0, 1)`.
Arah `higher` menghasilkan `100 × r`; arah `lower` menghasilkan `100 × (1 − r)`.
Komposit adalah jumlah `bobot × skor domain`. Angka di luar acuan diberi tanda `*` dan dibatasi ke 0–100; nilai mentah tetap tersimpan di ekspor.

Skor adalah respons relatif eksperimental, bukan persentase keindahan. Definisi fitur dan acuan perlu ditetapkan peneliti serta divalidasi; aplikasi tidak mengasumsikan bahwa amplitudo yang lebih besar selalu berarti respons estetika lebih tinggi.

## Penyimpanan dan batasan

- Model dan hasil disimpan sebagai file JSON terpisah. **Simpan project** belum menyimpan worksheet VARS; simpan model dan ekspor hasil sebelum menutup aplikasi.
- Ganti versi model ketika definisi, acuan, atau bobot berubah. Ekspor menyertakan snapshot konfigurasi untuk audit; aplikasi belum memiliki registry yang mengunci versi model.
- Perubahan isian menghapus hasil lama. Pergantian hasil analisis menghapus fitur mentah agar tidak terbawa ke event lain; konfigurasi model dipertahankan.
- Min–Max tersedia. Z-score, percentile, normalisasi subjek/kelompok otomatis, custom formula, ekstraksi fitur otomatis, dan validasi ilmiah masih tahap berikutnya.
