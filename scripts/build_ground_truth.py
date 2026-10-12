#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_ground_truth.py
=====================
Menggabungkan SELURUH segmen dari segmen.csv, hasil anotasi kedua anotator,
dan keputusan adjudikasi untuk menghasilkan dataset ground truth lengkap.

Aturan penggabungan:
1. Setiap segmen dalam segmen.csv yang sudah dibekukan HARUS ada di output.
2. Jika kedua anotator sepakat (himpunan label identik) DAN tidak ada flag
   DAN tidak ada TT → label final = konsensus, status = "final".
3. Jika segmen masuk antrean adjudikasi → ambil keputusan dari adjudikasi.csv.
4. Jika segmen memerlukan adjudikasi tetapi belum ada keputusan → status = "belum-selesai",
   laporan error, segmen TIDAK dianggap selesai.
5. Segmen dikecualikan tetap tercatat dengan status_akhir = "dikecualikan".
6. TT yang belum diselesaikan tetap TT; tidak diganti otomatis.

Deteksi masalah:
- Segmen di anotasi yang tidak ada di segmen.csv → error
- Segmen di segmen.csv yang tidak ada di anotasi salah satu anotator → warning
- ID segmen duplikat → error
- Segmen yang butuh adjudikasi tanpa keputusan → error (output "belum-selesai")

Output:
- ground_truth.csv (satu baris per segmen, semua status)
- laporan_ground_truth.txt (ringkasan jumlah per status)

Penggunaan:
    python scripts/build_ground_truth.py \\
        --segmen data/processed/segmen.csv \\
        --anotasi-1 data/processed/anotasi_an1.csv \\
        --anotasi-2 data/processed/anotasi_an2.csv \\
        --adjudikasi data/processed/adjudikasi.csv \\
        --output-dir data/processed
"""

import argparse
import csv
import logging
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("build_ground_truth")

VALID_STATUS_AKHIR: Set[str] = {"final", "batas-sisa", "dikecualikan"}

GT_COLS = [
    "id_abstrak", "id_segmen", "urutan", "teks_segmen",
    "label_an1", "label_an2",
    "label_akhir", "label_alt_sisa",
    "flag_an1", "flag_an2",
    "alasan_an1", "alasan_an2",
    "simpul_an1", "simpul_an2",
    "status_akhir",        # final | batas-sisa | dikecualikan | belum-selesai
    "sumber_keputusan",    # konsensus | adjudikasi | -
    "adjudikator_id",
    "alasan_adjudikasi",
    "versi_pedoman",
    "catatan_gt",
]


# ---------------------------------------------------------------------------
# Loader
# ---------------------------------------------------------------------------

def load_csv(path: Path) -> List[Dict]:
    with open(path, "r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def load_segmen(path: Path) -> Dict[str, Dict]:
    """id_segmen -> row; hanya baris yang dibekukan."""
    result: Dict[str, Dict] = {}
    for row in load_csv(path):
        sid = row.get("id_segmen", "").strip()
        if not sid:
            continue
        status = row.get("status_beku", "").strip().lower()
        if status not in ("disetujui", "beku"):
            logger.warning(
                f"Segmen '{sid}' belum berstatus disetujui/beku, dilewati dari GT."
            )
            continue
        if sid in result:
            logger.error(f"ID segmen duplikat di segmen.csv: '{sid}'")
        result[sid] = row
    return result


def load_anotasi(path: Path) -> Dict[str, Dict]:
    """id_segmen -> row (terakhir jika duplikat, dengan peringatan)."""
    result: Dict[str, Dict] = {}
    for row in load_csv(path):
        sid = row.get("id_segmen", "").strip()
        if not sid:
            continue
        if sid in result:
            logger.warning(
                f"ID segmen duplikat di {path.name}: '{sid}'. Hanya yang terakhir disimpan."
            )
        result[sid] = row
    return result


def load_adjudikasi(path: Path) -> Dict[str, Dict]:
    """id_segmen -> row keputusan adjudikasi terakhir."""
    result: Dict[str, Dict] = {}
    for row in load_csv(path):
        sid = row.get("id_segmen", "").strip()
        if not sid:
            continue
        if sid in result:
            # Cek apakah ada dua "final" untuk segmen yang sama
            if result[sid].get("status_akhir", "") == "final" and \
               row.get("status_akhir", "") == "final":
                logger.error(
                    f"ATURAN 14: Segmen '{sid}' memiliki dua keputusan 'final' "
                    "di adjudikasi.csv. Hanya satu yang diperbolehkan."
                )
        result[sid] = row
    return result


# ---------------------------------------------------------------------------
# Deteksi kebutuhan adjudikasi (sama dengan build_adjudication_queue.py)
# ---------------------------------------------------------------------------

def _parse_label_set(label_str: str) -> frozenset:
    return frozenset(l.strip() for l in label_str.split("+") if l.strip())


def needs_adjudication(ann1: Dict, ann2: Optional[Dict]) -> Tuple[bool, List[str]]:
    """
    Kembalikan (perlu_adjudikasi, alasan).
    Kondisi: label berbeda, ada flag, ada TT.
    """
    reasons: List[str] = []

    label1 = ann1.get("label", "")
    flag1 = ann1.get("flag", "").strip()

    if ann2 is None:
        if "TT" in label1.split("+"):
            reasons.append("label-TT-an1")
        if flag1:
            reasons.append(f"flag-an1={flag1}")
        return bool(reasons), reasons

    label2 = ann2.get("label", "")
    flag2 = ann2.get("flag", "").strip()

    if _parse_label_set(label1) != _parse_label_set(label2):
        reasons.append(f"label-berbeda ({label1} vs {label2})")
    if flag1:
        reasons.append(f"flag-an1={flag1}")
    if flag2:
        reasons.append(f"flag-an2={flag2}")
    if "TT" in label1.split("+"):
        reasons.append("label-TT-an1")
    if "TT" in label2.split("+"):
        reasons.append("label-TT-an2")

    return bool(reasons), reasons


# ---------------------------------------------------------------------------
# Build GT
# ---------------------------------------------------------------------------

def build_ground_truth(
    segmen_map: Dict[str, Dict],
    anotasi1: Dict[str, Dict],
    anotasi2: Optional[Dict[str, Dict]],
    adjudikasi: Dict[str, Dict],
) -> Tuple[List[Dict], Dict[str, int]]:
    """
    Gabungkan semua sumber data menjadi ground truth.
    Return: (gt_rows, stats_counter)
    """
    gt_rows: List[Dict] = []
    stats: Dict[str, int] = defaultdict(int)
    n_error = 0

    # Periksa segmen di anotasi yang tidak ada di segmen.csv
    all_ann_ids = set(anotasi1.keys())
    if anotasi2:
        all_ann_ids |= set(anotasi2.keys())
    for sid in sorted(all_ann_ids):
        if sid not in segmen_map:
            logger.error(
                f"ID segmen '{sid}' ada di anotasi tetapi tidak di segmen.csv "
                "(belum dibekukan atau tidak dikenali). Diabaikan dari GT."
            )

    # Proses setiap segmen yang dibekukan
    for sid in sorted(segmen_map.keys()):
        seg = segmen_map[sid]
        id_abstrak = seg.get("id_abstrak", "")
        urutan = seg.get("urutan", "")
        teks = seg.get("teks_segmen", "")

        ann1 = anotasi1.get(sid)
        ann2 = anotasi2.get(sid) if anotasi2 else None

        if ann1 is None:
            logger.warning(
                f"Segmen '{sid}' tidak ada di anotasi_1. "
                "Tidak dapat menghitung konsensus atau adjudikasi."
            )

        label_an1 = ann1.get("label", "") if ann1 else ""
        label_an2 = ann2.get("label", "") if ann2 else ""
        flag_an1 = ann1.get("flag", "") if ann1 else ""
        flag_an2 = ann2.get("flag", "") if ann2 else ""
        alasan_an1 = ann1.get("alasan", "") if ann1 else ""
        alasan_an2 = ann2.get("alasan", "") if ann2 else ""
        simpul_an1 = ann1.get("simpul_penentu", "") if ann1 else ""
        simpul_an2 = ann2.get("simpul_penentu", "") if ann2 else ""
        versi = ann1.get("versi_pedoman", "v1.0") if ann1 else "v1.0"

        perlu_adj, reasons = needs_adjudication(ann1 or {}, ann2)

        if not perlu_adj and ann1 is not None:
            # KONSENSUS: kedua anotator sepakat, tidak ada flag/TT
            label_akhir = label_an1
            gt_row = {
                "id_abstrak": id_abstrak,
                "id_segmen": sid,
                "urutan": urutan,
                "teks_segmen": teks,
                "label_an1": label_an1,
                "label_an2": label_an2,
                "label_akhir": label_akhir,
                "label_alt_sisa": "",
                "flag_an1": flag_an1,
                "flag_an2": flag_an2,
                "alasan_an1": alasan_an1,
                "alasan_an2": alasan_an2,
                "simpul_an1": simpul_an1,
                "simpul_an2": simpul_an2,
                "status_akhir": "final",
                "sumber_keputusan": "konsensus",
                "adjudikator_id": "",
                "alasan_adjudikasi": "",
                "versi_pedoman": versi,
                "catatan_gt": "",
            }
            stats["final-konsensus"] += 1

        else:
            # Perlu adjudikasi — cari di adjudikasi.csv
            adj = adjudikasi.get(sid)

            if adj is None:
                # Belum ada keputusan adjudikasi
                logger.error(
                    f"Segmen '{sid}' memerlukan adjudikasi ({'; '.join(reasons)}) "
                    "tetapi tidak ditemukan di adjudikasi.csv. "
                    "Status: belum-selesai."
                )
                n_error += 1
                gt_row = {
                    "id_abstrak": id_abstrak,
                    "id_segmen": sid,
                    "urutan": urutan,
                    "teks_segmen": teks,
                    "label_an1": label_an1,
                    "label_an2": label_an2,
                    "label_akhir": "",
                    "label_alt_sisa": "",
                    "flag_an1": flag_an1,
                    "flag_an2": flag_an2,
                    "alasan_an1": alasan_an1,
                    "alasan_an2": alasan_an2,
                    "simpul_an1": simpul_an1,
                    "simpul_an2": simpul_an2,
                    "status_akhir": "belum-selesai",
                    "sumber_keputusan": "-",
                    "adjudikator_id": "",
                    "alasan_adjudikasi": "",
                    "versi_pedoman": versi,
                    "catatan_gt": f"Perlu adjudikasi: {'; '.join(reasons)}",
                }
                stats["belum-selesai"] += 1

            else:
                # Ada keputusan adjudikasi
                adj_status = adj.get("status_akhir", "").strip()
                adj_label = adj.get("label_akhir", "").strip()
                adj_label_alt = adj.get("label_alt_sisa", "").strip()

                if adj_status not in VALID_STATUS_AKHIR:
                    logger.error(
                        f"Segmen '{sid}': status_akhir adjudikasi '{adj_status}' "
                        "tidak valid. Diperlakukan sebagai belum-selesai."
                    )
                    adj_status = "belum-selesai"
                    n_error += 1

                if not adj_label and adj_status not in ("dikecualikan",):
                    logger.error(
                        f"Segmen '{sid}': label_akhir kosong di adjudikasi.csv "
                        f"(status='{adj_status}'). Segmen dianggap belum-selesai."
                    )
                    adj_status = "belum-selesai"
                    n_error += 1

                gt_row = {
                    "id_abstrak": id_abstrak,
                    "id_segmen": sid,
                    "urutan": urutan,
                    "teks_segmen": teks,
                    "label_an1": label_an1,
                    "label_an2": label_an2,
                    "label_akhir": adj_label,
                    "label_alt_sisa": adj_label_alt,
                    "flag_an1": flag_an1,
                    "flag_an2": flag_an2,
                    "alasan_an1": alasan_an1,
                    "alasan_an2": alasan_an2,
                    "simpul_an1": simpul_an1,
                    "simpul_an2": simpul_an2,
                    "status_akhir": adj_status,
                    "sumber_keputusan": "adjudikasi",
                    "adjudikator_id": adj.get("adjudikator_id", ""),
                    "alasan_adjudikasi": adj.get("alasan", ""),
                    "versi_pedoman": versi,
                    "catatan_gt": f"Alasan adjudikasi: {'; '.join(reasons)}",
                }
                stats[adj_status] += 1

        gt_rows.append(gt_row)

    if n_error > 0:
        logger.error(
            f"{n_error} segmen memiliki error serius (belum-selesai atau status tidak valid). "
            "Hitung kelengkapan TIDAK boleh dijalankan sampai semua segmen selesai."
        )

    return gt_rows, stats


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Buat ground truth lengkap dari segmen + anotasi + adjudikasi."
    )
    parser.add_argument("--segmen", "-s", required=True,
                        help="Path ke segmen.csv yang sudah dibekukan")
    parser.add_argument("--anotasi-1", required=True,
                        help="Path ke anotasi.csv anotator 1")
    parser.add_argument("--anotasi-2", default=None,
                        help="Path ke anotasi.csv anotator 2 (opsional)")
    parser.add_argument("--adjudikasi", required=True,
                        help="Path ke adjudikasi.csv")
    parser.add_argument("--output-dir", "-o", default="data/processed",
                        help="Direktori output")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    segmen_map = load_segmen(Path(args.segmen))
    anotasi1 = load_anotasi(Path(args.anotasi_1))
    anotasi2 = load_anotasi(Path(args.anotasi_2)) if args.anotasi_2 else None
    adjudikasi = load_adjudikasi(Path(args.adjudikasi))

    if not segmen_map:
        logger.error("Tidak ada segmen yang dibekukan di segmen.csv.")
        return

    gt_rows, stats = build_ground_truth(segmen_map, anotasi1, anotasi2, adjudikasi)

    # Tulis ground_truth.csv
    gt_path = output_dir / "ground_truth.csv"
    with open(gt_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f, fieldnames=GT_COLS, quoting=csv.QUOTE_MINIMAL, extrasaction="ignore"
        )
        writer.writeheader()
        writer.writerows(gt_rows)
    logger.info(f"ground_truth.csv ditulis: {gt_path} ({len(gt_rows)} baris)")

    # Tulis laporan
    n_total = len(gt_rows)
    laporan_lines = [
        "=" * 60,
        "LAPORAN GROUND TRUTH",
        "=" * 60,
        f"Total segmen        : {n_total}",
        f"Final (konsensus)   : {stats.get('final-konsensus', 0)}",
        f"Final (adjudikasi)  : {stats.get('final', 0)}",
        f"Batas-sisa          : {stats.get('batas-sisa', 0)}",
        f"Dikecualikan        : {stats.get('dikecualikan', 0)}",
        f"BELUM SELESAI       : {stats.get('belum-selesai', 0)}",
        "",
    ]
    if stats.get("belum-selesai", 0) > 0:
        laporan_lines.append(
            "PERINGATAN: Ada segmen belum-selesai. "
            "Jangan hitung kelengkapan sampai semua selesai."
        )
    else:
        laporan_lines.append("Semua segmen telah selesai. Ground truth siap digunakan.")

    lap_path = output_dir / "laporan_ground_truth.txt"
    with open(lap_path, "w", encoding="utf-8") as f:
        f.write("\n".join(laporan_lines))
    logger.info(f"Laporan ditulis: {lap_path}")


if __name__ == "__main__":
    main()
