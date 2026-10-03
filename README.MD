# Visual Aesthetic Response Detection (VARD)

## Aplikasi desktop — versi awal 0.1

Aplikasi Python/PySide6 sudah tersedia dengan tema terang bergaya Metronic: sidebar putih, kartu ringkasan, aksen biru, grafik, dan tabel. Pengembangan serta pengujian dilakukan di macOS terlebih dahulu. Build `.exe` Windows menjadi tahap berikutnya.

### Menjalankan di Mac

```bash
python3 -m venv venv
venv/bin/python -m pip install -e ".[dev]"
venv/bin/python run.py
```

Jika virtual environment sudah disiapkan, cukup jalankan perintah terakhir. Aplikasi membuka **demo sintetis** agar antarmuka dan analisis dapat langsung dicoba. Gunakan `--empty` untuk memulai tanpa demo.

### Fitur yang tersedia

- Import BDF/EDF dan pembacaan trigger/annotation.
- Preview EEG hingga 16 channel pada 10 detik pertama, daftar event, dan metadata.
- Pengaturan filter, notch, reference, epoch, baseline, serta ambang peak-to-peak.
- ERP per event/channel; mean, absolute peak bertanda, latency, dan AUC.
- Cursor ERP, timeline, topomap, dan tabel channel pada sampel yang sama.
- Pilihan P300, LPP, early visual, serta window custom.
- ERP presentation: tiga topomap Early/P300/LPP dengan cache gambar dan transisi fade antar-event.
- VARS Scoring eksperimental: konfigurasi enam domain, Min–Max, fitur manual, model JSON, dan ekspor skor. Lihat [panduan VARS](docs/vars-scoring.md).
- Brain 3D: model ilustratif dengan proyeksi potensial scalp, orbit/zoom, dan playback timeline ERP.
- Simpan/buka project `.vard.json`, processing history, dan ekspor ERP CSV dalam ms/µV.
- Pemrosesan EEG melalui worker agar GUI tetap dapat merespons.

Untuk rekaman yang tidak menyimpan posisi elektroda, aktifkan montage standard 10–20 hanya jika nama dan susunan channel memang sesuai. Topomap menampilkan pesan bila posisi belum lengkap.

**Batas versi awal:** satu rekaman per project; ekstraksi fitur VARS otomatis, multi-subjek, impor MAT/SET, event editing, ICA, source localization, dan ekspor video belum diimplementasikan. Validasi MATLAB dan rekaman penelitian pengguna tetap diperlukan. Konfigurasi build Windows dan installer dengan uninstall tersedia; binary Windows belum dibuat/diuji. Lihat [panduan build Windows](docs/build-windows.md).

Panduan: **[panduan pengguna bergambar](docs/panduan-pengguna.md)** · [daftar dokumentasi](docs/README.md) · [pengembangan](docs/development.md) · [desain terang](docs/design.md) · [pengujian](docs/validation.md) · [panduan agen](AGENT.MD).

---

## Dokumen kebutuhan lengkap

Bagian berikut adalah spesifikasi target platform, termasuk fitur yang belum tersedia pada versi awal.

## Rancangan Fitur pada Platform EEG–ERP Neurovisualization

**Versi Dokumen:** 1.0
**Status:** Draft Requirement untuk Pengembangan
**Tujuan Dokumen:** Menjadi acuan kebutuhan fungsional dan teknis untuk tim IT dalam membangun modul **Visual Aesthetic Response Detection (VARD)** pada platform EEG–ERP.

---

## 1. Ringkasan

**Visual Aesthetic Response Detection (VARD)** adalah modul analisis dan visualisasi pada platform EEG–ERP yang dirancang untuk mendeteksi, mengukur, dan menampilkan pola respons neuroelektrik terhadap stimulus visual/estetika.

VARD tidak dimaksudkan untuk menyatakan secara langsung bahwa suatu objek adalah "indah" atau "tidak indah". Sistem mengukur **respons EEG/ERP terhadap stimulus visual**, kemudian menyajikannya sebagai profil respons yang dapat dibandingkan dengan data penilaian subjektif pengguna/responden.

Prinsip utama sistem:

> **ONE DATA — MULTIPLE SYNCHRONIZED REPRESENTATIONS**

Satu sumber data EEG digunakan secara konsisten untuk menghasilkan:

- EEG waveform;
- ERP waveform;
- ERP component;
- scalp topomap;
- channel/ROI activity;
- visual aesthetic response profile;
- dynamic brain/electrical-activity representation.

---

# 2. Tujuan Pengembangan

VARD dikembangkan untuk:

1. membaca dan memproses data EEG dari file BDF;
2. menampilkan EEG dan ERP secara terintegrasi;
3. mendeteksi respons EEG berdasarkan stimulus visual;
4. menyediakan pilihan komponen ERP;
5. menghasilkan topomap berdasarkan waktu atau ERP window;
6. menampilkan ERP dan topomap secara bersamaan dan tersinkronisasi;
7. mengekstraksi parameter respons visual;
8. membentuk **Visual Aesthetic Response Profile**;
9. mendukung pengembangan skala **Visual Aesthetic Response Scale (VARS)**;
10. membandingkan respons antarsubjek, stimulus, kondisi, atau kelompok;
11. menyediakan visualisasi ilmiah dan visualisasi presentasi secara terpisah;
12. menjaga kompatibilitas dengan workflow MATLAB/EEGLAB.

---

# 3. Batasan Ilmiah

VARD membaca aktivitas listrik yang direkam dari permukaan kepala melalui EEG.

Sistem **tidak boleh mengklaim** bahwa:

- EEG dapat menunjukkan neuron individual yang sedang aktif;
- topomap merupakan citra anatomi aktivitas otak;
- nilai VARD secara langsung berarti tingkat "keindahan";
- skor EEG dapat menggantikan penilaian subjektif estetika.

Untuk visualisasi network/neuron, antarmuka wajib menampilkan keterangan:

> **Neural Activity Representation — visualization derived from scalp EEG electrical potentials; not direct imaging of individual neuronal activity.**

---

# 4. Alur Sistem

```text
BDF / EEG DATA
      │
      ▼
RAW EEG READER
      │
      ▼
PREPROCESSING
 ├── Band-pass filter
 ├── High-pass filter
 ├── Low-pass filter
 ├── Notch filter
 ├── Re-reference
 ├── Bad-channel handling
 └── Artifact handling
      │
      ▼
EVENT / STIMULUS DETECTION
      │
      ▼
EPOCHING
      │
      ▼
BASELINE CORRECTION
      │
      ▼
ERP AVERAGING
      │
      ├──────────────────────┐
      ▼                      ▼
ERP WAVEFORM             CHANNEL VALUES
      │                      │
      ▼                      ▼
ERP COMPONENT            TOPOGRAPHIC MAP
      │                      │
      └──────────┬───────────┘
                 ▼
        FEATURE EXTRACTION
                 │
                 ▼
  VISUAL AESTHETIC RESPONSE
                 │
                 ▼
           VARS PROFILE
                 │
        ┌────────┼────────┐
        ▼        ▼        ▼
     GRAPH    TOPOMAP   DYNAMIC
                       VISUALIZATION
```

---

# 5. Input Data

## 5.1 Format EEG

Sistem minimal mendukung:

- `.bdf`
- `.edf`
- `.set`
- `.fdt`
- `.mat`
- `.csv`

Prioritas implementasi MVP:

1. BDF
2. MAT
3. EEGLAB SET/FDT

---

## 5.2 Metadata EEG

Sistem membaca:

- subject ID;
- session ID;
- sampling rate;
- jumlah channel;
- nama channel;
- channel location;
- durasi recording;
- event/trigger;
- waktu event;
- jenis stimulus;
- kode stimulus.

---

## 5.3 Data Stimulus

Setiap stimulus dapat memiliki:

- stimulus ID;
- nama stimulus;
- kategori;
- file gambar;
- deskripsi;
- kelompok eksperimen;
- kondisi;
- metadata tambahan.

Contoh:

```text
Stimulus ID   : RISHA-023
Category      : Architecture
Condition     : Modified
Image         : risha_023.jpg
```

---

# 6. Modul Utama

## 6.1 Project Manager

Pengguna dapat:

- membuat project baru;
- membuka project;
- menyimpan project;
- menggandakan project;
- memilih lokasi data;
- melihat processing history.

Struktur:

```text
PROJECT
├── SUBJECTS
├── STIMULI
├── RAW DATA
├── PREPROCESSING
├── ERP
├── TOPOGRAPHY
├── VARS
└── EXPORT
```

---

# 7. EEG Viewer

EEG Viewer harus mendukung:

- tampilan multichannel;
- zoom time;
- zoom amplitude;
- memilih channel;
- hide/show channel;
- channel grouping;
- event marker;
- stimulus marker;
- bad-channel marking;
- cursor nilai EEG.

Tampilan minimal:

```text
Fp1  ───╲_/╲____/╲────
Fp2  ─────╲___/╲──────
F3   ──╲____/╲________
F4   ─────╲_____/╲────
...
```

---

# 8. EEG Preprocessing

Semua parameter preprocessing harus dapat dikonfigurasi pengguna.

## 8.1 Filter

```text
High-pass    : configurable
Low-pass     : configurable
Band-pass    : configurable
Notch        : 50 Hz / 60 Hz / Off
```

---

## 8.2 Reference

Pilihan minimal:

- original reference;
- average reference;
- linked mastoid;
- custom reference.

---

## 8.3 Epoch

Parameter:

```text
Epoch start     : configurable
Epoch end       : configurable
Event source    : selected trigger
```

Contoh:

```text
-200 ms sampai +1000 ms
```

---

## 8.4 Baseline

User dapat menentukan baseline, contoh:

```text
-200 ms sampai 0 ms
```

---

## 8.5 Artifact Handling

Minimal mendukung:

- amplitude threshold;
- reject epoch;
- manual epoch rejection;
- bad-channel flag.

Pengembangan lanjutan:

- ICA;
- EOG detection;
- automated artifact detection.

---

# 9. Event dan Stimulus Manager

Sistem harus:

- membaca trigger dari BDF;
- menampilkan daftar event;
- menghubungkan event dengan stimulus;
- memungkinkan koreksi event;
- memungkinkan penambahan event manual;
- mendukung event code mapping.

Contoh:

| Event | Stimulus | Time |
|---|---|---:|
| S01 | RISHA-01 | 12.450 s |
| S02 | RISHA-02 | 18.930 s |
| S03 | RISHA-03 | 25.210 s |

---

# 10. ERP Engine

Sistem menghasilkan ERP berdasarkan:

- subject;
- stimulus;
- condition;
- electrode;
- ROI;
- selected trials.

Output:

- ERP waveform;
- mean amplitude;
- peak amplitude;
- peak latency;
- area under curve;
- duration;
- number of accepted trials.

---

# 11. ERP Component Manager

ERP tidak boleh dikunci hanya untuk P300 atau LPP.

User dapat membuat dan mengubah komponen ERP.

Default awal:

| Component | Window Awal |
|---|---:|
| Early Visual Response | 0–200 ms |
| Attention Window | 200–300 ms |
| P300 | 300–500 ms |
| LPP | 500–800 ms |
| Custom | User defined |

Contoh Custom:

```text
Component       : N170
Start           : 140 ms
End             : 200 ms
ROI             : P7, P8, O1, O2
Measurement     : Mean / Peak / AUC
```

---

# 12. ERP Graph Viewer

ERP graph:

```text
Y-axis : amplitude (µV)
X-axis : time (ms)
0 ms   : stimulus onset
```

Fitur:

- channel selector;
- ROI selector;
- component overlay;
- peak marker;
- baseline marker;
- stimulus onset marker;
- linked cursor;
- zoom;
- export image/data.

---

# 13. Linked Temporal Cursor

Ini merupakan **fitur wajib/core requirement**.

ERP, topomap, channel value, stimulus information, dan brain visualization menggunakan **satu timeline yang sama**.

Contoh:

```text
ERP
────────────────────│────────────────────
                   387 ms
                     │
       ┌─────────────┼──────────────┐
       ▼             ▼              ▼
   Topomap        Channels       Brain View
   387 ms         387 ms         387 ms
```

Requirement:

> Ketika pengguna memindahkan cursor ERP ke waktu tertentu, seluruh visualisasi lain harus diperbarui menggunakan data EEG/ERP pada waktu yang sama.

---

# 14. Topographic Map

Topomap harus memiliki dua mode.

## 14.1 Instantaneous Mode

Topomap dihitung pada satu timestamp.

Contoh:

```text
t = 387 ms
```

Sistem membaca nilai masing-masing channel pada timestamp tersebut dan melakukan spatial interpolation.

---

## 14.2 ERP Window Mode

Topomap dihitung berdasarkan rentang waktu.

Contoh:

```text
P300 = 300–500 ms
```

Nilai masing-masing electrode dihitung dari statistik yang dipilih:

- mean;
- peak;
- median;
- AUC.

---

# 15. Animated Topomap

Sistem dapat memutar perubahan topomap berdasarkan timeline.

Contoh:

```text
0 ms
↓
100 ms
↓
200 ms
↓
300 ms
↓
400 ms
↓
500 ms
↓
800 ms
```

Kontrol:

- play;
- pause;
- stop;
- frame step;
- playback speed;
- start/end time.

---

# 16. Visual Aesthetic Response Detection (VARD)

VARD merupakan engine yang mengekstraksi fitur EEG/ERP menjadi profil respons visual.

VARD versi awal memiliki enam domain:

| Kode | Domain | Window Awal | Parameter |
|---|---|---:|---|
| V1 | Visual Detection | 0–200 ms | amplitude / peak / response |
| V2 | Aesthetic Attention | 200–300 ms | amplitude / attention response |
| V3 | Cognitive Evaluation | 300–500 ms | P300 amplitude + latency |
| V4 | Sustained Aesthetic Processing | 500–800 ms | LPP amplitude + duration |
| V5 | Spatial Engagement | configurable | topographic distribution |
| V6 | Temporal Persistence | 0–800 ms | duration / AUC |

> Rentang waktu di atas adalah konfigurasi awal dan harus dapat diubah.

---

# 17. Visual Aesthetic Response Scale (VARS)

VARS adalah lapisan kuantifikasi dari fitur VARD.

## 17.1 Prinsip

VARS tidak digunakan untuk menyatakan:

```text
80 = objek 80% indah
```

Tetapi:

```text
80 = relative visual-neuroelectric response score
```

---

## 17.2 Output

Contoh:

```text
VISUAL AESTHETIC RESPONSE PROFILE

Stimulus              : RISHA-023
Subject               : S015

Visual Detection      : 72
Aesthetic Attention   : 61
Cognitive Evaluation  : 84
Sustained Processing  : 79
Spatial Engagement    : 67
Temporal Persistence  : 76

VARS Composite        : 74 / 100
```

---

# 18. VARS Scoring Engine

Tim IT harus membangun scoring engine yang **configurable**, bukan hard-coded.

Setiap domain memiliki:

```text
Raw Feature
    ↓
Normalization
    ↓
Domain Score
    ↓
Weight
    ↓
Composite Score
```

Rumus konseptual:

```text
VARS =
w1(V1) +
w2(V2) +
w3(V3) +
w4(V4) +
w5(V5) +
w6(V6)
```

dengan:

```text
w1 + w2 + w3 + w4 + w5 + w6 = 1
```

Bobot harus dapat disimpan per **Scoring Model Version**.

Contoh:

```text
Model        : VARS-1.0
V1 Weight    : configurable
V2 Weight    : configurable
V3 Weight    : configurable
V4 Weight    : configurable
V5 Weight    : configurable
V6 Weight    : configurable
```

---

# 19. Normalisasi

Scoring engine minimal mendukung:

- Min-Max;
- Z-score;
- percentile;
- subject-normalized;
- group-normalized;
- custom formula.

Normalisasi harus dapat dilakukan terhadap:

- satu subject;
- seluruh stimulus dalam subject;
- seluruh subject;
- kelompok eksperimen.

---

# 20. Visual Response Fingerprint

Selain total VARS, aplikasi wajib menyimpan enam domain secara terpisah.

Contoh:

```text
                Stimulus A     Stimulus B
Detection           82             55
Attention           76             62
Evaluation          91             73
Sustained           48             89
Spatial             72             81
Persistence         43             92
```

Tujuannya adalah menunjukkan bahwa dua stimulus dengan composite score mirip dapat menghasilkan **pola neuroelektrik yang berbeda**.

---

# 21. Subjective Aesthetic Rating

VARD perlu menyediakan data behavioral yang terpisah dari EEG.

Contoh pertanyaan:

> Seberapa menarik tampilan visual ini menurut Anda?

Skala default:

```text
1 = sangat tidak menarik
2 = tidak menarik
3 = agak tidak menarik
4 = netral
5 = agak menarik
6 = menarik
7 = sangat menarik
```

Skala harus configurable.

---

# 22. Hubungan Neural dan Behavioral

Database harus membedakan:

```text
VARS
=
EEG-derived response

Aesthetic Rating
=
Participant-reported response
```

Keduanya dapat dianalisis bersama:

```text
EEG Response
      +
Subjective Rating
      ↓
Neuro-Aesthetic Analysis
```

Analisis lanjutan dapat menggunakan:

- correlation;
- regression;
- classification;
- clustering;
- machine learning.

---

# 23. ROI Manager

Sistem dapat membuat Region of Interest.

Contoh:

```text
Frontal
Fp1, Fp2, F3, F4, Fz

Central
C3, C4, Cz

Parietal
P3, P4, Pz

Occipital
O1, O2, Oz
```

User dapat membuat ROI baru secara manual.

---

# 24. Spatial Engagement

Spatial Engagement dihitung dari distribusi aktivitas electrode/ROI.

Output dapat mencakup:

- dominant ROI;
- number of active channels;
- spatial spread;
- average ROI amplitude;
- topographic centroid;
- left/right asymmetry.

Contoh:

```text
Dominant ROI : Parietal
Secondary ROI: Occipital
```

---

# 25. Dynamic Brain Electrical Activity

Platform menyediakan visualisasi aktivitas listrik berdasarkan data topografi.

Mode:

### Mode 1 — Scientific
- ERP;
- topomap;
- channel value;
- electrode position.

### Mode 2 — Spatial Brain
- 3D head;
- electrode;
- interpolated electrical field.

### Mode 3 — Neural Representation
- brain outline;
- network/branch;
- electrical animation;
- intensity mapping.

Mode 3 bersifat **representational**, bukan rekonstruksi neuron individual.

---

# 26. Main Dashboard

Layout yang direkomendasikan:

```text
┌───────────────────────────────────────────────────────────────┐
│ EEG–ERP NEUROVISUALIZATION — VARD                            │
├───────────────────────┬───────────────────────────────────────┤
│                       │                                       │
│       TOPOMAP         │             ERP WAVEFORM              │
│                       │                                       │
│                       │           /\                          │
│                       │     _____/  \________                  │
│                       │             ↑                         │
│                       │           P300                        │
├───────────────────────┴───────────────────────────────────────┤
│ Timeline                                                      │
│ ▶ |────────────│──────────│─────────────│                     │
│   0           200        300           500          800 ms    │
├───────────────────────────────────────────────────────────────┤
│ VISUAL RESPONSE PROFILE                                       │
│ Detection       ████████░░                                    │
│ Attention       ███████░░░                                    │
│ Evaluation      █████████░                                    │
│ Sustained       ████████░░                                    │
│ Spatial         ███████░░░                                    │
│ Persistence     ████████░░                                    │
├───────────────────────────────────────────────────────────────┤
│ Dynamic Brain Electrical Activity                             │
│                                                               │
│                  [3D / NETWORK VIEW]                           │
└───────────────────────────────────────────────────────────────┘
```

---

# 27. Stimulus Dashboard

Saat user memilih stimulus:

```text
Subject  : S015
Stimulus : RISHA-023
ERP      : P300
```

sistem menampilkan bersamaan:

```text
Stimulus Image
      ↓
ERP Waveform
      ↓
ERP Component
      ↓
Topomap
      ↓
Dominant ROI
      ↓
VARD Features
      ↓
VARS Profile
      ↓
Dynamic Visualization
```

---

# 28. Comparison Mode

Aplikasi harus mendukung perbandingan:

- Subject A vs Subject B;
- Stimulus A vs Stimulus B;
- Condition A vs Condition B;
- Group A vs Group B;
- ERP component A vs component B.

Contoh layout:

```text
STIMULUS A                         STIMULUS B
──────────                         ──────────

[ IMAGE ]                          [ IMAGE ]

[TOPOMAP]                          [TOPOMAP]

ERP ──────────                     ERP ──────────

P300  : 4.6 µV                     P300  : 7.1 µV
LPP   : 3.8 µV                     LPP   : 6.4 µV
VARS  : 68                         VARS  : 77
```

---

# 29. Group Analysis

Pengguna dapat memilih beberapa subject.

Output:

- grand average ERP;
- group topomap;
- mean VARS;
- standard deviation;
- confidence interval;
- per-domain score;
- stimulus ranking berdasarkan metric yang dipilih.

Catatan:

Ranking harus berdasarkan parameter eksplisit, misalnya:

```text
Mean P300 amplitude
Mean LPP
VARS composite
Subjective rating
```

---

# 30. Database Model

Entitas minimal:

```text
projects
subjects
sessions
stimuli
recordings
channels
events
epochs
erp_components
erp_measurements
topomap_data
roi
roi_channels
vard_features
vars_models
vars_scores
subjective_ratings
processing_history
exports
```

---

# 31. Contoh Data VARD

```json
{
  "subject_id": "S015",
  "stimulus_id": "RISHA-023",
  "vard": {
    "visual_detection": 72,
    "aesthetic_attention": 61,
    "cognitive_evaluation": 84,
    "sustained_processing": 79,
    "spatial_engagement": 67,
    "temporal_persistence": 76
  },
  "vars_model": "VARS-1.0",
  "vars_composite": 74
}
```

---

# 32. MATLAB / EEGLAB Compatibility

Sistem harus mempertahankan interoperabilitas dengan MATLAB/EEGLAB.

Requirement:

> Original BDF files shall remain unchanged.

Sistem dapat membaca atau mengekspor:

- MAT;
- CSV;
- JSON;
- SET;
- ERP numerical values.

---

# 33. MATLAB Validation Mode

Fitur ini wajib digunakan sebelum modul dianggap valid.

Tujuan:

Membandingkan hasil aplikasi dengan hasil pipeline MATLAB.

Contoh:

| Parameter | MATLAB | Application |
|---|---:|---:|
| P3 P300 | 4.382 µV | 4.382 µV |
| P4 P300 | 4.105 µV | 4.105 µV |
| O1 LPP | 3.821 µV | 3.821 µV |
| Peak latency | 387 ms | 387 ms |

Yang dibandingkan:

- event timing;
- filter output;
- epoch;
- baseline;
- ERP waveform;
- amplitude;
- latency;
- topomap input values.

---

# 34. Processing History

Setiap proses harus tercatat.

Contoh:

```text
Raw BDF
↓
Bandpass 0.5–30 Hz
↓
Notch 50 Hz
↓
Average Reference
↓
Epoch -200–1000 ms
↓
Baseline -200–0 ms
↓
Artifact Threshold
↓
ERP Average
↓
P300 Analysis
↓
VARD
↓
VARS-1.0
```

Tujuannya untuk memastikan analisis dapat direplikasi.

---

# 35. Export

## Data

- CSV
- XLSX
- JSON
- MAT

## Gambar

- PNG
- JPG
- SVG
- PDF

## Video

- MP4
- animated topomap;
- dynamic brain activity;
- ERP synchronized animation.

Target video minimal:

```text
1920 × 1080
```

---

# 36. Performance Requirement

| Parameter | Target |
|---|---|
| EEG channel | ≥32, scalable ≥128 |
| Sampling rate | minimal support 2048 Hz |
| Subjects | unlimited secara desain |
| Stimuli | unlimited secara desain |
| ERP windows | configurable |
| Topomap refresh | target ≤100 ms |
| Interaction | near real-time |
| Processing | non-destructive |
| Export image | publication quality |
| OS awal | Windows 10/11 |

---

# 37. Non-Functional Requirement

## Usability

- antarmuka mudah digunakan peneliti;
- parameter advanced dapat disembunyikan;
- workflow berbasis project;
- setiap grafik memiliki tooltip.

## Reproducibility

Semua parameter proses disimpan.

## Data Integrity

Raw EEG tidak boleh diubah.

## Performance

Data besar tidak boleh memblokir UI.

## Maintainability

Engine analisis dipisahkan dari UI.

## Extensibility

ERP component, scoring model, dan ROI harus dapat ditambah tanpa mengubah core system.

---

# 38. Rekomendasi Arsitektur Software

```text
┌─────────────────────────┐
│        FRONTEND         │
│ Visualization / UI      │
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│    APPLICATION API      │
└────────────┬────────────┘
             │
     ┌───────┴──────────┐
     ▼                  ▼
┌───────────────┐  ┌──────────────┐
│ EEG ANALYSIS  │  │ VARD ENGINE  │
│ ENGINE        │  │ VARS ENGINE  │
└───────┬───────┘  └──────┬───────┘
        │                  │
        └────────┬─────────┘
                 ▼
        ┌─────────────────┐
        │ DATABASE / FILE │
        │ STORAGE         │
        └─────────────────┘
```

---

# 39. Rekomendasi Teknologi

Pilihan awal:

## Backend / Scientific Engine

- Python;
- MNE-Python;
- NumPy;
- SciPy;
- Pandas;
- scikit-learn untuk pengembangan model selanjutnya.

## Visualization

- Plotly;
- PyQtGraph untuk desktop;
- Three.js / WebGL untuk visualisasi 3D apabila menggunakan web frontend.

## Database

- PostgreSQL untuk metadata dan hasil;
- file storage untuk BDF/MAT;
- optional HDF5/Parquet untuk data numerik besar.

## MATLAB

MATLAB digunakan sebagai referensi/validator pada tahap awal.

---

# 40. Tahapan Pengembangan

## Phase 1 — Scientific Core / MVP

Scope:

- project;
- BDF import;
- EEG viewer;
- filter;
- event;
- epoch;
- baseline;
- ERP;
- ERP component;
- topomap;
- linked cursor.

### Acceptance Test

```text
Import BDF
→ Select Event
→ Generate ERP
→ Click 400 ms
→ ERP cursor = 400 ms
→ Channel values = 400 ms
→ Topomap = derived from same 400 ms data
```

---

## Phase 2 — VARD

Scope:

- stimulus manager;
- ROI manager;
- VARD feature extraction;
- six-domain profile;
- configurable VARS;
- subjective rating;
- comparison;
- group analysis.

---

## Phase 3 — Advanced Visualization

Scope:

- animated topomap;
- 3D head;
- dynamic electrical field;
- neural/network representation;
- video export.

---

## Phase 4 — Neuro-Aesthetic Analytics

Scope:

- neural vs subjective correlation;
- statistical comparison;
- clustering;
- predictive model;
- validation of VARS;
- research report generator.

---

# 41. Acceptance Criteria VARD

VARD dianggap memenuhi minimum requirement apabila:

- [ ] BDF berhasil dibaca;
- [ ] event dapat dideteksi;
- [ ] EEG dapat difilter;
- [ ] epoch dapat dibuat;
- [ ] baseline dapat dikoreksi;
- [ ] ERP dapat dihitung;
- [ ] ERP component dapat dikonfigurasi;
- [ ] cursor ERP terhubung dengan topomap;
- [ ] topomap menggunakan nilai EEG/ERP yang sama;
- [ ] stimulus dapat dihubungkan dengan event;
- [ ] V1–V6 berhasil dihitung;
- [ ] VARD profile ditampilkan;
- [ ] VARS model dapat dikonfigurasi;
- [ ] composite score dapat dihitung;
- [ ] subjective rating tersimpan terpisah;
- [ ] hasil dapat dibandingkan;
- [ ] processing history disimpan;
- [ ] hasil dapat diekspor;
- [ ] output utama dapat divalidasi dengan MATLAB.

---

# 42. Deliverable Tim IT

Tim pengembang minimal menyerahkan:

1. source code;
2. database schema;
3. installer/deployment package;
4. technical documentation;
5. user manual;
6. API documentation;
7. test report;
8. MATLAB validation report;
9. sample project;
10. source/project file visualisasi;
11. konfigurasi VARS;
12. deployment guide;
13. backup/restore procedure.

---

# 43. Prinsip Validasi VARS

**VARS v1.0 merupakan skala eksperimental yang harus divalidasi.**

Tahapan yang direkomendasikan:

```text
Feature Definition
      ↓
Pilot Dataset
      ↓
Normalization
      ↓
Reliability Evaluation
      ↓
Comparison with Subjective Rating
      ↓
Construct Validation
      ↓
Model Revision
      ↓
VARS 1.0
```

Dengan demikian formula dan bobot tidak boleh ditanam permanen di source code.

Semua harus disimpan sebagai **versioned scoring model**.

---

# 44. Future Development

Fitur yang dapat ditambahkan:

- ICA artifact correction;
- source localization;
- frequency-band analysis;
- alpha/beta/theta analysis;
- time-frequency analysis;
- functional connectivity;
- machine learning;
- automated ERP detection;
- automated aesthetic response classification;
- cross-subject normative model;
- cloud analysis;
- multi-laboratory dataset;
- API untuk sistem penelitian lain.

---

# 45. Definition of Done

Sistem dinyatakan berhasil apabila platform dapat melakukan alur berikut dalam satu project:

```text
IMPORT BDF
    ↓
PREPROCESS EEG
    ↓
DETECT STIMULUS
    ↓
GENERATE EPOCH
    ↓
GENERATE ERP
    ↓
SELECT ERP COMPONENT
    ↓
DISPLAY ERP + TOPOMAP SIMULTANEOUSLY
    ↓
MOVE LINKED TIMELINE
    ↓
EXTRACT VARD FEATURES
    ↓
GENERATE VARS PROFILE
    ↓
COMPARE STIMULUS / SUBJECT
    ↓
EXPORT RESULTS
```

---

## Kesimpulan

VARD dirancang sebagai bagian dari platform EEG–ERP untuk menghubungkan **analisis temporal, analisis spasial, stimulus visual, dan respons estetika** dalam satu sistem.

Arsitektur harus memastikan:

> **satu data EEG menghasilkan berbagai bentuk visualisasi dan indikator tanpa kehilangan hubungan temporal maupun nilai numeriknya.**

Tujuan akhirnya bukan hanya membuat visualisasi yang menarik, tetapi menghasilkan sebuah **research platform yang reproducible, configurable, dan dapat divalidasi secara ilmiah**.
