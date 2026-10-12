# Sistem Anotasi Fungsi Retoris Abstrak Artikel Ilmiah Berbahasa Indonesia

> **Penelitian:** "Hybrid Rule-Based dan IndoBERT untuk Klasifikasi Struktur dan Kelengkapan Bagian Abstrak Artikel Ilmiah Berbahasa Indonesia"
> **Pedoman:** `pedoman_v1.0_beku.md` (dibekukan 2026-10-11) — **TIDAK BOLEH DIUBAH**

---

## Daftar Isi

1. [Prasyarat dan Instalasi](#1-prasyarat-dan-instalasi)
2. [Cara Menjalankan Label Studio](#2-cara-menjalankan-label-studio)
3. [Cara Mengisi CSV Input](#3-cara-mengisi-csv-input)
4. [Alur Kerja Lengkap](#4-alur-kerja-lengkap)
5. [Lokasi Berkas Keluaran](#5-lokasi-berkas-keluaran)
6. [Cara Menjalankan Unit Test](#6-cara-menjalankan-unit-test)
7. [Keterbatasan Fitur Label Studio](#7-keterbatasan-fitur-label-studio)
8. [Struktur Proyek](#8-struktur-proyek)
9. [Langkah Pilot 2](#9-langkah-pilot-2)

---

## 1. Prasyarat dan Instalasi

- **Python 3.9+** (dianjurkan 3.11)
- **Windows PowerShell**
- **Label Studio** ≥ 1.10 (`pip install label-studio`)
- RAM minimal 4 GB

```powershell
cd "c:\Users\ahmad\OneDrive\Documents\semester_7\Tugas Akhir\Label dataset"
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

> Jika ada error `ExecutionPolicy`:
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
> ```

---

## 2. Cara Menjalankan Label Studio

```powershell
pip install label-studio
label-studio start    # buka http://localhost:8080
```

1. Buat proyek baru → **Labeling Interface** → **Code**
2. Salin isi `config/label_studio_config.xml` → **Save**

---

## 3. Cara Mengisi CSV Input

Gunakan templat `data/templates/abstrak_input_template.csv`.

### Kolom wajib (pipeline berhenti FATAL jika kosong/tidak valid)

| Kolom | Nilai yang valid |
|---|---|
| `id_abstrak` | Kode unik, contoh `A001` |
| `judul` | Judul artikel lengkap |
| `jurnal` | Nama jurnal |
| `tahun` | Tahun terbit (angka) |
| `jenis_studi` | `kuantitatif` / `kualitatif` / `campuran` / `pengembangan-produk` / `literatur` / `konseptual` |
| `peran_data` | `data-pengembangan` / `pilot2` / `korpus-anotasi` |
| `teks_mentah` | Salin **verbatim** dari PDF/HTML |

**Aturan fatal error** (pipeline berhenti, tidak ada output):
- Kolom wajib kosong atau `jenis_studi`/`peran_data` tidak dalam daftar enum yang valid
- ID abstrak duplikat
- Artikel yang sama digunakan di lebih dari satu `peran_data`

---

## 4. Alur Kerja Lengkap

### Langkah 1 – Persiapan abstrak

```powershell
python scripts\prepare_abstrak.py `
    --input data\raw\abstrak_input.csv `
    --output-dir data\processed
```

**Output:** `abstrak.csv`, `log_normalisasi.csv`, `log_dedup.csv`

> ⚠️ Periksa `log_dedup.csv`. Abstrak `duplikat-dekat-ditinjau` diblokir di Langkah 2 sampai review selesai. Perbarui `status_dedup` di `abstrak.csv` ke `unik` atau `duplikat-dibuang` setelah review manual.

---

### Langkah 2 – Segmentasi kalimat

```powershell
python scripts\segment_abstrak.py `
    --abstrak data\processed\abstrak.csv `
    --output-dir data\processed `
    --peran-data korpus-anotasi
```

**Output:** `kandidat_segmen.csv`, `review_segmentasi_{id}.csv` (satu per abstrak)

> ⚠️ Abstrak berstatus `duplikat-dekat-ditinjau` **diblokir** dan tidak disegmentasi. Selesaikan review → perbarui `status_dedup` → jalankan ulang.

---

### Langkah 3 – Pemeriksaan dan pembekuan segmen (MANUAL)

**Dikerjakan oleh pemeriksa segmentasi (bukan anotator).**

1. Buka setiap `data/processed/review_segmentasi_{id}.csv`
2. Periksa `perlu_review` dan `catatan_b5`
3. Isi kolom `disetujui` dengan `Ya` atau `Tidak`
4. Buat `segmen.csv` dengan kolom `status_beku = "disetujui"` untuk segmen yang disetujui

Kolom wajib `segmen.csv` (Pedoman 8.3):
`id_abstrak, id_segmen, urutan, teks_segmen, asal_segmentasi, catatan_segmentasi, status_beku`

---

### Langkah 4 – Buat dan impor task JSON ke Label Studio

```powershell
python scripts\prepare_labelstudio_tasks.py `
    --segmen data\processed\segmen.csv `
    --abstrak data\processed\abstrak.csv `
    --output-dir data\labelstudio `
    --anotator-ids an1,an2 `
    --peran-data korpus-anotasi `
    --seed 42
```

**Output:** `data/labelstudio/tasks_an1_*.json`, `tasks_an2_*.json`, `seed_info.json`

---

### Langkah 5 – Anotasi di Label Studio (MANUAL, dua proyek terpisah)

> ⚠️ **Wajib dua proyek terpisah.** Hasil anotator 1 TIDAK BOLEH dilihat anotator 2 sebelum adjudikasi (Pedoman 9.3).

Impor `tasks_an1_*.json` ke Proyek 1 (hanya untuk an1) dan `tasks_an2_*.json` ke Proyek 2 (hanya untuk an2).

---

### Langkah 6 – Ekspor dan konversi anotasi ke CSV

**Di Label Studio:** Export → JSON → simpan ke `data/exports/`

```powershell
python scripts\convert_labelstudio_export.py `
    --input data\exports\export_an1.json `
    --output data\processed\anotasi_an1.csv `
    --anotator-id an1

python scripts\convert_labelstudio_export.py `
    --input data\exports\export_an2.json `
    --output data\processed\anotasi_an2.csv `
    --anotator-id an2
```

**Output:** `anotasi_an1.csv`, `anotasi_an2.csv`, `audit_konversi_anotasi_an1.csv`, `audit_konversi_anotasi_an2.csv`

> ⚠️ Error eksplisit jika UP=Tidak tetapi label_2..6 terisi. Task tidak dikonversi. Perbaiki di Label Studio → ekspor ulang. Periksa `audit_konversi_*.csv` untuk detail.

---

### Langkah 7 – Validasi anotasi

```powershell
python scripts\validate_annotations.py `
    --anotasi data\processed\anotasi_an1.csv,data\processed\anotasi_an2.csv `
    --segmen data\processed\segmen.csv `
    --abstrak data\processed\abstrak.csv `
    --output-dir data\processed
```

---

### Langkah 8 – Susun antrean adjudikasi

```powershell
python scripts\build_adjudication_queue.py `
    --anotasi-1 data\processed\anotasi_an1.csv `
    --anotasi-2 data\processed\anotasi_an2.csv `
    --output data\processed\adjudikasi.csv
```

**Segmen masuk antrean jika** (Pedoman 7.3):
- Label kedua anotator berbeda, ATAU
- Salah satu memberi flag (B1–B6), ATAU
- Salah satu memberi label TT

**Adjudikator mengisi kolom:** `label_akhir`, `label_alt_sisa`, `status_akhir` (`final`/`batas-sisa`/`dikecualikan`), `konteks_dipakai`, `alasan`, `adjudikator_id`, `waktu_selesai`

---

### Langkah 9 – Buat ground truth lengkap

> ⚠️ **WAJIB sebelum Langkah 10.** Langkah ini menggabungkan SELURUH segmen (konsensus + adjudikasi) ke satu dataset.

```powershell
python scripts\build_ground_truth.py `
    --segmen data\processed\segmen.csv `
    --anotasi-1 data\processed\anotasi_an1.csv `
    --anotasi-2 data\processed\anotasi_an2.csv `
    --adjudikasi data\processed\adjudikasi.csv `
    --output-dir data\processed
```

**Output:** `ground_truth.csv`, `laporan_ground_truth.txt`

**Aturan penggabungan:**

| Kondisi | Status akhir | Sumber keputusan |
|---|---|---|
| Kedua anotator sepakat, tidak ada flag/TT | `final` | `konsensus-dua-anotator` |
| Perlu adjudikasi + keputusan sudah ada | `final`/`batas-sisa`/`dikecualikan` | `adjudikasi` |
| Perlu adjudikasi + belum ada keputusan | `belum-selesai` | `-` |
| Segmen belum dianotasi an1 | `belum-selesai` | `-` |

> ⚠️ Mode satu anotator **TIDAK** menghasilkan konsensus dua anotator. Gunakan `--anotasi-2` untuk Pilot 2 dan korpus anotasi. Jika hanya ada satu anotator (misal: data pengembangan internal), tambahkan flag `--single-annotator-no-adjudication` — hanya untuk data-pengembangan, BUKAN untuk korpus anotasi sesungguhnya.

> ⚠️ Jangan jalankan Langkah 10 jika `laporan_ground_truth.txt` menunjukkan `belum-selesai > 0`.

---

### Langkah 10 – Hitung kelengkapan abstrak

```powershell
python scripts\calculate_completeness.py `
    --ground-truth data\processed\ground_truth.csv `
    --abstrak data\processed\abstrak.csv `
    --output-dir data\processed
```

**Output:** `kelengkapan_abstrak.csv`, `laporan_kelengkapan_error.csv`, `ringkasan_kelengkapan.txt`

**Status kelengkapan** (Pedoman Bagian 6):

| Status | Arti | Masuk metrik utama? |
|---|---|---|
| `LENGKAP` | v=(1,1,1,1,1), kepastian pasti (K4) | ✅ Ya |
| `TIDAK LENGKAP` | Ada komponen=0, kepastian pasti | ✅ Ya |
| `TAK PASTI` | v-min ≠ v-maks; ada segmen batas-sisa/dikecualikan dengan alt berbeda (K5) | ❌ Tidak (analisis sensitivitas) |
| `BLOKIR-TT` | label_akhir masih TT; adjudikasi wajib (K3) | ❌ Tidak |
| `BLOKIR-BELUMSELESAI` | Ada segmen belum-selesai di GT | ❌ Tidak |

**Implementasi K5** (Pedoman 6.3):
- Segmen **final**: satu pembacaan = {label_akhir}
- Segmen **batas-sisa**: [{label_akhir}] + [{tiap label_alt}]
- Segmen **dikecualikan**: [∅] + [{tiap label kandidat dari label_alt}]
- v-min[k] = 1 jika ada segmen yang memuat k di SETIAP pembacaannya
- v-maks[k] = 1 jika ada segmen yang memuat k di MINIMAL satu pembacaannya
- Abstrak TAK PASTI, BLOKIR-TT, BLOKIR-BELUMSELESAI tidak masuk `kelengkapan_abstrak.csv`; masuk `laporan_kelengkapan_error.csv`

---

## 5. Lokasi Berkas Keluaran

```
data/
├── raw/                              # Taruh CSV input di sini
├── templates/
│   └── abstrak_input_template.csv
├── processed/
│   ├── abstrak.csv                   # Metadata + teks kerja + status dedup
│   ├── log_normalisasi.csv
│   ├── log_dedup.csv                 # Near-dup → review manual di sini
│   ├── kandidat_segmen.csv           # Kandidat segmen (sebelum dibekukan)
│   ├── review_segmentasi_*.csv       # Review per abstrak (satu file per abstrak)
│   ├── segmen.csv                    # Segmen dibekukan (dibuat/disetujui manual)
│   ├── anotasi_an1.csv
│   ├── anotasi_an2.csv
│   ├── audit_konversi_anotasi_an1.csv
│   ├── audit_konversi_anotasi_an2.csv
│   ├── adjudikasi.csv                # Antrean + keputusan adjudikasi
│   ├── ground_truth.csv              # ← DATASET FINAL (semua segmen)
│   ├── laporan_ground_truth.txt
│   ├── kelengkapan_abstrak.csv       # Abstrak yang dapat dihitung
│   ├── laporan_kelengkapan_error.csv # Abstrak diblokir (BLOKIR-TT, dll.)
│   └── ringkasan_kelengkapan.txt
├── labelstudio/
│   ├── tasks_an1_*.json
│   ├── tasks_an2_*.json
│   └── seed_info.json
└── exports/
    ├── export_an1.json
    └── export_an2.json
```

---

## 6. Cara Menjalankan Unit Test

```powershell
cd "c:\Users\ahmad\OneDrive\Documents\semester_7\Tugas Akhir\Label dataset"
python tests\test_pipeline.py

# Atau dengan pytest:
python -m pytest tests\test_pipeline.py -v
```

**Hasil terakhir: 80 test, 80 lulus, 0 gagal, 0 dilewati.**

| Kelompok | Jumlah | Cakupan |
|---|---|---|
| `TestNormalisasi` | 7 | Ligatur, baris, spasi, SHA-256, log |
| `TestDeduplikasi` | 7 | DOI, Jaccard, near-dup tidak dihapus |
| `TestValidasiPrepareFatal` | 4 | Fatal error menghentikan pipeline, tidak ada output |
| `TestSegmentasi` | 7 | Kalimat, singkatan, desimal, tanda tanya, B5, urutan |
| `TestSegmentasiURLDOI` | 3 | URL/DOI tidak menelan titik penutup kalimat |
| `TestKonversiLS` | 7 | Label tunggal/ganda, UP, label_alt valid |
| `TestKonversiLSError` | 2 | UP=Tidak + label terisi → error eksplisit |
| `TestGroundTruth` | 8 | Konsensus dua anotator, adj, flag, TT, segmen luar antrean |
| `TestGroundTruthSatuAnotator` | 3 | Satu anotator tidak diklaim konsensus |
| `TestGroundTruthBelumDianotasi` | 2 | ann1=None atau ann2=None → belum-selesai |
| `TestKelengkapan` | 8 | v utama, K2, K3, K4, segmen konsensus luar adj |
| `TestKelengkapanK5` | 11 | K5 per-segmen dan per-abstrak: final/batas-sisa/dikecualikan |
| `TestKelengkapanBlokir` | 4 | BLOKIR-TT dan BLOKIR-BELUMSELESAI (hard stop) |
| `TestSegmentasiNearDup` | 2 | Near-dup memblokir segmentasi; abstrak unik disegmentasi |
| `TestIntegrasi` | 5 | End-to-end: prepare, GT+kelengkapan, BLOKIR-TT, CLI args |

---

## 7. Keterbatasan Fitur Label Studio

| Keterbatasan | Mitigasi |
|---|---|
| Conditional display tidak tersedia (label_2 selalu tampil meski UP=Tidak) | Validasi kondisional di `convert_labelstudio_export.py`; UP=Tidak + label_2 terisi → error eksplisit |
| `waktu_mulai` tidak tersedia dari ekspor standar | Kolom dikosongkan; audit di `audit_konversi_*.csv` |
| Validasi lintas-field otomatis | `validate_annotations.py` pasca-ekspor |
| Anotator bisa melihat hasil masing-masing dalam satu proyek | Buat **dua proyek terpisah** (Langkah 5) |

---

## 8. Struktur Proyek

```
Label dataset/
├── config/
│   └── label_studio_config.xml
├── data/
│   ├── templates/abstrak_input_template.csv
│   ├── raw/
│   ├── processed/
│   ├── labelstudio/
│   └── exports/
├── scripts/
│   ├── prepare_abstrak.py               # Normalisasi, hash, dedup (fatal errors)
│   ├── segment_abstrak.py               # Segmentasi + blokir near-dup
│   ├── prepare_labelstudio_tasks.py     # Task JSON per anotator
│   ├── convert_labelstudio_export.py    # Konversi ekspor LS → anotasi.csv
│   ├── validate_annotations.py          # Validasi 15 aturan
│   ├── build_adjudication_queue.py      # Antrean adjudikasi
│   ├── build_ground_truth.py            # Ground truth lengkap (konsensus + adj)
│   └── calculate_completeness.py        # Kelengkapan dari ground_truth.csv (K1–K8)
├── tests/
│   └── test_pipeline.py                 # 80 test (15 kelompok, semua fungsi produksi)
├── pedoman_v1.0_beku.md                 # Pedoman Anotasi v1.0 (JANGAN DIUBAH)
├── requirements.txt
└── README.md
```

---

## 9. Langkah Pilot 2

Pilot 2 adalah uji reliabilitas antaranotator pertama (Pedoman Bagian 9).

**Prasyarat:**
- [ ] Empat abstrak data pengembangan sudah diproses
- [ ] `segmen.csv` untuk 10 abstrak Pilot 2 sudah dibekukan
- [ ] Dua anotator independen sudah dilatih (satu sesi: baca pedoman, labeli 4 abstrak pengembangan, diskusi kunci)
- [ ] `pedoman_v1.0_beku.md` sudah di-hash sebelum anotasi dimulai

**Urutan langkah Pilot 2:**

```powershell
# 1. Pastikan 10 abstrak Pilot 2 terdaftar dengan peran_data = "pilot2"
python scripts\prepare_abstrak.py `
    --input data\raw\abstrak_pilot2.csv `
    --output-dir data\processed

# 2. Segmentasi (hanya peran_data=pilot2)
python scripts\segment_abstrak.py `
    --abstrak data\processed\abstrak.csv `
    --output-dir data\processed `
    --peran-data pilot2

# 3. [MANUAL] Pemeriksa segmentasi (bukan anotator) memeriksa review_segmentasi_*.csv
#    → buat segmen.csv dengan status_beku=disetujui

# 4. Buat task JSON (urutan diacak per anotator, benih dicatat)
python scripts\prepare_labelstudio_tasks.py `
    --segmen data\processed\segmen.csv `
    --abstrak data\processed\abstrak.csv `
    --output-dir data\labelstudio `
    --anotator-ids an1,an2 `
    --peran-data pilot2 `
    --seed 42

# 5. [MANUAL] Impor ke dua proyek Label Studio terpisah

# 6. [MANUAL] Anotasi independen oleh dua anotator

# 7. Konversi ekspor
python scripts\convert_labelstudio_export.py `
    --input data\exports\export_an1.json `
    --output data\processed\anotasi_an1.csv `
    --anotator-id an1

python scripts\convert_labelstudio_export.py `
    --input data\exports\export_an2.json `
    --output data\processed\anotasi_an2.csv `
    --anotator-id an2

# 8. Validasi
python scripts\validate_annotations.py `
    --anotasi data\processed\anotasi_an1.csv,data\processed\anotasi_an2.csv `
    --segmen data\processed\segmen.csv `
    --abstrak data\processed\abstrak.csv `
    --output-dir data\processed

# 9. Antrean adjudikasi
python scripts\build_adjudication_queue.py `
    --anotasi-1 data\processed\anotasi_an1.csv `
    --anotasi-2 data\processed\anotasi_an2.csv `
    --output data\processed\adjudikasi.csv

# 10. [MANUAL] Adjudikator (orang ketiga) mengisi adjudikasi.csv

# 11. Ground truth lengkap (WAJIB --anotasi-2 untuk Pilot 2)
python scripts\build_ground_truth.py `
    --segmen data\processed\segmen.csv `
    --anotasi-1 data\processed\anotasi_an1.csv `
    --anotasi-2 data\processed\anotasi_an2.csv `
    --adjudikasi data\processed\adjudikasi.csv `
    --output-dir data\processed

# 12. Kelengkapan (dari ground_truth.csv, bukan adjudikasi.csv)
python scripts\calculate_completeness.py `
    --ground-truth data\processed\ground_truth.csv `
    --abstrak data\processed\abstrak.csv `
    --output-dir data\processed

# 13. Hitung ukuran kesepakatan (M1–M5, Pedoman 9.4)
#     → Dilakukan terpisah dari pipeline ini
```

**Setelah Pilot 2:**
- Hitung M1 (kappa Cohen), M2–M5
- Bandingkan dengan ambang di Pedoman 9.5
- Jika diterima: lanjut ke korpus anotasi penuh
- Jika tidak diterima: tinjau aturan yang menyebabkan ketidaksepakatan

> ⚠️ Abstrak Pilot 2 **tidak boleh** digunakan kembali untuk pelatihan anotator atau menyusun aturan baru (Pedoman 9.7.2).

---

## Referensi Cepat (Copy-Paste PowerShell)

```powershell
# Setup
cd "c:\Users\ahmad\OneDrive\Documents\semester_7\Tugas Akhir\Label dataset"
python -m venv .venv; .venv\Scripts\Activate.ps1
pip install -r requirements.txt

# 1. Persiapan (fatal jika metadata tidak valid)
python scripts\prepare_abstrak.py --input data\raw\abstrak_input.csv --output-dir data\processed

# 2. Segmentasi (near-dup diblokir)
python scripts\segment_abstrak.py --abstrak data\processed\abstrak.csv --output-dir data\processed

# [MANUAL] Review segmentasi → buat segmen.csv

# 3. Task JSON
python scripts\prepare_labelstudio_tasks.py --segmen data\processed\segmen.csv --abstrak data\processed\abstrak.csv --output-dir data\labelstudio --anotator-ids an1,an2 --peran-data korpus-anotasi --seed 42

# [MANUAL] Impor ke dua proyek Label Studio terpisah → anotasi

# 4. Konversi (error eksplisit jika UP=Tidak + label terisi)
python scripts\convert_labelstudio_export.py --input data\exports\export_an1.json --output data\processed\anotasi_an1.csv --anotator-id an1
python scripts\convert_labelstudio_export.py --input data\exports\export_an2.json --output data\processed\anotasi_an2.csv --anotator-id an2

# 5. Validasi
python scripts\validate_annotations.py --anotasi data\processed\anotasi_an1.csv,data\processed\anotasi_an2.csv --segmen data\processed\segmen.csv --abstrak data\processed\abstrak.csv --output-dir data\processed

# 6. Adjudikasi
python scripts\build_adjudication_queue.py --anotasi-1 data\processed\anotasi_an1.csv --anotasi-2 data\processed\anotasi_an2.csv --output data\processed\adjudikasi.csv

# [MANUAL] Adjudikator mengisi adjudikasi.csv

# 7. Ground truth lengkap (--anotasi-2 WAJIB untuk Pilot 2 dan korpus)
python scripts\build_ground_truth.py --segmen data\processed\segmen.csv --anotasi-1 data\processed\anotasi_an1.csv --anotasi-2 data\processed\anotasi_an2.csv --adjudikasi data\processed\adjudikasi.csv --output-dir data\processed

# 8. Kelengkapan (SELALU dari --ground-truth, bukan dari adjudikasi.csv)
python scripts\calculate_completeness.py --ground-truth data\processed\ground_truth.csv --abstrak data\processed\abstrak.csv --output-dir data\processed

# 9. Test
python tests\test_pipeline.py
```
