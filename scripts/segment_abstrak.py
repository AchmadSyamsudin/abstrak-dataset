#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
segment_abstrak.py
==================
Segmentasi kalimat berbasis aturan sesuai Bagian 2.3 Pedoman v1.0.

PERBAIKAN v2:
- Abstrak berstatus 'duplikat-dekat-ditinjau' diblokir sampai review dicatat.
- Perlindungan URL/DOI diperbaiki: titik penutup kalimat setelah URL/DOI
  kini dikenali dengan benar (URL tidak menelan titik penutup).
- Penanganan singkatan diperkuat: token singkatan hanya cocok jika diikuti
  spasi atau akhir string, bukan diikuti huruf kapital langsung.

Penggunaan:
    python scripts/segment_abstrak.py \\
        --abstrak data/processed/abstrak.csv \\
        --output-dir data/processed \\
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
# Singkatan bertitik (tidak mengakhiri kalimat)
# ---------------------------------------------------------------------------
ABBREVIATIONS = {
    "dkk", "dsb", "dst", "dll",
    "hlm", "no", "vol", "hal", "jur",
    "mis", "msl", "spt",
    "prof", "dr", "ir", "drs", "drg",
    "se", "sh", "st",
    "spd", "mkom", "msc", "phd", "spdi",
    "mkes", "msi", "mhum", "mph",
    "vs", "etc", "cf", "fig",
    "pp", "ed", "eds", "rev",
    "dept", "univ", "inst",
    "jan", "feb", "mar", "apr", "mei",
    "jun", "jul", "agt", "sep", "okt", "nov", "des",
}

# Pola gelar bertingkat: S.Pd., M.Kom.
DEGREE_PATTERN = re.compile(
    r"\b([A-Z][a-z]*\.){1,4}[A-Z][a-z]*\.",
    re.UNICODE,
)

# ---------------------------------------------------------------------------
# URL/DOI: cocokkan tapi JANGAN menelan titik penutup kalimat.
# Pola ini menggunakan negative lookbehind untuk titik di akhir token URL.
# Solusi: cocokkan URL tanpa titik di akhir jika diikuti spasi+huruf kapital.
# ---------------------------------------------------------------------------
# URL diakhiri sebelum titik yang diikuti spasi+kapital atau akhir string
URL_PATTERN = re.compile(
    r"(?:https?://|www\.)"
    r"[^\s,;\"'<>\[\](){}]*"
    r"(?<!\.)(?=\s|$)"      # jangan akhiri dengan titik
    r"|"
    r"(?:https?://|www\.)"
    r"[^\s,;\"'<>\[\](){}]+",
    re.IGNORECASE,
)

# DOI: hindari menelan titik penutup kalimat
DOI_PATTERN = re.compile(
    r"\b10\.\d{4,}/[^\s,;\"'<>\[\](){}]*(?<!\.)(?=[\s,;\"'\]\)}>]|$)"
    r"|"
    r"\b10\.\d{4,}/[^\s,;\"'<>\[\](){}]+",
    re.IGNORECASE,
)

EMAIL_PATTERN = re.compile(r"\b[\w.+-]+@[\w-]+\.[a-z]{2,}\b", re.IGNORECASE)
DECIMAL_PATTERN = re.compile(r"\d+[,.]\d+")
ELLIPSIS_PATTERN = re.compile(r"\.{2,}")
LIST_ITEM_PATTERN = re.compile(
    r"(?:^|\s)(?:\(?[0-9]+[.)]\s|\(?[a-zA-Z][.)]\s)",
    re.MULTILINE,
)


# ---------------------------------------------------------------------------
# Proteksi pola non-batas
# ---------------------------------------------------------------------------

def _protect_non_boundaries(text: str) -> Tuple[str, Dict[str, str]]:
    """
    Ganti pola yang mengandung titik tetapi bukan batas kalimat dengan
    placeholder aman. URL/DOI diproteksi tanpa menelan titik penutup kalimat.
    """
    placeholder_map: Dict[str, str] = {}
    counter = [0]

    def _sub(m: re.Match, prefix: str) -> str:
        # Periksa: apakah match diakhiri titik yang seharusnya batas kalimat?
        # Jika matched text berakhir '.', cek apakah itu titik penutup kalimat.
        matched = m.group(0)
        # Titik penutup kalimat: titik diikuti spasi+kapital atau akhir teks
        # Kita hanya buang titik terakhir dari placeholder jika ada indikator ini.
        suffix = ""
        after_pos = m.end()
        if matched.endswith("."):
            # Cek konteks setelah match
            rest = text[after_pos:]
            if rest and (rest[0].isupper() or rest[0].isdigit() or rest.startswith(" ")):
                # Titik ini mungkin adalah penutup kalimat; lepaskan dari match
                matched = matched[:-1]
                suffix = "."
        key = f"__PROT{prefix}{counter[0]}__"
        placeholder_map[key] = matched
        counter[0] += 1
        return key + suffix

    text = URL_PATTERN.sub(lambda m: _sub(m, "URL"), text)
    text = DOI_PATTERN.sub(lambda m: _sub(m, "DOI"), text)
    text = EMAIL_PATTERN.sub(lambda m: _sub(m, "EMAIL"), text)
    text = DECIMAL_PATTERN.sub(lambda m: _sub(m, "NUM"), text)
    text = ELLIPSIS_PATTERN.sub(lambda m: _sub(m, "ELLIP"), text)
    text = DEGREE_PATTERN.sub(lambda m: _sub(m, "DEG"), text)

    return text, placeholder_map


def _restore_placeholders(text: str, placeholder_map: Dict[str, str]) -> str:
    for key, orig in placeholder_map.items():
        text = text.replace(key, orig)
    return text


def _is_abbreviation(token: str) -> bool:
    """
    Periksa apakah token adalah singkatan.
    Hanya singkatan yang langsung diikuti tanda baca atau spasi — bukan
    diikuti langsung oleh huruf kapital (yang menandakan batas kalimat).
    """
    cleaned = token.lower().rstrip(".,;:?!")
    return cleaned in ABBREVIATIONS


# ---------------------------------------------------------------------------
# Segmentasi utama
# ---------------------------------------------------------------------------

def segment_text(text: str) -> List[Dict]:
    """
    Segmentasi teks kerja menjadi daftar kandidat segmen.
    """
    if not text.strip():
        return []

    protected, pmap = _protect_non_boundaries(text)

    # Batas kalimat: ., ?, ! diikuti spasi + huruf kapital/angka/kutip
    sentence_end_pattern = re.compile(
        r"[.?!](?=[ \t]+[A-Z0-9\"\u201c\u2018])",
        re.UNICODE,
    )

    raw_sentences: List[str] = []
    last = 0
    for m in sentence_end_pattern.finditer(protected):
        end_pos = m.end()  # end_pos mencakup tanda baca, tidak termasuk spasi

        # Ambil token sebelum tanda baca
        before = protected[:m.start()].rstrip()
        tokens = before.split()
        last_token = tokens[-1] if tokens else ""

        if _is_abbreviation(last_token):
            continue  # singkatan: bukan batas

        raw_sentences.append(protected[last:m.start() + 1].strip())
        last = m.start() + 1

    remainder = protected[last:].strip()
    if remainder:
        raw_sentences.append(remainder)

    candidates: List[Dict] = []
    for i, sent in enumerate(raw_sentences):
        sent_restored = _restore_placeholders(sent, pmap).strip()
        if not sent_restored:
            continue
        b5 = _detect_b5(sent_restored)
        candidates.append({
            "urutan": len(candidates) + 1,
            "teks_segmen": sent_restored,
            "asal_segmentasi": "skrip",
            "catatan_segmentasi": b5,
        })

    return candidates


def _detect_b5(text: str) -> str:
    """Heuristik deteksi kasus batas B5."""
    notes = []
    words = text.split()

    if len(words) < 3:
        notes.append(
            f"B5-kandidat: fragmen sangat pendek ({len(words)} kata)"
        )
    if LIST_ITEM_PATTERN.match(text):
        notes.append(
            "B5-kandidat: diawali penomor daftar"
        )
    if len(words) == 1 and not text.endswith("."):
        notes.append("B5-kandidat: satu token tanpa tanda baca")

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
    Baca abstrak.csv, segmentasi setiap teks kerja.
    Blokir abstrak berstatus 'duplikat-dekat-ditinjau'.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    abstrak_rows: List[Dict] = []
    n_blokir = 0

    with open(abstrak_path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if peran_filter and row.get("peran_data", "") != peran_filter:
                continue

            status = row.get("status_dedup", "")
            if status == "duplikat-dibuang":
                logger.info(f"Lewati {row['id_abstrak']}: duplikat-dibuang")
                continue

            if status == "duplikat-dekat-ditinjau":
                # BLOKIR sampai ada keputusan review
                logger.error(
                    f"BLOKIR {row['id_abstrak']}: status 'duplikat-dekat-ditinjau'. "
                    "Abstrak ini tidak akan disegmentasi sampai keputusan review "
                    "dicatat di log_dedup.csv (ubah status_dedup menjadi 'unik' "
                    "atau 'duplikat-dibuang' setelah review manual)."
                )
                n_blokir += 1
                continue

            abstrak_rows.append(row)

    if n_blokir > 0:
        logger.warning(
            f"{n_blokir} abstrak diblokir karena belum selesai review duplikat dekat. "
            "Selesaikan review di log_dedup.csv dan perbarui status_dedup di abstrak.csv."
        )

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

        review_path = output_dir / f"review_segmentasi_{id_abstrak}.csv"
        _write_review(review_path, segments, id_abstrak)

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
        "WAJIB memeriksa setiap file review_segmentasi_*.csv sebelum membekukan."
    )


def _write_review(path: Path, segments: List[Dict], id_abstrak: str) -> None:
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
            "disetujui": "",
        })
    _write_csv(path, cols, rows)


def _write_csv(path: Path, cols: List[str], rows: List[Dict]) -> None:
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f, fieldnames=cols, quoting=csv.QUOTE_MINIMAL, extrasaction="ignore"
        )
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Segmentasi kalimat abstrak berbasis aturan (Pedoman 2.3)."
    )
    parser.add_argument("--abstrak", "-a", default="data/processed/abstrak.csv")
    parser.add_argument("--output-dir", "-o", default="data/processed")
    parser.add_argument("--peran-data", "-p", default=None)
    args = parser.parse_args()

    segment_all(
        abstrak_path=Path(args.abstrak),
        output_dir=Path(args.output_dir),
        peran_filter=args.peran_data,
    )


if __name__ == "__main__":
    main()
