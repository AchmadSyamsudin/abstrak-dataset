#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
prepare_labelstudio_tasks.py
============================
Membaca segmen yang sudah dibekukan (segmen.csv) dan abstrak.csv,
lalu menghasilkan file JSON tasks untuk diimpor ke Label Studio.

Fitur:
- Satu task per segmen (sesuai konfigurasi XML)
- Menyertakan konteks: kalimat sebelum/sesudah + teks kerja abstrak
- Mendukung dua anotator independen (an1, an2) dengan urutan acak berbeda
  tetapi urutan segmen dalam abstrak tetap terjaga
- Random seed tersimpan untuk reprodusibilitas
- Mendukung filter peran_data

Output:
- data/labelstudio/tasks_{anotator_id}_{peran_data}.json
- data/labelstudio/seed_info.json (seed dan tanggal untuk reproduksi)

PENTING: Berkas task anotator 1 tidak boleh dilihat anotator 2.
Gunakan proyek Label Studio terpisah untuk setiap anotator.

Penggunaan:
    python scripts/prepare_labelstudio_tasks.py \
        --segmen data/processed/segmen.csv \
        --abstrak data/processed/abstrak.csv \
        --output-dir data/labelstudio \
        --anotator-ids an1,an2 \
        --peran-data korpus-anotasi \
        [--seed 42]
"""

import argparse
import csv
import json
import logging
import random
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Set

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("prepare_labelstudio_tasks")


# ---------------------------------------------------------------------------
# Baca data
# ---------------------------------------------------------------------------

def load_abstrak(path: Path) -> Dict[str, Dict]:
    """Muat abstrak.csv ke dict id_abstrak -> row."""
    abstrak_map: Dict[str, Dict] = {}
    with open(path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            abstrak_map[row["id_abstrak"]] = row
    return abstrak_map


def load_segmen(path: Path, peran_filter: Optional[str] = None) -> Dict[str, List[Dict]]:
    """
    Muat segmen.csv ke dict id_abstrak -> list segmen (urut).
    Hanya segmen dengan status_beku = 'disetujui' yang diproses.
    """
    segmen_map: Dict[str, List[Dict]] = {}
    n_total = 0
    n_skip = 0

    with open(path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Periksa status pembekuan
            status = row.get("status_beku", "").strip().lower()
            if status not in ("disetujui", "beku"):
                n_skip += 1
                continue

            id_abstrak = row["id_abstrak"]
            segmen_map.setdefault(id_abstrak, []).append(row)
            n_total += 1

    # Urutkan segmen per abstrak berdasarkan urutan
    for id_abstrak in segmen_map:
        segmen_map[id_abstrak].sort(key=lambda r: int(r.get("urutan", 0)))

    if n_skip > 0:
        logger.warning(
            f"{n_skip} segmen dilewati karena belum berstatus 'disetujui'/'beku'. "
            "Jalankan pemeriksaan segmentasi dan bekukan terlebih dahulu."
        )
    logger.info(f"Dimuat {n_total} segmen dari {len(segmen_map)} abstrak.")
    return segmen_map


# ---------------------------------------------------------------------------
# Filter berdasarkan peran_data
# ---------------------------------------------------------------------------

def filter_by_peran(
    segmen_map: Dict[str, List[Dict]],
    abstrak_map: Dict[str, Dict],
    peran_filter: Optional[str],
) -> Dict[str, List[Dict]]:
    """Filter segmen berdasarkan peran_data abstrak."""
    if not peran_filter:
        return segmen_map

    filtered = {}
    for id_abstrak, segs in segmen_map.items():
        row = abstrak_map.get(id_abstrak, {})
        if row.get("peran_data", "") == peran_filter:
            filtered[id_abstrak] = segs

    logger.info(
        f"Filter peran_data='{peran_filter}': "
        f"{len(filtered)}/{len(segmen_map)} abstrak."
    )
    return filtered


# ---------------------------------------------------------------------------
# Buat task JSON per segmen
# ---------------------------------------------------------------------------

def build_task(
    segmen: Dict,
    segmen_list: List[Dict],
    abstrak: Dict,
    urutan_penyajian: int,
    anotator_id: str,
) -> Dict:
    """Buat satu task Label Studio dari satu segmen."""
    id_abstrak = segmen["id_abstrak"]
    id_segmen = segmen["id_segmen"]
    urutan = int(segmen.get("urutan", 0))
    total = len(segmen_list)

    # Konteks: kalimat sebelum dan sesudah
    segmen_sebelum = ""
    segmen_sesudah = ""
    for i, s in enumerate(segmen_list):
        if s["id_segmen"] == id_segmen:
            if i > 0:
                segmen_sebelum = segmen_list[i-1]["teks_segmen"]
            if i < len(segmen_list) - 1:
                segmen_sesudah = segmen_list[i+1]["teks_segmen"]
            break

    # Teks kerja abstrak (tanpa subjudul; sudah dibersihkan saat normalisasi)
    teks_kerja_abstrak = abstrak.get("teks_kerja", "")

    task_data = {
        # Identitas
        "id_abstrak": id_abstrak,
        "id_segmen": id_segmen,
        "urutan_segmen": str(urutan),
        "total_segmen": str(total),
        "peran_data": abstrak.get("peran_data", ""),
        # Kalimat target
        "teks_segmen": segmen["teks_segmen"],
        # Konteks langsung
        "segmen_sebelum": segmen_sebelum if segmen_sebelum else "(tidak ada)",
        "segmen_sesudah": segmen_sesudah if segmen_sesudah else "(tidak ada)",
        # Konteks wacana
        "teks_kerja_abstrak": teks_kerja_abstrak,
        # Metadata yang disertakan
        "jenis_studi": abstrak.get("jenis_studi", ""),
        "urutan_penyajian": urutan_penyajian,
        # Metadata anotator (disimpan di task data agar tersedia saat ekspor)
        "_anotator_id": anotator_id,
        "_versi_pedoman": "v1.0",
    }

    return {"data": task_data}


# ---------------------------------------------------------------------------
# Buat task list per anotator
# ---------------------------------------------------------------------------

def build_tasks_for_annotator(
    segmen_map: Dict[str, List[Dict]],
    abstrak_map: Dict[str, Dict],
    anotator_id: str,
    seed: int,
) -> List[Dict]:
    """
    Buat daftar task untuk satu anotator.
    Urutan abstrak diacak dengan seed yang diberikan.
    Urutan segmen DALAM abstrak selalu terjaga.
    """
    # Acak urutan abstrak
    abstrak_ids = list(segmen_map.keys())
    rng = random.Random(seed)
    rng.shuffle(abstrak_ids)

    tasks: List[Dict] = []
    urutan_penyajian = 1

    for id_abstrak in abstrak_ids:
        segmen_list = segmen_map[id_abstrak]
        abstrak = abstrak_map.get(id_abstrak, {})

        for seg in segmen_list:
            task = build_task(
                segmen=seg,
                segmen_list=segmen_list,
                abstrak=abstrak,
                urutan_penyajian=urutan_penyajian,
                anotator_id=anotator_id,
            )
            tasks.append(task)
            urutan_penyajian += 1

    logger.info(
        f"Anotator {anotator_id}: {len(tasks)} tasks dari "
        f"{len(abstrak_ids)} abstrak (seed={seed})"
    )
    return tasks


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Buat task JSON untuk Label Studio dari segmen yang sudah dibekukan."
    )
    parser.add_argument(
        "--segmen", "-s",
        default="data/processed/segmen.csv",
        help="Path ke segmen.csv yang sudah dibekukan",
    )
    parser.add_argument(
        "--abstrak", "-a",
        default="data/processed/abstrak.csv",
        help="Path ke abstrak.csv",
    )
    parser.add_argument(
        "--output-dir", "-o",
        default="data/labelstudio",
        help="Direktori output (default: data/labelstudio)",
    )
    parser.add_argument(
        "--anotator-ids",
        default="an1,an2",
        help="Daftar ID anotator dipisah koma (default: an1,an2)",
    )
    parser.add_argument(
        "--peran-data", "-p",
        default=None,
        help="Filter peran_data: data-pengembangan | pilot2 | korpus-anotasi",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed untuk urutan abstrak (default: 42)",
    )
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load data
    abstrak_map = load_abstrak(Path(args.abstrak))
    segmen_map = load_segmen(Path(args.segmen))

    if not segmen_map:
        logger.error(
            "Tidak ada segmen yang ditemukan. "
            "Pastikan segmen.csv ada dan segmen sudah berstatus 'disetujui'."
        )
        return

    # Filter peran
    segmen_map = filter_by_peran(segmen_map, abstrak_map, args.peran_data)

    if not segmen_map:
        logger.error(
            f"Tidak ada abstrak dengan peran_data='{args.peran_data}'. "
            "Periksa filter dan isi abstrak.csv."
        )
        return

    anotator_ids = [a.strip() for a in args.anotator_ids.split(",") if a.strip()]
    seed_info = {
        "seed_dasar": args.seed,
        "tanggal": datetime.now(timezone.utc).isoformat(),
        "peran_data": args.peran_data or "semua",
        "anotator_seeds": {},
    }

    for i, anotator_id in enumerate(anotator_ids):
        # Setiap anotator mendapat seed berbeda (seed_dasar + indeks)
        # agar urutan abstrak berbeda antar anotator
        anotator_seed = args.seed + i * 1000
        seed_info["anotator_seeds"][anotator_id] = anotator_seed

        tasks = build_tasks_for_annotator(
            segmen_map=segmen_map,
            abstrak_map=abstrak_map,
            anotator_id=anotator_id,
            seed=anotator_seed,
        )

        # Tentukan nama file output
        suffix = f"_{args.peran_data}" if args.peran_data else ""
        out_path = output_dir / f"tasks_{anotator_id}{suffix}.json"

        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(tasks, f, ensure_ascii=False, indent=2)

        logger.info(f"Task disimpan: {out_path}")

    # Simpan seed info
    seed_path = output_dir / "seed_info.json"
    with open(seed_path, "w", encoding="utf-8") as f:
        json.dump(seed_info, f, ensure_ascii=False, indent=2)
    logger.info(f"Seed info disimpan: {seed_path}")

    logger.info(
        "\nPENTING: Buat proyek Label Studio TERPISAH untuk setiap anotator. "
        "Jangan impor task anotator 1 ke proyek anotator 2 atau sebaliknya. "
        "Hasil anotator 1 tidak boleh dilihat anotator 2 sebelum adjudikasi."
    )


if __name__ == "__main__":
    main()
