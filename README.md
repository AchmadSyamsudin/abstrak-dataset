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
   - [Langkah 9 – Hitung kelengkapan abstrak](#langkah-9--hitung-kelengkapan-abstrak)
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
# Buka PowerShell di direktori proyek
cd "c:\Users\ahmad\OneDrive\Documents\semester_7\Tugas Akhir\Label dataset"

# (Opsional tapi dianjurkan) Buat virtual environment
python -m venv .venv
.venv\Scripts\Activate.ps1

# Install dependensi
pip install -r requirements.txt
```

> **Catatan:** Jika ada error `ExecutionPolicy`, jalankan dulu:
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
> ```

---

## 2. Cara Menjalankan Label Studio

### Instalasi Label Studio

```powershell
pip install label-studio
```

### Menjalankan Label Studio secara lokal

```powershell
# Aktifkan environment jika belum
.venv\Scripts\Activate.ps1

# Jalankan Label Studio (akan membuka browser otomatis di http://localhost:8080)
label-studio start
```

### Konfigurasi awal Label Studio
1. Buka browser di `http://localhost:8080`
2. Daftar atau login
3. Buat proyek baru (lihat Langkah 5 untuk detail dua proyek per anotator)
4. Di pengaturan proyek, pilih tab **Labeling Interface** → **Code**
5. Salin seluruh isi `config/label_studio_config.xml` dan tempel
6. Klik **Save**

---

## 3. Cara Mengisi CSV Input

Gunakan templat di `data/templates/abstrak_input_template.csv` sebagai panduan.
Buka file dengan **Microsoft Excel** atau editor teks.

### Kolom wajib (tidak boleh kosong)

| Kolom | Keterangan |
|---|---|
| `id_abstrak` | Kode unik, contoh: `A001`, `A002` |
| `judul` | Judul artikel lengkap |
| `jurnal` | Nama jurnal |
| `tahun` | Tahun terbit, contoh: `2024` |
| `jenis_studi` | Salah satu dari: `kuantitatif`, `kualitatif`, `campuran`, `pengembangan-produk`, `literatur`, `konseptual` |
| `peran_data` | Salah satu dari: `data-pengembangan`, `pilot2`, `korpus-anotasi` |
| `teks_mentah` | Salin VERBATIM dari PDF/HTML, **tidak boleh diubah setelah diisi** |

### Kolom opsional

`volume_nomor`, `doi`, `url`, `jenis_sumber`, `versi_dokumen`, `tanggal_akses`, `lisensi`

### Aturan penting
- `jenis_sumber`: `pdf_terbit` atau `halaman_artikel`
- `tanggal_akses`: format `YYYY-MM-DD`
- Kolom yang belum diketahui dikosongkan (dua koma berurutan dalam CSV)
- Satu artikel hanya boleh muncul di **satu** `peran_data`
- `teks_mentah`: salin dari karakter pertama kalimat pertama sampai karakter terakhir kalimat terakhir; **tanpa** label seksi, judul, atau kata kunci

---

## 4. Alur Kerja Lengkap

### Langkah 1 – Persiapan abstrak

```powershell
# Normalisasi, hash SHA-256, deduplikasi
python scripts\prepare_abstrak.py `
    --input data\raw\abstrak_input.csv `
    --output-dir data\processed

# Output:
#   data\processed\abstrak.csv          (metadata + teks mentah + teks kerja)
#   data\processed\log_normalisasi.csv  (setiap perubahan normalisasi)
#   data\processed\log_dedup.csv        (entri yang dibuang atau perlu ditinjau)
```

> ⚠️ **Periksa log_dedup.csv** sebelum melanjutkan. Duplikat dekat (Jaccard ≥ 0,90) ditandai `duplikat-dekat-ditinjau` dan **wajib diperiksa manual** sebelum dilanjutkan.

---

### Langkah 2 – Segmentasi kalimat

```powershell
# Segmentasi berbasis aturan (menghasilkan kandidat)
python scripts\segment_abstrak.py `
    --abstrak data\processed\abstrak.csv `
    --output-dir data\processed `
    --peran-data korpus-anotasi

# Output:
#   data\processed\kandidat_segmen.csv              (semua kandidat)
#   data\processed\review_segmentasi_{id}.csv       (per abstrak, untuk review)
```

> ℹ️ Tanpa argumen `--peran-data`, semua abstrak di semua peran akan diproses.

---

### Langkah 3 – Pemeriksaan dan pembekuan segmen

**WAJIB dilakukan sebelum anotasi dimulai** oleh pemeriksa yang bukan anotator.

1. Buka setiap file `data/processed/review_segmentasi_{id_abstrak}.csv`
2. Periksa kolom `perlu_review` (= `Ya` = perlu perhatian)
3. Baca `catatan_b5` untuk keterangan keraguan segmentasi
4. Isi kolom `disetujui` dengan `Ya` atau `Tidak` (jika tidak disetujui, tulis usulan batas)
5. Setelah semua segmen diperiksa, susun `segmen.csv` berdasarkan kandidat yang sudah disetujui:

```powershell
# Salin kandidat_segmen.csv ke segmen.csv HANYA setelah pemeriksaan manual selesai
# Tambahkan kolom status_beku = "disetujui" untuk setiap segmen yang sudah OK
# Format segmen.csv:
#   id_abstrak, id_segmen, urutan, teks_segmen, asal_segmentasi,
#   catatan_segmentasi, status_beku
```

> ⚠️ **Segmentasi yang belum berstatus `disetujui` atau `beku` tidak akan diproses** oleh `prepare_labelstudio_tasks.py`.

---

### Langkah 4 – Buat dan impor task JSON ke Label Studio

```powershell
# Buat task untuk dua anotator (an1 dan an2)
python scripts\prepare_labelstudio_tasks.py `
    --segmen data\processed\segmen.csv `
    --abstrak data\processed\abstrak.csv `
    --output-dir data\labelstudio `
    --anotator-ids an1,an2 `
    --peran-data korpus-anotasi `
    --seed 42

# Output:
#   data\labelstudio\tasks_an1_korpus-anotasi.json
#   data\labelstudio\tasks_an2_korpus-anotasi.json
#   data\labelstudio\seed_info.json   (catat seed untuk reproduksi)
```

**Impor ke Label Studio:**
1. Buka proyek di Label Studio
2. Klik **Import** → pilih file JSON sesuai anotatornya
3. Konfirmasi impor

---

### Langkah 5 – Buat proyek terpisah untuk dua anotator

> ⚠️ **Prinsip kritis:** Hasil anotator 1 **TIDAK BOLEH** dilihat anotator 2 sebelum adjudikasi.

**Cara membuat dua proyek terpisah:**

1. **Proyek Anotator 1 (`an1`):**
   - Login sebagai admin di Label Studio
   - Buat proyek baru: nama `Anotasi-Korpus-an1`
   - Impor `data/labelstudio/tasks_an1_korpus-anotasi.json`
   - Undang user dengan akun `an1`; **jangan** undang `an2`

2. **Proyek Anotator 2 (`an2`):**
   - Buat proyek baru terpisah: nama `Anotasi-Korpus-an2`
   - Impor `data/labelstudio/tasks_an2_korpus-anotasi.json`
   - Undang user dengan akun `an2`; **jangan** undang `an1`

**Atau, jika hanya satu mesin:**
```powershell
# Jalankan dua instance Label Studio pada port berbeda
# Instance 1 (untuk an1):
label-studio start --port 8080

# Instance 2 (untuk an2) - buka terminal baru:
label-studio start --port 8081 --data-dir .label-studio-an2
```

---

### Langkah 6 – Ekspor dan konversi anotasi ke CSV

**Di Label Studio:**
1. Buka proyek → klik **Export**
2. Pilih format **JSON** (bukan JSON-MIN)
3. Simpan file ke `data/exports/export_an1.json` (atau `export_an2.json`)

**Konversi ke CSV penelitian:**

```powershell
# Konversi anotasi anotator 1
python scripts\convert_labelstudio_export.py `
    --input data\exports\export_an1.json `
    --output data\processed\anotasi_an1.csv `
    --anotator-id an1

# Konversi anotasi anotator 2
python scripts\convert_labelstudio_export.py `
    --input data\exports\export_an2.json `
    --output data\processed\anotasi_an2.csv `
    --anotator-id an2
```

> ℹ️ Skrip ini **tidak menimpa** file anotasi yang sudah ada. Ganti nama file lama jika perlu mengonversi ulang.

---

### Langkah 7 – Validasi anotasi

```powershell
python scripts\validate_annotations.py `
    --anotasi data\processed\anotasi_an1.csv,data\processed\anotasi_an2.csv `
    --segmen data\processed\segmen.csv `
    --abstrak data\processed\abstrak.csv `
    --output-dir data\processed

# Output:
#   data\processed\laporan_validasi.csv          (detail per masalah)
#   data\processed\laporan_validasi_ringkasan.txt
```

> ⚠️ Perbaiki semua **ERROR** sebelum melanjutkan. **WARNING** dicatat tetapi tidak memblokir proses.

---

### Langkah 8 – Susun antrean adjudikasi

```powershell
python scripts\build_adjudication_queue.py `
    --anotasi-1 data\processed\anotasi_an1.csv `
    --anotasi-2 data\processed\anotasi_an2.csv `
    --output data\processed\adjudikasi.csv

# Untuk mode satu anotator (tanpa --anotasi-2):
python scripts\build_adjudication_queue.py `
    --anotasi-1 data\processed\anotasi_an1.csv `
    --output data\processed\adjudikasi.csv
```

**Antrean adjudikasi masuk jika:**
- Label kedua anotator berbeda
- Salah satu memberi flag (B1–B6)
- Salah satu memberi label TT

**Adjudikator mengisi kolom berikut di `adjudikasi.csv`:**
- `label_akhir` – label final menurut pedoman
- `label_alt_sisa` – alternatif yang tersisa
- `status_akhir` – `final` | `batas-sisa` | `dikecualikan`
- `konteks_dipakai` – `ya` atau `tidak` (hanya sah pada B2/B3)
- `alasan` – alasan keputusan
- `adjudikator_id` – ID adjudikator
- `waktu_selesai` – waktu selesai adjudikasi

> ⚠️ Sistem **tidak otomatis** memilih label. Adjudikator adalah orang ketiga yang **wajib** membaca seluruh abstrak dan pedoman v1.0.

---

### Langkah 9 – Hitung kelengkapan abstrak

```powershell
python scripts\calculate_completeness.py `
    --adjudikasi data\processed\adjudikasi.csv `
    --abstrak data\processed\abstrak.csv `
    --output-dir data\processed

# Output:
#   data\processed\kelengkapan_abstrak.csv    (vektor per abstrak)
#   data\processed\ringkasan_kelengkapan.txt  (statistik per jenis studi)
```

**Kolom penting di `kelengkapan_abstrak.csv`:**
- `vektor` – `(LB,TJ,MT,HS,SI)`, mis. `(1,1,1,1,0)`
- `status` – `LENGKAP` | `TIDAK LENGKAP` | `TAK PASTI`
- `komponen_hilang` – mis. `SI` atau `HS, SI`
- `status_kepastian` – `pasti` | `TAK PASTI`
- `vmin_vektor`, `vmaks_vektor` – untuk analisis sensitivitas

> ℹ️ Abstrak `TAK PASTI` (v-min ≠ v-maks) **tidak masuk metrik utama** dan dilaporkan terpisah pada analisis sensitivitas.

---

## 5. Lokasi Berkas Keluaran

```
data/
├── raw/                          # Taruh CSV input di sini
├── templates/
│   └── abstrak_input_template.csv
├── processed/
│   ├── abstrak.csv               # Metadata + teks mentah + teks kerja
│   ├── log_normalisasi.csv       # Log perubahan normalisasi
│   ├── log_dedup.csv             # Log deduplikasi
│   ├── kandidat_segmen.csv       # Kandidat segmen (belum dibekukan)
│   ├── review_segmentasi_*.csv   # File review per abstrak (untuk pemeriksa)
│   ├── segmen.csv                # Segmen yang sudah dibekukan (dibuat manual)
│   ├── anotasi_an1.csv           # Anotasi anotator 1
│   ├── anotasi_an2.csv           # Anotasi anotator 2
│   ├── adjudikasi.csv            # Antrean adjudikasi + hasil adjudikator
│   ├── kelengkapan_abstrak.csv   # Vektor kelengkapan per abstrak
│   ├── ringkasan_kelengkapan.txt
│   ├── laporan_validasi.csv
│   └── laporan_validasi_ringkasan.txt
├── labelstudio/
│   ├── tasks_an1_*.json          # Task JSON untuk anotator 1
│   ├── tasks_an2_*.json          # Task JSON untuk anotator 2
│   └── seed_info.json            # Seed acak untuk reproduksi
└── exports/
    ├── export_an1.json           # Ekspor mentah Label Studio an1
    └── export_an2.json           # Ekspor mentah Label Studio an2
```

---

## 6. Cara Menjalankan Unit Test

```powershell
# Dari direktori proyek
cd "c:\Users\ahmad\OneDrive\Documents\semester_7\Tugas Akhir\Label dataset"

# Jalankan semua test dengan output verbose
python tests\test_pipeline.py

# Atau dengan pytest (jika terinstal)
pip install pytest
python -m pytest tests\test_pipeline.py -v
```

**Kelompok test yang tersedia (53 test total):**

| Kelas | Jumlah Test | Cakupan |
|---|---|---|
| `TestNormalisasi` | 7 | Normalisasi ligatur, baris, spasi, SHA-256 |
| `TestDeduplikasi` | 8 | DOI, hash, Jaccard, non-hapus-diam-diam |
| `TestSegmentasi` | 8 | Kalimat normal, singkatan, URL, angka, urutan |
| `TestKonversiLS` | 7 | Label tunggal/ganda, UP, label alt |
| `TestValidasiMultiLabel` | 7 | TT+B2, flag+alasan, 3label+B5, label ganda+UP |
| `TestAdjudikasi` | 7 | Antrean: beda label, flag, TT, mode 1 anotator |
| `TestKelengkapan` | 9 | LENGKAP/TIDAK LENGKAP/TAK PASTI, K2, K3, K5 |

> ⚠️ Semua data uji bertanda `[SINTETIS]` atau menggunakan prefix `TEST_`. Tidak boleh dicampur dengan data penelitian asli.

---

## 7. Keterbatasan Fitur Label Studio

Berikut fitur pedoman yang **tidak dapat diterapkan sepenuhnya** melalui fitur bawaan Label Studio v1.x, beserta mitigasi yang sudah diterapkan di Python:

### 7.1 Tampilan kondisional (conditional display)
**Keterbatasan:** Label Studio tidak mendukung tampilan field yang berubah secara kondisional berdasarkan nilai field lain (mis. tampilkan `label_2` hanya jika `uji_pemecahan = Ya`).

**Mitigasi:** Field `label_2`–`label_6` dan `pemicu_up` selalu ditampilkan. Validasi kondisional dilakukan oleh `validate_annotations.py` (Aturan 6 & 7).

### 7.2 Pencatatan waktu mulai (waktu_mulai)
**Keterbatasan:** Label Studio tidak menyimpan waktu saat anotator pertama kali membuka sebuah task (waktu_mulai). Yang tersedia hanya `completed_at` (waktu menyimpan anotasi).

**Mitigasi:** Kolom `waktu_mulai` dan `durasi_detik` dikosongkan di `anotasi.csv`. Jika pencatatan waktu diperlukan, gunakan Label Studio SDK dengan event tracking kustom.

### 7.3 Validasi lintas-field otomatis
**Keterbatasan:** Label Studio tidak mendukung validasi seperti "jika label = TT maka flag harus B2" secara native di antarmuka.

**Mitigasi:** Semua validasi lintas-field dilakukan oleh `validate_annotations.py` setelah ekspor.

### 7.4 Urutan label ganda
**Keterbatasan:** Label Studio tidak memaksa anotator mengisi label dalam urutan kemunculan teks.

**Mitigasi:** Instruksi urutan ditampilkan eksplisit di antarmuka. Pengecekan urutan adalah tanggung jawab anotator; `validate_annotations.py` memperingatkan jika ada ketidakwajaran.

### 7.5 Pencegahan anotator melihat hasil anotator lain
**Keterbatasan:** Dalam satu proyek Label Studio, anggota bisa melihat anotasi satu sama lain jika diizinkan.

**Mitigasi:** Buat dua **proyek terpisah** untuk dua anotator. Jangan tambahkan anotator ke proyek yang bukan miliknya (lihat Langkah 5).

---

## 8. Struktur Proyek

```
Label dataset/
├── config/
│   └── label_studio_config.xml       # Konfigurasi antarmuka Label Studio
├── data/
│   ├── templates/
│   │   └── abstrak_input_template.csv
│   ├── raw/                           # Taruh file CSV input di sini
│   ├── processed/                     # Output pipeline
│   ├── labelstudio/                   # Task JSON untuk Label Studio
│   └── exports/                       # Ekspor mentah dari Label Studio
├── scripts/
│   ├── prepare_abstrak.py             # Normalisasi, hash, deduplikasi
│   ├── segment_abstrak.py             # Segmentasi kalimat berbasis aturan
│   ├── prepare_labelstudio_tasks.py   # Buat task JSON untuk Label Studio
│   ├── convert_labelstudio_export.py  # Konversi ekspor LS ke anotasi.csv
│   ├── validate_annotations.py        # Validator 15 aturan penelitian
│   ├── build_adjudication_queue.py    # Susun antrean adjudikasi
│   └── calculate_completeness.py      # Hitung vektor kelengkapan
├── tests/
│   └── test_pipeline.py               # 53 unit test dengan data sintetis
├── pedoman_v1.0_beku.md               # Pedoman Anotasi v1.0 (dibekukan)
├── requirements.txt
└── README.md
```

---

## Referensi Cepat: Perintah Lengkap (Copy-Paste)

```powershell
# 0. Setup
cd "c:\Users\ahmad\OneDrive\Documents\semester_7\Tugas Akhir\Label dataset"
python -m venv .venv; .venv\Scripts\Activate.ps1
pip install -r requirements.txt

# 1. Persiapan abstrak
python scripts\prepare_abstrak.py --input data\raw\abstrak_input.csv --output-dir data\processed

# 2. Segmentasi
python scripts\segment_abstrak.py --abstrak data\processed\abstrak.csv --output-dir data\processed

# 3. [MANUAL] Periksa review_segmentasi_*.csv → susun segmen.csv dengan status_beku=disetujui

# 4. Buat task JSON
python scripts\prepare_labelstudio_tasks.py --segmen data\processed\segmen.csv --abstrak data\processed\abstrak.csv --output-dir data\labelstudio --anotator-ids an1,an2 --peran-data korpus-anotasi --seed 42

# 5. [MANUAL] Impor ke Label Studio (dua proyek terpisah)

# 6. [MANUAL] Ekspor dari Label Studio → simpan ke data\exports\

# 7. Konversi ekspor ke CSV
python scripts\convert_labelstudio_export.py --input data\exports\export_an1.json --output data\processed\anotasi_an1.csv --anotator-id an1
python scripts\convert_labelstudio_export.py --input data\exports\export_an2.json --output data\processed\anotasi_an2.csv --anotator-id an2

# 8. Validasi
python scripts\validate_annotations.py --anotasi data\processed\anotasi_an1.csv,data\processed\anotasi_an2.csv --segmen data\processed\segmen.csv --abstrak data\processed\abstrak.csv --output-dir data\processed

# 9. Adjudikasi
python scripts\build_adjudication_queue.py --anotasi-1 data\processed\anotasi_an1.csv --anotasi-2 data\processed\anotasi_an2.csv --output data\processed\adjudikasi.csv

# 10. [MANUAL] Isi adjudikasi.csv oleh adjudikator

# 11. Kelengkapan
python scripts\calculate_completeness.py --adjudikasi data\processed\adjudikasi.csv --abstrak data\processed\abstrak.csv --output-dir data\processed

# 12. Unit test
python tests\test_pipeline.py
```
