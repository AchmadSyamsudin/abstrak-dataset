#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
calculate_completeness.py
==========================
Menghitung vektor kelengkapan abstrak dari GROUND TRUTH LENGKAP (ground_truth.csv),
sesuai Bagian 6 Pedoman v1.0.

PERBAIKAN v2:
- Input utama: ground_truth.csv (bukan adjudikasi.csv) agar segmen konsensus
  di luar antrean adjudikasi tidak terlewat.
- TT yang belum diselesaikan MENGHENTIKAN metrik utama untuk abstrak terkait
  (status = "BLOKIR-TT", bukan dilewati diam-diam).
- Segmen 'belum-selesai' di ground truth menyebabkan abstrak menjadi "TAK PASTI"
  dan tidak masuk metrik utama.
- v-min/v-maks diimplementasikan persis sesuai K5: per-segmen tentukan semua
  pembacaan, lalu agregasikan per komponen.

Aturan:
- K1: Hanya label_akhir yang masuk vektor utama (v). Label alternatif hanya untuk v-maks.
- K2: Segmen berlabel ganda menyumbang semua labelnya ke v.
- K3: LAINNYA dan dikecualikan tidak menyumbang v utama.
- K4: LENGKAP ⟺ v = (1,1,1,1,1).
- K5: v-min = komponen hadir di SETIAP pembacaan sah;
      v-maks = komponen hadir di SEKURANG-KURANGNYA satu pembacaan sah.
      "Pembacaan sah" per segmen: {label_akhir} DAN {tiap label_alt} dihitung
      sebagai pembacaan alternatif. Semua himpunan pembacaan per segmen:
        readings = [{label_akhir_komponen}]
        jika batas-sisa: readings += [{tiap label_alt komponen}]
      v-min per abstrak = ∩ (union_per_segmen) (komponen yang hadir di semua segmen
      dari semua pembacaan; didefinisikan: komponen selalu menyumbang jika hadir di
      SEMUA pembacaan SEMUA segmen relevan)
      Implementasi: untuk v-min, komponen k diperhitungkan hanya jika k hadir di
      setiap pembacaan dari setiap segmen batas-sisa.
- K6: Tidak diimplementasikan sebagai aturan terpisah (tercakup oleh K4).
- K7: Kehadiran tidak menilai ukuran; satu segmen cukup per komponen.
- K8: Satuan satu abstrak.

TT belum selesai: status abstrak = "BLOKIR-TT"; metrik utama tidak dihitung.
Segmen belum-selesai: status abstrak = "TAK PASTI"; tidak masuk metrik utama.

Output:
- kelengkapan_abstrak.csv
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
from typing import Dict, FrozenSet, List, Optional, Set, Tuple

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("calculate_completeness")

KOMPONEN: List[str] = ["LB", "TJ", "MT", "HS", "SI"]
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


# ---------------------------------------------------------------------------
# Loader
# ---------------------------------------------------------------------------

def load_csv(path: Path) -> List[Dict]:
    with open(path, "r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def load_abstrak(path: Path) -> Dict[str, Dict]:
    result = {}
    for row in load_csv(path):
        result[row["id_abstrak"]] = row
    return result


# ---------------------------------------------------------------------------
# Parsing label
# ---------------------------------------------------------------------------

def parse_labels(label_str: str) -> Set[str]:
    """Parse '+'-separated label menjadi set komponen."""
    return {l.strip() for l in label_str.split("+") if l.strip()}


def parse_label_alt_readings(label_alt_str: str) -> List[Set[str]]:
    """
    Parse label_alt menjadi daftar himpunan pembacaan alternatif.
    Setiap alternatif (dipisah ';') dianggap satu pembacaan terpisah.
    """
    readings: List[Set[str]] = []
    for part in label_alt_str.split(";"):
        part = part.strip()
        if not part:
            continue
        # Setiap alternatif bisa berupa label ganda ('+')
        readings.append(parse_labels(part))
    return readings


# ---------------------------------------------------------------------------
# v-min/v-maks per segmen (K5)
# ---------------------------------------------------------------------------

def get_segment_readings(
    label_akhir_str: str,
    label_alt_str: str,
    status: str,
) -> List[Set[str]]:
    """
    Tentukan SEMUA pembacaan sah untuk satu segmen sesuai K5.

    Untuk segmen 'final': satu pembacaan = {label_akhir komponen}.
    Untuk segmen 'batas-sisa': pembacaan = [{label_akhir}] + [tiap label_alt].
    Komponen yang bukan dalam KOMPONEN (mis. LAINNYA, TT) disaring.
    """
    label_akhir = {l for l in parse_labels(label_akhir_str) if l in KOMPONEN}
    readings = [label_akhir]

    if status == "batas-sisa" and label_alt_str.strip():
        alt_readings = parse_label_alt_readings(label_alt_str)
        for alt_set in alt_readings:
            alt_komponen = {l for l in alt_set if l in KOMPONEN}
            readings.append(alt_komponen)

    return readings


def segment_vmin_vmaks(readings: List[Set[str]]) -> Tuple[Set[str], Set[str]]:
    """
    Hitung v-min dan v-maks untuk satu segmen berdasarkan daftar pembacaan.
    v-min = ∩ (semua pembacaan) — komponen yang hadir di SETIAP pembacaan.
    v-maks = ∪ (semua pembacaan) — komponen yang hadir di minimal satu pembacaan.
    """
    if not readings:
        return set(), set()
    vmin = readings[0].copy()
    for r in readings[1:]:
        vmin &= r  # irisan
    vmaks: Set[str] = set()
    for r in readings:
        vmaks |= r  # gabungan
    return vmin, vmaks


# ---------------------------------------------------------------------------
# Struktur data kelengkapan per abstrak
# ---------------------------------------------------------------------------

class AbstractCompleteness:
    def __init__(self, id_abstrak: str):
        self.id_abstrak = id_abstrak
        self.v: Dict[str, int] = {k: 0 for k in KOMPONEN}
        self.vmin: Dict[str, int] = {k: 1 for k in KOMPONEN}  # mulai semua 1
        self.vmaks: Dict[str, int] = {k: 0 for k in KOMPONEN}
        self.catatan: List[str] = []
        self.has_unresolved_tt: bool = False
        self.has_pending_segments: bool = False  # belum-selesai
        self.has_boundary_segments: bool = False  # batas-sisa
        self._any_segment_seen: bool = False  # untuk inisialisasi vmin

    def update_from_segment(self, readings: List[Set[str]], status: str) -> None:
        """
        Update v, v-min, v-maks dari satu segmen (label sudah dalam KOMPONEN).
        """
        if not readings:
            return

        # v: dari pembacaan pertama (label_akhir)
        for k in readings[0]:
            self.v[k] = 1

        # v-min dan v-maks per segmen
        seg_vmin, seg_vmaks = segment_vmin_vmaks(readings)

        # Agregasi v-maks: union ke seluruh abstrak
        for k in seg_vmaks:
            self.vmaks[k] = 1

        # Agregasi v-min: inisialisasi pertama kali, lalu interseksi
        if not self._any_segment_seen:
            # Pertama: set vmin sesuai vmin segmen pertama
            self.vmin = {k: (1 if k in seg_vmin else 0) for k in KOMPONEN}
            self._any_segment_seen = True
        else:
            # Interseksi: komponen harus hadir di SEMUA segmen
            for k in KOMPONEN:
                if k not in seg_vmin:
                    self.vmin[k] = 0

        if status == "batas-sisa":
            self.has_boundary_segments = True


# ---------------------------------------------------------------------------
# Hitung kelengkapan dari ground truth
# ---------------------------------------------------------------------------

def compute_completeness(
    gt_rows: List[Dict],
) -> Dict[str, AbstractCompleteness]:
    """
    Hitung vektor kelengkapan untuk setiap abstrak dari ground_truth.csv.
    """
    results: Dict[str, AbstractCompleteness] = {}

    for row in gt_rows:
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

        # Segmen belum-selesai: tandai abstrak TAK PASTI
        if status == "belum-selesai" or status not in VALID_STATUS_GT:
            comp.has_pending_segments = True
            comp.catatan.append(
                f"{id_segmen}: belum-selesai, abstrak tidak dapat dihitung."
            )
            continue

        # Dikecualikan: tetap dicatat, tidak menyumbang v utama
        if status == "dikecualikan":
            comp.catatan.append(f"{id_segmen}: dikecualikan.")
            # Menyumbang v-maks dari label_alt jika ada
            for alt_set in parse_label_alt_readings(label_alt_raw):
                for k in alt_set:
                    if k in KOMPONEN:
                        comp.vmaks[k] = 1
            comp.has_boundary_segments = True
            continue

        # TT yang belum diselesaikan (seharusnya sudah diresolvasi di adj, tapi jaga-jaga)
        label_set = parse_labels(label_akhir_raw)
        if "TT" in label_set:
            comp.has_unresolved_tt = True
            comp.catatan.append(
                f"{id_segmen}: label_akhir masih TT. "
                "TT harus diselesaikan melalui adjudikasi. "
                "Segmen ini tidak menyumbang vektor."
            )
            continue

        # LAINNYA: tidak menyumbang komponen apapun
        if label_set == {"LAINNYA"} or not label_set:
            comp.catatan.append(f"{id_segmen}: LAINNYA/kosong, tidak menyumbang.")
            continue

        # Tentukan semua pembacaan dan update
        readings = get_segment_readings(label_akhir_raw, label_alt_raw, status)
        comp.update_from_segment(readings, status)

    # Reset vmin untuk abstrak yang tidak ada segmen sama sekali
    for comp in results.values():
        if not comp._any_segment_seen:
            comp.vmin = {k: 0 for k in KOMPONEN}

    return results


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
        description="Hitung vektor kelengkapan abstrak dari ground truth lengkap."
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

    # Periksa: ada segmen belum-selesai?
    n_pending = sum(1 for r in gt_rows if r.get("status_akhir", "") == "belum-selesai")
    if n_pending > 0:
        logger.error(
            f"BLOKIR: {n_pending} segmen berstatus 'belum-selesai' di ground_truth.csv. "
            "Selesaikan adjudikasi terlebih dahulu sebelum menghitung kelengkapan. "
            "Abstrak yang terdampak akan dilaporkan sebagai TAK PASTI."
        )

    abstrak_map: Dict[str, Dict] = {}
    abstrak_path = Path(args.abstrak)
    if abstrak_path.exists():
        abstrak_map = load_abstrak(abstrak_path)
    else:
        logger.warning(f"abstrak.csv tidak ditemukan: {abstrak_path}.")

    completeness = compute_completeness(gt_rows)

    if not completeness:
        logger.error("Tidak ada data kelengkapan yang dapat dihitung.")
        return

    output_rows: List[Dict] = []
    n_lengkap = 0
    n_tidak_lengkap = 0
    n_tak_pasti = 0
    n_blokir_tt = 0
    jenis_studi_stats: Dict[str, Dict[str, int]] = defaultdict(
        lambda: {"LENGKAP": 0, "TIDAK LENGKAP": 0, "TAK PASTI": 0, "BLOKIR-TT": 0}
    )

    for id_abstrak, comp in sorted(completeness.items()):
        abst_meta = abstrak_map.get(id_abstrak, {})
        jenis_studi = abst_meta.get("jenis_studi", "")
        peran_data = abst_meta.get("peran_data", "")

        catatan = "; ".join(comp.catatan)

        # TT yang belum selesai → BLOKIR metrik utama
        if comp.has_unresolved_tt:
            final_status = "BLOKIR-TT"
            status_kepastian = "TIDAK PASTI"
            n_blokir_tt += 1
            jenis_studi_stats[jenis_studi]["BLOKIR-TT"] += 1
            catatan = "PERINGATAN: Ada TT belum diselesaikan. " + catatan

        # Segmen belum-selesai → TAK PASTI
        elif comp.has_pending_segments:
            final_status = "TAK PASTI"
            status_kepastian = "TIDAK PASTI"
            n_tak_pasti += 1
            jenis_studi_stats[jenis_studi]["TAK PASTI"] += 1

        else:
            status_v, missing = determine_status(comp.v)
            # Periksa apakah v-min == v-maks untuk semua komponen
            all_same = all(comp.vmin[k] == comp.vmaks[k] for k in KOMPONEN)
            if all_same or not comp.has_boundary_segments:
                status_kepastian = "pasti"
                final_status = status_v
            else:
                status_kepastian = "TAK PASTI"
                final_status = "TAK PASTI"
                n_tak_pasti += 1
                jenis_studi_stats[jenis_studi]["TAK PASTI"] += 1

            if status_kepastian == "pasti":
                if final_status == "LENGKAP":
                    n_lengkap += 1
                    jenis_studi_stats[jenis_studi]["LENGKAP"] += 1
                else:
                    n_tidak_lengkap += 1
                    jenis_studi_stats[jenis_studi]["TIDAK LENGKAP"] += 1

        status_v, missing = determine_status(comp.v)
        vmin_status, vmin_missing = determine_status(comp.vmin)
        vmaks_status, _ = determine_status(comp.vmaks)

        output_rows.append({
            "id_abstrak": id_abstrak,
            "jenis_studi": jenis_studi,
            "peran_data": peran_data,
            "v_LB": comp.v["LB"],
            "v_TJ": comp.v["TJ"],
            "v_MT": comp.v["MT"],
            "v_HS": comp.v["HS"],
            "v_SI": comp.v["SI"],
            "vektor": format_vector(comp.v),
            "status": final_status,
            "komponen_hilang": missing if final_status not in ("TAK PASTI", "BLOKIR-TT") else "",
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
        })

    # Tulis CSV
    out_path = output_dir / "kelengkapan_abstrak.csv"
    with open(out_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=KELENGKAPAN_COLS, quoting=csv.QUOTE_MINIMAL)
        writer.writeheader()
        writer.writerows(output_rows)
    logger.info(f"kelengkapan_abstrak.csv ditulis: {out_path} ({len(output_rows)} baris)")

    # Ringkasan
    n_total = len(output_rows)
    ringkasan_lines = [
        "=" * 60,
        "RINGKASAN KELENGKAPAN ABSTRAK",
        "=" * 60,
        f"Total abstrak   : {n_total}",
        f"LENGKAP         : {n_lengkap}",
        f"TIDAK LENGKAP   : {n_tidak_lengkap}",
        f"TAK PASTI       : {n_tak_pasti} (v-min != v-maks; analisis sensitivitas)",
        f"BLOKIR-TT       : {n_blokir_tt} (ada TT belum diselesaikan)",
        "",
        "CATATAN PENTING:",
        "- Kelengkapan hanya mengukur kehadiran fungsi retoris sesuai definisi",
        "  operasional penelitian, bukan mutu atau kualitas bahasa.",
        "- Abstrak TAK PASTI dan BLOKIR-TT tidak masuk metrik utama.",
        "- v-min = batas bawah; v-maks = batas atas (analisis sensitivitas K5).",
        "",
        "PER JENIS STUDI:",
    ]
    for js in sorted(jenis_studi_stats):
        s = jenis_studi_stats[js]
        total_js = sum(s.values())
        ringkasan_lines.append(
            f"  {js or '(tidak diketahui)':30s}: "
            f"LENGKAP={s['LENGKAP']}, TIDAK LENGKAP={s['TIDAK LENGKAP']}, "
            f"TAK PASTI={s['TAK PASTI']}, BLOKIR-TT={s['BLOKIR-TT']} (n={total_js})"
        )

    ring_path = output_dir / "ringkasan_kelengkapan.txt"
    with open(ring_path, "w", encoding="utf-8") as f:
        f.write("\n".join(ringkasan_lines))
    logger.info(f"Ringkasan ditulis: {ring_path}")


if __name__ == "__main__":
    main()
