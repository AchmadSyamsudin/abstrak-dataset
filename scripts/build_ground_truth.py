#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_ground_truth.py
=====================
Menggabungkan SELURUH segmen dari segmen.csv, hasil anotasi, dan keputusan
adjudikasi untuk menghasilkan dataset ground truth lengkap.

Aturan penggabungan (mengikuti Pedoman v1.0, Bagian 7.3-7.4):
1. Setiap segmen dibekukan di segmen.csv HARUS ada di output.
2. Mode dua anotator:
   Jika kedua anotator sepakat (himpunan label identik) DAN tidak ada flag
   DAN tidak ada TT → label final = konsensus, status = "final",
   sumber_keputusan = "konsensus-dua-anotator".
3. Jika segmen perlu adjudikasi → ambil keputusan dari adjudikasi.csv.
4. Jika segmen memerlukan adjudikasi tetapi belum ada keputusan →
   status = "belum-selesai", error di log.
5. Mode satu anotator (ann2 tidak ada):
   TIDAK ada konsensus dua anotator. Segmen tanpa flag/TT diberi
   sumber_keputusan = "anotator-tunggal" dan HARUS masuk adjudikasi.csv
   untuk divalidasi. Jika belum ada keputusan adjudikasi → belum-selesai.
   KECUALI jika --single-annotator-no-adjudication diberikan secara eksplisit
   (untuk tahap pengembangan/pilot internal).
6. Segmen yang ann1=None (belum dianotasi an1) → belum-selesai.
7. Segmen dikecualikan tetap tercatat tetapi tidak dipakai melatih/menguji model.

Deteksi masalah:
- Segmen di anotasi yang tidak ada di segmen.csv → error
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

Mode satu anotator (hanya untuk pengembangan internal):
    python scripts/build_ground_truth.py \\
        --segmen data/processed/segmen.csv \\
        --anotasi-1 data/processed/anotasi_an1.csv \\
        --adjudikasi data/processed/adjudikasi.csv \\
        --output-dir data/processed
"""

import argparse
import csv
import logging
import sys
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
VALID_LABELS: Set[str] = {"LB", "TJ", "MT", "HS", "SI", "LAINNYA", "TT"}

GT_COLS = [
    "id_abstrak", "id_segmen", "urutan", "teks_segmen",
    "label_an1", "label_an2",
    "label_akhir", "label_alt_sisa",
    "flag_an1", "flag_an2",
    "alasan_an1", "alasan_an2",
    "simpul_an1", "simpul_an2",
    "status_akhir",        # final | batas-sisa | dikecualikan | belum-selesai
    "sumber_keputusan",    # konsensus-dua-anotator | adjudikasi | anotator-tunggal | -
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


def load_segmen(path: Path) -> Tuple[Dict[str, Dict], int]:
    """
    id_segmen -> row; hanya baris yang dibekukan.
    Return: (result_dict, n_fatal_errors)
    ID segmen duplikat adalah FATAL ERROR — berhenti setelah pelaporan.
    """
    result: Dict[str, Dict] = {}
    n_skip = 0
    n_dup = 0
    for row in load_csv(path):
        sid = row.get("id_segmen", "").strip()
        if not sid:
            continue
        status = row.get("status_beku", "").strip().lower()
        if status not in ("disetujui", "beku"):
            logger.warning(
                f"Segmen '{sid}' status_beku='{status}' (bukan 'disetujui'/'beku'), "
                "dilewati dari GT."
            )
            n_skip += 1
            continue
        if sid in result:
            logger.error(
                f"FATAL: ID segmen duplikat di segmen.csv: '{sid}'. "
                "Setiap segmen harus memiliki ID unik. Perbaiki segmen.csv."
            )
            n_dup += 1
        result[sid] = row
    if n_skip:
        logger.warning(f"{n_skip} segmen belum dibekukan, dilewati dari GT.")
    return result, n_dup


def load_anotasi(path: Path) -> Tuple[Dict[str, Dict], int]:
    """
    id_segmen -> row.
    ID segmen duplikat di anotasi adalah FATAL ERROR.
    Return: (result_dict, n_fatal_errors)
    """
    result: Dict[str, Dict] = {}
    n_dup = 0
    for row in load_csv(path):
        sid = row.get("id_segmen", "").strip()
        if not sid:
            continue
        if sid in result:
            logger.error(
                f"FATAL: ID segmen duplikat di {path.name}: '{sid}'. "
                "Satu anotator hanya boleh memiliki satu baris per segmen. "
                "Hapus duplikat sebelum melanjutkan."
            )
            n_dup += 1
        result[sid] = row
    return result, n_dup


def load_adjudikasi(path: Path) -> Tuple[Dict[str, Dict], int]:
    """
    id_segmen -> row keputusan adjudikasi.
    Dua baris apapun (bukan hanya 'final') untuk segmen yang sama adalah FATAL.
    Return: (result_dict, n_fatal_errors)
    """
    result: Dict[str, Dict] = {}
    n_dup = 0
    for row in load_csv(path):
        sid = row.get("id_segmen", "").strip()
        if not sid:
            continue
        if sid in result:
            logger.error(
                f"FATAL: Segmen '{sid}' memiliki lebih dari satu keputusan di adjudikasi.csv. "
                "Hanya satu keputusan per segmen yang diperbolehkan. "
                "Hapus duplikat sebelum melanjutkan."
            )
            n_dup += 1
        result[sid] = row
    return result, n_dup


# ---------------------------------------------------------------------------
# Deteksi kebutuhan adjudikasi (Pedoman 7.3 butir a-c)
# ---------------------------------------------------------------------------

def _parse_label_set(label_str: str) -> frozenset:
    return frozenset(l.strip() for l in label_str.split("+") if l.strip())


def needs_adjudication_two_annotators(ann1: Dict, ann2: Dict) -> Tuple[bool, List[str]]:
    """
    Dua anotator: kembalikan (perlu_adjudikasi, alasan).
    Kondisi (Pedoman 7.3.a-c): label berbeda, ada flag, ada TT, label kosong.
    """
    reasons: List[str] = []
    label1 = ann1.get("label", "").strip()
    label2 = ann2.get("label", "").strip()
    flag1 = ann1.get("flag", "").strip()
    flag2 = ann2.get("flag", "").strip()

    if not label1:
        reasons.append("label-kosong-an1")
    if not label2:
        reasons.append("label-kosong-an2")
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


def needs_adjudication_single_annotator(ann1: Dict) -> Tuple[bool, List[str]]:
    """
    Mode satu anotator: selalu perlu adjudikasi ATAU TT/flag memicu adjudikasi.
    Segmen tanpa flag/TT dikembalikan (True, ["mode-satu-anotator"]) karena
    tidak ada bukti konsensus antaranotator.
    """
    reasons = ["mode-satu-anotator"]
    flag1 = ann1.get("flag", "").strip()
    label1 = ann1.get("label", "")
    if flag1:
        reasons.append(f"flag-an1={flag1}")
    if "TT" in label1.split("+"):
        reasons.append("label-TT-an1")
    return True, reasons


# ---------------------------------------------------------------------------
# Build GT
# ---------------------------------------------------------------------------

def build_ground_truth(
    segmen_map: Dict[str, Dict],
    anotasi1: Dict[str, Dict],
    anotasi2: Optional[Dict[str, Dict]],
    adjudikasi: Dict[str, Dict],
    single_annotator_no_adj: bool = False,
) -> Tuple[List[Dict], Dict[str, int]]:
    """
    Gabungkan semua sumber data menjadi ground truth.

    single_annotator_no_adj=True: khusus pengembangan internal (Pilot 1/data-pengembangan).
    Jangan gunakan untuk korpus anotasi sesungguhnya.

    Return: (gt_rows, stats_counter)
    """
    mode_dua_anotator = anotasi2 is not None

    gt_rows: List[Dict] = []
    stats: Dict[str, int] = defaultdict(int)
    n_error = 0

    # Periksa segmen di anotasi yang tidak ada di segmen.csv (anotasi yatim)
    n_orphan = 0
    all_ann_ids = set(anotasi1.keys())
    if anotasi2:
        all_ann_ids |= set(anotasi2.keys())
    for sid in sorted(all_ann_ids):
        if sid not in segmen_map:
            logger.error(
                f"FATAL: ID segmen '{sid}' ada di anotasi tetapi tidak di segmen.csv. "
                "Anotasi yatim ini tidak diakui. Perbaiki anotasi atau segmen.csv."
            )
            n_orphan += 1
    n_error += n_orphan

    # Proses setiap segmen yang dibekukan
    for sid in sorted(segmen_map.keys()):
        seg = segmen_map[sid]
        id_abstrak = seg.get("id_abstrak", "")
        urutan = seg.get("urutan", "")
        teks = seg.get("teks_segmen", "")

        ann1 = anotasi1.get(sid)
        ann2 = anotasi2.get(sid) if anotasi2 else None

        label_an1 = ann1.get("label", "") if ann1 else ""
        label_an2 = ann2.get("label", "") if ann2 else ""
        flag_an1 = ann1.get("flag", "") if ann1 else ""
        flag_an2 = ann2.get("flag", "") if ann2 else ""
        alasan_an1 = ann1.get("alasan", "") if ann1 else ""
        alasan_an2 = ann2.get("alasan", "") if ann2 else ""
        simpul_an1 = ann1.get("simpul_penentu", "") if ann1 else ""
        simpul_an2 = ann2.get("simpul_penentu", "") if ann2 else ""
        versi = ann1.get("versi_pedoman", "v1.0") if ann1 else "v1.0"

        # Segmen belum dianotasi oleh an1
        if ann1 is None:
            logger.error(
                f"Segmen '{sid}' tidak ada di anotasi_1. "
                "Status: belum-selesai."
            )
            n_error += 1
            gt_rows.append({
                "id_abstrak": id_abstrak, "id_segmen": sid,
                "urutan": urutan, "teks_segmen": teks,
                "label_an1": "", "label_an2": label_an2,
                "label_akhir": "", "label_alt_sisa": "",
                "flag_an1": "", "flag_an2": flag_an2,
                "alasan_an1": "", "alasan_an2": alasan_an2,
                "simpul_an1": "", "simpul_an2": simpul_an2,
                "status_akhir": "belum-selesai",
                "sumber_keputusan": "-",
                "adjudikator_id": "", "alasan_adjudikasi": "",
                "versi_pedoman": versi,
                "catatan_gt": "Segmen belum dianotasi oleh anotator 1.",
            })
            stats["belum-selesai"] += 1
            continue

        # Mode dua anotator: an2 tidak ada untuk segmen ini → warning
        if mode_dua_anotator and ann2 is None:
            logger.warning(
                f"Segmen '{sid}' tidak ada di anotasi_2. "
                "Segmen ini tidak dapat memiliki konsensus dua anotator."
            )

        # Tentukan apakah perlu adjudikasi
        if mode_dua_anotator and ann2 is not None:
            perlu_adj, reasons = needs_adjudication_two_annotators(ann1, ann2)
        elif mode_dua_anotator and ann2 is None:
            # an2 ada di mode tapi tidak menganotasi segmen ini
            perlu_adj = True
            reasons = ["anotator-2-tidak-menganotasi-segmen-ini"]
        else:
            # Mode satu anotator
            if single_annotator_no_adj:
                # Hanya untuk pengembangan internal (Pilot 1)
                perlu_adj = bool(flag_an1 or "TT" in label_an1.split("+"))
                reasons = []
                if flag_an1:
                    reasons.append(f"flag-an1={flag_an1}")
                if "TT" in label_an1.split("+"):
                    reasons.append("label-TT-an1")
            else:
                perlu_adj, reasons = needs_adjudication_single_annotator(ann1)

        # Validasi label an1 sebelum konsensus dapat ditetapkan
        if ann1 and label_an1:
            label_parts_an1 = {l.strip() for l in label_an1.split("+") if l.strip()}
            invalid_an1 = label_parts_an1 - VALID_LABELS
            if invalid_an1:
                logger.error(
                    f"Segmen '{sid}': label_an1 mengandung nilai tidak valid: "
                    f"{sorted(invalid_an1)}. Segmen tidak dapat ditetapkan konsensus."
                )
                perlu_adj = True
                reasons = [f"label-tidak-valid-an1={invalid_an1}"]

        if ann2 and label_an2:
            label_parts_an2 = {l.strip() for l in label_an2.split("+") if l.strip()}
            invalid_an2 = label_parts_an2 - VALID_LABELS
            if invalid_an2:
                logger.error(
                    f"Segmen '{sid}': label_an2 mengandung nilai tidak valid: "
                    f"{sorted(invalid_an2)}. Segmen tidak dapat ditetapkan konsensus."
                )
                perlu_adj = True
                reasons = [f"label-tidak-valid-an2={invalid_an2}"]

        # Label kosong: segmen belum dianotasi dengan benar
        if ann1 and not label_an1:
            logger.error(
                f"Segmen '{sid}': label_an1 KOSONG. Label kosong tidak dapat "
                "menjadi konsensus. Segmen dinyatakan belum-selesai."
            )
            n_error += 1
            gt_rows.append({
                "id_abstrak": id_abstrak, "id_segmen": sid,
                "urutan": urutan, "teks_segmen": teks,
                "label_an1": label_an1, "label_an2": label_an2,
                "label_akhir": "", "label_alt_sisa": "",
                "flag_an1": flag_an1, "flag_an2": flag_an2,
                "alasan_an1": alasan_an1, "alasan_an2": alasan_an2,
                "simpul_an1": simpul_an1, "simpul_an2": simpul_an2,
                "status_akhir": "belum-selesai",
                "sumber_keputusan": "-",
                "adjudikator_id": "", "alasan_adjudikasi": "",
                "versi_pedoman": versi,
                "catatan_gt": "label_an1 kosong; bukan konsensus.",
            })
            stats["belum-selesai"] += 1
            continue

        if mode_dua_anotator and ann2 and not label_an2:
            logger.error(
                f"Segmen '{sid}': label_an2 KOSONG. Label kosong tidak dapat "
                "menjadi konsensus. Segmen dinyatakan belum-selesai."
            )
            n_error += 1
            gt_rows.append({
                "id_abstrak": id_abstrak, "id_segmen": sid,
                "urutan": urutan, "teks_segmen": teks,
                "label_an1": label_an1, "label_an2": label_an2,
                "label_akhir": "", "label_alt_sisa": "",
                "flag_an1": flag_an1, "flag_an2": flag_an2,
                "alasan_an1": alasan_an1, "alasan_an2": alasan_an2,
                "simpul_an1": simpul_an1, "simpul_an2": simpul_an2,
                "status_akhir": "belum-selesai",
                "sumber_keputusan": "-",
                "adjudikator_id": "", "alasan_adjudikasi": "",
                "versi_pedoman": versi,
                "catatan_gt": "label_an2 kosong; bukan konsensus.",
            })
            stats["belum-selesai"] += 1
            continue

        konsensus_dua = (not perlu_adj and mode_dua_anotator and ann2 is not None)
        konsensus_satu_internal = (not perlu_adj and not mode_dua_anotator
                                   and single_annotator_no_adj)

        if konsensus_dua or konsensus_satu_internal:
            # KONSENSUS
            sumber = "konsensus-dua-anotator" if konsensus_dua else "anotator-tunggal-internal"
            label_akhir = label_an1
            gt_rows.append({
                "id_abstrak": id_abstrak, "id_segmen": sid,
                "urutan": urutan, "teks_segmen": teks,
                "label_an1": label_an1, "label_an2": label_an2,
                "label_akhir": label_akhir, "label_alt_sisa": "",
                "flag_an1": flag_an1, "flag_an2": flag_an2,
                "alasan_an1": alasan_an1, "alasan_an2": alasan_an2,
                "simpul_an1": simpul_an1, "simpul_an2": simpul_an2,
                "status_akhir": "final",
                "sumber_keputusan": sumber,
                "adjudikator_id": "", "alasan_adjudikasi": "",
                "versi_pedoman": versi,
                "catatan_gt": "",
            })
            stats["final-konsensus"] += 1

        else:
            # Perlu adjudikasi
            adj = adjudikasi.get(sid)

            if adj is None:
                logger.error(
                    f"Segmen '{sid}' memerlukan adjudikasi ({'; '.join(reasons)}) "
                    "tetapi tidak ditemukan di adjudikasi.csv. "
                    "Status: belum-selesai."
                )
                n_error += 1
                gt_rows.append({
                    "id_abstrak": id_abstrak, "id_segmen": sid,
                    "urutan": urutan, "teks_segmen": teks,
                    "label_an1": label_an1, "label_an2": label_an2,
                    "label_akhir": "", "label_alt_sisa": "",
                    "flag_an1": flag_an1, "flag_an2": flag_an2,
                    "alasan_an1": alasan_an1, "alasan_an2": alasan_an2,
                    "simpul_an1": simpul_an1, "simpul_an2": simpul_an2,
                    "status_akhir": "belum-selesai",
                    "sumber_keputusan": "-",
                    "adjudikator_id": "", "alasan_adjudikasi": "",
                    "versi_pedoman": versi,
                    "catatan_gt": f"Perlu adjudikasi: {'; '.join(reasons)}",
                })
                stats["belum-selesai"] += 1

            else:
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

                gt_rows.append({
                    "id_abstrak": id_abstrak, "id_segmen": sid,
                    "urutan": urutan, "teks_segmen": teks,
                    "label_an1": label_an1, "label_an2": label_an2,
                    "label_akhir": adj_label,
                    "label_alt_sisa": adj_label_alt,
                    "flag_an1": flag_an1, "flag_an2": flag_an2,
                    "alasan_an1": alasan_an1, "alasan_an2": alasan_an2,
                    "simpul_an1": simpul_an1, "simpul_an2": simpul_an2,
                    "status_akhir": adj_status,
                    "sumber_keputusan": "adjudikasi",
                    "adjudikator_id": adj.get("adjudikator_id", ""),
                    "alasan_adjudikasi": adj.get("alasan", ""),
                    "versi_pedoman": versi,
                    "catatan_gt": f"Alasan adjudikasi: {'; '.join(reasons)}",
                })
                stats[adj_status] += 1

    if n_error > 0:
        logger.error(
            f"{n_error} segmen memiliki error serius (belum-selesai atau fatal). "
            "Hitung kelengkapan TIDAK boleh dijalankan sampai semua segmen selesai."
        )

    stats["n_error"] = n_error
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
    parser.add_argument(
        "--single-annotator-no-adjudication",
        action="store_true",
        default=False,
        help=(
            "Mode pengembangan internal: segmen satu anotator tanpa flag/TT "
            "diterima sebagai final tanpa adjudikasi. "
            "JANGAN gunakan untuk korpus anotasi sesungguhnya."
        ),
    )
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    n_fatal = 0

    segmen_map, n_seg_dup = load_segmen(Path(args.segmen))
    n_fatal += n_seg_dup

    anotasi1, n_ann1_dup = load_anotasi(Path(args.anotasi_1))
    n_fatal += n_ann1_dup

    anotasi2 = None
    if args.anotasi_2:
        anotasi2_raw, n_ann2_dup = load_anotasi(Path(args.anotasi_2))
        n_fatal += n_ann2_dup
        anotasi2 = anotasi2_raw

    adjudikasi, n_adj_dup = load_adjudikasi(Path(args.adjudikasi))
    n_fatal += n_adj_dup

    if n_fatal > 0:
        msg = (
            f"FATAL ERROR: {n_fatal} error fatal ditemukan pada input "
            "(duplikat ID segmen/anotasi atau keputusan adjudikasi ganda). "
            "Proses dihentikan tanpa menghasilkan ground_truth.csv."
        )
        logger.error(msg)
        lap_path = output_dir / "laporan_ground_truth.txt"
        with open(lap_path, "w", encoding="utf-8") as f:
            f.write(
                "=" * 60 + "\n"
                + "LAPORAN GROUND TRUTH (GAGAL)\n"
                + "=" * 60 + "\n"
                + msg + "\n"
            )
        sys.exit(1)

    if not segmen_map:
        msg = "FATAL ERROR: Tidak ada segmen yang dibekukan di segmen.csv."
        logger.error(msg)
        lap_path = output_dir / "laporan_ground_truth.txt"
        with open(lap_path, "w", encoding="utf-8") as f:
            f.write(
                "=" * 60 + "\n"
                + "LAPORAN GROUND TRUTH (GAGAL)\n"
                + "=" * 60 + "\n"
                + msg + "\n"
            )
        sys.exit(1)

    if args.single_annotator_no_adjudication:
        logger.warning(
            "MODE PENGEMBANGAN INTERNAL: --single-annotator-no-adjudication aktif. "
            "Segmen tanpa flag/TT dari satu anotator diterima tanpa adjudikasi. "
            "JANGAN gunakan ini untuk korpus anotasi Pilot 2 atau korpus sesungguhnya."
        )

    gt_rows, stats = build_ground_truth(
        segmen_map=segmen_map,
        anotasi1=anotasi1,
        anotasi2=anotasi2,
        adjudikasi=adjudikasi,
        single_annotator_no_adj=args.single_annotator_no_adjudication,
    )
    n_error = stats.get("n_error", 0) + stats.get("belum-selesai", 0)

    gt_path = output_dir / "ground_truth.csv"
    with open(gt_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f, fieldnames=GT_COLS, quoting=csv.QUOTE_MINIMAL, extrasaction="ignore"
        )
        writer.writeheader()
        writer.writerows(gt_rows)
    logger.info(f"ground_truth.csv ditulis: {gt_path} ({len(gt_rows)} baris)")

    n_total = len(gt_rows)
    laporan_lines = [
        "=" * 60,
        "LAPORAN GROUND TRUTH",
        "=" * 60,
        f"Total segmen              : {n_total}",
        f"Final (konsensus)         : {stats.get('final-konsensus', 0)}",
        f"Final (adjudikasi)        : {stats.get('final', 0)}",
        f"Batas-sisa                : {stats.get('batas-sisa', 0)}",
        f"Dikecualikan              : {stats.get('dikecualikan', 0)}",
        f"BELUM SELESAI             : {stats.get('belum-selesai', 0)}",
        "",
    ]
    if n_error > 0:
        laporan_lines.append(
            f"ERROR: {n_error} segmen belum-selesai. "
            "Jangan hitung kelengkapan sampai semua selesai."
        )
    else:
        laporan_lines.append(
            "Semua segmen telah selesai. Ground truth siap digunakan."
        )

    lap_path = output_dir / "laporan_ground_truth.txt"
    with open(lap_path, "w", encoding="utf-8") as f:
        f.write("\n".join(laporan_lines))
    logger.info(f"Laporan ditulis: {lap_path}")

    if n_error > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
