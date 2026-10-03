# Desain antarmuka VARD Studio

## Arah visual

Tema terang bergaya Metronic diterapkan menggunakan PySide6/Qt Widgets. Sidebar putih berada di kiri, header dan aksi utama di atas, lalu kartu metadata serta panel analisis. Aplikasi menggunakan gaya visual tersebut sebagai inspirasi; tidak membundel template atau aset Metronic.

| Token | Warna | Penggunaan |
|---|---|---|
| Workspace | `#F5F7FA` | Latar halaman |
| Surface | `#FFFFFF` | Sidebar, kartu, grafik, dialog |
| Primary | `#1B84FF` | Aksi utama, waveform, navigasi aktif |
| Text | `#252F4A` | Judul dan nilai |
| Muted | `#78829D` | Label sekunder |
| Border | `#E8EDF3` | Batas kartu dan tabel |
| Success | `#17C653` | Linked cursor |
| Warning | `#FFF8DD` | Badge demo sintetis |

## Tata letak

- Sidebar 218 px, dengan Overview & ERP, EEG recording, Events, dan Processing history.
- Kartu metadata: jumlah channel EEG, sampling rate, event, dan trial diterima.
- Toolbar analisis: pemilihan event/channel, parameter, serta Generate ERP.
- Waveform dan topomap ditampilkan berdampingan, dengan timeline bersama di bawahnya.
- Panel pengukuran komponen dan tabel nilai channel memakai sumber hasil ERP yang sama.
- Ukuran awal window 1400 × 920; panel analisis dapat di-scroll pada layar lebih kecil. Minimum window 1100 × 740.
- Font memakai font sistem melalui Qt; tidak perlu mengunduh font.

## Perilaku

Tema tetap terang ketika macOS memakai dark mode. Tombol terkait proses dinonaktifkan selama worker berjalan. Perubahan event atau parameter membatalkan hasil lama sehingga pengguna perlu Generate ERP kembali. Demo ditandai pada header dan pada kolom CSV.

Topomap memakai colormap divergen `RdBu_r` dan batas warna simetris yang tetap selama cursor bergerak dalam satu hasil ERP. Tanda dan amplitudo data menentukan warna, bukan tema dekoratif.

Tabel channel dan waktu cursor diperbarui segera. Render topomap ditunda 70 ms setelah perubahan cursor terakhir untuk mengurangi render berulang; ini belum merupakan bukti target latency ≤100 ms.

## Presentasi ERP

Halaman ERP presentation memakai tiga topomap sejajar dengan label elektroda, judul Early/P300/LPP, colorbar µV, dan kontrol slideshow. Acuan tata letak adalah video WhatsApp yang diberikan pengguna. Warna tetap divergen dengan skala bersama berdasarkan hasil analisis. Frame berganti berdasarkan jenis event dan tidak merepresentasikan animasi neuron atau anatomi 3D.


## Brain 3D dan gerakan

Halaman 3D mempertahankan tema terang dan kontrol yang sama: Play/Pause, Stop, kecepatan, serta timeline. Permukaan ilustratif diberi shading untuk kedalaman. Label polaritas dan batas µV tetap terlihat; shading bukan pengukuran amplitudo tambahan. Pernyataan keterbatasan ilmiah selalu ditampilkan.

ERP presentation memakai fade dari gambar event ke event berikutnya. Label transisi menjelaskan bahwa efek ini merupakan pembauran visual; menghentikan playback mengembalikan frame aktual. Waktu idle tidak memutar animasi. Semua timer playback dihentikan ketika halaman ditinggalkan.
