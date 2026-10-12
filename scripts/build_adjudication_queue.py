#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_adjudication_queue.py
============================
Membaca dua file anotasi.csv (satu per anotator) dan membangun
antrean adjudikasi sesuai Bagian 7.3 Pedoman v1.0 dan Bagian 8.5.

Segmen masuk antrean jika:
1. Label atau himpunan label kedua anotator berbeda
2. Salah satu anotator memberikan flag apa pun
3. Salah satu anotator memberikan label TT

Output:
- adjudikasi.csv (antrean adjudikasi kosong untuk diisi adjudikator)

Kolom adjudikasi.csv (Bagian 8.5):
  id_abstrak, id_segmen, label_anotator_1, label_anotator_2,
  label_akhir, label_alt_sisa, status_akhir, konteks_dipakai,
  alasan, adjudikator_id, versi_pedoman, waktu_selesai

Nilai status_akhir yang diperbolehkan: final | batas-sisa | dikecualikan

Sistem TIDAK otomatis memilih label. Adjudikator adalah pihak terpisah
yang membaca konteks dan menetapkan hasil menurut pedoman.

Penggunaan:
    python scripts/build_adjudication_queue.py \
        --anotasi-1 data/processed/anotasi_an1.csv \
        --anotasi-2 data/processed/anotasi_an2.csv \
        --output data/processed/adjudikasi.csv \
        [--tambah-ke adjudikasi_existing.csv]
"""

import argparse
import csv
import logging
import sys
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("build_adjudication_queue")

ADJUDIKASI_COLS = [
    "id_abstrak", "id_segmen",
    "label_anotator_1", "label_anotator_2",
    "flag_anotator_1", "flag_anotator_2",
    "alasan_anotator_1", "alasan_anotator_2",
    "simpul_anotator_1", "simpul_anotator_2",
    "label_alt_anotator_1", "label_alt_anotator_2",
    "penyebab_antrean",
    # Kolom untuk diisi adjudikator (kosong saat generate)
    "label_akhir", "label_alt_sisa",
    "status_akhir", "konteks_dipakai",
    "alasan", "adjudikator_id", "versi_pedoman", "waktu_selesai",
]


def load_anotasi(path: Path) -> Dict[str, Dict]:
    """Muat anotasi.csv ke dict id_segmen -> row."""
    result: Dict[str, Dict] = {}
    with open(path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            seg_id = row.get("id_segmen", "")
            if seg_id in result:
                logger.warning(
                    f"Duplikat id_segmen '{seg_id}' di {path}. "
                    "Hanya yang terakhir disimpan."
                )
            result[seg_id] = row
    return result


def parse_label_set(label_str: str) -> Set[str]:
    """Parse string label '+'-separated menjadi frozenset."""
    return frozenset(l.strip() for l in label_str.split("+") if l.strip())


def determine_queue_reasons(
    ann1: Dict,
    ann2: Optional[Dict],
) -> List[str]:
    """
    Tentukan apakah segmen harus masuk antrean dan mengapa.
    Kembalikan daftar alasan (kosong = tidak perlu adjudikasi).
    """
    reasons: List[str] = []

    label1 = ann1.get("label", "")
    flag1 = ann1.get("flag", "")

    # Jika hanya ada satu anotator (mode satu anotator), hanya periksa flag dan TT
    if ann2 is None:
        if "TT" in label1.split("+"):
            reasons.append("label-TT-an1")
        if flag1.strip():
            reasons.append(f"flag-an1={flag1.strip()}")
        return reasons

    label2 = ann2.get("label", "")
    flag2 = ann2.get("flag", "")

    # Aturan 1: label kosong atau berbeda
    if not label1.strip():
        reasons.append("label-kosong-an1")
    if not label2.strip():
        reasons.append("label-kosong-an2")
    set1 = parse_label_set(label1)
    set2 = parse_label_set(label2)
    if set1 != set2:
        reasons.append(f"label-berbeda ({label1} vs {label2})")

    # Aturan 2: salah satu memberi flag
    if flag1.strip():
        reasons.append(f"flag-an1={flag1.strip()}")
    if flag2.strip():
        reasons.append(f"flag-an2={flag2.strip()}")

    # Aturan 3: salah satu memberi TT
    if "TT" in label1.split("+"):
        reasons.append("label-TT-an1")
    if "TT" in label2.split("+"):
        reasons.append("label-TT-an2")

    return reasons


def build_queue(
    anotasi1: Dict[str, Dict],
    anotasi2: Optional[Dict[str, Dict]],
    existing_ids: Set[str],
) -> List[Dict]:
    """
    Bangun antrean adjudikasi.
    Jika anotasi2 = None (mode satu anotator), hanya periksa flag dan TT.
    Jangan tambahkan segmen yang sudah ada di antrean existing.
    """
    queue: List[Dict] = []
    all_seg_ids: Set[str] = set(anotasi1.keys())
    if anotasi2:
        all_seg_ids |= set(anotasi2.keys())

    for seg_id in sorted(all_seg_ids):
        if seg_id in existing_ids:
            continue

        ann1 = anotasi1.get(seg_id)
        ann2 = anotasi2.get(seg_id) if anotasi2 else None

        if ann1 is None:
            logger.warning(
                f"Segmen '{seg_id}' ada di anotasi_2 tetapi tidak di anotasi_1. "
                "Ditambahkan ke antrean untuk pemeriksaan."
            )
            reasons = ["segmen-hanya-an2"]
        else:
            reasons = determine_queue_reasons(ann1, ann2)

        if not reasons:
            continue  # Tidak perlu adjudikasi

        row: Dict = {
            "id_abstrak": (ann1 or ann2).get("id_abstrak", ""),
            "id_segmen": seg_id,
            "label_anotator_1": ann1.get("label", "") if ann1 else "",
            "label_anotator_2": ann2.get("label", "") if ann2 else "",
            "flag_anotator_1": ann1.get("flag", "") if ann1 else "",
            "flag_anotator_2": ann2.get("flag", "") if ann2 else "",
            "alasan_anotator_1": ann1.get("alasan", "") if ann1 else "",
            "alasan_anotator_2": ann2.get("alasan", "") if ann2 else "",
            "simpul_anotator_1": ann1.get("simpul_penentu", "") if ann1 else "",
            "simpul_anotator_2": ann2.get("simpul_penentu", "") if ann2 else "",
            "label_alt_anotator_1": ann1.get("label_alt", "") if ann1 else "",
            "label_alt_anotator_2": ann2.get("label_alt", "") if ann2 else "",
            "penyebab_antrean": "; ".join(reasons),
            # Kosong, diisi adjudikator
            "label_akhir": "",
            "label_alt_sisa": "",
            "status_akhir": "",
            "konteks_dipakai": "",
            "alasan": "",
            "adjudikator_id": "",
            "versi_pedoman": "v1.0",
            "waktu_selesai": "",
        }
        queue.append(row)

    return queue


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Buat antrean adjudikasi dari dua file anotasi."
    )
    parser.add_argument("--anotasi-1", required=True, help="Path anotasi.csv anotator 1")
    parser.add_argument("--anotasi-2", default=None, help="Path anotasi.csv anotator 2 (opsional)")
    parser.add_argument("--output", required=True, help="Path output adjudikasi.csv")
    parser.add_argument(
        "--tambah-ke",
        default=None,
        help="Path adjudikasi.csv yang sudah ada; segmen yang sudah ada tidak ditambahkan ulang",
    )
    args = parser.parse_args()

    anotasi1 = load_anotasi(Path(args.anotasi_1))
    anotasi2 = load_anotasi(Path(args.anotasi_2)) if args.anotasi_2 else None

    # Muat existing adjudikasi untuk cegah duplikat
    existing_ids: Set[str] = set()
    existing_rows: List[Dict] = []
    output_path = Path(args.output)

    if args.tambah_ke and Path(args.tambah_ke).exists():
        existing_rows = []
        with open(Path(args.tambah_ke), "r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                existing_rows.append(row)
                existing_ids.add(row.get("id_segmen", ""))
        logger.info(f"Memuat {len(existing_ids)} segmen yang sudah ada di antrean adjudikasi.")
    elif output_path.exists():
        # Jika output sudah ada dan tidak ada --tambah-ke, cegah penimpaan
        logger.error(
            f"File output sudah ada: {output_path}. "
            "Gunakan --tambah-ke untuk menggabungkan, atau hapus file lama terlebih dahulu."
        )
        sys.exit(1)

    new_queue = build_queue(anotasi1, anotasi2, existing_ids)

    # Statistik
    n_total = len(anotasi1)
    n_match = sum(
        1 for seg_id in anotasi1
        if anotasi2 and parse_label_set(anotasi1[seg_id].get("label", "")) ==
        parse_label_set(anotasi2.get(seg_id, {}).get("label", ""))
        and not anotasi1[seg_id].get("flag", "")
        and not (anotasi2.get(seg_id, {}) or {}).get("flag", "")
        and "TT" not in anotasi1[seg_id].get("label", "").split("+")
    )

    logger.info(
        f"Total segmen anotator 1: {n_total} | "
        f"Sepakat (tanpa flag/TT): {n_match} | "
        f"Masuk antrean baru: {len(new_queue)} | "
        f"Sudah di antrean: {len(existing_ids)}"
    )

    # Gabung dan tulis
    all_rows = existing_rows + new_queue
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f, fieldnames=ADJUDIKASI_COLS, quoting=csv.QUOTE_MINIMAL, extrasaction="ignore"
        )
        writer.writeheader()
        writer.writerows(all_rows)

    logger.info(f"adjudikasi.csv ditulis: {output_path} ({len(all_rows)} baris)")
    logger.info(
        "PERINGATAN: Adjudikator WAJIB membaca seluruh abstrak dan pedoman v1.0 "
        "sebelum mengisi kolom label_akhir, status_akhir, dll. "
        "Sistem tidak memilih label secara otomatis."
    )


if __name__ == "__main__":
    main()
