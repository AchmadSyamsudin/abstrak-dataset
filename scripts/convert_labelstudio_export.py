#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
convert_labelstudio_export.py
=============================
Membaca hasil ekspor JSON Label Studio dan mengonversinya ke format penelitian:
- anotasi.csv  (satu baris per segmen per anotator)

Sesuai Bagian 8.4 pedoman:
  id_abstrak, id_segmen, anotator_id, label, label_alt, simpul_penentu,
  flag, alasan, versi_pedoman, urutan_penyajian,
  waktu_mulai, waktu_selesai, durasi_detik

Ketentuan konversi:
- Label ganda ditulis dengan '+' dalam urutan kemunculan (misal: TJ+MT)
- Label alternatif dipisah ';' maks. dua
- Flag dipisah ';'
- Simpul penentu dipisah ';'
- Teks berisi koma/tanda kutip/baris baru: quoting CSV benar
- UTF-8 tanpa BOM
- ID abstrak dan ID segmen TIDAK diubah
- File anotasi mentah Label Studio TIDAK ditimpa

CATATAN KETERBATASAN waktu:
Label Studio tidak menyediakan waktu_mulai (saat task pertama kali dibuka)
secara langsung melalui ekspor standar. Yang tersedia adalah created_at
(saat task dibuat) dan completed_at (saat annotation disimpan).
Skrip ini menggunakan completed_at sebagai waktu_selesai.
waktu_mulai dan durasi_detik dikosongkan karena tidak dapat ditentukan
dengan andal dari ekspor standar Label Studio.
Jika Label Studio SDK digunakan dengan event tracking, waktu_mulai dapat
diperoleh; ini dicatat sebagai keterbatasan implementasi.

Penggunaan:
    python scripts/convert_labelstudio_export.py \
        --input data/exports/export_an1.json \
        --output data/processed/anotasi_an1.csv \
        [--anotator-id an1]
"""

import argparse
import csv
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("convert_labelstudio_export")

# Label yang diperbolehkan
VALID_LABELS = {"LB", "TJ", "MT", "HS", "SI", "LAINNYA", "TT"}
VALID_FLAGS = {"B1", "B2", "B3", "B4", "B5", "B6"}
VALID_PEMICU = {"U1", "U2", "U3", "U4", "U5"}

# Kolom output anotasi.csv (Bagian 8.4)
ANOTASI_COLS = [
    "id_abstrak", "id_segmen", "anotator_id", "label", "label_alt",
    "simpul_penentu", "flag", "alasan", "versi_pedoman",
    "urutan_penyajian", "waktu_mulai", "waktu_selesai", "durasi_detik",
]


# ---------------------------------------------------------------------------
# Ekstraksi nilai dari struktur Label Studio
# ---------------------------------------------------------------------------

def _get_result_value(results: List[Dict], name: str) -> Any:
    """Ambil nilai dari result berdasarkan from_name."""
    for r in results:
        if r.get("from_name") == name:
            val = r.get("value", {})
            # Choices
            if "choices" in val:
                return val["choices"]
            # TextArea
            if "text" in val:
                texts = val["text"]
                return texts[0] if texts else ""
    return None


def _get_choices(results: List[Dict], name: str) -> List[str]:
    """Ambil pilihan dari field Choices; kembalikan list."""
    val = _get_result_value(results, name)
    if isinstance(val, list):
        return val
    if isinstance(val, str):
        return [val]
    return []


def _get_text(results: List[Dict], name: str) -> str:
    """Ambil teks dari field TextArea; kembalikan string."""
    val = _get_result_value(results, name)
    if isinstance(val, str):
        return val.strip()
    return ""


# ---------------------------------------------------------------------------
# Bangun label gabungan dari hasil UP
# ---------------------------------------------------------------------------

def build_label_string(results: List[Dict]) -> str:
    """
    Susun string label final dari label_1 + label_2..label_6
    berdasarkan Uji Pemecahan.

    Aturan:
    - Jika uji_pemecahan = 'Tidak', hanya label_1 yang dipakai.
    - Jika uji_pemecahan = 'Ya', label_2..label_6 digabung ke label_1
      dengan '+', urutannya sesuai kemunculan dalam form (label_1 dulu).
    - Label '(kosong)' diabaikan.
    """
    up = _get_choices(results, "uji_pemecahan")
    up_ya = "Ya" in up

    label_1_list = _get_choices(results, "label_1")
    label_1 = label_1_list[0] if label_1_list else ""

    if not up_ya:
        return label_1

    # Kumpulkan label ganda
    labels: List[str] = [label_1] if label_1 else []
    for fname in ["label_2", "label_3", "label_4", "label_5", "label_6"]:
        chosen = _get_choices(results, fname)
        if chosen:
            val = chosen[0]
            if val and val != "(kosong)":
                labels.append(val)

    # Hapus duplikat SAMBIL menjaga urutan (Bagian 4, Langkah 0b butir 5)
    seen = set()
    unique_labels = []
    for l in labels:
        if l not in seen:
            seen.add(l)
            unique_labels.append(l)

    return "+".join(unique_labels) if unique_labels else label_1


# ---------------------------------------------------------------------------
# Konversi satu task
# ---------------------------------------------------------------------------

def convert_task(
    task: Dict,
    default_anotator_id: Optional[str],
) -> List[Dict]:
    """
    Konversi satu task Label Studio ke satu atau lebih baris anotasi.
    Satu task bisa punya beberapa anotasi (jika mode multi-annotator
    dalam satu proyek digunakan, yang tidak dianjurkan).
    Mengembalikan list baris anotasi.
    """
    data = task.get("data", {})
    id_abstrak = data.get("id_abstrak", "")
    id_segmen = data.get("id_segmen", "")
    urutan_penyajian = data.get("urutan_penyajian", "")
    versi_pedoman = data.get("_versi_pedoman", "v1.0")

    annotations = task.get("annotations", [])
    if not annotations:
        logger.warning(f"Task {id_segmen}: tidak ada anotasi, dilewati.")
        return []

    rows = []
    for ann in annotations:
        results = ann.get("result", [])
        completed_at = ann.get("completed_at", "")

        # Anotator ID: dari form anotator_id > dari task data > argumen default
        anotator_from_form = _get_text(results, "anotator_id").strip()
        anotator_from_data = data.get("_anotator_id", "")
        anotator_id = anotator_from_form or anotator_from_data or default_anotator_id or ""

        if not anotator_id:
            logger.warning(
                f"Task {id_segmen}: anotator_id tidak ditemukan "
                "(form, task data, atau argumen --anotator-id semuanya kosong)."
            )

        # Label
        label = build_label_string(results)

        # Label alternatif (maks. 2)
        label_alt_raw = _get_text(results, "label_alt")
        label_alt = _normalize_label_alt(label_alt_raw)

        # Simpul penentu
        simpul_penentu = _get_text(results, "simpul_penentu")

        # Flag
        flag_list = _get_choices(results, "flag")
        flag = ";".join(sorted(f for f in flag_list if f in VALID_FLAGS))

        # Alasan
        alasan = _get_text(results, "alasan")

        # Validasi dasar
        _warn_conversion_issues(
            id_segmen=id_segmen,
            label=label,
            flag=flag,
            alasan=alasan,
            anotator_id=anotator_id,
        )

        rows.append({
            "id_abstrak": id_abstrak,
            "id_segmen": id_segmen,
            "anotator_id": anotator_id,
            "label": label,
            "label_alt": label_alt,
            "simpul_penentu": simpul_penentu,
            "flag": flag,
            "alasan": alasan,
            "versi_pedoman": versi_pedoman,
            "urutan_penyajian": urutan_penyajian,
            # waktu_mulai tidak tersedia dari ekspor standar LS (lihat docstring)
            "waktu_mulai": "",
            "waktu_selesai": completed_at,
            "durasi_detik": "",
        })

    return rows


def _normalize_label_alt(raw: str) -> str:
    """
    Normalisasi label_alt: ambil maks. 2 label valid, pisah ';'.
    Abaikan label yang tidak valid.
    """
    if not raw:
        return ""
    parts = [p.strip() for p in raw.replace(",", ";").split(";")]
    valid = [p for p in parts if p in VALID_LABELS]
    if len(valid) > 2:
        logger.warning(
            f"label_alt '{raw}' memiliki lebih dari 2 alternatif; "
            "hanya 2 pertama yang diambil."
        )
        valid = valid[:2]
    return ";".join(valid)


def _warn_conversion_issues(
    id_segmen: str,
    label: str,
    flag: str,
    alasan: str,
    anotator_id: str,
) -> None:
    """Peringatan konversi tanpa menghentikan proses."""
    if not label:
        logger.warning(f"{id_segmen}: label kosong.")
        return

    # Periksa label-label individual valid
    for lbl in label.split("+"):
        if lbl not in VALID_LABELS:
            logger.warning(
                f"{id_segmen}: label '{lbl}' tidak dikenali. "
                f"Nilai yang diperbolehkan: {sorted(VALID_LABELS)}"
            )

    # TT harus ada B2
    if "TT" in label.split("+") and "B2" not in flag.split(";"):
        logger.warning(
            f"{id_segmen}: label TT tanpa flag B2. "
            "Pedoman mengharuskan TT selalu disertai B2."
        )

    # Flag tanpa alasan
    if flag and not alasan:
        logger.warning(
            f"{id_segmen}: flag '{flag}' tanpa alasan. "
            "Pedoman mengharuskan alasan satu kalimat bila ada flag."
        )

    if not anotator_id:
        logger.warning(f"{id_segmen}: anotator_id kosong.")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Konversi ekspor Label Studio JSON ke anotasi.csv penelitian."
    )
    parser.add_argument(
        "--input", "-i",
        required=True,
        help="Path ke file JSON ekspor Label Studio",
    )
    parser.add_argument(
        "--output", "-o",
        required=True,
        help="Path output anotasi.csv",
    )
    parser.add_argument(
        "--anotator-id",
        default=None,
        help="ID anotator fallback jika tidak ada di form atau task data",
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    if not input_path.exists():
        logger.error(f"File input tidak ditemukan: {input_path}")
        return

    # Jangan timpa file anotasi yang sudah ada tanpa konfirmasi
    if output_path.exists():
        logger.error(
            f"File output sudah ada: {output_path}. "
            "Ganti nama atau hapus file lama terlebih dahulu. "
            "Skrip ini tidak menimpa anotasi yang sudah ada."
        )
        return

    output_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Membaca: {input_path}")
    with open(input_path, "r", encoding="utf-8") as f:
        tasks = json.load(f)

    if not isinstance(tasks, list):
        # Label Studio kadang membungkus dalam dict
        if isinstance(tasks, dict) and "annotations" in tasks:
            tasks = [tasks]
        else:
            logger.error("Format JSON tidak dikenali. Ekspor Label Studio harus berupa list task.")
            return

    all_rows: List[Dict] = []
    n_skip = 0

    for task in tasks:
        rows = convert_task(task, default_anotator_id=args.anotator_id)
        if not rows:
            n_skip += 1
        all_rows.extend(rows)

    if not all_rows:
        logger.error("Tidak ada anotasi yang berhasil dikonversi.")
        return

    # Tulis output
    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=ANOTASI_COLS,
            quoting=csv.QUOTE_MINIMAL,
            extrasaction="ignore",
        )
        writer.writeheader()
        writer.writerows(all_rows)

    logger.info(
        f"anotasi.csv ditulis: {output_path} "
        f"({len(all_rows)} baris, {n_skip} task dilewati)"
    )
    logger.info(
        "File ekspor JSON mentah Label Studio TIDAK diubah. "
        "Simpan file ekspor asli sebagai cadangan."
    )


if __name__ == "__main__":
    main()
