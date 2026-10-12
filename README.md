# Sistem Anotasi Fungsi Retoris Abstrak Artikel Ilmiah Berbahasa Indonesia

> **Penelitian:** "Hybrid Rule-Based dan IndoBERT untuk Klasifikasi Struktur dan Kelengkapan Bagian Abstrak Artikel Ilmiah Berbahasa Indonesia"
> **Pedoman:** `pedoman_v1.0_beku.md` (dibekukan 2026-10-11)

---

## Daftar Isi

1. [Prasyarat dan Instalasi](#1-prasyarat-dan-instalasi)
2. [Cara Menjalankan Label Studio](#2-cara-menjalankan-label-studio)
3. [Cara Mengisi CSV Input](#3-cara-mengisi-csv-input)
4. [Alur Kerja Lengkap](#4-alur-kerja-lengkap)
   - [Langkah 1 – Persiapan abstrak](#langkah-1--persiapan-abstrak)
   - [Langkah 2 – Segmentasi kalimat](#langkah-2--segmentasi-kalimat)
   - [Langkah 3 – Pemeriksaan dan pembekuan segmen](#langkah-3--pemeriksaan-dan-pembekuan-segmen)
   - [Langkah 4 – Buat dan impor task JSON ke Label Studio](#langkah-4--buat-dan-impor-task-json-ke-label-studio)
   - [Langkah 5 – Buat proyek terpisah untuk dua anotator](#langkah-5--buat-proyek-terpisah-untuk-dua-anotator)
   - [Langkah 6 – Ekspor dan konversi anotasi ke CSV](#langkah-6--ekspor-dan-konversi-anotasi-ke-csv)
   - [Langkah 7 – Validasi anotasi](#langkah-7--validasi-anotasi)
   - [Langkah 8 – Susun antrean adjudikasi](#langkah-8--susun-antrean-adjudikasi)
   - [Langkah 9 – Buat ground truth lengkap ⚠️ WAJIB sebelum kelengkapan](#langkah-9--buat-ground-truth-lengkap)
   - [Langkah 10 – Hitung kelengkapan abstrak](#langkah-10--hitung-kelengkapan-abstrak)
5. [Lokasi Berkas Keluaran](#5-lokasi-berkas-keluaran)
6. [Cara Menjalankan Unit Test](#6-cara-menjalankan-unit-test)
7. [Keterbatasan Fitur Label Studio](#7-keterbatasan-fitur-label-studio)
8. [Struktur Proyek](#8-struktur-proyek)

---

## 1. Prasyarat dan Instalasi

### Kebutuhan sistem
- **Python 3.9+** (dianjurkan Python 3.11)
- **Windows PowerShell**
- **Label Studio** versi terbaru (diuji dengan Label Studio ≥ 1.10)
- RAM minimal 4 GB (8 GB dianjurkan untuk korpus > 100 abstrak)

### Instalasi dependensi Python

```powershell
cd "c:\Users\ahmad\OneDrive\Documents\semester_7\Tugas Akhir\Label dataset"

# (Opsional tapi dianjurkan) Buat virtual environment
python -m venv .venv
.venv\Scripts\Activate.ps1

pip install -r requirements.txt
```

> **Catatan:** Jika ada error `ExecutionPolicy`:
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
> ```

---

## 2. Cara Menjalankan Label Studio

```powershell
pip install label-studio
label-studio start    # buka http://localhost:8080
```

**Setup antarmuka:**
1. Buat proyek baru → **Labeling Interface** → **Code**
2. Salin isi `config/label_studio_config.xml` dan tempel → **Save**

---

## 3. Cara Mengisi CSV Input

Gunakan templat `data/templates/abstrak_input_template.csv`.

### Kolom wajib (pipeline berhenti jika kosong)

| Kolom | Keterangan |
|---|---|
| `id_abstrak` | Kode unik, contoh: `A001` |
| `judul` | Judul artikel lengkap |
| `jurnal` | Nama jurnal |
| `tahun` | Tahun terbit, contoh: `2024` |
| `jenis_studi` | `kuantitatif` / `kualitatif` / `campuran` / `pengembangan-produk` / `literatur` / `konseptual` |
| `peran_data` | `data-pengembangan` / `pilot2` / `korpus-anotasi` |
| `teks_mentah` | Salin VERBATIM dari PDF/HTML |

### Aturan penting
- Pipeline berhenti (**fatal error**) jika: kolom wajib kosong, ID duplikat, atau satu artikel di lebih dari satu peran data
- Satu artikel hanya boleh di **satu** `peran_data`
- `teks_mentah`: salin verbatim, **tanpa** label seksi atau kata kunci

---

## 4. Alur Kerja Lengkap

### Langkah 1 – Persiapan abstrak

```powershell
python scripts\prepare_abstrak.py `
    --input data\raw\abstrak_input.csv `
    --output-dir data\processed
```

**Error FATAL** (tidak ada output jika ini terjadi):
- Kolom wajib kosong / enum tidak valid
- ID abstrak duplikat
- Artikel sama di lebih dari satu peran

> ⚠️ **Periksa `log_dedup.csv`** — abstrak `duplikat-dekat-ditinjau` diblokir di langkah 2 sampai review selesai.

---

### Langkah 2 – Segmentasi kalimat

```powershell
python scripts\segment_abstrak.py `
    --abstrak data\processed\abstrak.csv `
    --output-dir data\processed `
    --peran-data korpus-anotasi
```

> ⚠️ Abstrak berstatus `duplikat-dekat-ditinjau` **diblokir** dan tidak disegmentasi. Selesaikan review manual di `log_dedup.csv`, perbarui `status_dedup` di `abstrak.csv`, lalu jalankan ulang.

---

### Langkah 3 – Pemeriksaan dan pembekuan segmen

**WAJIB dilakukan sebelum anotasi** oleh pemeriksa (bukan anotator).

1. Buka setiap `data/processed/review_segmentasi_{id}.csv`
2. Periksa kolom `perlu_review` dan `catatan_b5`
3. Isi `disetujui` dengan `Ya` atau `Tidak`
4. Susun `segmen.csv` dengan kolom `status_beku = "disetujui"` untuk segmen yang sudah disetujui

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

---

### Langkah 5 – Buat proyek terpisah untuk dua anotator

> ⚠️ Hasil anotator 1 **TIDAK BOLEH** dilihat anotator 2 sebelum adjudikasi.

Buat **dua proyek terpisah** di Label Studio, masing-masing hanya diakses oleh satu anotator.

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

> ⚠️ Jika UP=Tidak tetapi label tambahan terisi → **error eksplisit**, task tidak dikonversi. Perbaiki di Label Studio dan ekspor ulang. Hasil audit disimpan di `audit_konversi_anotasi_*.csv`.

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

**Adjudikator mengisi kolom:** `label_akhir`, `label_alt_sisa`, `status_akhir`, `konteks_dipakai`, `alasan`, `adjudikator_id`, `waktu_selesai`

---

### Langkah 9 – Buat ground truth lengkap

> ⚠️ **WAJIB sebelum menghitung kelengkapan.** Langkah ini menggabungkan SELURUH segmen (konsensus + adjudikasi) menjadi satu dataset.

```powershell
python scripts\build_ground_truth.py `
    --segmen data\processed\segmen.csv `
    --anotasi-1 data\processed\anotasi_an1.csv `
    --anotasi-2 data\processed\anotasi_an2.csv `
    --adjudikasi data\processed\adjudikasi.csv `
    --output-dir data\processed
```

**Yang dilakukan:**
- Segmen konsensus (tanpa flag/TT, kedua anotator sepakat) → `status_akhir = final, sumber = konsensus`
- Segmen yang perlu adjudikasi + keputusan sudah ada → `status_akhir = final/batas-sisa/dikecualikan`
- Segmen yang perlu adjudikasi tapi **belum ada keputusan** → `status_akhir = belum-selesai` (error di log)

> ⚠️ Jangan jalankan Langkah 10 jika masih ada `belum-selesai` di `ground_truth.csv`.

---

### Langkah 10 – Hitung kelengkapan abstrak

```powershell
python scripts\calculate_completeness.py `
    --ground-truth data\processed\ground_truth.csv `
    --abstrak data\processed\abstrak.csv `
    --output-dir data\processed
```

**Status kelengkapan:**
- `LENGKAP` — v = (1,1,1,1,1), kepastian pasti
- `TIDAK LENGKAP` — ada komponen hilang, kepastian pasti
- `TAK PASTI` — v-min ≠ v-maks (ada segmen batas-sisa dengan alternatif berbeda)
- `BLOKIR-TT` — ada label TT yang belum diselesaikan; tidak masuk metrik utama

---

## 5. Lokasi Berkas Keluaran

```
data/
├── raw/                          # Taruh CSV input di sini
├── templates/
│   └── abstrak_input_template.csv
├── processed/
│   ├── abstrak.csv               # Metadata + teks kerja + status dedup
│   ├── log_normalisasi.csv
│   ├── log_dedup.csv             # Duplikat dekat perlu ditinjau di sini
│   ├── kandidat_segmen.csv       # Kandidat segmen (sebelum dibekukan)
│   ├── review_segmentasi_*.csv   # Review per abstrak
│   ├── segmen.csv                # Segmen dibekukan (dibuat manual)
│   ├── anotasi_an1.csv
│   ├── anotasi_an2.csv
│   ├── audit_konversi_anotasi_an1.csv  # Audit field konversi (UP, dll.)
│   ├── audit_konversi_anotasi_an2.csv
│   ├── adjudikasi.csv            # Antrean + keputusan adjudikasi
│   ├── ground_truth.csv          # ← DATASET FINAL (semua segmen)
│   ├── laporan_ground_truth.txt
│   ├── kelengkapan_abstrak.csv
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

**67 test, 11 kelompok:**

| Kelompok | Test | Cakupan |
|---|---|---|
| `TestNormalisasi` | 8 | Ligatur, baris, spasi, SHA-256, log |
| `TestDeduplikasi` | 8 | DOI, hash, Jaccard, near-dup tidak dihapus |
| `TestValidasiPrepareFatal` | 4 | Fatal errors menghentikan pipeline, tidak ada output |
| `TestSegmentasi` | 7 | Kalimat, singkatan, desimal, tanda tanya, B5, urutan |
| `TestSegmentasiURLDOI` | 3 | URL/DOI tidak menelan titik penutup kalimat |
| `TestKonversiLS` | 7 | Label tunggal/ganda, UP, label alt valid |
| `TestKonversiLSError` | 2 | UP=Tidak + label terisi → error eksplisit |
| `TestGroundTruth` | 8 | Konsensus, adj, flag, TT, dikecualikan, segmen luar antrean |
| `TestKelengkapan` | 11 | LENGKAP/TIDAK LENGKAP, K2, K3, K5, v-min, v-maks |
| `TestKelengkapanTT` | 2 | BLOKIR-TT, pending |
| `TestIntegrasi` | 3 | End-to-end: prepare, GT+kelengkapan, near-dup blokir |

---

## 7. Keterbatasan Fitur Label Studio

| Keterbatasan | Mitigasi |
|---|---|
| Conditional display (tampilkan label_2 hanya jika UP=Ya) | Field label_2–6 selalu tampil; validasi kondisional di `convert_labelstudio_export.py` dan `validate_annotations.py` |
| UP=Tidak tapi label_2 terisi → sebelumnya dibuang diam-diam | Sekarang **error eksplisit**; task tidak dikonversi |
| `waktu_mulai` tidak tersedia dari ekspor standar | Kolom dikosongkan; audit di `audit_konversi_*.csv` |
| Validasi lintas-field otomatis | Dilakukan `validate_annotations.py` pasca-ekspor |
| Anotator bisa melihat hasil satu sama lain dalam satu proyek | Buat **dua proyek terpisah** (lihat Langkah 5) |

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
│   ├── prepare_abstrak.py             # Normalisasi, hash, dedup (fatal errors)
│   ├── segment_abstrak.py             # Segmentasi + blokir near-dup
│   ├── prepare_labelstudio_tasks.py   # Task JSON per anotator
│   ├── convert_labelstudio_export.py  # Konversi ekspor LS → anotasi.csv
│   ├── validate_annotations.py        # 15 aturan validasi
│   ├── build_adjudication_queue.py    # Antrean adjudikasi
│   ├── build_ground_truth.py          # ← BARU: Ground truth lengkap
│   └── calculate_completeness.py      # Kelengkapan dari ground_truth.csv
├── tests/
│   └── test_pipeline.py               # 67 test (produksi + integrasi)
├── pedoman_v1.0_beku.md               # Pedoman Anotasi v1.0 (JANGAN DIUBAH)
├── requirements.txt
└── README.md
```

---

## Referensi Cepat (Copy-Paste PowerShell)

```powershell
# 0. Setup
cd "c:\Users\ahmad\OneDrive\Documents\semester_7\Tugas Akhir\Label dataset"
python -m venv .venv; .venv\Scripts\Activate.ps1
pip install -r requirements.txt

# 1. Persiapan abstrak (fatal jika metadata tidak valid)
python scripts\prepare_abstrak.py --input data\raw\abstrak_input.csv --output-dir data\processed

# 2. Segmentasi (near-dup diblokir)
python scripts\segment_abstrak.py --abstrak data\processed\abstrak.csv --output-dir data\processed

# 3. [MANUAL] Review review_segmentasi_*.csv → susun segmen.csv

# 4. Task JSON
python scripts\prepare_labelstudio_tasks.py --segmen data\processed\segmen.csv --abstrak data\processed\abstrak.csv --output-dir data\labelstudio --anotator-ids an1,an2 --peran-data korpus-anotasi --seed 42

# 5. [MANUAL] Impor ke Label Studio (dua proyek terpisah)

# 6. [MANUAL] Ekspor JSON dari Label Studio → data\exports\

# 7. Konversi (error eksplisit jika UP=Tidak + label terisi)
python scripts\convert_labelstudio_export.py --input data\exports\export_an1.json --output data\processed\anotasi_an1.csv --anotator-id an1
python scripts\convert_labelstudio_export.py --input data\exports\export_an2.json --output data\processed\anotasi_an2.csv --anotator-id an2

# 8. Validasi
python scripts\validate_annotations.py --anotasi data\processed\anotasi_an1.csv,data\processed\anotasi_an2.csv --segmen data\processed\segmen.csv --abstrak data\processed\abstrak.csv --output-dir data\processed

# 9. Adjudikasi
python scripts\build_adjudication_queue.py --anotasi-1 data\processed\anotasi_an1.csv --anotasi-2 data\processed\anotasi_an2.csv --output data\processed\adjudikasi.csv

# 10. [MANUAL] Isi adjudikasi.csv oleh adjudikator

# 11. Ground truth lengkap (WAJIB sebelum kelengkapan)
python scripts\build_ground_truth.py --segmen data\processed\segmen.csv --anotasi-1 data\processed\anotasi_an1.csv --anotasi-2 data\processed\anotasi_an2.csv --adjudikasi data\processed\adjudikasi.csv --output-dir data\processed

# 12. Kelengkapan (dari ground_truth.csv, bukan adjudikasi.csv)
python scripts\calculate_completeness.py --ground-truth data\processed\ground_truth.csv --abstrak data\processed\abstrak.csv --output-dir data\processed

# 13. Unit test
python tests\test_pipeline.py
```
