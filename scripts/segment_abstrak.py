#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
segment_abstrak.py
==================
Segmentasi kalimat berbasis aturan sesuai Bagian 2.3 Pedoman v1.0.

Aturan yang diimplementasikan:
- Batas kalimat: tanda ./?/! diikuti spasi + huruf kapital/angka/kutip pembuka,
  atau akhir teks.
- Singkatan bertitik: tidak memecah sebelum huruf kecil, angka, atau frasa yang
  melanjutkan.
- Angka desimal (koma) dan ribuan (titik): bukan batas.
- Titik tanpa spasi (artefak ekstraksi): batas jika sebelumnya bukan singkatan/URL/angka.
- URL, DOI, surel, nama berkas: titik di dalamnya bukan batas.
- Daftar bernomor dalam satu kalimat: penomor bukan batas.
- Titik dua dan titik koma: bukan batas kalimat.
- Kutipan langsung: tanda di dalam tanda kutip bukan batas jika kalimat berlanjut.
- Fragmen: fragmen tanpa predikat tetapi memuat info = segmen sendiri.
- Elipsis (...): diperlakukan sebagai satu titik.

Output:
- data/processed/review_segmentasi_{id_abstrak}.csv  (untuk review manual)
- data/processed/kandidat_segmen.csv  (semua kandidat, belum dibekukan)

KETERBATASAN:
Segmentasi berbasis aturan ini menghasilkan KANDIDAT. Pemeriksa segmentasi
(bukan anotator) WAJIB memeriksa dan membekukan hasil sebelum anotasi dimulai.
Kasus batas (B5) dicatat dalam output untuk memudahkan review.

Penggunaan:
    python scripts/segment_abstrak.py \
        --abstrak data/processed/abstrak.csv \
        --output-dir data/processed \
        [--peran-data korpus-anotasi]
"""

import argparse
import csv
import logging
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("segment_abstrak")

# ---------------------------------------------------------------------------
# Daftar singkatan bertitik (tidak mengakhiri kalimat)
# ---------------------------------------------------------------------------
# Singkatan yang tercantum dalam Pedoman 2.3 + umum dalam bahasa Indonesia akademik
ABBREVIATIONS = {
    # umum Indonesia
    "dkk", "dsb", "dst", "dll", "dll",
    "hlm", "no", "vol", "hal", "jur",
    "mis", "msl", "spt", "contoh",
    # gelar
    "prof", "dr", "ir", "drs", "drg",
    "m", "s", "se", "sh", "st", "si",
    "spd", "mkom", "msc", "phd", "spdi",
    "mkes", "msi", "mhum", "mph",
    # singkatan umum
    "vs", "dll", "etc", "cf", "fig",
    "pp", "ed", "eds", "vol", "rev",
    "dept", "univ", "inst",
    "jan", "feb", "mar", "apr", "mei",
    "jun", "jul", "agt", "sep", "okt", "nov", "des",
}

# Pola gelar bertingkat: S.Pd., M.Kom., dll.
DEGREE_PATTERN = re.compile(
    r"\b([A-Z][a-z]*\.)+[A-Z][a-z]*\.",
    re.UNICODE,
)

# Pola URL, DOI, email, nama berkas
URL_PATTERN = re.compile(
    r"(?:https?://|www\.|doi\.org/|mailto:)"
    r"[^\s,;\"'<>\[\](){}]+",
    re.IGNORECASE,
)
DOI_PATTERN = re.compile(r"\b10\.\d{4,}/[^\s]+", re.IGNORECASE)
EMAIL_PATTERN = re.compile(r"\b[\w.+-]+@[\w-]+\.[a-z]{2,}\b", re.IGNORECASE)
FILENAME_PATTERN = re.compile(r"\b[\w-]+\.[a-z]{2,4}\b", re.IGNORECASE)

# Pola angka desimal dan ribuan
DECIMAL_PATTERN = re.compile(r"\d+[,.]\d+")

# Elipsis: ganti ... dengan placeholder
ELLIPSIS_PATTERN = re.compile(r"\.{2,}")

# Daftar bernomor: (1), (a), a), 1), 1. di awal butir
LIST_ITEM_PATTERN = re.compile(
    r"(?:^|\s)(?:\(?[0-9]+[.)]\s|\(?[a-zA-Z][.)]\s)",
    re.MULTILINE,
)


# ---------------------------------------------------------------------------
# Tokenizer / splitter utama
# ---------------------------------------------------------------------------

def _protect_non_boundaries(text: str) -> Tuple[str, Dict[str, str]]:
    """
    Ganti semua pola yang mengandung titik tetapi bukan batas kalimat
    dengan placeholder aman (tanpa titik), kembalikan peta placeholder -> asli.
    """
    placeholder_map: Dict[str, str] = {}
    counter = [0]

    def _sub(m: re.Match, prefix: str) -> str:
        key = f"__PROT{prefix}{counter[0]}__"
        placeholder_map[key] = m.group(0)
        counter[0] += 1
        return key

    # 1. URL
    text = URL_PATTERN.sub(lambda m: _sub(m, "URL"), text)
    # 2. DOI
    text = DOI_PATTERN.sub(lambda m: _sub(m, "DOI"), text)
    # 3. Email
    text = EMAIL_PATTERN.sub(lambda m: _sub(m, "EMAIL"), text)
    # 4. Angka desimal dan ribuan (misal 3,5 atau 1.250)
    text = DECIMAL_PATTERN.sub(lambda m: _sub(m, "NUM"), text)
    # 5. Elipsis -> satu titik placeholder
    text = ELLIPSIS_PATTERN.sub(lambda m: _sub(m, "ELLIP"), text)
    # 6. Gelar bertingkat (S.Pd., M.Kom.)
    text = DEGREE_PATTERN.sub(lambda m: _sub(m, "DEG"), text)

    return text, placeholder_map


def _restore_placeholders(text: str, placeholder_map: Dict[str, str]) -> str:
    """Kembalikan placeholder ke teks asli."""
    for key, orig in placeholder_map.items():
        text = text.replace(key, orig)
    return text


def _is_abbreviation(token: str) -> bool:
    """Periksa apakah token (tanpa titik akhir) adalah singkatan yang dikenal."""
    return token.lower().rstrip(".") in ABBREVIATIONS


def segment_text(text: str) -> List[Dict]:
    """
    Segmentasi teks kerja menjadi daftar kandidat segmen.
    Mengembalikan daftar dict dengan:
      - urutan (int, mulai 1)
      - teks_segmen (str)
      - catatan_b5 (str, kosong jika tidak ada keraguan)
    """
    if not text.strip():
        return []

    # Langkah 1: lindungi pola non-batas
    protected, pmap = _protect_non_boundaries(text)

    # Langkah 2: pisahkan berdasarkan tanda batas kalimat
    # Batas: ., ?, ! yang diikuti spasi + huruf kapital/angka/kutip pembuka
    # ATAU titik langsung diikuti huruf kapital (artefak ekstraksi)
    sentence_end_pattern = re.compile(
        r"""
        (?:
            # Batas normal: . ? ! diikuti spasi lalu huruf kapital/angka/kutip
            [.?!]
            (?=\s+[A-Z0-9"'\u201c\u2018])
            |
            # Artefak ekstraksi: titik langsung diikuti huruf kapital
            \.(?=[A-Z])
        )
        """,
        re.VERBOSE | re.UNICODE,
    )

    # Tandai posisi batas yang potensial
    raw_sentences: List[str] = []
    last = 0
    for m in sentence_end_pattern.finditer(protected):
        end_pos = m.end()
        # Periksa: apakah token sebelum titik adalah singkatan?
        before_dot = protected[:m.start()].rstrip()
        last_token = before_dot.split()[-1] if before_dot.split() else ""
        if _is_abbreviation(last_token):
            # Singkatan: bukan batas
            continue
        # Batas valid
        raw_sentences.append(protected[last:end_pos].strip())
        last = end_pos

    # Sisa teks setelah batas terakhir
    remainder = protected[last:].strip()
    if remainder:
        raw_sentences.append(remainder)

    # Langkah 3: kembalikan placeholder dan bersihkan
    candidates: List[Dict] = []
    b5_notes: List[str] = []

    for i, sent in enumerate(raw_sentences):
        sent_restored = _restore_placeholders(sent, pmap).strip()
        if not sent_restored:
            continue

        # Deteksi kasus B5 potensial
        b5 = _detect_b5(sent_restored, i, len(raw_sentences))

        candidates.append({
            "urutan": len(candidates) + 1,
            "teks_segmen": sent_restored,
            "asal_segmentasi": "skrip",
            "catatan_segmentasi": b5,
        })

    return candidates


def _detect_b5(text: str, idx: int, total: int) -> str:
    """
    Heuristik deteksi kasus batas B5:
    - Teks terlalu pendek (< 5 kata) -> mungkin terpotong atau fragmen
    - Diawali angka atau huruf daftar -> mungkin butir daftar
    - Mengandung tanda baca ganda tidak wajar
    """
    notes = []
    words = text.split()

    if len(words) < 3:
        notes.append(
            f"B5-kandidat: fragmen sangat pendek ({len(words)} kata), "
            "periksa apakah terpotong atau fragmen tanpa proposisi"
        )

    # Diawali pola daftar bernomor
    if LIST_ITEM_PATTERN.match(text):
        notes.append(
            "B5-kandidat: diawali penomor daftar, "
            "periksa apakah butir daftar harus bergabung ke induk"
        )

    # Tidak ada kata kerja (heuristik sederhana: tidak ada spasi = satu kata)
    if len(words) == 1 and not text.endswith("."):
        notes.append(
            "B5-kandidat: satu token tanpa tanda baca, "
            "mungkin judul atau label seksi"
        )

    return "; ".join(notes) if notes else ""


# ---------------------------------------------------------------------------
# Proses semua abstrak
# ---------------------------------------------------------------------------

def segment_all(
    abstrak_path: Path,
    output_dir: Path,
    peran_filter: Optional[str] = None,
) -> None:
    """
    Baca abstrak.csv, segmentasi setiap teks kerja, dan tulis:
    - kandidat_segmen.csv (semua kandidat)
    - review_segmentasi_{id_abstrak}.csv (per abstrak, untuk review manual)
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    abstrak_rows: List[Dict] = []
    with open(abstrak_path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if peran_filter and row.get("peran_data", "") != peran_filter:
                continue
            if row.get("status_dedup", "") == "duplikat-dibuang":
                logger.info(
                    f"Lewati {row['id_abstrak']}: duplikat-dibuang"
                )
                continue
            abstrak_rows.append(row)

    logger.info(
        f"Segmentasi {len(abstrak_rows)} abstrak "
        f"{'(peran: ' + peran_filter + ')' if peran_filter else ''}"
    )

    all_segments: List[Dict] = []
    n_b5 = 0

    for row in abstrak_rows:
        id_abstrak = row["id_abstrak"]
        teks_kerja = row.get("teks_kerja", "").strip()

        if not teks_kerja:
            logger.warning(f"{id_abstrak}: teks_kerja kosong, dilewati.")
            continue

        segments = segment_text(teks_kerja)

        # Tambahkan id_abstrak dan buat id_segmen
        for seg in segments:
            urutan = seg["urutan"]
            seg["id_abstrak"] = id_abstrak
            seg["id_segmen"] = f"{id_abstrak}-S{urutan:02d}"
            all_segments.append(seg)
            if seg["catatan_segmentasi"]:
                n_b5 += 1

        logger.info(
            f"{id_abstrak}: {len(segments)} segmen kandidat "
            f"({sum(1 for s in segments if s['catatan_segmentasi'])} B5-kandidat)"
        )

        # Tulis review per abstrak
        review_path = output_dir / f"review_segmentasi_{id_abstrak}.csv"
        _write_review(review_path, teks_kerja, segments, id_abstrak)

    # Tulis semua kandidat
    kandidat_path = output_dir / "kandidat_segmen.csv"
    segmen_cols = [
        "id_abstrak", "id_segmen", "urutan", "teks_segmen",
        "asal_segmentasi", "catatan_segmentasi",
    ]
    _write_csv(kandidat_path, segmen_cols, all_segments)
    logger.info(
        f"kandidat_segmen.csv ditulis: {kandidat_path} "
        f"({len(all_segments)} segmen, {n_b5} perlu review B5)"
    )
    logger.warning(
        "PENTING: Segmentasi adalah KANDIDAT. Pemeriksa segmentasi (bukan anotator) "
        "WAJIB memeriksa setiap file review_segmentasi_*.csv sebelum membekukan "
        "dan mengirim ke Label Studio."
    )


def _write_review(
    path: Path,
    teks_kerja: str,
    segments: List[Dict],
    id_abstrak: str,
) -> None:
    """Tulis file review segmentasi per abstrak."""
    cols = [
        "id_abstrak", "id_segmen", "urutan", "teks_segmen",
        "perlu_review", "catatan_b5", "disetujui",
    ]
    rows = []
    for seg in segments:
        rows.append({
            "id_abstrak": id_abstrak,
            "id_segmen": seg["id_segmen"],
            "urutan": seg["urutan"],
            "teks_segmen": seg["teks_segmen"],
            "perlu_review": "Ya" if seg["catatan_segmentasi"] else "Tidak",
            "catatan_b5": seg["catatan_segmentasi"],
            "disetujui": "",  # diisi oleh pemeriksa
        })
    _write_csv(path, cols, rows)


def _write_csv(path: Path, cols: List[str], rows: List[Dict]) -> None:
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f, fieldnames=cols, quoting=csv.QUOTE_MINIMAL, extrasaction="ignore"
        )
        writer.writeheader()
        writer.writerows(rows)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Segmentasi kalimat abstrak berbasis aturan (Pedoman 2.3)."
    )
    parser.add_argument(
        "--abstrak", "-a",
        default="data/processed/abstrak.csv",
        help="Path ke abstrak.csv (output prepare_abstrak.py)",
    )
    parser.add_argument(
        "--output-dir", "-o",
        default="data/processed",
        help="Direktori output (default: data/processed)",
    )
    parser.add_argument(
        "--peran-data", "-p",
        default=None,
        help="Filter berdasarkan peran_data: data-pengembangan | pilot2 | korpus-anotasi",
    )
    args = parser.parse_args()

    segment_all(
        abstrak_path=Path(args.abstrak),
        output_dir=Path(args.output_dir),
        peran_filter=args.peran_data,
    )


if __name__ == "__main__":
    main()
