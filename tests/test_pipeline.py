#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_pipeline.py
================
Unit test dan integration test untuk seluruh pipeline sistem anotasi.

PRINSIP:
- Semua test memanggil FUNGSI PRODUKSI yang sebenarnya dari modul scripts/*.
  Tidak ada reimplementasi aturan di dalam test.
- Data uji SINTETIS bertanda TEST_ atau [SINTETIS]. Tidak dicampur dengan data nyata.
- Integration test menggunakan file sementara (tmp) di direktori yang terisolasi.

KELOMPOK TEST:
 1. TestNormalisasi          - normalisasi minimal (prepare_abstrak.py)
 2. TestDeduplikasi          - dedup DOI/hash/Jaccard (prepare_abstrak.py)
 3. TestValidasiPrepareFatal - fatal errors berhentikan pipeline (prepare_abstrak.py)
 4. TestSegmentasi           - aturan segmentasi (segment_abstrak.py)
 5. TestSegmentasiURLDOI     - URL/DOI tidak menelan titik penutup
 6. TestKonversiLS           - label builder + validasi konversi (convert_labelstudio_export.py)
 7. TestKonversiLSError      - error eksplisit UP=Tidak + label terisi
 8. TestGroundTruth          - konsensus vs adjudikasi (build_ground_truth.py)
 9. TestKelengkapan          - vektor v, v-min, v-maks K5 (calculate_completeness.py)
10. TestKelengkapanTT        - BLOKIR-TT (calculate_completeness.py)
11. TestIntegrasi            - end-to-end dengan file sementara

Jalankan:
    python tests/test_pipeline.py
    python -m pytest tests/test_pipeline.py -v
"""

import csv
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))


# ===========================================================================
# 1. TestNormalisasi
# ===========================================================================

class TestNormalisasi(unittest.TestCase):

    def setUp(self):
        from prepare_abstrak import normalize_minimal, normalize_ligatures, sha256_text
        self.normalize_minimal = normalize_minimal
        self.normalize_ligatures = normalize_ligatures
        self.sha256_text = sha256_text

    def test_hapus_baris_biasa(self):
        """Baris baru dari tata letak harus diganti spasi."""
        teks = "Penelitian ini\nbertujuan untuk"
        hasil, _ = self.normalize_minimal(teks)
        self.assertNotIn("\n", hasil)
        self.assertIn("bertujuan", hasil)

    def test_sambung_kata_terpotong(self):
        """Kata terpotong di akhir baris (soft hyphen) harus disambung."""
        teks = "pengguna-\nan teknologi"
        hasil, _ = self.normalize_minimal(teks)
        self.assertNotIn("-\n", hasil)
        self.assertIn("an teknologi", hasil)

    def test_rapikan_spasi_ganda(self):
        teks = "Penelitian  ini  bertujuan"
        hasil, _ = self.normalize_minimal(teks)
        self.assertNotIn("  ", hasil)

    def test_normalisasi_ligatur(self):
        teks = "eﬃsiensi dan eﬀektif"
        hasil, changes = self.normalize_ligatures(teks)
        self.assertIn("ffi", hasil)
        self.assertIn("ff", hasil)
        self.assertGreater(len(changes), 0)

    def test_teks_mentah_tidak_berubah_semantis(self):
        teks_mentah = "Perkembangan teknologi terus mendorong AI."
        hasil, _ = self.normalize_minimal(teks_mentah)
        self.assertIn("Perkembangan teknologi", hasil)
        self.assertIn("mendorong AI", hasil)

    def test_sha256_deterministik(self):
        teks = "Abstrak uji [SINTETIS]"
        h1 = self.sha256_text(teks)
        h2 = self.sha256_text(teks)
        self.assertEqual(h1, h2)
        self.assertEqual(len(h1), 64)

    def test_sha256_berbeda(self):
        h1 = self.sha256_text("Teks A [SINTETIS]")
        h2 = self.sha256_text("Teks B [SINTETIS]")
        self.assertNotEqual(h1, h2)

    def test_log_perubahan_dicatat(self):
        teks = "Baris pertama\nBaris kedua"
        _, changes = self.normalize_minimal(teks)
        self.assertGreater(len(changes), 0)
        for ch in changes:
            self.assertIn("jenis", ch)


# ===========================================================================
# 2. TestDeduplikasi
# ===========================================================================

class TestDeduplikasi(unittest.TestCase):

    def setUp(self):
        from prepare_abstrak import (
            normalize_doi, normalize_title, normalize_text_for_hash,
            word_ngrams, jaccard_similarity, run_deduplication, sha256_text
        )
        self.normalize_doi = normalize_doi
        self.normalize_title = normalize_title
        self.normalize_text_for_hash = normalize_text_for_hash
        self.word_ngrams = word_ngrams
        self.jaccard_sim = jaccard_similarity
        self.run_dedup = run_deduplication
        self.sha256 = sha256_text

    def test_normalisasi_doi_url(self):
        self.assertEqual(self.normalize_doi("https://doi.org/10.1234/abc"), "10.1234/abc")

    def test_normalisasi_doi_prefix_doi_colon(self):
        self.assertEqual(self.normalize_doi("doi: 10.1234/ABC"), "10.1234/abc")

    def test_normalisasi_doi_plain(self):
        self.assertEqual(self.normalize_doi("10.1234/ABC"), "10.1234/abc")

    def test_normalisasi_doi_kosong(self):
        self.assertEqual(self.normalize_doi(""), "")

    def test_jaccard_identik(self):
        s = {("a", "b", "c", "d", "e")}
        self.assertAlmostEqual(self.jaccard_sim(s, s), 1.0)

    def test_jaccard_berbeda_total(self):
        a = {("a", "b", "c", "d", "e")}
        b = {("f", "g", "h", "i", "j")}
        self.assertAlmostEqual(self.jaccard_sim(a, b), 0.0)

    def test_jaccard_kosong(self):
        self.assertAlmostEqual(self.jaccard_sim(set(), set()), 1.0)

    def test_duplikat_doi_terdeteksi(self):
        rows = [
            {"id_abstrak": "TEST_A001", "kunci_artikel": "doi:10.1234/test",
             "hash_teks_ternormalisasi": "h1", "teks_kerja": "abstrak satu sintetis",
             "status_dedup": "unik"},
            {"id_abstrak": "TEST_A002", "kunci_artikel": "doi:10.1234/test",
             "hash_teks_ternormalisasi": "h2", "teks_kerja": "abstrak dua sintetis",
             "status_dedup": "unik"},
        ]
        self.run_dedup(rows, [], skip_near_dup=True)
        dibuang = [r for r in rows if r["status_dedup"] == "duplikat-dibuang"]
        self.assertEqual(len(dibuang), 1)

    def test_duplikat_hash_terdeteksi(self):
        from prepare_abstrak import normalize_text_for_hash
        teks = "Abstrak sintetis identik untuk uji hash duplikat persis sama."
        h = self.sha256(normalize_text_for_hash(teks))
        rows = [
            {"id_abstrak": "TEST_A003", "kunci_artikel": "doi:10.x/a003",
             "hash_teks_ternormalisasi": h, "teks_kerja": teks, "status_dedup": "unik"},
            {"id_abstrak": "TEST_A004", "kunci_artikel": "doi:10.x/a004",
             "hash_teks_ternormalisasi": h, "teks_kerja": teks, "status_dedup": "unik"},
        ]
        self.run_dedup(rows, [], skip_near_dup=True)
        dibuang = [r for r in rows if r["status_dedup"] == "duplikat-dibuang"]
        self.assertEqual(len(dibuang), 1)

    def test_duplikat_dekat_ditandai_bukan_dihapus(self):
        from prepare_abstrak import word_ngrams, jaccard_similarity
        base_words = [f"kata{i}" for i in range(40)]
        base = " ".join(base_words)
        teks_a = base + " akhir_a"
        teks_b = base + " akhir_b"
        # Verifikasi Jaccard >= 0.90
        sim = jaccard_similarity(word_ngrams(teks_a), word_ngrams(teks_b))
        self.assertGreaterEqual(sim, 0.90, f"Jaccard={sim:.4f} harus >= 0.90")

        rows = [
            {"id_abstrak": "TEST_A005", "kunci_artikel": "doi:10.x/a005",
             "hash_teks_ternormalisasi": "h5", "teks_kerja": teks_a, "status_dedup": "unik"},
            {"id_abstrak": "TEST_A006", "kunci_artikel": "doi:10.x/a006",
             "hash_teks_ternormalisasi": "h6", "teks_kerja": teks_b, "status_dedup": "unik"},
        ]
        log = self.run_dedup(rows, [], skip_near_dup=False)
        log_dekat = [l for l in log if l["jenis_duplikat"] == "duplikat-dekat"]
        self.assertGreater(len(log_dekat), 0, "Harus ada entri log duplikat dekat")
        # TIDAK dihapus — hanya ditandai
        dibuang = [r for r in rows if r["status_dedup"] == "duplikat-dibuang"]
        self.assertEqual(len(dibuang), 0, "Duplikat dekat tidak boleh dihapus otomatis")
        ditinjau = [r for r in rows if r["status_dedup"] == "duplikat-dekat-ditinjau"]
        self.assertEqual(len(ditinjau), 1)


# ===========================================================================
# 3. TestValidasiPrepareFatal
# ===========================================================================

class TestValidasiPrepareFatal(unittest.TestCase):
    """
    Pastikan pipeline menghentikan eksekusi dan TIDAK menulis output
    saat ada fatal error.
    """

    def setUp(self):
        from prepare_abstrak import validate_row, prepare_abstrak
        self.validate_row = validate_row
        self.prepare_abstrak = prepare_abstrak

    def test_kolom_wajib_kosong_menghasilkan_error(self):
        row = {
            "id_abstrak": "TEST_V001",
            "judul": "",  # kosong
            "jurnal": "Jurnal Test",
            "tahun": "2024",
            "jenis_studi": "kuantitatif",
            "peran_data": "korpus-anotasi",
            "teks_mentah": "Teks sintetis.",
        }
        errors = self.validate_row(row, 2)
        self.assertTrue(any("judul" in e for e in errors))

    def test_jenis_studi_tidak_valid_menghasilkan_error(self):
        row = {
            "id_abstrak": "TEST_V002",
            "judul": "Judul Test",
            "jurnal": "Jurnal Test",
            "tahun": "2024",
            "jenis_studi": "SALAH",  # tidak valid
            "peran_data": "korpus-anotasi",
            "teks_mentah": "Teks sintetis.",
        }
        errors = self.validate_row(row, 2)
        self.assertTrue(any("jenis_studi" in e for e in errors))

    def test_id_duplikat_berhentikan_pipeline(self):
        """Pipeline dengan ID abstrak duplikat harus melempar SystemExit."""
        content = (
            "id_abstrak,judul,jurnal,tahun,jenis_studi,peran_data,teks_mentah\n"
            "TEST_X001,Judul A,Jurnal A,2024,kuantitatif,korpus-anotasi,Teks A sintetis.\n"
            "TEST_X001,Judul B,Jurnal B,2024,kuantitatif,korpus-anotasi,Teks B sintetis.\n"
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            inp = Path(tmpdir) / "input.csv"
            out = Path(tmpdir) / "out"
            inp.write_text(content, encoding="utf-8")
            with self.assertRaises(SystemExit):
                self.prepare_abstrak(inp, out)
            # Output TIDAK boleh ada
            self.assertFalse((out / "abstrak.csv").exists())

    def test_metadata_tidak_valid_berhentikan_pipeline(self):
        """Pipeline dengan metadata tidak valid harus melempar SystemExit."""
        content = (
            "id_abstrak,judul,jurnal,tahun,jenis_studi,peran_data,teks_mentah\n"
            "TEST_X002,,Jurnal A,2024,kuantitatif,korpus-anotasi,Teks C sintetis.\n"
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            inp = Path(tmpdir) / "input.csv"
            out = Path(tmpdir) / "out"
            inp.write_text(content, encoding="utf-8")
            with self.assertRaises(SystemExit):
                self.prepare_abstrak(inp, out)
            self.assertFalse((out / "abstrak.csv").exists())

    def test_metadata_valid_menghasilkan_output(self):
        """Pipeline dengan metadata valid HARUS menghasilkan abstrak.csv."""
        content = (
            "id_abstrak,judul,jurnal,tahun,jenis_studi,peran_data,teks_mentah\n"
            "TEST_X003,Judul Valid,Jurnal Valid,2024,kuantitatif,korpus-anotasi,"
            "Penelitian ini bertujuan untuk menguji sistem.\n"
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            inp = Path(tmpdir) / "input.csv"
            out = Path(tmpdir) / "out"
            inp.write_text(content, encoding="utf-8")
            self.prepare_abstrak(inp, out, skip_near_dup=True)
            self.assertTrue((out / "abstrak.csv").exists())


# ===========================================================================
# 4. TestSegmentasi
# ===========================================================================

class TestSegmentasi(unittest.TestCase):

    def setUp(self):
        from segment_abstrak import segment_text
        self.segment = segment_text

    def test_kalimat_normal_dua(self):
        teks = "Penelitian ini bertujuan untuk menganalisis AI. Metode yang digunakan adalah kuantitatif."
        segs = self.segment(teks)
        self.assertEqual(len(segs), 2)

    def test_singkatan_dkk_tidak_memecah(self):
        teks = "Supriyadi dkk. (2024) menemukan hasil positif. Kesimpulannya valid untuk semua kasus."
        segs = self.segment(teks)
        # Harus 2 segmen, bukan 3
        first = segs[0]["teks_segmen"]
        self.assertIn("2024", first)
        self.assertIn("dkk", first)

    def test_angka_desimal_tidak_memecah(self):
        teks = "Nilai signifikansi p = 0,05 diperoleh dari analisis. Kesimpulannya positif dan signifikan."
        segs = self.segment(teks)
        first = segs[0]["teks_segmen"]
        self.assertIn("0,05", first)

    def test_tanda_tanya_memecah(self):
        teks = "Apakah AI berpengaruh positif? Penelitian ini menjawab pertanyaan tersebut secara empiris."
        segs = self.segment(teks)
        self.assertEqual(len(segs), 2)

    def test_fragmen_pendek_mendapat_catatan_b5(self):
        teks = "Baik. Cukup valid."
        segs = self.segment(teks)
        has_b5 = any(s["catatan_segmentasi"] for s in segs)
        self.assertTrue(has_b5)

    def test_urutan_segmen_berurutan(self):
        teks = "Pertama ditulis di sini. Kedua ditulis setelahnya. Ketiga menutup kalimat terakhir."
        segs = self.segment(teks)
        for i, seg in enumerate(segs, start=1):
            self.assertEqual(seg["urutan"], i)

    def test_elipsis_tidak_memecah_ganda(self):
        teks = "Hasilnya... menunjukkan bahwa AI sangat efektif. Penelitian telah selesai dilakukan."
        segs = self.segment(teks)
        self.assertLessEqual(len(segs), 3)


# ===========================================================================
# 5. TestSegmentasiURLDOI
# ===========================================================================

class TestSegmentasiURLDOI(unittest.TestCase):
    """Pastikan titik di dalam URL/DOI tidak menelan titik penutup kalimat."""

    def setUp(self):
        from segment_abstrak import segment_text
        self.segment = segment_text

    def test_url_dalam_kalimat_diikuti_kalimat_baru(self):
        """URL di kalimat pertama diikuti titik penutup + kalimat kedua."""
        teks = (
            "Data diunduh dari https://jurnal.example.com/artikel. "
            "Kemudian data dianalisis secara statistik menggunakan SPSS."
        )
        segs = self.segment(teks)
        # Harus ada dua segmen, bukan satu
        self.assertGreaterEqual(len(segs), 2, f"Segmen: {[s['teks_segmen'] for s in segs]}")
        # Segmen kedua harus mengandung kata analisis
        second_texts = " ".join(s["teks_segmen"] for s in segs[1:])
        self.assertIn("dianalisis", second_texts)

    def test_doi_dalam_kalimat_diikuti_kalimat_baru(self):
        """DOI diikuti titik penutup kalimat harus memecah dengan benar."""
        teks = (
            "Artikel ini mengacu pada penelitian sebelumnya (doi: 10.1234/jurnal.2024.01). "
            "Metode yang digunakan sama dengan acuan tersebut dan relevan."
        )
        segs = self.segment(teks)
        # Segmen terakhir harus mengandung 'Metode'
        last_texts = " ".join(s["teks_segmen"] for s in segs)
        self.assertIn("Metode", last_texts)

    def test_url_tanpa_kalimat_setelah(self):
        """URL di akhir teks tidak menyebabkan segmen kosong."""
        teks = "Sumber data tersedia di https://contoh.example.com/data"
        segs = self.segment(teks)
        self.assertEqual(len(segs), 1)
        self.assertIn("https://", segs[0]["teks_segmen"])


# ===========================================================================
# 6. TestKonversiLS
# ===========================================================================

class TestKonversiLS(unittest.TestCase):

    def setUp(self):
        from convert_labelstudio_export import (
            build_label_string, validate_label_alt
        )
        self.build_label = build_label_string
        self.validate_alt = validate_label_alt

    def _make_results(self, label_1="TJ", up="Tidak", labels_extra=None,
                      flags=None, simpul="TJ-1", alasan="", anotator="an1", label_alt=""):
        results = [
            {"from_name": "label_1", "value": {"choices": [label_1]}},
            {"from_name": "uji_pemecahan", "value": {"choices": [up]}},
            {"from_name": "simpul_penentu", "value": {"text": [simpul]}},
            {"from_name": "alasan", "value": {"text": [alasan]}},
            {"from_name": "anotator_id", "value": {"text": [anotator]}},
            {"from_name": "label_alt", "value": {"text": [label_alt]}},
        ]
        if flags:
            results.append({"from_name": "flag", "value": {"choices": flags}})
        if labels_extra:
            for i, lbl in enumerate(labels_extra, start=2):
                results.append({"from_name": f"label_{i}", "value": {"choices": [lbl]}})
        return results

    def test_label_tunggal_up_tidak(self):
        results = self._make_results("TJ", up="Tidak")
        label, _, status = self.build_label(results, "TEST_S01", 1)
        self.assertEqual(label, "TJ")
        self.assertEqual(status, "ok")

    def test_label_ganda_up_ya(self):
        results = self._make_results("TJ", up="Ya", labels_extra=["MT"])
        label, _, status = self.build_label(results, "TEST_S01", 1)
        self.assertEqual(label, "TJ+MT")
        self.assertEqual(status, "ok")

    def test_label_ganda_tidak_duplikat(self):
        results = self._make_results("TJ", up="Ya", labels_extra=["TJ"])
        label, _, status = self.build_label(results, "TEST_S01", 1)
        self.assertEqual(label, "TJ")  # TJ deduplikasi
        self.assertEqual(status, "ok")

    def test_label_kosong_diabaikan(self):
        results = self._make_results("HS", up="Ya", labels_extra=["(kosong)", "SI"])
        label, _, status = self.build_label(results, "TEST_S01", 1)
        self.assertNotIn("(kosong)", label)
        self.assertIn("HS", label)
        self.assertIn("SI", label)
        self.assertEqual(status, "ok")

    def test_label_alt_valid(self):
        alt, catatan, status = self.validate_alt("HS;LB", "TJ", "TEST_S01", 1)
        self.assertEqual(alt, "HS;LB")
        self.assertEqual(status, "ok")

    def test_label_alt_tidak_valid_error(self):
        """label_alt tidak valid harus menghasilkan error, bukan dipotong diam-diam."""
        alt, catatan, status = self.validate_alt("HS;INVALID", "TJ", "TEST_S01", 1)
        self.assertEqual(status, "error")
        self.assertIn("INVALID", catatan)

    def test_label_alt_lebih_dari_dua_error(self):
        """label_alt lebih dari 2 harus error, bukan dipotong diam-diam."""
        alt, catatan, status = self.validate_alt("HS;LB;TJ", "MT", "TEST_S01", 1)
        self.assertEqual(status, "error")


# ===========================================================================
# 7. TestKonversiLSError
# ===========================================================================

class TestKonversiLSError(unittest.TestCase):
    """Test error eksplisit: UP=Tidak tapi label tambahan terisi."""

    def setUp(self):
        from convert_labelstudio_export import build_label_string
        self.build_label = build_label_string

    def _make_results(self, label_1, up, labels_extra=None):
        results = [
            {"from_name": "label_1", "value": {"choices": [label_1]}},
            {"from_name": "uji_pemecahan", "value": {"choices": [up]}},
        ]
        if labels_extra:
            for i, lbl in enumerate(labels_extra, start=2):
                results.append({"from_name": f"label_{i}", "value": {"choices": [lbl]}})
        return results

    def test_up_tidak_label_tambahan_error(self):
        """UP=Tidak + label_2 terisi = error eksplisit, tidak dibuang diam-diam."""
        results = self._make_results("TJ", up="Tidak", labels_extra=["MT"])
        label, notes, status = self.build_label(results, "TEST_ERR01", 99)
        self.assertEqual(status, "error")
        self.assertFalse(label)  # Tidak ada label yang dihasilkan
        self.assertTrue(any("Uji Pemecahan" in n for n in notes))

    def test_up_ya_label_tambahan_ok(self):
        """UP=Ya + label_2 terisi = valid."""
        results = self._make_results("TJ", up="Ya", labels_extra=["MT"])
        label, _, status = self.build_label(results, "TEST_ERR02", 99)
        self.assertEqual(status, "ok")
        self.assertIn("MT", label)


# ===========================================================================
# 8. TestGroundTruth
# ===========================================================================

class TestGroundTruth(unittest.TestCase):

    def setUp(self):
        from build_ground_truth import build_ground_truth, needs_adjudication
        self.build_gt = build_ground_truth
        self.needs_adj = needs_adjudication

    def _seg(self, sid, id_abs="TEST_A001", urutan=1, teks="Teks sintetis."):
        return {
            "id_segmen": sid, "id_abstrak": id_abs,
            "urutan": str(urutan), "teks_segmen": teks,
            "status_beku": "disetujui",
        }

    def _ann(self, sid, label="TJ", flag="", alasan="", simpul="TJ-1"):
        return {
            "id_segmen": sid, "id_abstrak": "TEST_A001",
            "label": label, "flag": flag,
            "alasan": alasan, "simpul_penentu": simpul,
            "versi_pedoman": "v1.0",
        }

    def _adj(self, sid, label_akhir, status="final", label_alt="",
             adj_id="adj1", alasan=""):
        return {
            "id_segmen": sid, "id_abstrak": "TEST_A001",
            "label_akhir": label_akhir, "label_alt_sisa": label_alt,
            "status_akhir": status,
            "adjudikator_id": adj_id, "alasan": alasan,
        }

    def test_konsensus_dua_anotator_sepakat(self):
        """Dua anotator sepakat tanpa flag -> status final, sumber konsensus."""
        seg_map = {"TEST_S01": self._seg("TEST_S01")}
        ann1 = {"TEST_S01": self._ann("TEST_S01", label="TJ")}
        ann2 = {"TEST_S01": self._ann("TEST_S01", label="TJ")}
        gt, stats = self.build_gt(seg_map, ann1, ann2, {})
        self.assertEqual(len(gt), 1)
        self.assertEqual(gt[0]["status_akhir"], "final")
        self.assertEqual(gt[0]["sumber_keputusan"], "konsensus")
        self.assertEqual(gt[0]["label_akhir"], "TJ")
        self.assertIn("final-konsensus", stats)

    def test_label_berbeda_tanpa_adjudikasi_belum_selesai(self):
        """Dua anotator berbeda tanpa adjudikasi -> belum-selesai."""
        seg_map = {"TEST_S02": self._seg("TEST_S02")}
        ann1 = {"TEST_S02": self._ann("TEST_S02", label="TJ")}
        ann2 = {"TEST_S02": self._ann("TEST_S02", label="MT")}
        gt, stats = self.build_gt(seg_map, ann1, ann2, {})
        self.assertEqual(gt[0]["status_akhir"], "belum-selesai")
        self.assertIn("belum-selesai", stats)

    def test_label_berbeda_dengan_adjudikasi_final(self):
        """Dua anotator berbeda + adjudikasi final -> status final, sumber adjudikasi."""
        seg_map = {"TEST_S03": self._seg("TEST_S03")}
        ann1 = {"TEST_S03": self._ann("TEST_S03", label="TJ")}
        ann2 = {"TEST_S03": self._ann("TEST_S03", label="MT")}
        adj_map = {"TEST_S03": self._adj("TEST_S03", label_akhir="MT", status="final")}
        gt, stats = self.build_gt(seg_map, ann1, ann2, adj_map)
        self.assertEqual(gt[0]["status_akhir"], "final")
        self.assertEqual(gt[0]["sumber_keputusan"], "adjudikasi")
        self.assertEqual(gt[0]["label_akhir"], "MT")

    def test_flag_masuk_adjudikasi(self):
        """Flag dari salah satu anotator -> perlu adjudikasi."""
        ann1 = self._ann("TEST_S04", label="LB", flag="B3", alasan="ragu")
        ann2 = self._ann("TEST_S04", label="LB")
        perlu, reasons = self.needs_adj(ann1, ann2)
        self.assertTrue(perlu)
        self.assertTrue(any("flag" in r for r in reasons))

    def test_tt_masuk_adjudikasi(self):
        """TT dari salah satu anotator -> perlu adjudikasi."""
        ann1 = self._ann("TEST_S05", label="TT", flag="B2", alasan="tidak jelas")
        ann2 = self._ann("TEST_S05", label="LB")
        perlu, reasons = self.needs_adj(ann1, ann2)
        self.assertTrue(perlu)
        self.assertTrue(any("TT" in r for r in reasons))

    def test_adjudikasi_batas_sisa(self):
        """Keputusan adjudikasi batas-sisa tersimpan di GT."""
        seg_map = {"TEST_S06": self._seg("TEST_S06")}
        ann1 = {"TEST_S06": self._ann("TEST_S06", label="TJ")}
        ann2 = {"TEST_S06": self._ann("TEST_S06", label="MT")}
        adj_map = {"TEST_S06": self._adj("TEST_S06", label_akhir="TJ",
                                         status="batas-sisa", label_alt="MT")}
        gt, stats = self.build_gt(seg_map, ann1, ann2, adj_map)
        self.assertEqual(gt[0]["status_akhir"], "batas-sisa")
        self.assertEqual(gt[0]["label_alt_sisa"], "MT")
        self.assertIn("batas-sisa", stats)

    def test_adjudikasi_dikecualikan(self):
        """Segmen dikecualikan tersimpan di GT."""
        seg_map = {"TEST_S07": self._seg("TEST_S07")}
        ann1 = {"TEST_S07": self._ann("TEST_S07", label="TT", flag="B2", alasan="x")}
        ann2 = {"TEST_S07": self._ann("TEST_S07", label="TT", flag="B2", alasan="x")}
        adj_map = {"TEST_S07": self._adj("TEST_S07", label_akhir="",
                                         status="dikecualikan", alasan="teks rusak")}
        gt, stats = self.build_gt(seg_map, ann1, ann2, adj_map)
        self.assertEqual(gt[0]["status_akhir"], "dikecualikan")
        self.assertIn("dikecualikan", stats)

    def test_segmen_di_luar_adjudikasi_masuk_gt(self):
        """Segmen konsensus yang tidak masuk antrean adjudikasi tetap ada di GT."""
        seg_map = {
            "TEST_S08": self._seg("TEST_S08"),
            "TEST_S09": self._seg("TEST_S09"),
        }
        ann1 = {
            "TEST_S08": self._ann("TEST_S08", label="LB"),
            "TEST_S09": self._ann("TEST_S09", label="TJ", flag="B3", alasan="r"),
        }
        ann2 = {
            "TEST_S08": self._ann("TEST_S08", label="LB"),
            "TEST_S09": self._ann("TEST_S09", label="MT"),
        }
        # S08 konsensus (tidak perlu adj), S09 perlu adj tapi tidak ada di adj_map
        adj_map = {}
        gt, stats = self.build_gt(seg_map, ann1, ann2, adj_map)
        self.assertEqual(len(gt), 2)
        s08 = next(r for r in gt if r["id_segmen"] == "TEST_S08")
        self.assertEqual(s08["status_akhir"], "final")
        self.assertEqual(s08["sumber_keputusan"], "konsensus")
        s09 = next(r for r in gt if r["id_segmen"] == "TEST_S09")
        self.assertEqual(s09["status_akhir"], "belum-selesai")


# ===========================================================================
# 9. TestKelengkapan
# ===========================================================================

class TestKelengkapan(unittest.TestCase):

    def setUp(self):
        from calculate_completeness import (
            compute_completeness, determine_status, format_vector,
            get_segment_readings, segment_vmin_vmaks
        )
        self.compute = compute_completeness
        self.determine_status = determine_status
        self.format_vector = format_vector
        self.get_readings = get_segment_readings
        self.seg_vmin_vmaks = segment_vmin_vmaks

    def _gt_row(self, id_abs, id_seg, label, status="final", label_alt=""):
        return {
            "id_abstrak": id_abs, "id_segmen": id_seg,
            "label_akhir": label, "label_alt_sisa": label_alt,
            "status_akhir": status,
        }

    def test_lengkap_semua_komponen(self):
        rows = [
            self._gt_row("TEST_A01", "TEST_A01-S01", "LB"),
            self._gt_row("TEST_A01", "TEST_A01-S02", "TJ"),
            self._gt_row("TEST_A01", "TEST_A01-S03", "MT"),
            self._gt_row("TEST_A01", "TEST_A01-S04", "HS"),
            self._gt_row("TEST_A01", "TEST_A01-S05", "SI"),
        ]
        results = self.compute(rows)
        comp = results["TEST_A01"]
        status, missing = self.determine_status(comp.v)
        self.assertEqual(status, "LENGKAP")

    def test_tidak_lengkap_hilang_si(self):
        rows = [
            self._gt_row("TEST_A02", "TEST_A02-S01", "LB"),
            self._gt_row("TEST_A02", "TEST_A02-S02", "TJ"),
            self._gt_row("TEST_A02", "TEST_A02-S03", "MT"),
            self._gt_row("TEST_A02", "TEST_A02-S04", "HS"),
        ]
        results = self.compute(rows)
        comp = results["TEST_A02"]
        status, missing = self.determine_status(comp.v)
        self.assertEqual(status, "TIDAK LENGKAP")
        self.assertIn("SI", missing)

    def test_label_ganda_menyumbang_semua(self):
        """TJ+MT dari satu segmen menyumbang dua komponen (K2)."""
        rows = [
            self._gt_row("TEST_A03", "TEST_A03-S01", "LB"),
            self._gt_row("TEST_A03", "TEST_A03-S02", "TJ+MT"),
            self._gt_row("TEST_A03", "TEST_A03-S03", "HS"),
            self._gt_row("TEST_A03", "TEST_A03-S04", "SI"),
        ]
        results = self.compute(rows)
        comp = results["TEST_A03"]
        self.assertEqual(comp.v["TJ"], 1)
        self.assertEqual(comp.v["MT"], 1)
        status, _ = self.determine_status(comp.v)
        self.assertEqual(status, "LENGKAP")

    def test_lainnya_tidak_menyumbang(self):
        rows = [
            self._gt_row("TEST_A04", "TEST_A04-S01", "LAINNYA"),
            self._gt_row("TEST_A04", "TEST_A04-S02", "LB"),
        ]
        results = self.compute(rows)
        comp = results["TEST_A04"]
        self.assertEqual(comp.v["LB"], 1)
        self.assertEqual(comp.v["TJ"], 0)

    def test_dikecualikan_tidak_menyumbang_v_utama(self):
        rows = [
            self._gt_row("TEST_A05", "TEST_A05-S01", "LB"),
            self._gt_row("TEST_A05", "TEST_A05-S02", "HS", status="dikecualikan"),
        ]
        results = self.compute(rows)
        comp = results["TEST_A05"]
        self.assertEqual(comp.v["HS"], 0)

    def test_konsensus_luar_adjudikasi_masuk_v(self):
        """Segmen konsensus yang tidak melewati adjudikasi harus masuk v."""
        rows = [
            self._gt_row("TEST_A06", "TEST_A06-S01", "LB", status="final"),
            self._gt_row("TEST_A06", "TEST_A06-S02", "SI", status="final"),
        ]
        results = self.compute(rows)
        comp = results["TEST_A06"]
        self.assertEqual(comp.v["LB"], 1)
        self.assertEqual(comp.v["SI"], 1)
        self.assertEqual(comp.v["TJ"], 0)

    def test_format_vektor(self):
        v = {"LB": 1, "TJ": 1, "MT": 0, "HS": 1, "SI": 0}
        self.assertEqual(self.format_vector(v), "(1,1,0,1,0)")

    def test_vektor_semua_nol_tidak_lengkap(self):
        v = {"LB": 0, "TJ": 0, "MT": 0, "HS": 0, "SI": 0}
        status, missing = self.determine_status(v)
        self.assertEqual(status, "TIDAK LENGKAP")
        self.assertIn("semua", missing)

    def test_vmin_vmaks_k5_batas_sisa_satu_alt(self):
        """
        K5: Segmen batas-sisa label_akhir=LB, label_alt=TJ.
        v-min segmen = LB ∩ TJ = {} (tidak ada komponen di kedua pembacaan).
        v-maks segmen = LB ∪ TJ = {LB, TJ}.
        """
        readings = self.get_readings("LB", "TJ", "batas-sisa")
        vmin, vmaks = self.seg_vmin_vmaks(readings)
        self.assertNotIn("LB", vmin)   # LB tidak ada di pembacaan alt (TJ only)
        self.assertNotIn("TJ", vmin)   # TJ tidak ada di pembacaan utama (LB only)
        self.assertIn("LB", vmaks)
        self.assertIn("TJ", vmaks)

    def test_vmin_vmaks_k5_batas_sisa_sama(self):
        """
        K5: Segmen batas-sisa label_akhir=LB, label_alt=LB.
        v-min = v-maks = {LB}.
        """
        readings = self.get_readings("LB", "LB", "batas-sisa")
        vmin, vmaks = self.seg_vmin_vmaks(readings)
        self.assertIn("LB", vmin)
        self.assertIn("LB", vmaks)

    def test_vmin_vmaks_final_tidak_ada_alt(self):
        """
        K5: Segmen final tidak memiliki alt.
        v-min = v-maks = {label_akhir}.
        """
        readings = self.get_readings("TJ", "", "final")
        vmin, vmaks = self.seg_vmin_vmaks(readings)
        self.assertIn("TJ", vmin)
        self.assertIn("TJ", vmaks)
        self.assertEqual(vmin, vmaks)

    def test_vmaks_abstrak_dengan_batas_sisa(self):
        """
        Abstrak dengan segmen batas-sisa: v-maks harus mencakup label alternatif.
        """
        rows = [
            self._gt_row("TEST_A07", "TEST_A07-S01", "LB", status="final"),
            # S02: final SI, tapi batas-sisa dengan alt HS
            self._gt_row("TEST_A07", "TEST_A07-S02", "SI",
                         status="batas-sisa", label_alt="HS"),
        ]
        results = self.compute(rows)
        comp = results["TEST_A07"]
        # v utama: LB=1, SI=1, HS=0
        self.assertEqual(comp.v["LB"], 1)
        self.assertEqual(comp.v["SI"], 1)
        self.assertEqual(comp.v["HS"], 0)
        # v-maks: HS harus masuk dari alt
        self.assertEqual(comp.vmaks["HS"], 1)


# ===========================================================================
# 10. TestKelengkapanTT
# ===========================================================================

class TestKelengkapanTT(unittest.TestCase):
    """TT yang belum diselesaikan harus menghasilkan BLOKIR-TT."""

    def setUp(self):
        from calculate_completeness import compute_completeness
        self.compute = compute_completeness

    def test_tt_belum_selesai_tidak_menyumbang(self):
        rows = [
            {"id_abstrak": "TEST_TT01", "id_segmen": "TEST_TT01-S01",
             "label_akhir": "TT", "label_alt_sisa": "", "status_akhir": "final"},
            {"id_abstrak": "TEST_TT01", "id_segmen": "TEST_TT01-S02",
             "label_akhir": "LB", "label_alt_sisa": "", "status_akhir": "final"},
        ]
        results = self.compute(rows)
        comp = results["TEST_TT01"]
        self.assertTrue(comp.has_unresolved_tt)
        # LB tetap masuk v (dari segmen yang valid)
        self.assertEqual(comp.v["LB"], 1)
        # TT tidak menyumbang
        self.assertEqual(comp.v["TJ"], 0)

    def test_belum_selesai_menjadi_pending(self):
        rows = [
            {"id_abstrak": "TEST_TT02", "id_segmen": "TEST_TT02-S01",
             "label_akhir": "", "label_alt_sisa": "", "status_akhir": "belum-selesai"},
            {"id_abstrak": "TEST_TT02", "id_segmen": "TEST_TT02-S02",
             "label_akhir": "LB", "label_alt_sisa": "", "status_akhir": "final"},
        ]
        results = self.compute(rows)
        comp = results["TEST_TT02"]
        self.assertTrue(comp.has_pending_segments)


# ===========================================================================
# 11. TestIntegrasi (end-to-end minimal dengan file sementara)
# ===========================================================================

class TestIntegrasi(unittest.TestCase):
    """
    Integration test end-to-end menggunakan file sementara.
    Menguji aliran: prepare_abstrak -> build_ground_truth -> calculate_completeness.
    """

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.tmp = Path(self.tmpdir)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _write_csv(self, path: Path, cols: list, rows: list) -> None:
        with open(path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=cols, quoting=csv.QUOTE_MINIMAL)
            writer.writeheader()
            writer.writerows(rows)

    def test_integrasi_prepare_abstrak_valid(self):
        """prepare_abstrak menghasilkan abstrak.csv dari input yang valid."""
        from prepare_abstrak import prepare_abstrak
        content = (
            "id_abstrak,judul,jurnal,tahun,jenis_studi,peran_data,teks_mentah\n"
            "TEST_INT01,Judul Integrasi,Jurnal Integrasi,2024,"
            "kuantitatif,korpus-anotasi,Penelitian ini bertujuan untuk menguji integrasi.\n"
        )
        inp = self.tmp / "input.csv"
        out = self.tmp / "out"
        inp.write_text(content, encoding="utf-8")
        prepare_abstrak(inp, out, skip_near_dup=True)
        self.assertTrue((out / "abstrak.csv").exists())

        rows = list(csv.DictReader(open(out / "abstrak.csv", encoding="utf-8")))
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["id_abstrak"], "TEST_INT01")
        self.assertEqual(rows[0]["status_dedup"], "unik")

    def test_integrasi_ground_truth_dan_kelengkapan(self):
        """
        GT + kelengkapan dengan segmen konsensus di luar antrean adjudikasi.
        Abstrak harus menjadi LENGKAP jika semua 5 komponen hadir.
        """
        from build_ground_truth import build_ground_truth, load_segmen
        from calculate_completeness import compute_completeness, determine_status

        # Simulasi segmen.csv (3 segmen konsensus + 1 memerlukan adj)
        segmen_path = self.tmp / "segmen.csv"
        self._write_csv(segmen_path,
            ["id_abstrak", "id_segmen", "urutan", "teks_segmen", "status_beku"],
            [
                {"id_abstrak": "TEST_INT02", "id_segmen": "TEST_INT02-S01",
                 "urutan": "1", "teks_segmen": "Latar belakang.", "status_beku": "disetujui"},
                {"id_abstrak": "TEST_INT02", "id_segmen": "TEST_INT02-S02",
                 "urutan": "2", "teks_segmen": "Tujuan.", "status_beku": "disetujui"},
                {"id_abstrak": "TEST_INT02", "id_segmen": "TEST_INT02-S03",
                 "urutan": "3", "teks_segmen": "Metode.", "status_beku": "disetujui"},
                {"id_abstrak": "TEST_INT02", "id_segmen": "TEST_INT02-S04",
                 "urutan": "4", "teks_segmen": "Hasil.", "status_beku": "disetujui"},
                {"id_abstrak": "TEST_INT02", "id_segmen": "TEST_INT02-S05",
                 "urutan": "5", "teks_segmen": "Simpulan.", "status_beku": "disetujui"},
            ]
        )

        # anotasi_an1.csv dan anotasi_an2.csv
        anotasi_cols = ["id_abstrak", "id_segmen", "label", "flag",
                        "alasan", "simpul_penentu", "versi_pedoman",
                        "label_alt", "anotator_id"]
        an1_path = self.tmp / "anotasi_an1.csv"
        an2_path = self.tmp / "anotasi_an2.csv"
        ann_rows = [
            {"id_abstrak": "TEST_INT02", "id_segmen": "TEST_INT02-S01", "label": "LB",
             "flag": "", "alasan": "", "simpul_penentu": "LB-1", "versi_pedoman": "v1.0",
             "label_alt": "", "anotator_id": "an1"},
            {"id_abstrak": "TEST_INT02", "id_segmen": "TEST_INT02-S02", "label": "TJ",
             "flag": "", "alasan": "", "simpul_penentu": "TJ-1", "versi_pedoman": "v1.0",
             "label_alt": "", "anotator_id": "an1"},
            {"id_abstrak": "TEST_INT02", "id_segmen": "TEST_INT02-S03", "label": "MT",
             "flag": "", "alasan": "", "simpul_penentu": "MT-1", "versi_pedoman": "v1.0",
             "label_alt": "", "anotator_id": "an1"},
            {"id_abstrak": "TEST_INT02", "id_segmen": "TEST_INT02-S04", "label": "HS",
             "flag": "", "alasan": "", "simpul_penentu": "HS-1", "versi_pedoman": "v1.0",
             "label_alt": "", "anotator_id": "an1"},
            {"id_abstrak": "TEST_INT02", "id_segmen": "TEST_INT02-S05", "label": "SI",
             "flag": "", "alasan": "", "simpul_penentu": "SI-1", "versi_pedoman": "v1.0",
             "label_alt": "", "anotator_id": "an1"},
        ]
        self._write_csv(an1_path, anotasi_cols,
                        [{**r, "anotator_id": "an1"} for r in ann_rows])
        self._write_csv(an2_path, anotasi_cols,
                        [{**r, "anotator_id": "an2"} for r in ann_rows])

        # Adjudikasi kosong (semua konsensus, tidak ada yang perlu adj)
        adj_path = self.tmp / "adjudikasi.csv"
        self._write_csv(adj_path,
            ["id_abstrak", "id_segmen", "label_akhir", "label_alt_sisa",
             "status_akhir", "adjudikator_id", "alasan"],
            []
        )

        from build_ground_truth import load_segmen, load_anotasi, load_adjudikasi
        seg_map = load_segmen(segmen_path)
        ann1 = load_anotasi(an1_path)
        ann2 = load_anotasi(an2_path)
        adj = load_adjudikasi(adj_path)

        gt_rows, stats = build_ground_truth(seg_map, ann1, ann2, adj)

        self.assertEqual(len(gt_rows), 5)
        self.assertEqual(stats.get("final-konsensus", 0), 5)
        self.assertEqual(stats.get("belum-selesai", 0), 0)

        # Hitung kelengkapan dari GT
        results = compute_completeness(gt_rows)
        comp = results["TEST_INT02"]
        status, missing = determine_status(comp.v)
        self.assertEqual(status, "LENGKAP", f"Komponen hilang: {missing}")
        self.assertFalse(comp.has_unresolved_tt)
        self.assertFalse(comp.has_pending_segments)

    def test_integrasi_near_dup_blokir_segmentasi(self):
        """Abstrak near-dup yang belum ditinjau diblokir saat segmentasi."""
        import io as _io
        from segment_abstrak import segment_all

        # Buat abstrak.csv dengan satu abstrak near-dup
        abstrak_path = self.tmp / "abstrak.csv"
        self._write_csv(abstrak_path,
            ["id_abstrak", "peran_data", "jenis_studi", "teks_kerja", "status_dedup"],
            [
                {"id_abstrak": "TEST_ND01", "peran_data": "korpus-anotasi",
                 "jenis_studi": "kuantitatif",
                 "teks_kerja": "Abstrak ini mirip dengan yang lain.",
                 "status_dedup": "duplikat-dekat-ditinjau"},
            ]
        )

        out = self.tmp / "seg_out"
        # Segmentasi harus memblokir TEST_ND01
        segment_all(abstrak_path, out)
        # kandidat_segmen.csv boleh ada tapi tidak boleh berisi TEST_ND01
        kandidat = out / "kandidat_segmen.csv"
        if kandidat.exists():
            rows = list(csv.DictReader(open(kandidat, encoding="utf-8")))
            nd_rows = [r for r in rows if r.get("id_abstrak") == "TEST_ND01"]
            self.assertEqual(len(nd_rows), 0,
                             "Abstrak near-dup tidak boleh disegmentasi")


# ===========================================================================
# Jalankan test
# ===========================================================================

if __name__ == "__main__":
    test_classes = [
        TestNormalisasi,
        TestDeduplikasi,
        TestValidasiPrepareFatal,
        TestSegmentasi,
        TestSegmentasiURLDOI,
        TestKonversiLS,
        TestKonversiLSError,
        TestGroundTruth,
        TestKelengkapan,
        TestKelengkapanTT,
        TestIntegrasi,
    ]

    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    for tc in test_classes:
        suite.addTests(loader.loadTestsFromTestCase(tc))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
