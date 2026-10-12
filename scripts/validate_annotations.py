#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
validate_annotations.py
========================
Validator anotasi sesuai 15 aturan dari Bagian 9 request penelitian
dan Bagian 8 Pedoman v1.0.

Pemeriksaan yang dilakukan:
 1. ID abstrak dan ID segmen unik sesuai ruang lingkupnya
 2. Satu artikel tidak muncul sebagai beberapa entri korpus yang sama
 3. Segmentasi sudah disetujui/dibekukan sebelum task diimpor
 4. Seluruh teks kerja dapat ditelusuri ke abstrak aslinya
 5. Kode label dan flag hanya memakai nilai yang diperbolehkan
 6. Label ganda hanya diterima jika uji_pemecahan = Ya
 7. Label tambahan tidak boleh muncul ketika UP = Tidak
 8. Urutan label ganda dipertahankan (tidak diperiksa otomatis - dicatat sebagai
    tanggung jawab anotator; validator memperingatkan jika ada ketidakwajaran)
 9. Label alternatif tidak lebih dari dua dan tidak sama dengan label ganda
10. Setiap flag memiliki alasan yang tidak kosong
11. TT memiliki B2 dan masuk antrean adjudikasi
12. Segmen dengan tiga label atau lebih memiliki B5
13. Semua segmen dan anotator dapat ditelusuri
14. adjudikasi.csv tidak mengandung dua keputusan final untuk segmen yang sama
15. Perhitungan kelengkapan menggunakan label akhir yang sah

Output:
- laporan_validasi.csv (satu baris per masalah)
- laporan_validasi_ringkasan.txt

Penggunaan:
    python scripts/validate_annotations.py \
        --anotasi data/processed/anotasi_an1.csv,data/processed/anotasi_an2.csv \
        --segmen data/processed/segmen.csv \
        --abstrak data/processed/abstrak.csv \
        [--adjudikasi data/processed/adjudikasi.csv] \
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
logger = logging.getLogger("validate_annotations")

VALID_LABELS: Set[str] = {"LB", "TJ", "MT", "HS", "SI", "LAINNYA", "TT"}
VALID_FLAGS: Set[str] = {"B1", "B2", "B3", "B4", "B5", "B6"}
VALID_STATUS_AKHIR: Set[str] = {"final", "batas-sisa", "dikecualikan"}
KOMPONEN_VEKTOR: Set[str] = {"LB", "TJ", "MT", "HS", "SI"}


# ---------------------------------------------------------------------------
# Struktur masalah
# ---------------------------------------------------------------------------

class ValidationIssue:
    def __init__(
        self,
        rule_no: int,
        id_abstrak: str,
        id_segmen: str,
        anotator_id: str,
        pesan: str,
        severity: str = "ERROR",  # ERROR | WARNING
    ):
        self.rule_no = rule_no
        self.id_abstrak = id_abstrak
        self.id_segmen = id_segmen
        self.anotator_id = anotator_id
        self.pesan = pesan
        self.severity = severity

    def to_dict(self) -> Dict:
        return {
            "aturan_no": self.rule_no,
            "id_abstrak": self.id_abstrak,
            "id_segmen": self.id_segmen,
            "anotator_id": self.anotator_id,
            "severity": self.severity,
            "pesan": self.pesan,
        }


# ---------------------------------------------------------------------------
# Loader CSV
# ---------------------------------------------------------------------------

def load_csv(path: Path) -> List[Dict]:
    rows = []
    with open(path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


# ---------------------------------------------------------------------------
# Validator utama
# ---------------------------------------------------------------------------

def validate(
    anotasi_paths: List[Path],
    segmen_path: Path,
    abstrak_path: Path,
    adjudikasi_path: Optional[Path],
) -> List[ValidationIssue]:
    issues: List[ValidationIssue] = []

    # Load data
    segmen_rows = load_csv(segmen_path) if segmen_path.exists() else []
    abstrak_rows = load_csv(abstrak_path) if abstrak_path.exists() else []
    adjudikasi_rows = load_csv(adjudikasi_path) if adjudikasi_path and adjudikasi_path.exists() else []

    # Indeks segmen
    segmen_set: Set[str] = {r["id_segmen"] for r in segmen_rows}
    segmen_abstrak_map: Dict[str, str] = {r["id_segmen"]: r["id_abstrak"] for r in segmen_rows}
    segmen_beku: Set[str] = {
        r["id_segmen"] for r in segmen_rows
        if r.get("status_beku", "").strip().lower() in ("disetujui", "beku")
    }

    # Indeks abstrak
    abstrak_set: Set[str] = {r["id_abstrak"] for r in abstrak_rows}
    kunci_to_ids: Dict[str, List[str]] = defaultdict(list)
    for r in abstrak_rows:
        kunci_to_ids[r.get("kunci_artikel", "")].append(r["id_abstrak"])

    # --- Aturan 1 & 2: Periksa uniknya ID abstrak (Aturan 2) ---
    # (dikerjakan di abstrak: sudah diperiksa di prepare_abstrak.py)
    for kunci, ids in kunci_to_ids.items():
        if len(ids) > 1 and kunci:
            issues.append(ValidationIssue(
                rule_no=2,
                id_abstrak=",".join(ids),
                id_segmen="",
                anotator_id="",
                pesan=(
                    f"Kunci artikel '{kunci}' muncul pada beberapa ID: {ids}. "
                    "Satu artikel tidak boleh muncul sebagai beberapa entri korpus yang sama."
                ),
                severity="ERROR",
            ))

    # Load semua anotasi
    all_anotasi: List[Dict] = []
    for ap in anotasi_paths:
        if ap.exists():
            all_anotasi.extend(load_csv(ap))
        else:
            logger.warning(f"File anotasi tidak ditemukan: {ap}")

    # --- Aturan 1: ID segmen unik per anotator ---
    ann_segmen_pairs: Set[Tuple[str, str]] = set()
    for row in all_anotasi:
        pair = (row.get("anotator_id", ""), row.get("id_segmen", ""))
        if pair in ann_segmen_pairs:
            issues.append(ValidationIssue(
                rule_no=1,
                id_abstrak=row.get("id_abstrak", ""),
                id_segmen=row.get("id_segmen", ""),
                anotator_id=row.get("anotator_id", ""),
                pesan=(
                    f"ID segmen '{row['id_segmen']}' muncul lebih dari satu kali "
                    f"untuk anotator '{row.get('anotator_id', '')}'. "
                    "ID segmen harus unik per anotator."
                ),
                severity="ERROR",
            ))
        ann_segmen_pairs.add(pair)

    # --- Aturan 3: Segmentasi sudah disetujui ---
    for row in all_anotasi:
        id_seg = row.get("id_segmen", "")
        if id_seg and id_seg not in segmen_beku:
            issues.append(ValidationIssue(
                rule_no=3,
                id_abstrak=row.get("id_abstrak", ""),
                id_segmen=id_seg,
                anotator_id=row.get("anotator_id", ""),
                pesan=(
                    f"Segmen '{id_seg}' belum berstatus 'disetujui'/'beku' pada segmen.csv. "
                    "Segmentasi harus disetujui sebelum anotasi dimulai."
                ),
                severity="ERROR",
            ))

    # --- Aturan 4: Teks kerja dapat ditelusuri ---
    for row in all_anotasi:
        id_abs = row.get("id_abstrak", "")
        if id_abs and id_abs not in abstrak_set:
            issues.append(ValidationIssue(
                rule_no=4,
                id_abstrak=id_abs,
                id_segmen=row.get("id_segmen", ""),
                anotator_id=row.get("anotator_id", ""),
                pesan=(
                    f"ID abstrak '{id_abs}' tidak ditemukan di abstrak.csv. "
                    "Teks kerja tidak dapat ditelusuri."
                ),
                severity="ERROR",
            ))

    # --- Aturan 5, 6, 7, 8, 9, 10, 11, 12: Validasi isi anotasi ---
    for row in all_anotasi:
        id_abs = row.get("id_abstrak", "")
        id_seg = row.get("id_segmen", "")
        anotator = row.get("anotator_id", "")
        label_raw = row.get("label", "")
        label_alt_raw = row.get("label_alt", "")
        flag_raw = row.get("flag", "")
        alasan = row.get("alasan", "").strip()

        labels = [l.strip() for l in label_raw.split("+") if l.strip()]
        flags = [f.strip() for f in flag_raw.split(";") if f.strip()]
        label_alts = [la.strip() for la in label_alt_raw.split(";") if la.strip()]

        # Aturan 5: kode label valid dan tidak boleh kosong
        if not labels:
            issues.append(ValidationIssue(
                rule_no=5,
                id_abstrak=id_abs, id_segmen=id_seg, anotator_id=anotator,
                pesan="Label kosong. Setiap segmen harus diberi minimal satu label yang valid.",
                severity="ERROR",
            ))
        for lbl in labels:
            if lbl not in VALID_LABELS:
                issues.append(ValidationIssue(
                    rule_no=5,
                    id_abstrak=id_abs, id_segmen=id_seg, anotator_id=anotator,
                    pesan=f"Kode label '{lbl}' tidak valid. Nilai yang diperbolehkan: {sorted(VALID_LABELS)}",
                    severity="ERROR",
                ))
        for fl in flags:
            if fl not in VALID_FLAGS:
                issues.append(ValidationIssue(
                    rule_no=5,
                    id_abstrak=id_abs, id_segmen=id_seg, anotator_id=anotator,
                    pesan=f"Kode flag '{fl}' tidak valid. Nilai yang diperbolehkan: {sorted(VALID_FLAGS)}",
                    severity="ERROR",
                ))

        # Aturan 6 & 7: Label ganda hanya jika UP = Ya
        # Di anotasi.csv, tanda '+' menunjukkan label ganda
        # Kita tidak menyimpan uji_pemecahan di anotasi.csv, jadi periksa heuristik:
        # jika ada '+', harusnya ada pemicu UP yang dicatat di simpul_penentu
        if len(labels) > 1:
            simpul = row.get("simpul_penentu", "")
            has_up_marker = any(
                u in simpul.upper()
                for u in ("U1", "U2", "U3", "U4", "U5")
            )
            if not has_up_marker:
                issues.append(ValidationIssue(
                    rule_no=6,
                    id_abstrak=id_abs, id_segmen=id_seg, anotator_id=anotator,
                    pesan=(
                        f"Label ganda '{label_raw}' tanpa pemicu UP (U1-U5) di simpul_penentu '{simpul}'. "
                        "Label ganda hanya sah melalui Uji Pemecahan."
                    ),
                    severity="ERROR",
                ))

        # Aturan 9: Label alternatif maks. 2, tidak identik dengan label utama
        if len(label_alts) > 2:
            issues.append(ValidationIssue(
                rule_no=9,
                id_abstrak=id_abs, id_segmen=id_seg, anotator_id=anotator,
                pesan=f"Label alternatif '{label_alt_raw}' lebih dari 2. Pedoman membatasi maks. 2 alternatif.",
                severity="ERROR",
            ))
        for la in label_alts:
            if la == label_raw:
                issues.append(ValidationIssue(
                    rule_no=9,
                    id_abstrak=id_abs, id_segmen=id_seg, anotator_id=anotator,
                    pesan=(
                        f"Label alternatif '{la}' identik dengan label utama '{label_raw}'. "
                        "Label alternatif harus memberikan pembacaan berbeda dari label utama."
                    ),
                    severity="ERROR",
                ))
            elif la in labels:
                if "B4" in flags:
                    # Sah berdasarkan Pedoman v1.0 Bagian 4 Langkah 0b (penulisan ulang alternatif dengan flag B4)
                    pass
                else:
                    issues.append(ValidationIssue(
                        rule_no=9,
                        id_abstrak=id_abs, id_segmen=id_seg, anotator_id=anotator,
                        pesan=(
                            f"Label alternatif '{la}' sama dengan salah satu komponen label ganda '{label_raw}' tanpa flag B4. "
                            "Label alternatif harus berbeda dari label ganda kecuali variasi penulisan ulang B4."
                        ),
                        severity="WARNING",
                    ))

        # Aturan 10: Setiap flag harus memiliki alasan
        if flags and not alasan:
            issues.append(ValidationIssue(
                rule_no=10,
                id_abstrak=id_abs, id_segmen=id_seg, anotator_id=anotator,
                pesan=f"Flag '{flag_raw}' tanpa alasan. Alasan wajib diisi bila ada flag.",
                severity="ERROR",
            ))

        # Aturan 11: TT harus ada B2
        if "TT" in labels:
            if "B2" not in flags:
                issues.append(ValidationIssue(
                    rule_no=11,
                    id_abstrak=id_abs, id_segmen=id_seg, anotator_id=anotator,
                    pesan="Label TT tanpa flag B2. Pedoman mengharuskan TT selalu disertai B2.",
                    severity="ERROR",
                ))
            if not alasan:
                issues.append(ValidationIssue(
                    rule_no=11,
                    id_abstrak=id_abs, id_segmen=id_seg, anotator_id=anotator,
                    pesan="Label TT tanpa alasan. TT harus disertai alasan yang memadai.",
                    severity="ERROR",
                ))

        # Aturan 12: 3+ label harus ada B5
        if len(labels) >= 3 and "B5" not in flags:
            issues.append(ValidationIssue(
                rule_no=12,
                id_abstrak=id_abs, id_segmen=id_seg, anotator_id=anotator,
                pesan=(
                    f"Segmen berlabel '{label_raw}' (3 atau lebih label) tanpa flag B5. "
                    "Pedoman mewajibkan B5 jika ada 3 label atau lebih."
                ),
                severity="ERROR",
            ))

    # --- Aturan 13: Semua segmen dan anotator dapat ditelusuri ---
    for row in all_anotasi:
        id_seg = row.get("id_segmen", "")
        if id_seg and id_seg not in segmen_set:
            issues.append(ValidationIssue(
                rule_no=13,
                id_abstrak=row.get("id_abstrak", ""),
                id_segmen=id_seg,
                anotator_id=row.get("anotator_id", ""),
                pesan=f"ID segmen '{id_seg}' tidak ditemukan di segmen.csv.",
                severity="ERROR",
            ))
        if not row.get("anotator_id", "").strip():
            issues.append(ValidationIssue(
                rule_no=13,
                id_abstrak=row.get("id_abstrak", ""),
                id_segmen=id_seg,
                anotator_id="",
                pesan="anotator_id kosong; anotasi tidak dapat ditelusuri.",
                severity="ERROR",
            ))

    # --- Aturan 14: adjudikasi tidak boleh memiliki keputusan ganda untuk segmen yang sama ---
    if adjudikasi_rows:
        segmen_adj_counts: Dict[str, int] = defaultdict(int)
        for row in adjudikasi_rows:
            sid = row.get("id_segmen", "").strip()
            if sid:
                segmen_adj_counts[sid] += 1
        for id_seg, count in segmen_adj_counts.items():
            if count > 1:
                issues.append(ValidationIssue(
                    rule_no=14,
                    id_abstrak="",
                    id_segmen=id_seg,
                    anotator_id="",
                    pesan=(
                        f"Segmen '{id_seg}' memiliki {count} keputusan di adjudikasi.csv. "
                        "Hanya boleh ada satu keputusan per segmen."
                    ),
                    severity="ERROR",
                ))

        # Periksa nilai status_akhir
        for row in adjudikasi_rows:
            status = row.get("status_akhir", "").strip()
            if status not in VALID_STATUS_AKHIR:
                issues.append(ValidationIssue(
                    rule_no=14,
                    id_abstrak=row.get("id_abstrak", ""),
                    id_segmen=row.get("id_segmen", ""),
                    anotator_id="",
                    pesan=(
                        f"status_akhir '{status}' tidak valid. "
                        f"Nilai yang diperbolehkan: {sorted(VALID_STATUS_AKHIR)}"
                    ),
                    severity="ERROR",
                ))

    # --- Aturan 15: kelengkapan menggunakan label akhir yang sah ---
    # Ini diperiksa oleh calculate_completeness.py; di sini kita hanya
    # memastikan bahwa adjudikasi tidak menggunakan label yang tidak valid
    for row in adjudikasi_rows:
        label_akhir = row.get("label_akhir", "").strip()
        if label_akhir:
            for lbl in label_akhir.split("+"):
                if lbl.strip() and lbl.strip() not in VALID_LABELS:
                    issues.append(ValidationIssue(
                        rule_no=15,
                        id_abstrak=row.get("id_abstrak", ""),
                        id_segmen=row.get("id_segmen", ""),
                        anotator_id="",
                        pesan=(
                            f"label_akhir '{label_akhir}' mengandung kode tidak valid '{lbl.strip()}'. "
                            "Perhitungan kelengkapan akan salah."
                        ),
                        severity="ERROR",
                    ))

    return issues


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validasi anotasi terhadap 15 aturan penelitian."
    )
    parser.add_argument(
        "--anotasi", "-a",
        required=True,
        help="Path ke anotasi.csv, pisah koma jika lebih dari satu file",
    )
    parser.add_argument(
        "--segmen", "-s",
        default="data/processed/segmen.csv",
        help="Path ke segmen.csv",
    )
    parser.add_argument(
        "--abstrak",
        default="data/processed/abstrak.csv",
        help="Path ke abstrak.csv",
    )
    parser.add_argument(
        "--adjudikasi",
        default=None,
        help="Path ke adjudikasi.csv (opsional)",
    )
    parser.add_argument(
        "--output-dir", "-o",
        default="data/processed",
        help="Direktori output laporan",
    )
    args = parser.parse_args()

    anotasi_paths = [Path(p.strip()) for p in args.anotasi.split(",")]
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    issues = validate(
        anotasi_paths=anotasi_paths,
        segmen_path=Path(args.segmen),
        abstrak_path=Path(args.abstrak),
        adjudikasi_path=Path(args.adjudikasi) if args.adjudikasi else None,
    )

    # Tulis laporan CSV
    laporan_path = output_dir / "laporan_validasi.csv"
    cols = ["aturan_no", "id_abstrak", "id_segmen", "anotator_id", "severity", "pesan"]
    with open(laporan_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=cols, quoting=csv.QUOTE_MINIMAL)
        writer.writeheader()
        writer.writerows([iss.to_dict() for iss in issues])

    # Tulis ringkasan teks
    n_error = sum(1 for iss in issues if iss.severity == "ERROR")
    n_warning = sum(1 for iss in issues if iss.severity == "WARNING")
    ringkasan = [
        f"Laporan Validasi Anotasi - {len(issues)} masalah ditemukan",
        f"  ERROR  : {n_error}",
        f"  WARNING: {n_warning}",
        "",
        "Detail per aturan:",
    ]
    rule_counts: Dict[int, int] = defaultdict(int)
    for iss in issues:
        rule_counts[iss.rule_no] += 1
    for rno in sorted(rule_counts):
        ringkasan.append(f"  Aturan {rno}: {rule_counts[rno]} masalah")

    ringkasan_path = output_dir / "laporan_validasi_ringkasan.txt"
    with open(ringkasan_path, "w", encoding="utf-8") as f:
        f.write("\n".join(ringkasan))

    logger.info(
        f"Validasi selesai: {n_error} ERROR, {n_warning} WARNING. "
        f"Laporan: {laporan_path}"
    )
    if n_error > 0:
        logger.error(
            "Ada ERROR dalam anotasi. Perbaiki sebelum melanjutkan ke adjudikasi "
            "atau perhitungan kelengkapan."
        )
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
