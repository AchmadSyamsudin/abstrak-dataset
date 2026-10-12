#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
calculate_completeness.py
==========================
Menghitung vektor kelengkapan abstrak dari GROUND TRUTH LENGKAP (ground_truth.csv),
sesuai Bagian 6 Pedoman v1.0 (dibekukan 2026-10-11).

INPUT: ground_truth.csv (output build_ground_truth.py)
BUKAN lagi adjudikasi.csv — hal ini memastikan segmen konsensus yang tidak
masuk antrean adjudikasi tetap dihitung.

Implementasi aturan K1–K8 (Bagian 6.3):
──────────────────────────────────────────
K1. Yang dihitung adalah label_akhir (data emas). Label alternatif hanya
    dipakai pada v-min dan v-maks (K5).
K2. Segmen berlabel ganda menyumbang semua labelnya ke v.
K3. LAINNYA dan segmen dikecualikan tidak menyumbang v utama.
    Label TT harus sudah diselesaikan lewat adjudikasi sebelum vektor dihitung.
K4. LENGKAP ⟺ v = (1,1,1,1,1). Selain itu TIDAK LENGKAP.
K5. Dua vektor tambahan dihitung secara simetris:
    • Segmen final: satu pembacaan = {label_akhir_komponen}
    • Segmen batas-sisa: pembacaan = [{label_akhir}] + [satu untuk tiap label_alt]
    • Segmen dikecualikan: pembacaan = [∅] + [satu untuk tiap label kandidat]
      (pembacaan tanpa label mewakili "mungkin tidak ada komponen sama sekali")
    v-min[k] = 1 jika ada SEGMEN yang memuat k pada SETIAP pembacaannya
    v-maks[k] = 1 jika ada SEGMEN yang memuat k pada SEKURANG-KURANGNYA
                satu pembacaannya
    Jika v-min == v-maks: status pasti; jika berbeda: TAK PASTI.
K6. Abstrak tanpa HS → HS=0 → TIDAK LENGKAP.
K7. Satu segmen cukup untuk satu komponen.
K8. Satuan: satu abstrak.

Penghentian metrik (HARD STOP per abstrak):
──────────────────────────────────────────
• Segmen berstatus 'belum-selesai' di ground truth → abstrak ditandai
  BLOKIR-BELUMSELESAI dan TIDAK MASUK kelengkapan_abstrak.csv sama sekali
  (kecuali dengan --include-incomplete).
• Label TT yang belum diselesaikan di label_akhir → abstrak ditandai
  BLOKIR-TT dan TIDAK MASUK metrik utama.
• Keduanya dilaporkan terpisah di laporan_kelengkapan_error.csv.

Output:
- kelengkapan_abstrak.csv      — abstrak yang dapat dihitung (pasti & TAK PASTI)
- laporan_kelengkapan_error.csv — abstrak yang diblokir (BLOKIR-TT, BLOKIR-BELUMSELESAI)
- ringkasan_kelengkapan.txt

Penggunaan:
    python scripts/calculate_completeness.py \\
        --ground-truth data/processed/ground_truth.csv \\
        --abstrak data/processed/abstrak.csv \\
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
logger = logging.getLogger("calculate_completeness")

KOMPONEN: List[str] = ["LB", "TJ", "MT", "HS", "SI"]

# Status segmen yang valid dari ground_truth.csv
VALID_STATUS_GT: Set[str] = {"final", "batas-sisa", "dikecualikan", "belum-selesai"}

KELENGKAPAN_COLS = [
    "id_abstrak", "jenis_studi", "peran_data",
    "v_LB", "v_TJ", "v_MT", "v_HS", "v_SI",
    "vektor", "status", "komponen_hilang",
    "vmin_LB", "vmin_TJ", "vmin_MT", "vmin_HS", "vmin_SI",
    "vmaks_LB", "vmaks_TJ", "vmaks_MT", "vmaks_HS", "vmaks_SI",
    "vmin_vektor", "vmaks_vektor",
    "status_kepastian",
    "catatan",
]

ERROR_COLS = [
    "id_abstrak", "jenis_studi", "peran_data",
    "status_blokir", "catatan",
]


# ---------------------------------------------------------------------------
# Loader
# ---------------------------------------------------------------------------

def load_csv(path: Path) -> List[Dict]:
    with open(path, "r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def load_abstrak(path: Path) -> Dict[str, Dict]:
    result = {}
    for row in load_csv(path):
        aid = row.get("id_abstrak", "")
        if aid:
            result[aid] = row
    return result


# ---------------------------------------------------------------------------
# Parsing label
# ---------------------------------------------------------------------------

def parse_labels(label_str: str) -> Set[str]:
    """Parse '+'-separated label menjadi set."""
    return {l.strip() for l in label_str.split("+") if l.strip()}


def parse_label_alt_readings(label_alt_str: str) -> List[Set[str]]:
    """
    Parse label_alt menjadi daftar himpunan pembacaan alternatif.
    Setiap alternatif dipisah ';'; tiap alternatif bisa label ganda ('+').
    """
    readings: List[Set[str]] = []
    for part in label_alt_str.split(";"):
        part = part.strip()
        if not part:
            continue
        readings.append(parse_labels(part))
    return readings


# ---------------------------------------------------------------------------
# K5: pembacaan per segmen
# ---------------------------------------------------------------------------

def get_segment_readings(
    label_akhir_str: str,
    label_alt_str: str,
    status: str,
) -> List[Set[str]]:
    """
    Tentukan SEMUA pembacaan sah untuk satu segmen sesuai K5 Pedoman v1.0.

    Segmen final:
        satu pembacaan = {komponen dari label_akhir}

    Segmen batas-sisa:
        pembacaan = [{label_akhir_komponen}]
                  + [{tiap label_alt_komponen}]

    Segmen dikecualikan:
        pembacaan = [∅]  (pembacaan tanpa label — tidak ada yang dapat dipastikan)
                  + [{tiap label_kandidat_komponen dari label_alt}]
        Catatan: pembacaan ∅ memastikan v-min untuk segmen ini selalu 0
        untuk semua komponen (irisan dengan {} = {}).

    Hanya komponen dalam KOMPONEN (LB, TJ, MT, HS, SI) yang dipertahankan.
    """
    label_akhir_komp = {l for l in parse_labels(label_akhir_str) if l in KOMPONEN}

    if status == "dikecualikan":
        # Pembacaan pertama: himpunan kosong (tidak ada komponen yang pasti)
        readings: List[Set[str]] = [set()]
        # Tambahkan tiap label kandidat dari label_alt sebagai pembacaan alternatif
        for alt_set in parse_label_alt_readings(label_alt_str):
            alt_komp = {l for l in alt_set if l in KOMPONEN}
            readings.append(alt_komp)
        return readings

    if status == "batas-sisa":
        readings = [label_akhir_komp]
        for alt_set in parse_label_alt_readings(label_alt_str):
            alt_komp = {l for l in alt_set if l in KOMPONEN}
            readings.append(alt_komp)
        return readings

    # Status final (atau status lain yang tidak dikenali): satu pembacaan
    return [label_akhir_komp]


def segment_vmin_vmaks(readings: List[Set[str]]) -> Tuple[Set[str], Set[str]]:
    """
    Hitung v-min dan v-maks untuk satu segmen dari daftar pembacaan.

    v-min (segmen) = ∩ semua pembacaan — komponen yang hadir di SETIAP pembacaan.
    v-maks (segmen) = ∪ semua pembacaan — komponen yang hadir di MINIMAL satu pembacaan.

    Jika tidak ada pembacaan: kembalikan (∅, ∅).
    """
    if not readings:
        return set(), set()
    vmin = readings[0].copy()
    for r in readings[1:]:
        vmin &= r
    vmaks: Set[str] = set()
    for r in readings:
        vmaks |= r
    return vmin, vmaks


# ---------------------------------------------------------------------------
# Struktur data kelengkapan per abstrak
# ---------------------------------------------------------------------------

class AbstractCompleteness:
    """
    Akumulasi vektor kelengkapan untuk satu abstrak.

    Agregasi v-min antar-segmen (K5):
        v-min_abstrak[k] = 1 jika ADA segmen yang memuat k di SETIAP pembacaannya.
        → Ini adalah UNION dari v-min_segmen atas semua segmen.
        Implementasi: v-min_abstrak[k] = max(v-min_segmen[k]) untuk semua segmen.

    Agregasi v-maks antar-segmen (K5):
        v-maks_abstrak[k] = 1 jika ADA segmen yang memuat k di MINIMAL satu pembacaannya.
        → Ini adalah UNION dari v-maks_segmen atas semua segmen.
        Implementasi: v-maks_abstrak[k] = max(v-maks_segmen[k]) untuk semua segmen.
    """

    def __init__(self, id_abstrak: str):
        self.id_abstrak = id_abstrak
        # v utama (dari label_akhir, K1)
        self.v: Dict[str, int] = {k: 0 for k in KOMPONEN}
        # v-min: union dari vmin per segmen (K5)
        self.vmin: Dict[str, int] = {k: 0 for k in KOMPONEN}
        # v-maks: union dari vmaks per segmen (K5)
        self.vmaks: Dict[str, int] = {k: 0 for k in KOMPONEN}
        self.catatan: List[str] = []
        # Flag penghentian keras
        self.has_unresolved_tt: bool = False    # label_akhir masih TT
        self.has_pending_segments: bool = False  # status belum-selesai
        # Flag untuk menentukan kepastian
        self.has_uncertain_segments: bool = False  # batas-sisa atau dikecualikan

    def update_from_segment(self, readings: List[Set[str]], status: str) -> None:
        """
        Update v, v-min, v-maks dari satu segmen.

        v hanya dari readings[0] (label_akhir sesuai K1).
        v-min dan v-maks: union ke seluruh abstrak.
        """
        if not readings:
            return

        # v utama: dari pembacaan pertama saja (K1 — label_akhir)
        for k in readings[0]:
            self.v[k] = 1

        # Per-segmen v-min dan v-maks (K5)
        seg_vmin, seg_vmaks = segment_vmin_vmaks(readings)

        # Agregasi ke abstrak: union (komponen hadir jika ADA SEGMEN yang memuat)
        for k in seg_vmin:
            self.vmin[k] = 1
        for k in seg_vmaks:
            self.vmaks[k] = 1

        if status in ("batas-sisa", "dikecualikan"):
            self.has_uncertain_segments = True


# ---------------------------------------------------------------------------
# Hitung kelengkapan dari ground truth
# ---------------------------------------------------------------------------

def compute_completeness(
    gt_rows: List[Dict],
) -> Tuple[Dict[str, AbstractCompleteness], Dict[str, Dict]]:
    """
    Hitung vektor kelengkapan untuk setiap abstrak dari ground_truth.csv.

    Return: (completeness_map, blocked_map)
    - completeness_map: id_abstrak -> AbstractCompleteness (abstrak yang bisa dihitung)
    - blocked_map: id_abstrak -> {"status_blokir": ..., "catatan": [...]}
    """
    results: Dict[str, AbstractCompleteness] = {}
    blocked: Dict[str, Dict] = {}  # abstrak yang diblokir

    for row in gt_rows:
        id_abstrak = row.get("id_abstrak", "").strip()
        id_segmen = row.get("id_segmen", "").strip()
        status = row.get("status_akhir", "").strip()
        label_akhir_raw = row.get("label_akhir", "").strip()
        label_alt_raw = row.get("label_alt_sisa", "").strip()

        if not id_abstrak:
            continue

        # Inisialisasi struktur jika belum ada
        if id_abstrak not in results:
            results[id_abstrak] = AbstractCompleteness(id_abstrak)
        if id_abstrak not in blocked:
            blocked[id_abstrak] = {"status_blokir": None, "catatan": []}

        comp = results[id_abstrak]
        blk = blocked[id_abstrak]

        # 1. HARD STOP: Segmen belum-selesai
        if status == "belum-selesai" or (status and status not in VALID_STATUS_GT):
            comp.has_pending_segments = True
            msg = f"{id_segmen}: status='{status}' (belum-selesai)."
            comp.catatan.append(msg)
            if blk["status_blokir"] not in ("BLOKIR-TT",):
                blk["status_blokir"] = "BLOKIR-BELUMSELESAI"
            blk["catatan"].append(msg)
            continue

        # 2. HARD STOP: TT belum diselesaikan di label_akhir
        label_set = parse_labels(label_akhir_raw)
        if "TT" in label_set:
            comp.has_unresolved_tt = True
            msg = (
                f"{id_segmen}: label_akhir='TT' belum diselesaikan. "
                "TT harus diselesaikan melalui adjudikasi (Pedoman K3)."
            )
            comp.catatan.append(msg)
            blk["status_blokir"] = "BLOKIR-TT"  # TT menang atas belum-selesai
            blk["catatan"].append(msg)
            continue

        # 3. Dikecualikan: tidak menyumbang v utama (K3), tetapi menyumbang v-min/v-maks (K5)
        if status == "dikecualikan":
            comp.catatan.append(f"{id_segmen}: dikecualikan (K3).")
            readings = get_segment_readings("", label_alt_raw, "dikecualikan")
            comp.update_from_segment(readings, "dikecualikan")
            continue

        # 4. LAINNYA / label kosong: tidak menyumbang apapun
        if label_set == {"LAINNYA"} or not label_set:
            comp.catatan.append(f"{id_segmen}: LAINNYA/kosong, tidak menyumbang.")
            continue

        # 5. Normal (final atau batas-sisa): update v, v-min, v-maks
        readings = get_segment_readings(label_akhir_raw, label_alt_raw, status)
        comp.update_from_segment(readings, status)

    return results, blocked


# ---------------------------------------------------------------------------
# Format hasil
# ---------------------------------------------------------------------------

def format_vector(v: Dict[str, int]) -> str:
    return f"({v['LB']},{v['TJ']},{v['MT']},{v['HS']},{v['SI']})"


def determine_status(v: Dict[str, int]) -> Tuple[str, str]:
    missing = [k for k in KOMPONEN if v[k] == 0]
    if not missing:
        return "LENGKAP", ""
    if len(missing) == 5:
        return "TIDAK LENGKAP", "semua komponen"
    return "TIDAK LENGKAP", ", ".join(missing)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Hitung vektor kelengkapan abstrak dari ground truth lengkap "
            "(sesuai Pedoman v1.0 Bagian 6)."
        )
    )
    parser.add_argument(
        "--ground-truth", "-g",
        required=True,
        help="Path ke ground_truth.csv (output build_ground_truth.py)",
    )
    parser.add_argument(
        "--abstrak", "-a",
        default="data/processed/abstrak.csv",
        help="Path ke abstrak.csv (untuk metadata jenis studi)",
    )
    parser.add_argument(
        "--output-dir", "-o",
        default="data/processed",
    )
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    gt_path = Path(args.ground_truth)
    if not gt_path.exists():
        logger.error(f"File ground truth tidak ditemukan: {gt_path}")
        return

    gt_rows = load_csv(gt_path)

    # Informasi awal tentang segmen bermasalah
    n_pending = sum(1 for r in gt_rows if r.get("status_akhir", "") == "belum-selesai")
    if n_pending > 0:
        logger.error(
            f"DITEMUKAN {n_pending} segmen 'belum-selesai' di ground_truth.csv. "
            "Abstrak yang terdampak akan diblokir dari metrik kelengkapan. "
            "Selesaikan adjudikasi dan jalankan ulang build_ground_truth.py."
        )

    abstrak_map: Dict[str, Dict] = {}
    abstrak_path = Path(args.abstrak)
    if abstrak_path.exists():
        abstrak_map = load_abstrak(abstrak_path)
    else:
        logger.warning(f"abstrak.csv tidak ditemukan: {abstrak_path}.")

    completeness, blocked = compute_completeness(gt_rows)

    if not completeness:
        logger.error("Tidak ada data kelengkapan yang dapat dihitung.")
        return

    output_rows: List[Dict] = []
    error_rows: List[Dict] = []
    n_lengkap = 0
    n_tidak_lengkap = 0
    n_tak_pasti = 0
    n_blokir_tt = 0
    n_blokir_pending = 0
    jenis_studi_stats: Dict[str, Dict[str, int]] = defaultdict(
        lambda: {"LENGKAP": 0, "TIDAK LENGKAP": 0, "TAK PASTI": 0,
                 "BLOKIR-TT": 0, "BLOKIR-BELUMSELESAI": 0}
    )

    for id_abstrak in sorted(completeness.keys()):
        comp = completeness[id_abstrak]
        blk = blocked.get(id_abstrak, {})
        abst_meta = abstrak_map.get(id_abstrak, {})
        jenis_studi = abst_meta.get("jenis_studi", "")
        peran_data = abst_meta.get("peran_data", "")
        catatan = "; ".join(comp.catatan)

        status_blokir = blk.get("status_blokir")

        # Abstrak diblokir: catat di laporan error, TIDAK masuk kelengkapan_abstrak.csv
        if status_blokir == "BLOKIR-TT":
            n_blokir_tt += 1
            jenis_studi_stats[jenis_studi]["BLOKIR-TT"] += 1
            error_rows.append({
                "id_abstrak": id_abstrak,
                "jenis_studi": jenis_studi,
                "peran_data": peran_data,
                "status_blokir": "BLOKIR-TT",
                "catatan": "; ".join(blk.get("catatan", [])),
            })
            logger.error(
                f"BLOKIR-TT: {id_abstrak} — label_akhir masih TT. "
                "Tidak masuk metrik kelengkapan."
            )
            continue

        if status_blokir == "BLOKIR-BELUMSELESAI" or comp.has_pending_segments:
            n_blokir_pending += 1
            jenis_studi_stats[jenis_studi]["BLOKIR-BELUMSELESAI"] += 1
            error_rows.append({
                "id_abstrak": id_abstrak,
                "jenis_studi": jenis_studi,
                "peran_data": peran_data,
                "status_blokir": "BLOKIR-BELUMSELESAI",
                "catatan": "; ".join(blk.get("catatan", [])),
            })
            logger.error(
                f"BLOKIR-BELUMSELESAI: {id_abstrak} — ada segmen belum-selesai. "
                "Tidak masuk metrik kelengkapan."
            )
            continue

        # Abstrak dapat dihitung
        status_v, missing = determine_status(comp.v)
        vmin_eq_vmaks = all(comp.vmin[k] == comp.vmaks[k] for k in KOMPONEN)

        if vmin_eq_vmaks and not comp.has_uncertain_segments:
            # Pasti (tidak ada segmen batas-sisa/dikecualikan atau v-min == v-maks)
            status_kepastian = "pasti"
            final_status = status_v
        elif vmin_eq_vmaks:
            # Ada segmen tidak pasti tapi v-min == v-maks → hasilnya tetap pasti
            status_kepastian = "pasti"
            final_status = status_v
        else:
            # v-min != v-maks → TAK PASTI (K5)
            status_kepastian = "TAK PASTI"
            final_status = "TAK PASTI"

        if status_kepastian == "pasti":
            if final_status == "LENGKAP":
                n_lengkap += 1
                jenis_studi_stats[jenis_studi]["LENGKAP"] += 1
            else:
                n_tidak_lengkap += 1
                jenis_studi_stats[jenis_studi]["TIDAK LENGKAP"] += 1
        else:
            n_tak_pasti += 1
            jenis_studi_stats[jenis_studi]["TAK PASTI"] += 1

        output_rows.append({
            "id_abstrak": id_abstrak,
            "jenis_studi": jenis_studi,
            "peran_data": peran_data,
            "v_LB": comp.v["LB"], "v_TJ": comp.v["TJ"],
            "v_MT": comp.v["MT"], "v_HS": comp.v["HS"], "v_SI": comp.v["SI"],
            "vektor": format_vector(comp.v),
            "status": final_status,
            "komponen_hilang": missing if final_status not in ("TAK PASTI",) else "",
            "vmin_LB": comp.vmin["LB"], "vmin_TJ": comp.vmin["TJ"],
            "vmin_MT": comp.vmin["MT"], "vmin_HS": comp.vmin["HS"],
            "vmin_SI": comp.vmin["SI"],
            "vmaks_LB": comp.vmaks["LB"], "vmaks_TJ": comp.vmaks["TJ"],
            "vmaks_MT": comp.vmaks["MT"], "vmaks_HS": comp.vmaks["HS"],
            "vmaks_SI": comp.vmaks["SI"],
            "vmin_vektor": format_vector(comp.vmin),
            "vmaks_vektor": format_vector(comp.vmaks),
            "status_kepastian": status_kepastian,
            "catatan": catatan,
        })

    # Tulis kelengkapan_abstrak.csv
    out_path = output_dir / "kelengkapan_abstrak.csv"
    with open(out_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f, fieldnames=KELENGKAPAN_COLS, quoting=csv.QUOTE_MINIMAL
        )
        writer.writeheader()
        writer.writerows(output_rows)
    logger.info(
        f"kelengkapan_abstrak.csv ditulis: {out_path} ({len(output_rows)} baris)"
    )

    # Tulis laporan_kelengkapan_error.csv
    err_path = output_dir / "laporan_kelengkapan_error.csv"
    with open(err_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f, fieldnames=ERROR_COLS, quoting=csv.QUOTE_MINIMAL
        )
        writer.writeheader()
        writer.writerows(error_rows)
    if error_rows:
        logger.error(
            f"laporan_kelengkapan_error.csv ditulis: {err_path} "
            f"({len(error_rows)} abstrak diblokir)"
        )

    # Tulis ringkasan
    n_total_dihitung = len(output_rows)
    n_total_blokir = len(error_rows)
    ringkasan_lines = [
        "=" * 65,
        "RINGKASAN KELENGKAPAN ABSTRAK (Pedoman v1.0, Bagian 6)",
        "=" * 65,
        f"Total abstrak di GT          : {n_total_dihitung + n_total_blokir}",
        f"Abstrak dapat dihitung       : {n_total_dihitung}",
        f"  LENGKAP (pasti)            : {n_lengkap}",
        f"  TIDAK LENGKAP (pasti)      : {n_tidak_lengkap}",
        f"  TAK PASTI (v-min≠v-maks)   : {n_tak_pasti}",
        f"Abstrak diblokir             : {n_total_blokir}",
        f"  BLOKIR-TT                  : {n_blokir_tt}",
        f"  BLOKIR-BELUMSELESAI        : {n_blokir_pending}",
        "",
        "DEFINISI STATUS:",
        "  LENGKAP       : v=(1,1,1,1,1), semua 5 komponen hadir (K4)",
        "  TIDAK LENGKAP : ada komponen = 0 (K4)",
        "  TAK PASTI     : v-min≠v-maks; tidak masuk metrik utama;",
        "                  masuk analisis sensitivitas (K5)",
        "  BLOKIR-TT     : label_akhir masih TT; adjudikasi wajib (K3)",
        "  BLOKIR-BELUMSELESAI: ada segmen belum-selesai di GT",
        "",
        "CATATAN PENTING:",
        "  - Kelengkapan = kehadiran fungsi retoris, bukan mutu isi (6.1)",
        "  - v-min = batas bawah; v-maks = batas atas (analisis sensitivitas)",
        "  - Abstrak TAK PASTI, BLOKIR-TT, BLOKIR-BELUMSELESAI",
        "    TIDAK masuk metrik utama (6.5)",
        "  - Segmen dikecualikan: pembacaan ∅ membuat v-min = 0 (K5)",
        "",
        "PER JENIS STUDI:",
    ]
    for js in sorted(jenis_studi_stats):
        s = jenis_studi_stats[js]
        total_js = sum(s.values())
        ringkasan_lines.append(
            f"  {js or '(tidak diketahui)':30s}: "
            f"LENGKAP={s['LENGKAP']} TIDAK LENGKAP={s['TIDAK LENGKAP']} "
            f"TAK PASTI={s['TAK PASTI']} "
            f"BLOKIR-TT={s['BLOKIR-TT']} "
            f"BLOKIR-BS={s['BLOKIR-BELUMSELESAI']} (n={total_js})"
        )

    ring_path = output_dir / "ringkasan_kelengkapan.txt"
    with open(ring_path, "w", encoding="utf-8") as f:
        f.write("\n".join(ringkasan_lines))
    logger.info(f"Ringkasan ditulis: {ring_path}")


if __name__ == "__main__":
    main()
