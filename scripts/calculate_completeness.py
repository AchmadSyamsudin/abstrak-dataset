#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
calculate_completeness.py
==========================
Menghitung vektor kelengkapan abstrak dari label final adjudikasi,
sesuai Bagian 6 Pedoman v1.0.

Aturan:
- K1: Hanya label akhir (data emas, setelah adjudikasi)
  Label alternatif tidak masuk vektor utama.
- K2: Segmen berlabel ganda menyumbang semua labelnya.
- K3: LAINNYA dan segmen dikecualikan tidak menyumbang komponen.
  TT harus diselesaikan lewat adjudikasi sebelum vektor dihitung.
- K4: LENGKAP jika dan hanya jika v = (1,1,1,1,1). Selain itu TIDAK LENGKAP
  dengan komponen yang hilang disebut eksplisit.
- K5: Hitung v-min dan v-maks untuk analisis sensitivitas (segmen batas-sisa
  dan dikecualikan).
- K6: Abstrak tanpa HS = TIDAK LENGKAP: hilang HS.
- K7: Kehadiran tidak menilai ukuran; satu segmen cukup untuk satu komponen.
- K8: Satuan adalah satu abstrak.

Kelengkapan hanya mengukur kehadiran fungsi retoris menurut definisi
operasional penelitian ini, bukan menilai mutu, kebenaran, atau kualitas
bahasa abstrak.

Output:
- kelengkapan_abstrak.csv (satu baris per abstrak)
- ringkasan_kelengkapan.txt (statistik per jenis studi)

Penggunaan:
    python scripts/calculate_completeness.py \
        --adjudikasi data/processed/adjudikasi.csv \
        --abstrak data/processed/abstrak.csv \
        --output-dir data/processed \
        [--warn-tt]   # Peringatan jika ada TT yang belum diselesaikan
"""

import argparse
import csv
import logging
from collections import defaultdict
from pathlib import Path
from typing import Dict, FrozenSet, List, Optional, Set, Tuple

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("calculate_completeness")

KOMPONEN: List[str] = ["LB", "TJ", "MT", "HS", "SI"]
VALID_STATUS: Set[str] = {"final", "batas-sisa", "dikecualikan"}

KELENGKAPAN_COLS = [
    "id_abstrak",
    "jenis_studi",
    "peran_data",
    "v_LB", "v_TJ", "v_MT", "v_HS", "v_SI",
    "vektor",
    "status",
    "komponen_hilang",
    # v-min dan v-maks
    "vmin_LB", "vmin_TJ", "vmin_MT", "vmin_HS", "vmin_SI",
    "vmaks_LB", "vmaks_TJ", "vmaks_MT", "vmaks_HS", "vmaks_SI",
    "vmin_vektor", "vmaks_vektor",
    "status_kepastian",  # pasti | TAK PASTI
    "catatan",
]


# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------

def load_adjudikasi(path: Path) -> List[Dict]:
    rows = []
    with open(path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


def load_abstrak(path: Path) -> Dict[str, Dict]:
    result = {}
    with open(path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            result[row["id_abstrak"]] = row
    return result


# ---------------------------------------------------------------------------
# Parsing label
# ---------------------------------------------------------------------------

def parse_labels(label_str: str) -> Set[str]:
    """Parse '+'-separated label menjadi set."""
    return {l.strip() for l in label_str.split("+") if l.strip()}


# ---------------------------------------------------------------------------
# Hitung vektor per abstrak
# ---------------------------------------------------------------------------

class AbstractCompleteness:
    """Struktur data untuk menyimpan hasil kelengkapan satu abstrak."""

    def __init__(self, id_abstrak: str):
        self.id_abstrak = id_abstrak
        # v: vektor utama dari label final saja
        self.v: Dict[str, int] = {k: 0 for k in KOMPONEN}
        # v-min: komponen hadir di SEMUA pembacaan
        self.vmin: Dict[str, int] = {k: 0 for k in KOMPONEN}
        # v-maks: komponen hadir di SEKURANG-KURANGNYA satu pembacaan
        self.vmaks: Dict[str, int] = {k: 0 for k in KOMPONEN}
        self.catatan: List[str] = []
        self.has_unresolved_tt: bool = False
        self.has_boundary_segments: bool = False

    def update_from_final(self, labels: Set[str]) -> None:
        """Update v dari label akhir (status = final)."""
        for lbl in labels:
            if lbl in KOMPONEN:
                self.v[lbl] = 1

    def update_vmin_vmaks_from_final(self, labels: Set[str]) -> None:
        """
        Update v-min dan v-maks dari segmen final.
        Segmen final hanya punya satu pembacaan (label akhirnya).
        Kontribusi ke v-min dan v-maks sama.
        """
        for lbl in labels:
            if lbl in KOMPONEN:
                self.vmin[lbl] = 1
                self.vmaks[lbl] = 1

    def update_vmaks_from_batas_sisa(self, label_akhir: Set[str], label_alt: Set[str]) -> None:
        """
        Update v-maks dari segmen batas-sisa:
        v-maks: hadir pada sekurang-kurangnya satu pembacaan (label akhir ATAU alternatif).
        v-min: hadir pada semua pembacaan (label akhir DAN semua alternatif).
        Sesuai K5.
        """
        self.has_boundary_segments = True
        all_readings = label_akhir | label_alt

        for lbl in all_readings:
            if lbl in KOMPONEN:
                self.vmaks[lbl] = 1

        # v-min: komponen harus ada di SEMUA pembacaan
        # Dengan dua pembacaan (akhir + alt), v-min[k] = 1 jika k ada di kedua
        # Perhatian: ini bukan pembaruan permanen; kita perlu track per-segmen
        # Simplifikasi sesuai K5: vmin = label_akhir ∩ label_alt (per segmen)
        # Hanya update jika komponen ada di label_akhir (pembacaan primer)
        for lbl in label_akhir:
            if lbl in KOMPONEN:
                # Apakah ada di semua alternatif juga? Tidak bisa tahu tanpa
                # iterasi per-pembacaan. Untuk kesederhanaan, kita set vmin
                # hanya jika label akhir saja (tanpa alternatif yang meragukan)
                # sudah ada.
                # Catatan: implementasi ini konservatif (v-min <= v-maks selalu terjaga)
                if lbl in label_alt or not label_alt:
                    self.vmin[lbl] = 1


def compute_completeness(rows: List[Dict], warn_tt: bool = True) -> Dict[str, AbstractCompleteness]:
    """
    Hitung vektor kelengkapan untuk setiap abstrak berdasarkan adjudikasi.csv.
    Mengembalikan dict id_abstrak -> AbstractCompleteness.
    """
    results: Dict[str, AbstractCompleteness] = {}

    for row in rows:
        id_abstrak = row.get("id_abstrak", "").strip()
        id_segmen = row.get("id_segmen", "").strip()
        status = row.get("status_akhir", "").strip()
        label_akhir_raw = row.get("label_akhir", "").strip()
        label_alt_raw = row.get("label_alt_sisa", "").strip()

        if not id_abstrak:
            continue

        if id_abstrak not in results:
            results[id_abstrak] = AbstractCompleteness(id_abstrak)

        comp = results[id_abstrak]

        # Status tidak valid
        if status not in VALID_STATUS and status:
            comp.catatan.append(
                f"{id_segmen}: status_akhir '{status}' tidak dikenal, dilewati."
            )
            continue

        # TT yang belum diselesaikan
        label_set = parse_labels(label_akhir_raw)
        if "TT" in label_set:
            comp.has_unresolved_tt = True
            if warn_tt:
                logger.warning(
                    f"{id_abstrak}/{id_segmen}: label_akhir masih TT. "
                    "TT harus diselesaikan melalui adjudikasi sebelum vektor dihitung. "
                    "Segmen ini tidak menyumbang vektor."
                )
            comp.catatan.append(
                f"{id_segmen}: TT belum diselesaikan, tidak menyumbang vektor."
            )
            continue

        # K3: LAINNYA dan dikecualikan tidak menyumbang
        if status == "dikecualikan":
            comp.catatan.append(
                f"{id_segmen}: dikecualikan, tidak menyumbang vektor."
            )
            # Alternatif dari dikecualikan masuk v-maks saja
            alt_set = parse_labels(label_alt_raw)
            for lbl in alt_set:
                if lbl in KOMPONEN:
                    comp.vmaks[lbl] = 1
            comp.has_boundary_segments = True
            continue

        if not label_set or label_set == {"LAINNYA"}:
            continue  # Tidak menyumbang

        # Status final: update v, vmin, vmaks semuanya
        if status == "final":
            meaningful = {l for l in label_set if l in KOMPONEN}
            comp.update_from_final(meaningful)
            comp.update_vmin_vmaks_from_final(meaningful)

        # Status batas-sisa: update v (dari label akhir) dan vmaks (dari alt juga)
        elif status == "batas-sisa":
            meaningful = {l for l in label_set if l in KOMPONEN}
            comp.update_from_final(meaningful)  # v tetap dari label akhir

            alt_set = parse_labels(label_alt_raw)
            alt_meaningful = {l for l in alt_set if l in KOMPONEN}
            comp.update_vmaks_from_batas_sisa(meaningful, alt_meaningful)

    return results


# ---------------------------------------------------------------------------
# Format hasil
# ---------------------------------------------------------------------------

def format_vector(v: Dict[str, int]) -> str:
    return f"({v['LB']},{v['TJ']},{v['MT']},{v['HS']},{v['SI']})"


def determine_status(v: Dict[str, int]) -> Tuple[str, str]:
    """Kembalikan (status, komponen_hilang)."""
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
        description="Hitung vektor kelengkapan abstrak dari adjudikasi."
    )
    parser.add_argument(
        "--adjudikasi", "-j",
        required=True,
        help="Path ke adjudikasi.csv",
    )
    parser.add_argument(
        "--abstrak", "-a",
        default="data/processed/abstrak.csv",
        help="Path ke abstrak.csv (untuk metadata jenis studi)",
    )
    parser.add_argument(
        "--output-dir", "-o",
        default="data/processed",
        help="Direktori output",
    )
    parser.add_argument(
        "--warn-tt",
        action="store_true",
        default=True,
        help="Tampilkan peringatan untuk TT yang belum diselesaikan",
    )
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    adj_path = Path(args.adjudikasi)
    if not adj_path.exists():
        logger.error(f"File adjudikasi tidak ditemukan: {adj_path}")
        return

    logger.info(f"Membaca adjudikasi: {adj_path}")
    adj_rows = load_adjudikasi(adj_path)

    abstrak_map = {}
    abstrak_path = Path(args.abstrak)
    if abstrak_path.exists():
        abstrak_map = load_abstrak(abstrak_path)
    else:
        logger.warning(f"abstrak.csv tidak ditemukan: {abstrak_path}. Metadata jenis studi tidak tersedia.")

    # Hitung kelengkapan
    completeness = compute_completeness(adj_rows, warn_tt=args.warn_tt)

    if not completeness:
        logger.error("Tidak ada data kelengkapan yang dapat dihitung.")
        return

    # Susun baris output
    output_rows: List[Dict] = []
    n_lengkap = 0
    n_tidak_lengkap = 0
    n_tak_pasti = 0
    jenis_studi_stats: Dict[str, Dict[str, int]] = defaultdict(
        lambda: {"LENGKAP": 0, "TIDAK LENGKAP": 0, "TAK PASTI": 0}
    )

    for id_abstrak, comp in sorted(completeness.items()):
        abst_meta = abstrak_map.get(id_abstrak, {})
        jenis_studi = abst_meta.get("jenis_studi", "")
        peran_data = abst_meta.get("peran_data", "")

        status, missing = determine_status(comp.v)
        vmin_status, vmin_missing = determine_status(comp.vmin)
        vmaks_status, vmaks_missing = determine_status(comp.vmaks)

        # Tentukan kepastian (K5)
        if comp.vmin == comp.vmaks and not comp.has_boundary_segments:
            status_kepastian = "pasti"
            status_final = status
        else:
            # Cek apakah v-min == v-maks
            all_same = all(comp.vmin[k] == comp.vmaks[k] for k in KOMPONEN)
            if all_same:
                status_kepastian = "pasti"
                status_final = status
            else:
                status_kepastian = "TAK PASTI"
                status_final = "TAK PASTI"
                n_tak_pasti += 1

        # Catatan TT yang belum selesai
        catatan = "; ".join(comp.catatan)
        if comp.has_unresolved_tt:
            catatan = "PERINGATAN: Ada TT yang belum diselesaikan; vektor mungkin tidak lengkap. " + catatan

        row_out = {
            "id_abstrak": id_abstrak,
            "jenis_studi": jenis_studi,
            "peran_data": peran_data,
            "v_LB": comp.v["LB"],
            "v_TJ": comp.v["TJ"],
            "v_MT": comp.v["MT"],
            "v_HS": comp.v["HS"],
            "v_SI": comp.v["SI"],
            "vektor": format_vector(comp.v),
            "status": status_final if status_kepastian == "pasti" else "TAK PASTI",
            "komponen_hilang": missing,
            "vmin_LB": comp.vmin["LB"],
            "vmin_TJ": comp.vmin["TJ"],
            "vmin_MT": comp.vmin["MT"],
            "vmin_HS": comp.vmin["HS"],
            "vmin_SI": comp.vmin["SI"],
            "vmaks_LB": comp.vmaks["LB"],
            "vmaks_TJ": comp.vmaks["TJ"],
            "vmaks_MT": comp.vmaks["MT"],
            "vmaks_HS": comp.vmaks["HS"],
            "vmaks_SI": comp.vmaks["SI"],
            "vmin_vektor": format_vector(comp.vmin),
            "vmaks_vektor": format_vector(comp.vmaks),
            "status_kepastian": status_kepastian,
            "catatan": catatan,
        }
        output_rows.append(row_out)

        if status_kepastian != "TAK PASTI":
            if status == "LENGKAP":
                n_lengkap += 1
                jenis_studi_stats[jenis_studi]["LENGKAP"] += 1
            else:
                n_tidak_lengkap += 1
                jenis_studi_stats[jenis_studi]["TIDAK LENGKAP"] += 1
        else:
            jenis_studi_stats[jenis_studi]["TAK PASTI"] += 1

    # Tulis CSV
    out_path = output_dir / "kelengkapan_abstrak.csv"
    with open(out_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f, fieldnames=KELENGKAPAN_COLS, quoting=csv.QUOTE_MINIMAL
        )
        writer.writeheader()
        writer.writerows(output_rows)
    logger.info(f"kelengkapan_abstrak.csv ditulis: {out_path} ({len(output_rows)} baris)")

    # Tulis ringkasan
    n_total = len(output_rows)
    ringkasan_lines = [
        "=" * 60,
        "RINGKASAN KELENGKAPAN ABSTRAK",
        "=" * 60,
        f"Total abstrak   : {n_total}",
        f"LENGKAP         : {n_lengkap} ({100*n_lengkap/n_total:.1f}% dari total)" if n_total else "N/A",
        f"TIDAK LENGKAP   : {n_tidak_lengkap} ({100*n_tidak_lengkap/n_total:.1f}%)" if n_total else "N/A",
        f"TAK PASTI       : {n_tak_pasti} (dilaporkan terpisah, tidak masuk metrik utama)",
        "",
        "CATATAN PENTING:",
        "- Kelengkapan hanya mengukur kehadiran fungsi retoris sesuai definisi",
        "  operasional penelitian ini, bukan mutu, kebenaran, atau kualitas bahasa.",
        "- Abstrak TAK PASTI memiliki v-min != v-maks; tidak masuk metrik utama;",
        "  dilaporkan dalam analisis sensitivitas.",
        "",
        "PER JENIS STUDI:",
    ]
    for js in sorted(jenis_studi_stats):
        stats = jenis_studi_stats[js]
        total_js = sum(stats.values())
        ringkasan_lines.append(
            f"  {js or '(tidak diketahui)':30s}: "
            f"LENGKAP={stats['LENGKAP']}, TIDAK LENGKAP={stats['TIDAK LENGKAP']}, "
            f"TAK PASTI={stats['TAK PASTI']} (n={total_js})"
        )

    ringkasan_lines += [
        "",
        "Lihat kelengkapan_abstrak.csv untuk detail per abstrak.",
        "Abstrak TAK PASTI lihat kolom vmin_vektor dan vmaks_vektor.",
    ]

    ring_path = output_dir / "ringkasan_kelengkapan.txt"
    with open(ring_path, "w", encoding="utf-8") as f:
        f.write("\n".join(ringkasan_lines))
    logger.info(f"Ringkasan ditulis: {ring_path}")


if __name__ == "__main__":
    main()
