#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
convert_labelstudio_export.py
=============================
Membaca hasil ekspor JSON Label Studio dan mengonversinya ke format penelitian:
- anotasi.csv  (satu baris per segmen per anotator)
- audit_konversi.csv  (field tambahan untuk audit: uji_pemecahan, task_id, dll.)

PERBAIKAN v2:
- Error eksplisit jika UP=Tidak tetapi label_2..6 terisi (tidak dibuang diam-diam).
- Error eksplisit jika label alternatif lebih dari 2 atau tidak valid (tidak dipotong
  diam-diam; konversi dibatalkan untuk task tersebut).
- Hasil konversi dapat ditelusuri ke task sumber via kolom task_id.
- Field audit (uji_pemecahan, dll.) disimpan di audit_konversi.csv terpisah,
  tanpa mengubah skema baku anotasi.csv.

Penggunaan:
    python scripts/convert_labelstudio_export.py \\
        --input data/exports/export_an1.json \\
        --output data/processed/anotasi_an1.csv \\
        [--anotator-id an1]
"""

import argparse
import csv
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("convert_labelstudio_export")

VALID_LABELS = {"LB", "TJ", "MT", "HS", "SI", "LAINNYA", "TT"}
VALID_FLAGS = {"B1", "B2", "B3", "B4", "B5", "B6"}

ANOTASI_COLS = [
    "id_abstrak", "id_segmen", "anotator_id", "label", "label_alt",
    "simpul_penentu", "flag", "alasan", "versi_pedoman",
    "urutan_penyajian", "waktu_mulai", "waktu_selesai", "durasi_detik",
    "task_id",  # untuk keterlacakan ke task sumber
]

AUDIT_COLS = [
    "task_id", "id_segmen", "anotator_id",
    "uji_pemecahan", "label_1_raw", "label_2_raw", "label_3_raw",
    "label_4_raw", "label_5_raw", "label_6_raw",
    "konversi_status", "konversi_catatan",
]


# ---------------------------------------------------------------------------
# Ekstraksi nilai dari struktur Label Studio
# ---------------------------------------------------------------------------

def _get_result_value(results: List[Dict], name: str) -> Any:
    for r in results:
        if r.get("from_name") == name:
            val = r.get("value", {})
            if "choices" in val:
                return val["choices"]
            if "text" in val:
                texts = val["text"]
                return texts[0] if texts else ""
    return None


def _get_choices(results: List[Dict], name: str) -> List[str]:
    val = _get_result_value(results, name)
    if isinstance(val, list):
        return val
    if isinstance(val, str):
        return [val]
    return []


def _get_text(results: List[Dict], name: str) -> str:
    val = _get_result_value(results, name)
    if isinstance(val, str):
        return val.strip()
    return ""


# ---------------------------------------------------------------------------
# Konversi label — dengan validasi eksplisit
# ---------------------------------------------------------------------------

def build_label_string(
    results: List[Dict],
    id_segmen: str,
    task_id: Any,
) -> tuple[str, List[str], str]:
    """
    Susun string label final dari uji_pemecahan dan label_1..6.

    Return: (label_str, audit_notes, konversi_status)
    konversi_status: "ok" | "error"
    """
    audit_notes: List[str] = []
    up = _get_choices(results, "uji_pemecahan")
    up_ya = "Ya" in up

    label_1_list = _get_choices(results, "label_1")
    label_1 = label_1_list[0] if label_1_list else ""

    extra_labels = []
    for fname in ["label_2", "label_3", "label_4", "label_5", "label_6"]:
        chosen = _get_choices(results, fname)
        if chosen:
            val = chosen[0]
            if val and val != "(kosong)":
                extra_labels.append(val)

    # VALIDASI: label_1 tidak boleh kosong
    if not label_1 or label_1 == "(kosong)":
        msg = (
            f"ERROR KONVERSI [{id_segmen}/task {task_id}]: "
            "label_1 kosong. Setiap segmen harus memiliki minimal satu label."
        )
        logger.error(msg)
        audit_notes.append(msg)
        return "", audit_notes, "error"

    # VALIDASI: label_1 harus kode valid
    if label_1 not in VALID_LABELS:
        msg = (
            f"ERROR KONVERSI [{id_segmen}/task {task_id}]: "
            f"label_1 '{label_1}' tidak valid (diperbolehkan: {sorted(VALID_LABELS)})."
        )
        logger.error(msg)
        audit_notes.append(msg)
        return "", audit_notes, "error"

    # VALIDASI: semua extra_labels harus valid
    for lbl in extra_labels:
        if lbl not in VALID_LABELS:
            msg = (
                f"ERROR KONVERSI [{id_segmen}/task {task_id}]: "
                f"label tambahan '{lbl}' tidak valid (diperbolehkan: {sorted(VALID_LABELS)})."
            )
            logger.error(msg)
            audit_notes.append(msg)
            return "", audit_notes, "error"

    # VALIDASI: UP=Tidak tapi ada label tambahan terisi
    if not up_ya and extra_labels:
        msg = (
            f"ERROR KONVERSI [{id_segmen}/task {task_id}]: "
            f"Uji Pemecahan = 'Tidak' tetapi label_2..6 terisi: {extra_labels}. "
            "Task ini tidak dikonversi. Perbaiki anotasi di Label Studio."
        )
        logger.error(msg)
        audit_notes.append(msg)
        return "", audit_notes, "error"

    if not up_ya:
        return label_1, audit_notes, "ok"

    # UP=Ya: gabungkan dengan +, pertahankan urutan, hapus duplikat
    labels: List[str] = [label_1] if label_1 else []
    for lbl in extra_labels:
        if lbl not in labels:
            labels.append(lbl)

    return "+".join(labels) if labels else label_1, audit_notes, "ok"


def validate_label_alt(
    raw: str,
    label_final: str,
    id_segmen: str,
    task_id: Any,
) -> tuple[str, str, str]:
    """
    Validasi label_alt. Return (label_alt_str, catatan, status).
    Tidak memotong atau memperbaiki diam-diam — error eksplisit jika tidak valid.
    """
    if not raw:
        return "", "", "ok"

    parts = [p.strip() for p in raw.replace(",", ";").split(";") if p.strip()]

    # Periksa semua label valid
    invalid = [p for p in parts if p not in VALID_LABELS]
    if invalid:
        msg = (
            f"ERROR KONVERSI [{id_segmen}/task {task_id}]: "
            f"label_alt mengandung nilai tidak valid: {invalid}. "
            "Task ini tidak dikonversi."
        )
        logger.error(msg)
        return "", msg, "error"

    if len(parts) > 2:
        msg = (
            f"ERROR KONVERSI [{id_segmen}/task {task_id}]: "
            f"label_alt '{raw}' memiliki {len(parts)} alternatif (maks. 2 sesuai pedoman). "
            "Task ini tidak dikonversi. Perbaiki anotasi."
        )
        logger.error(msg)
        return "", msg, "error"

    # Periksa label alt tidak sama dengan label final
    final_parts = {l.strip() for l in label_final.split("+") if l.strip()}
    overlap = [p for p in parts if p in final_parts]
    if overlap:
        msg = (
            f"PERINGATAN [{id_segmen}/task {task_id}]: "
            f"label_alt {parts} bertumpang tindih dengan label final '{label_final}'. "
            "Pedoman mensyaratkan alternatif berbeda dari label ganda."
        )
        logger.warning(msg)
        # Ini WARNING, bukan ERROR — konversi tetap jalan

    return ";".join(parts), "", "ok"


# ---------------------------------------------------------------------------
# Konversi satu task
# ---------------------------------------------------------------------------

def convert_task(
    task: Dict,
    default_anotator_id: Optional[str],
) -> tuple[List[Dict], List[Dict]]:
    """
    Konversi satu task Label Studio.
    Return: (anotasi_rows, audit_rows)
    Task dengan error TIDAK masuk anotasi_rows tetapi tetap masuk audit_rows.
    """
    data = task.get("data", {})
    id_abstrak = data.get("id_abstrak", "")
    id_segmen = data.get("id_segmen", "")
    urutan_penyajian = data.get("urutan_penyajian", "")
    versi_pedoman = data.get("_versi_pedoman", "v1.0")
    task_id = task.get("id", "")

    annotations = task.get("annotations", [])
    if not annotations:
        logger.warning(
            f"Task {id_segmen} (id={task_id}): tidak ada anotasi. "
            "Task ini belum dianotasi dan tidak masuk anotasi.csv."
        )
        # Kembalikan audit baris kosong agar terdeteksi sebagai 'belum-dianotasi'
        return [], [{
            "task_id": task_id,
            "id_segmen": id_segmen,
            "anotator_id": default_anotator_id or "",
            "uji_pemecahan": "",
            "label_1_raw": "", "label_2_raw": "", "label_3_raw": "",
            "label_4_raw": "", "label_5_raw": "", "label_6_raw": "",
            "konversi_status": "belum-dianotasi",
            "konversi_catatan": "Task belum memiliki anotasi.",
        }]

    anotasi_rows: List[Dict] = []
    audit_rows: List[Dict] = []

    for ann in annotations:
        results = ann.get("result", [])
        completed_at = ann.get("completed_at", "")

        anotator_from_form = _get_text(results, "anotator_id").strip()
        anotator_from_data = data.get("_anotator_id", "")
        # --anotator-id CLI arg SELALU didahulukan atas form field atau metadata task.
        # Anotator tidak boleh mengubah ID mereka sendiri dengan mengetik di form.
        if default_anotator_id:
            anotator_id = default_anotator_id
            if anotator_from_form and anotator_from_form != default_anotator_id:
                logger.warning(
                    f"Task {id_segmen} (id={task_id}): anotator_id dari form "
                    f"'{anotator_from_form}' DIABAIKAN — "
                    f"--anotator-id '{default_anotator_id}' digunakan."
                )
        else:
            anotator_id = anotator_from_form or anotator_from_data or ""

        if not anotator_id:
            logger.warning(
                f"Task {id_segmen} (id={task_id}): anotator_id tidak ditemukan. "
                "Gunakan --anotator-id untuk menetapkan ID anotator secara eksplisit."
            )

        # UP raw untuk audit
        up_raw = _get_choices(results, "uji_pemecahan")
        up_val = up_raw[0] if up_raw else ""

        # Label per field untuk audit
        audit_label_fields = {}
        for i in range(1, 7):
            chosen = _get_choices(results, f"label_{i}")
            audit_label_fields[f"label_{i}_raw"] = chosen[0] if chosen else ""

        # Build label
        label, label_notes, label_status = build_label_string(results, id_segmen, task_id)

        # Flag
        flag_list = _get_choices(results, "flag")
        flag = ";".join(sorted(f for f in flag_list if f in VALID_FLAGS))

        # Label alt
        label_alt_raw = _get_text(results, "label_alt")
        label_alt, alt_note, alt_status = validate_label_alt(
            label_alt_raw, label, id_segmen, task_id
        )

        # Simpul penentu dan alasan
        simpul_penentu = _get_text(results, "simpul_penentu")
        alasan = _get_text(results, "alasan")

        # Gabungkan status
        all_notes = label_notes + ([alt_note] if alt_note else [])
        final_status = "error" if (label_status == "error" or alt_status == "error") else "ok"

        # Audit row (selalu dicatat)
        audit_rows.append({
            "task_id": task_id,
            "id_segmen": id_segmen,
            "anotator_id": anotator_id,
            "uji_pemecahan": up_val,
            **audit_label_fields,
            "konversi_status": final_status,
            "konversi_catatan": " | ".join(all_notes),
        })

        if final_status == "error":
            continue  # Jangan masuk anotasi.csv

        # Peringatan tambahan (tidak memblokir konversi)
        if "TT" in label.split("+") and "B2" not in flag.split(";"):
            logger.warning(
                f"[{id_segmen}/task {task_id}]: label TT tanpa flag B2. "
                "Pedoman mengharuskan TT selalu disertai B2."
            )
        if flag and not alasan:
            logger.warning(
                f"[{id_segmen}/task {task_id}]: flag '{flag}' tanpa alasan."
            )

        anotasi_rows.append({
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
            "waktu_mulai": "",  # tidak tersedia dari ekspor standar LS
            "waktu_selesai": completed_at,
            "durasi_detik": "",
            "task_id": task_id,
        })

    return anotasi_rows, audit_rows


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Konversi ekspor Label Studio JSON ke anotasi.csv penelitian."
    )
    parser.add_argument("--input", "-i", required=True)
    parser.add_argument("--output", "-o", required=True)
    parser.add_argument("--anotator-id", default=None)
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    if not input_path.exists():
        logger.error(f"File input tidak ditemukan: {input_path}")
        sys.exit(1)

    if output_path.exists():
        logger.error(
            f"File output sudah ada: {output_path}. "
            "Ganti nama atau hapus file lama terlebih dahulu. "
            "Skrip ini tidak menimpa anotasi yang sudah ada."
        )
        sys.exit(1)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(input_path, "r", encoding="utf-8") as f:
        tasks = json.load(f)

    if isinstance(tasks, dict) and "annotations" in tasks:
        tasks = [tasks]
    elif not isinstance(tasks, list):
        logger.error("Format JSON tidak dikenali.")
        sys.exit(1)

    all_anotasi: List[Dict] = []
    all_audit: List[Dict] = []
    n_error = 0
    n_belum_dianotasi = 0

    for task in tasks:
        anotasi_rows, audit_rows = convert_task(task, default_anotator_id=args.anotator_id)
        all_anotasi.extend(anotasi_rows)
        all_audit.extend(audit_rows)
        n_belum_dianotasi += sum(
            1 for a in audit_rows if a.get("konversi_status") == "belum-dianotasi"
        )
        n_error += sum(1 for a in audit_rows if a["konversi_status"] == "error")

    if not all_anotasi and n_error == 0 and n_belum_dianotasi == 0:
        logger.error("Tidak ada anotasi yang berhasil dikonversi.")
        sys.exit(1)

    # Tulis anotasi.csv
    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f, fieldnames=ANOTASI_COLS, quoting=csv.QUOTE_MINIMAL, extrasaction="ignore",
        )
        writer.writeheader()
        writer.writerows(all_anotasi)

    # Tulis audit_konversi.csv
    audit_path = output_path.parent / f"audit_konversi_{output_path.stem}.csv"
    with open(audit_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f, fieldnames=AUDIT_COLS, quoting=csv.QUOTE_MINIMAL, extrasaction="ignore",
        )
        writer.writeheader()
        writer.writerows(all_audit)

    logger.info(
        f"anotasi.csv ditulis: {output_path} ({len(all_anotasi)} baris)"
    )
    logger.info(f"audit_konversi ditulis: {audit_path} ({len(all_audit)} baris)")

    has_failure = False

    if n_error > 0:
        logger.error(
            f"{n_error} task memiliki error konversi dan TIDAK masuk anotasi.csv. "
            f"Periksa {audit_path} untuk detail, perbaiki di Label Studio, lalu ekspor ulang. "
            "File anotasi.csv yang dihasilkan TIDAK LENGKAP."
        )
        has_failure = True

    if n_belum_dianotasi > 0:
        logger.error(
            f"{n_belum_dianotasi} task belum dianotasi sama sekali. "
            "Selesaikan anotasi di Label Studio dan ekspor ulang. "
            "File anotasi.csv yang dihasilkan TIDAK LENGKAP."
        )
        has_failure = True

    if has_failure:
        sys.exit(1)


if __name__ == "__main__":
    main()
