#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
prepare_abstrak.py
==================
Membaca CSV input abstrak, melakukan normalisasi minimal sesuai Pedoman v1.0
(Bagian 2.2), deduplikasi (Bagian 2.5), menghitung hash SHA-256, dan
menghasilkan abstrak.csv serta log_normalisasi.csv, log_dedup.csv.

CATATAN IMPLEMENTASI:
- Teks mentah TIDAK PERNAH diubah.
- Teks kerja dibuat sebagai salinan yang telah dinormalisasi.
- Setiap perubahan normalisasi dicatat per karakter/posisi pada log_normalisasi.csv.
- Deduplikasi berbasis DOI ternormalisasi, lalu judul+tahun+jurnal, lalu hash,
  lalu Jaccard 5-gram kata (threshold >= 0.90).
- Duplikat dekat TIDAK dihapus secara diam-diam; hanya ditandai untuk review manual.

Penggunaan:
    python scripts/prepare_abstrak.py \
        --input data/templates/abstrak_input_template.csv \
        --output-dir data/processed \
        [--skip-near-dup]
"""

import argparse
import csv
import hashlib
import json
import logging
import re
import unicodedata
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

# ---------------------------------------------------------------------------
# Konfigurasi logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("prepare_abstrak")

# ---------------------------------------------------------------------------
# Konstanta
# ---------------------------------------------------------------------------
VALID_JENIS_STUDI: Set[str] = {
    "kuantitatif", "kualitatif", "campuran",
    "pengembangan-produk", "literatur", "konseptual",
}
VALID_PERAN_DATA: Set[str] = {
    "data-pengembangan", "pilot2", "korpus-anotasi",
}
VALID_JENIS_SUMBER: Set[str] = {"pdf_terbit", "halaman_artikel"}
KOLOM_WAJIB: List[str] = [
    "id_abstrak", "judul", "jurnal", "tahun", "jenis_studi",
    "peran_data", "teks_mentah",
]
KOLOM_OPSIONAL: List[str] = [
    "volume_nomor", "doi", "url", "jenis_sumber", "versi_dokumen",
    "tanggal_akses", "lisensi",
]
NEAR_DUP_THRESHOLD: float = 0.90  # Jaccard 5-gram kata (Bagian 2.5 butir 3)


# ---------------------------------------------------------------------------
# Utilitas hash
# ---------------------------------------------------------------------------
def sha256_text(text: str) -> str:
    """Hitung SHA-256 dari string UTF-8."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Normalisasi minimal (Bagian 2.2)
# ---------------------------------------------------------------------------

# Peta ligatur Unicode ke karakter biasa
_LIGATURE_MAP: Dict[str, str] = {
    "\ufb00": "ff",   # ﬀ
    "\ufb01": "fi",   # ﬁ
    "\ufb02": "fl",   # ﬂ
    "\ufb03": "ffi",  # ﬃ
    "\ufb04": "ffl",  # ﬄ
    "\ufb05": "st",   # ﬅ
    "\ufb06": "st",   # ﬆ
    # tambahkan ligatur lain jika diperlukan
}

_LIGATURE_RE = re.compile("|".join(re.escape(k) for k in _LIGATURE_MAP))


def normalize_ligatures(text: str) -> Tuple[str, List[Dict]]:
    """Ganti ligatur dengan karakter biasa; catat setiap penggantian."""
    changes: List[Dict] = []
    pos_offset = 0

    def _replace(m: re.Match) -> str:
        nonlocal pos_offset
        orig = m.group(0)
        repl = _LIGATURE_MAP[orig]
        changes.append({
            "posisi_karakter": m.start() + pos_offset,
            "teks_asal": orig,
            "teks_baru": repl,
            "jenis": "ligatur",
        })
        pos_offset += len(repl) - len(orig)
        return repl

    result = _LIGATURE_RE.sub(_replace, text)
    return result, changes


def normalize_minimal(teks_mentah: str) -> Tuple[str, List[Dict]]:
    """
    Normalisasi minimal sesuai Bagian 2.2:
    1. Menyambungkan kata yang terpotong karena pergantian baris (soft hyphen).
    2. Menghilangkan pemisah baris dari tata letak dokumen.
    3. Merapikan spasi ganda.
    4. Menormalkan ligatur.

    Tidak memperbaiki ejaan atau tata bahasa.
    Mengembalikan (teks_kerja, daftar_perubahan).
    """
    changes: List[Dict] = []
    text = teks_mentah

    # 1. Normalisasi ligatur
    text, lig_changes = normalize_ligatures(text)
    changes.extend(lig_changes)

    # 2. Sambung kata terpotong di akhir baris: "kata-\nbaru" -> "katabaru"
    #    (soft hyphen sebelum newline)
    pattern_hyphen_newline = re.compile(r"-\n(\S)")

    def _fix_hyphen(m: re.Match) -> str:
        changes.append({
            "posisi_karakter": m.start(),
            "teks_asal": m.group(0),
            "teks_baru": m.group(1),
            "jenis": "sambung_kata",
        })
        return m.group(1)

    text = pattern_hyphen_newline.sub(_fix_hyphen, text)

    # 3. Hapus pemisah baris tata letak: newline yang bukan pemisah kalimat
    #    -> ganti dengan spasi
    lines_before = text.split("\n")
    new_lines = []
    for i, line in enumerate(lines_before):
        stripped = line.rstrip()
        if stripped:
            new_lines.append(stripped)
        else:
            new_lines.append("")  # baris kosong tetap sebagai pemisah paragraf

    new_text = " ".join(l for l in new_lines if l)
    if new_text != text:
        # Catat jumlah baris yang dihapus
        n_newlines = text.count("\n")
        if n_newlines > 0:
            changes.append({
                "posisi_karakter": 0,
                "teks_asal": f"[{n_newlines} karakter newline]",
                "teks_baru": "[diganti spasi]",
                "jenis": "hapus_baris",
            })
    text = new_text

    # 4. Rapikan spasi ganda
    text_clean = re.sub(r" {2,}", " ", text)
    if text_clean != text:
        changes.append({
            "posisi_karakter": 0,
            "teks_asal": "[spasi ganda]",
            "teks_baru": "[satu spasi]",
            "jenis": "spasi",
        })
    text = text_clean.strip()

    return text, changes


# ---------------------------------------------------------------------------
# Normalisasi untuk kunci deduplikasi
# ---------------------------------------------------------------------------

def normalize_doi(doi: str) -> str:
    """Normalisasi DOI: huruf kecil, hapus awalan URL dan whitespace."""
    if not doi:
        return ""
    doi = doi.strip().lower()
    for prefix in ("https://doi.org/", "http://doi.org/", "doi:", "doi.org/"):
        if doi.startswith(prefix):
            doi = doi[len(prefix):]
            break
    return doi.strip()


def normalize_title(title: str) -> str:
    """Normalisasi judul: huruf kecil, tanpa tanda baca, spasi tunggal."""
    title = unicodedata.normalize("NFC", title.lower())
    title = re.sub(r"[^\w\s]", " ", title)
    title = re.sub(r"\s+", " ", title).strip()
    return title


def normalize_text_for_hash(text: str) -> str:
    """Normalisasi teks untuk hash duplikat: huruf kecil, tanpa tanda baca, spasi tunggal."""
    text = unicodedata.normalize("NFC", text.lower())
    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


# ---------------------------------------------------------------------------
# Jaccard 5-gram kata untuk duplikat dekat
# ---------------------------------------------------------------------------

def word_ngrams(text: str, n: int = 5) -> Set[Tuple[str, ...]]:
    """Buat himpunan n-gram kata dari teks."""
    words = text.lower().split()
    if len(words) < n:
        return {tuple(words)} if words else set()
    return {tuple(words[i:i+n]) for i in range(len(words) - n + 1)}


def jaccard_similarity(set_a: Set, set_b: Set) -> float:
    """Hitung Jaccard similarity antara dua himpunan."""
    if not set_a and not set_b:
        return 1.0
    if not set_a or not set_b:
        return 0.0
    return len(set_a & set_b) / len(set_a | set_b)


# ---------------------------------------------------------------------------
# Validasi metadata wajib
# ---------------------------------------------------------------------------

def validate_row(row: Dict, row_idx: int) -> List[str]:
    """Periksa metadata wajib dan nilai enum. Kembalikan daftar pesan error."""
    errors: List[str] = []

    for col in KOLOM_WAJIB:
        if not row.get(col, "").strip():
            errors.append(
                f"Baris {row_idx}: kolom wajib '{col}' kosong "
                f"(id_abstrak={row.get('id_abstrak', '?')})"
            )

    js = row.get("jenis_studi", "").strip()
    if js and js not in VALID_JENIS_STUDI:
        errors.append(
            f"Baris {row_idx}: jenis_studi='{js}' tidak valid. "
            f"Nilai yang diperbolehkan: {sorted(VALID_JENIS_STUDI)}"
        )

    pd_ = row.get("peran_data", "").strip()
    if pd_ and pd_ not in VALID_PERAN_DATA:
        errors.append(
            f"Baris {row_idx}: peran_data='{pd_}' tidak valid. "
            f"Nilai yang diperbolehkan: {sorted(VALID_PERAN_DATA)}"
        )

    js2 = row.get("jenis_sumber", "").strip()
    if js2 and js2 not in VALID_JENIS_SUMBER:
        errors.append(
            f"Baris {row_idx}: jenis_sumber='{js2}' tidak valid. "
            f"Nilai yang diperbolehkan: {sorted(VALID_JENIS_SUMBER)}"
        )

    return errors


# ---------------------------------------------------------------------------
# Fungsi utama
# ---------------------------------------------------------------------------

def prepare_abstrak(
    input_path: Path,
    output_dir: Path,
    skip_near_dup: bool = False,
) -> None:
    """
    Pipeline utama:
    1. Baca CSV input
    2. Validasi metadata
    3. Normalisasi minimal -> teks_kerja
    4. Hitung hash
    5. Deduplikasi
    6. Tulis abstrak.csv, log_normalisasi.csv, log_dedup.csv
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    rows: List[Dict] = []
    all_errors: List[str] = []

    # --- Baca CSV ---
    logger.info(f"Membaca input: {input_path}")
    with open(input_path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(
            (line for line in f if not line.lstrip().startswith("#"))
        )
        for idx, row in enumerate(reader, start=2):  # mulai baris 2 (header di baris 1)
            errs = validate_row(row, idx)
            all_errors.extend(errs)
            rows.append(row)

    if all_errors:
        logger.warning(f"{len(all_errors)} masalah validasi ditemukan:")
        for err in all_errors:
            logger.warning(f"  {err}")
    else:
        logger.info("Semua baris lulus validasi metadata.")

    # --- Normalisasi dan hash ---
    norm_log_rows: List[Dict] = []
    processed: List[Dict] = []

    for row in rows:
        id_abstrak = row.get("id_abstrak", "").strip()
        teks_mentah = row.get("teks_mentah", "")

        # Hash teks mentah (sebelum normalisasi)
        hash_mentah = sha256_text(teks_mentah)

        # Normalisasi minimal
        teks_kerja, changes = normalize_minimal(teks_mentah)

        # Hash teks kerja ternormalisasi (untuk deduplikasi)
        teks_ternormalisasi = normalize_text_for_hash(teks_kerja)
        hash_ternormalisasi = sha256_text(teks_ternormalisasi)

        # Catat perubahan normalisasi
        for ch in changes:
            norm_log_rows.append({
                "id_abstrak": id_abstrak,
                "posisi_karakter": ch["posisi_karakter"],
                "teks_asal": ch["teks_asal"],
                "teks_baru": ch["teks_baru"],
                "jenis": ch["jenis"],
            })

        # Hitung kunci artikel
        doi_norm = normalize_doi(row.get("doi", ""))
        if doi_norm:
            kunci_artikel = f"doi:{doi_norm}"
        else:
            judul_norm = normalize_title(row.get("judul", ""))
            tahun = str(row.get("tahun", "")).strip()
            jurnal_norm = normalize_title(row.get("jurnal", ""))
            kunci_artikel = f"title:{judul_norm}|{tahun}|{jurnal_norm}"

        processed.append({
            # metadata asli
            "id_abstrak": id_abstrak,
            "bahasa": "id",
            "peran_data": row.get("peran_data", "").strip(),
            "jenis_studi": row.get("jenis_studi", "").strip(),
            "judul": row.get("judul", "").strip(),
            "jurnal": row.get("jurnal", "").strip(),
            "tahun": row.get("tahun", "").strip(),
            "volume_nomor": row.get("volume_nomor", "").strip(),
            "doi": row.get("doi", "").strip(),
            "url": row.get("url", "").strip(),
            "jenis_sumber": row.get("jenis_sumber", "").strip(),
            "versi_dokumen": row.get("versi_dokumen", "").strip(),
            "tanggal_akses": row.get("tanggal_akses", "").strip(),
            "teks_mentah": teks_mentah,  # TIDAK PERNAH DIUBAH
            "hash_teks_mentah": hash_mentah,
            "teks_kerja": teks_kerja,
            "lisensi": row.get("lisensi", "").strip(),
            "kunci_artikel": kunci_artikel,
            "hash_teks_ternormalisasi": hash_ternormalisasi,
            "status_dedup": "unik",  # default; akan diperbarui saat deduplikasi
        })

    # --- Periksa duplikat ID abstrak ---
    id_set: Set[str] = set()
    for p in processed:
        if p["id_abstrak"] in id_set:
            logger.error(
                f"ID abstrak duplikat: '{p['id_abstrak']}'. "
                "ID abstrak harus unik dalam satu file input."
            )
        id_set.add(p["id_abstrak"])

    # --- Deduplikasi (Bagian 2.5) ---
    dedup_log: List[Dict] = []
    dedup_log = run_deduplication(processed, dedup_log, skip_near_dup)

    # --- Periksa satu artikel satu peran (Bagian 2.5 butir 5) ---
    check_single_role(processed, dedup_log)

    # --- Tulis abstrak.csv ---
    abstrak_path = output_dir / "abstrak.csv"
    abstrak_cols = [
        "id_abstrak", "bahasa", "peran_data", "jenis_studi",
        "judul", "jurnal", "tahun", "volume_nomor", "doi", "url",
        "jenis_sumber", "versi_dokumen", "tanggal_akses",
        "teks_mentah", "hash_teks_mentah",
        "teks_kerja", "lisensi",
        "kunci_artikel", "hash_teks_ternormalisasi", "status_dedup",
    ]
    write_csv(abstrak_path, abstrak_cols, processed)
    logger.info(f"abstrak.csv ditulis: {abstrak_path} ({len(processed)} baris)")

    # --- Tulis log_normalisasi.csv ---
    norm_path = output_dir / "log_normalisasi.csv"
    norm_cols = ["id_abstrak", "posisi_karakter", "teks_asal", "teks_baru", "jenis"]
    write_csv(norm_path, norm_cols, norm_log_rows)
    logger.info(
        f"log_normalisasi.csv ditulis: {norm_path} ({len(norm_log_rows)} perubahan)"
    )

    # --- Tulis log_dedup.csv ---
    dedup_path = output_dir / "log_dedup.csv"
    dedup_cols = [
        "id_abstrak_dibuang", "id_abstrak_disimpan",
        "jenis_duplikat", "alasan", "skor_jaccard",
    ]
    write_csv(dedup_path, dedup_cols, dedup_log)
    logger.info(f"log_dedup.csv ditulis: {dedup_path} ({len(dedup_log)} entri)")

    # --- Ringkasan ---
    n_unik = sum(1 for p in processed if p["status_dedup"] == "unik")
    n_buang = sum(1 for p in processed if p["status_dedup"] == "duplikat-dibuang")
    n_dekat = sum(1 for p in processed if p["status_dedup"] == "duplikat-dekat-ditinjau")
    logger.info(
        f"Ringkasan: {len(processed)} total | "
        f"{n_unik} unik | {n_buang} duplikat dibuang | "
        f"{n_dekat} duplikat dekat (perlu review manual)"
    )

    if all_errors:
        logger.warning(
            f"Ada {len(all_errors)} peringatan validasi. "
            "Periksa log di atas sebelum melanjutkan ke segmentasi."
        )


def run_deduplication(
    rows: List[Dict],
    dedup_log: List[Dict],
    skip_near_dup: bool,
) -> List[Dict]:
    """
    Jalankan deduplikasi sesuai Bagian 2.5:
    1. Kunci artikel (DOI atau judul+tahun+jurnal)
    2. Hash teks ternormalisasi
    3. Jaccard 5-gram >= 0.90 (jika tidak di-skip)
    Tandai status_dedup tanpa menghapus baris.
    """
    # 1. Deduplikasi kunci artikel
    kunci_seen: Dict[str, str] = {}  # kunci -> id_abstrak pertama
    for row in rows:
        k = row["kunci_artikel"]
        if k in kunci_seen:
            first_id = kunci_seen[k]
            if row["status_dedup"] == "unik":
                row["status_dedup"] = "duplikat-dibuang"
                dedup_log.append({
                    "id_abstrak_dibuang": row["id_abstrak"],
                    "id_abstrak_disimpan": first_id,
                    "jenis_duplikat": "kunci-artikel",
                    "alasan": f"Kunci artikel sama: {k}",
                    "skor_jaccard": "",
                })
                logger.warning(
                    f"Duplikat kunci artikel: '{row['id_abstrak']}' == '{first_id}' "
                    f"(kunci: {k})"
                )
        else:
            kunci_seen[k] = row["id_abstrak"]

    # 2. Duplikat teks persis (hash)
    hash_seen: Dict[str, str] = {}
    for row in rows:
        if row["status_dedup"] != "unik":
            continue
        h = row["hash_teks_ternormalisasi"]
        if h in hash_seen:
            first_id = hash_seen[h]
            row["status_dedup"] = "duplikat-dibuang"
            dedup_log.append({
                "id_abstrak_dibuang": row["id_abstrak"],
                "id_abstrak_disimpan": first_id,
                "jenis_duplikat": "hash-teks",
                "alasan": "Hash teks ternormalisasi identik (teks persis sama)",
                "skor_jaccard": "1.0",
            })
            logger.warning(
                f"Duplikat teks persis: '{row['id_abstrak']}' == '{first_id}'"
            )
        else:
            hash_seen[h] = row["id_abstrak"]

    # 3. Duplikat dekat (Jaccard >= 0.90)
    if not skip_near_dup:
        unik_rows = [r for r in rows if r["status_dedup"] == "unik"]
        ngrams_cache: Dict[str, Set] = {
            r["id_abstrak"]: word_ngrams(r["teks_kerja"], 5)
            for r in unik_rows
        }

        checked_pairs: Set[Tuple[str, str]] = set()
        for i, row_a in enumerate(unik_rows):
            for row_b in unik_rows[i+1:]:
                pair = (row_a["id_abstrak"], row_b["id_abstrak"])
                if pair in checked_pairs:
                    continue
                checked_pairs.add(pair)

                sim = jaccard_similarity(
                    ngrams_cache[row_a["id_abstrak"]],
                    ngrams_cache[row_b["id_abstrak"]],
                )
                if sim >= NEAR_DUP_THRESHOLD:
                    # Tandai yang kedua; jangan hapus otomatis
                    row_b["status_dedup"] = "duplikat-dekat-ditinjau"
                    dedup_log.append({
                        "id_abstrak_dibuang": row_b["id_abstrak"],
                        "id_abstrak_disimpan": row_a["id_abstrak"],
                        "jenis_duplikat": "duplikat-dekat",
                        "alasan": (
                            f"Jaccard 5-gram = {sim:.4f} >= {NEAR_DUP_THRESHOLD}. "
                            "PERLU REVIEW MANUAL sebelum melanjutkan."
                        ),
                        "skor_jaccard": f"{sim:.4f}",
                    })
                    logger.warning(
                        f"Duplikat dekat: '{row_a['id_abstrak']}' <-> "
                        f"'{row_b['id_abstrak']}' (Jaccard={sim:.4f}). "
                        "Ditandai untuk review manual."
                    )

    return dedup_log


def check_single_role(rows: List[Dict], dedup_log: List[Dict]) -> None:
    """
    Periksa Bagian 2.5 butir 5: satu artikel tidak boleh ada di dua peran data.
    Gunakan kunci artikel untuk identifikasi.
    """
    kunci_to_roles: Dict[str, List[Tuple[str, str]]] = {}
    for row in rows:
        k = row["kunci_artikel"]
        if k not in kunci_to_roles:
            kunci_to_roles[k] = []
        kunci_to_roles[k].append((row["id_abstrak"], row["peran_data"]))

    for k, entries in kunci_to_roles.items():
        roles = {e[1] for e in entries}
        if len(roles) > 1:
            ids = [e[0] for e in entries]
            logger.error(
                f"PELANGGARAN SATU ARTIKEL SATU PERAN: kunci '{k}' "
                f"muncul di peran berbeda: {entries}. "
                "Artikel yang sama tidak boleh ada di data-pengembangan, "
                "pilot2, DAN korpus-anotasi sekaligus."
            )


# ---------------------------------------------------------------------------
# Utilitas tulis CSV
# ---------------------------------------------------------------------------

def write_csv(path: Path, cols: List[str], rows: List[Dict]) -> None:
    """Tulis CSV UTF-8 tanpa BOM, dengan quoting benar."""
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=cols,
            quoting=csv.QUOTE_MINIMAL,
            extrasaction="ignore",
        )
        writer.writeheader()
        writer.writerows(rows)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Persiapan abstrak: normalisasi, hash, deduplikasi."
    )
    parser.add_argument(
        "--input", "-i",
        required=True,
        help="Path ke CSV input abstrak (lihat data/templates/abstrak_input_template.csv)",
    )
    parser.add_argument(
        "--output-dir", "-o",
        default="data/processed",
        help="Direktori output (default: data/processed)",
    )
    parser.add_argument(
        "--skip-near-dup",
        action="store_true",
        help="Lewati pemeriksaan duplikat dekat Jaccard (mempercepat proses pada korpus besar)",
    )
    args = parser.parse_args()

    prepare_abstrak(
        input_path=Path(args.input),
        output_dir=Path(args.output_dir),
        skip_near_dup=args.skip_near_dup,
    )


if __name__ == "__main__":
    main()
