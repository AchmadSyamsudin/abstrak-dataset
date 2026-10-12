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
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

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


def load_segmen(path: Path) -> Tuple[Dict[str, List[Dict]], int]:
    """
    Muat segmen.csv ke dict id_abstrak -> list segmen (urut).
    Memeriksa keunikan ID segmen (ID duplikat dihitung sebagai fatal).
    Return: (segmen_map, n_duplikat)
    """
    segmen_map: Dict[str, List[Dict]] = {}
    seen_ids: Set[str] = set()
    n_dup = 0

    with open(path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            sid = row.get("id_segmen", "").strip()
            if not sid:
                continue
            if sid in seen_ids:
                logger.error(f"FATAL: ID segmen duplikat di segmen.csv: '{sid}'")
                n_dup += 1
            seen_ids.add(sid)

            id_abstrak = row.get("id_abstrak", "").strip()
            segmen_map.setdefault(id_abstrak, []).append(row)

    # Urutkan segmen per abstrak berdasarkan urutan
    for id_abstrak in segmen_map:
        segmen_map[id_abstrak].sort(key=lambda r: int(r.get("urutan", 0)))

    return segmen_map, n_dup


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

    abstrak_path = Path(args.abstrak)
    segmen_path = Path(args.segmen)

    if not abstrak_path.exists():
        logger.error(f"FATAL: File abstrak tidak ditemukan: {abstrak_path}")
        sys.exit(1)

    if not segmen_path.exists():
        logger.error(f"FATAL: File segmen tidak ditemukan: {segmen_path}")
        sys.exit(1)

    # Load data
    abstrak_map = load_abstrak(abstrak_path)
    segmen_map, n_dup = load_segmen(segmen_path)

    # Hentikan jika terdapat ID segmen duplikat
    if n_dup > 0:
        logger.error(
            f"FATAL: Ditemukan {n_dup} ID segmen duplikat di segmen.csv. "
            "Pipeline dihentikan."
        )
        sys.exit(1)

    # Periksa ID abstrak yang tidak ditemukan dalam metadata abstrak
    unknown_abstrak = set()
    for aid in segmen_map:
        if aid not in abstrak_map:
            unknown_abstrak.add(aid)

    if unknown_abstrak:
        logger.error(
            f"FATAL: Ditemukan {len(unknown_abstrak)} ID abstrak pada segmen.csv "
            f"yang tidak terdaftar di abstrak.csv: {sorted(unknown_abstrak)}. "
            "Pipeline dihentikan."
        )
        sys.exit(1)

    n_abstrak_sebelum = len(segmen_map)
    n_segmen_sebelum = sum(len(segs) for segs in segmen_map.values())

    # Filter peran_data
    filtered_map = filter_by_peran(segmen_map, abstrak_map, args.peran_data)
    n_abstrak_sesudah = len(filtered_map)
    n_segmen_sesudah = sum(len(segs) for segs in filtered_map.values())

    # Laporkan jumlah abstrak dan segmen sebelum serta sesudah filter peran_data
    logger.info(
        f"Jumlah sebelum filter peran_data: {n_abstrak_sebelum} abstrak, {n_segmen_sebelum} segmen."
    )
    logger.info(
        f"Jumlah sesudah filter peran_data='{args.peran_data or 'semua'}': "
        f"{n_abstrak_sesudah} abstrak, {n_segmen_sesudah} segmen."
    )

    # Hentikan dengan kode nonzero jika tidak ada task yang dihasilkan
    if n_abstrak_sesudah == 0 or n_segmen_sesudah == 0:
        logger.error(
            "FATAL: Tidak ada segmen yang memenuhi syarat peran_data. "
            f"Tidak ada task yang dihasilkan untuk peran_data='{args.peran_data}'. "
            "Pipeline dihentikan."
        )
        sys.exit(1)

    # Hentikan pembuatan task jika ada segmen yang belum dibekukan dalam korpus yang akan diimpor
    unfrozen_segments = []
    for aid, segs in filtered_map.items():
        for seg in segs:
            st = seg.get("status_beku", "").strip().lower()
            if st not in ("disetujui", "beku"):
                unfrozen_segments.append(seg.get("id_segmen", ""))

    if unfrozen_segments:
        logger.error(
            f"FATAL: Ditemukan {len(unfrozen_segments)} segmen yang belum dibekukan "
            f"(status_beku bukan 'disetujui'/'beku') dalam korpus yang akan diimpor: "
            f"{unfrozen_segments[:10]}. Seluruh segmen korpus wajib dibekukan. "
            "Hentikan pembuatan task."
        )
        sys.exit(1)

    anotator_ids = [a.strip() for a in args.anotator_ids.split(",") if a.strip()]
    if not anotator_ids:
        logger.error("FATAL: Parameter --anotator-ids tidak boleh kosong.")
        sys.exit(1)

    seed_info = {
        "seed_dasar": args.seed,
        "tanggal": datetime.now(timezone.utc).isoformat(),
        "peran_data": args.peran_data or "semua",
        "anotator_seeds": {},
    }

    expected_seg_ids = [s["id_segmen"] for segs in filtered_map.values() for s in segs]

    for i, anotator_id in enumerate(anotator_ids):
        anotator_seed = args.seed + i * 1000
        seed_info["anotator_seeds"][anotator_id] = anotator_seed

        tasks = build_tasks_for_annotator(
            segmen_map=filtered_map,
            abstrak_map=abstrak_map,
            anotator_id=anotator_id,
            seed=anotator_seed,
        )

        if not tasks:
            logger.error(
                f"FATAL: Tidak ada task yang dihasilkan untuk anotator '{anotator_id}'."
            )
            sys.exit(1)

        # Pastikan semua segmen beku dari abstrak yang dipilih terwakili tepat satu kali per anotator
        task_seg_ids = [t["data"]["id_segmen"] for t in tasks]
        if len(task_seg_ids) != len(expected_seg_ids):
            logger.error(
                f"FATAL: Jumlah task ({len(task_seg_ids)}) tidak sama dengan "
                f"jumlah segmen beku ({len(expected_seg_ids)}) untuk anotator '{anotator_id}'."
            )
            sys.exit(1)

        if set(task_seg_ids) != set(expected_seg_ids):
            missing = set(expected_seg_ids) - set(task_seg_ids)
            extra = set(task_seg_ids) - set(expected_seg_ids)
            logger.error(
                f"FATAL: Verifikasi identitas segmen gagal untuk anotator '{anotator_id}'. "
                f"Hilang: {missing}, Lebih: {extra}."
            )
            sys.exit(1)

        # Tentukan nama file output
        suffix = f"_{args.peran_data}" if args.peran_data else ""
        out_path = output_dir / f"tasks_{anotator_id}{suffix}.json"

        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(tasks, f, ensure_ascii=False, indent=2)

        logger.info(f"Task disimpan: {out_path} ({len(tasks)} task)")

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
