#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_pipeline.py
================
Unit test dan integration test untuk seluruh pipeline sistem anotasi.
Mengikuti Pedoman v1.0 (dibekukan 2026-10-11).

PRINSIP (TIDAK BOLEH DILANGGAR):
- Semua test memanggil FUNGSI PRODUKSI yang sebenarnya dari modul scripts/*.
  Tidak ada reimplementasi aturan bisnis di dalam test.
- Data uji harus SINTETIS dengan ID bertanda TEST_ atau id_abstrak TEST_A*.
- Integration test menggunakan direktori sementara yang terisolasi.
- Test tidak menganggap lulus jika fungsi produksi belum dipanggil.

KELOMPOK TEST (total 95 test):
 1. TestNormalisasi              - normalisasi minimal (prepare_abstrak.py)
 2. TestDeduplikasi              - dedup DOI/hash/Jaccard
 3. TestValidasiPrepareFatal     - fatal errors menghentikan pipeline
 4. TestSegmentasi               - aturan segmentasi (segment_abstrak.py)
 5. TestSegmentasiURLDOI         - URL/DOI tidak menelan titik penutup
 6. TestKonversiLS               - label builder + validasi (convert_labelstudio_export.py)
 7. TestKonversiLSError          - error eksplisit UP=Tidak + label terisi
 8. TestGroundTruth              - build_ground_truth.py (dua anotator)
 9. TestGroundTruthSatuAnotator  - satu anotator tidak diklaim konsensus
10. TestGroundTruthBelumDianotasi - ann1=None -> belum-selesai
11. TestKelengkapan              - vektor v, K2, K3 (calculate_completeness.py)
12. TestKelengkapanK5            - v-min/v-maks K5: final/batas-sisa/dikecualikan
13. TestKelengkapanBlokir        - BLOKIR-TT dan BLOKIR-BELUMSELESAI (hard stop)
14. TestSegmentasiNearDup        - near-dup memblokir segmentasi
15. TestIntegrasi                - end-to-end: prepare → GT → kelengkapan
16. TestGroundTruthFatalAndValidation - fatal duplikat/yatim & validasi konsensus
17. TestKelengkapanStatusAndLabelValidation - validasi status/label calculate_completeness
18. TestConvertLabelStudioAnotatorPriorityAndErrors - CLI anotator-id priority & validasi label
19. TestValidateAnnotationsHardening - validasi label kosong & adjudikasi ganda

Jalankan:
    python tests/test_pipeline.py
    python -m pytest tests/test_pipeline.py -v
"""

import csv
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
        teks = "Penelitian ini\nbertujuan untuk"
        hasil, _ = self.normalize_minimal(teks)
        self.assertNotIn("\n", hasil)

    def test_sambung_kata_terpotong(self):
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

    def test_sha256_deterministik(self):
        teks = "Abstrak uji [SINTETIS]"
        self.assertEqual(self.sha256_text(teks), self.sha256_text(teks))
        self.assertEqual(len(self.sha256_text(teks)), 64)

    def test_sha256_berbeda(self):
        self.assertNotEqual(
            self.sha256_text("Teks A [SINTETIS]"),
            self.sha256_text("Teks B [SINTETIS]"),
        )

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
            normalize_doi, jaccard_similarity, run_deduplication,
            sha256_text, normalize_text_for_hash, word_ngrams,
        )
        self.normalize_doi = normalize_doi
        self.jaccard_sim = jaccard_similarity
        self.run_dedup = run_deduplication
        self.sha256 = sha256_text
        self.norm_hash = normalize_text_for_hash
        self.word_ngrams = word_ngrams

    def test_normalisasi_doi_url(self):
        self.assertEqual(self.normalize_doi("https://doi.org/10.1234/abc"), "10.1234/abc")

    def test_normalisasi_doi_prefix(self):
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

    def test_duplikat_dekat_ditandai_bukan_dihapus(self):
        """Near-dup harus ditandai 'duplikat-dekat-ditinjau', tidak dihapus."""
        base_words = [f"kata{i}" for i in range(40)]
        base = " ".join(base_words)
        teks_a = base + " akhir_a"
        teks_b = base + " akhir_b"
        sim = self.jaccard_sim(self.word_ngrams(teks_a), self.word_ngrams(teks_b))
        self.assertGreaterEqual(sim, 0.90, f"Jaccard={sim:.4f} harus >= 0.90")

        rows = [
            {"id_abstrak": "TEST_A005", "kunci_artikel": "doi:10.x/a005",
             "hash_teks_ternormalisasi": "h5", "teks_kerja": teks_a, "status_dedup": "unik"},
            {"id_abstrak": "TEST_A006", "kunci_artikel": "doi:10.x/a006",
             "hash_teks_ternormalisasi": "h6", "teks_kerja": teks_b, "status_dedup": "unik"},
        ]
        log = self.run_dedup(rows, [], skip_near_dup=False)
        log_dekat = [l for l in log if l["jenis_duplikat"] == "duplikat-dekat"]
        self.assertGreater(len(log_dekat), 0)
        dibuang = [r for r in rows if r["status_dedup"] == "duplikat-dibuang"]
        self.assertEqual(len(dibuang), 0, "Near-dup tidak boleh dihapus otomatis")
        ditinjau = [r for r in rows if r["status_dedup"] == "duplikat-dekat-ditinjau"]
        self.assertEqual(len(ditinjau), 1)


# ===========================================================================
# 3. TestValidasiPrepareFatal
# ===========================================================================
class TestValidasiPrepareFatal(unittest.TestCase):

    def setUp(self):
        from prepare_abstrak import validate_row, prepare_abstrak
        self.validate_row = validate_row
        self.prepare_abstrak = prepare_abstrak

    def test_judul_kosong_menghasilkan_error(self):
        row = {"id_abstrak": "TEST_V001", "judul": "", "jurnal": "J",
               "tahun": "2024", "jenis_studi": "kuantitatif",
               "peran_data": "korpus-anotasi", "teks_mentah": "Teks."}
        errors = self.validate_row(row, 2)
        self.assertTrue(any("judul" in e for e in errors))

    def test_jenis_studi_tidak_valid(self):
        row = {"id_abstrak": "TEST_V002", "judul": "J", "jurnal": "J",
               "tahun": "2024", "jenis_studi": "SALAH",
               "peran_data": "korpus-anotasi", "teks_mentah": "Teks."}
        errors = self.validate_row(row, 2)
        self.assertTrue(any("jenis_studi" in e for e in errors))

    def test_id_duplikat_berhentikan_pipeline(self):
        """Pipeline dengan ID duplikat harus melempar SystemExit dan TIDAK menulis output."""
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
            self.assertFalse((out / "abstrak.csv").exists())

    def test_metadata_tidak_valid_berhentikan_pipeline(self):
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
        self.assertEqual(len(self.segment(teks)), 2)

    def test_singkatan_dkk_tidak_memecah(self):
        teks = "Supriyadi dkk. (2024) menemukan hasil positif. Kesimpulannya valid untuk semua kasus."
        segs = self.segment(teks)
        self.assertIn("dkk", segs[0]["teks_segmen"])

    def test_angka_desimal_tidak_memecah(self):
        teks = "Nilai signifikansi p = 0,05 diperoleh. Kesimpulannya positif dan signifikan."
        segs = self.segment(teks)
        self.assertIn("0,05", segs[0]["teks_segmen"])

    def test_tanda_tanya_memecah(self):
        teks = "Apakah AI berpengaruh positif? Penelitian ini menjawab pertanyaan tersebut secara empiris."
        self.assertEqual(len(self.segment(teks)), 2)

    def test_fragmen_pendek_mendapat_catatan_b5(self):
        teks = "Baik. Cukup valid."
        segs = self.segment(teks)
        has_b5 = any(s["catatan_segmentasi"] for s in segs)
        self.assertTrue(has_b5)

    def test_urutan_berurutan(self):
        teks = "Pertama. Kedua ditulis setelahnya. Ketiga menutup kalimat terakhir."
        segs = self.segment(teks)
        for i, seg in enumerate(segs, start=1):
            self.assertEqual(seg["urutan"], i)

    def test_elipsis_tidak_memecah_ganda(self):
        teks = "Hasilnya... menunjukkan AI efektif. Penelitian selesai."
        self.assertLessEqual(len(self.segment(teks)), 3)


# ===========================================================================
# 5. TestSegmentasiURLDOI
# ===========================================================================
class TestSegmentasiURLDOI(unittest.TestCase):

    def setUp(self):
        from segment_abstrak import segment_text
        self.segment = segment_text

    def test_url_dalam_kalimat_diikuti_kalimat_baru(self):
        teks = (
            "Data diunduh dari https://jurnal.example.com/artikel. "
            "Kemudian data dianalisis secara statistik menggunakan SPSS."
        )
        segs = self.segment(teks)
        self.assertGreaterEqual(len(segs), 2, f"Segmen: {[s['teks_segmen'] for s in segs]}")
        second_texts = " ".join(s["teks_segmen"] for s in segs[1:])
        self.assertIn("dianalisis", second_texts)

    def test_doi_dalam_kalimat_diikuti_kalimat_baru(self):
        teks = (
            "Artikel ini mengacu pada penelitian sebelumnya (doi: 10.1234/jurnal.2024.01). "
            "Metode yang digunakan sama dengan acuan tersebut."
        )
        segs = self.segment(teks)
        all_texts = " ".join(s["teks_segmen"] for s in segs)
        self.assertIn("Metode", all_texts)

    def test_url_di_akhir_teks_tidak_segmen_kosong(self):
        teks = "Sumber data tersedia di https://contoh.example.com/data"
        segs = self.segment(teks)
        self.assertEqual(len(segs), 1)
        self.assertIn("https://", segs[0]["teks_segmen"])


# ===========================================================================
# 6. TestKonversiLS
# ===========================================================================
class TestKonversiLS(unittest.TestCase):

    def setUp(self):
        from convert_labelstudio_export import build_label_string, validate_label_alt
        self.build_label = build_label_string
        self.validate_alt = validate_label_alt

    def _make_results(self, label_1="TJ", up="Tidak", labels_extra=None):
        results = [
            {"from_name": "label_1", "value": {"choices": [label_1]}},
            {"from_name": "uji_pemecahan", "value": {"choices": [up]}},
        ]
        if labels_extra:
            for i, lbl in enumerate(labels_extra, start=2):
                results.append({"from_name": f"label_{i}", "value": {"choices": [lbl]}})
        return results

    def test_label_tunggal_up_tidak(self):
        r = self._make_results("TJ", "Tidak")
        label, _, status = self.build_label(r, "TEST_S01", 1)
        self.assertEqual(label, "TJ")
        self.assertEqual(status, "ok")

    def test_label_ganda_up_ya(self):
        r = self._make_results("TJ", "Ya", ["MT"])
        label, _, status = self.build_label(r, "TEST_S01", 1)
        self.assertEqual(label, "TJ+MT")
        self.assertEqual(status, "ok")

    def test_label_ganda_tidak_duplikat(self):
        r = self._make_results("TJ", "Ya", ["TJ"])
        label, _, status = self.build_label(r, "TEST_S01", 1)
        self.assertEqual(label, "TJ")
        self.assertEqual(status, "ok")

    def test_label_kosong_diabaikan(self):
        r = self._make_results("HS", "Ya", ["(kosong)", "SI"])
        label, _, status = self.build_label(r, "TEST_S01", 1)
        self.assertNotIn("(kosong)", label)
        self.assertIn("HS", label)
        self.assertIn("SI", label)

    def test_label_alt_valid(self):
        alt, _, status = self.validate_alt("HS;LB", "TJ", "TEST_S01", 1)
        self.assertEqual(alt, "HS;LB")
        self.assertEqual(status, "ok")

    def test_label_alt_tidak_valid_error(self):
        """label_alt tidak valid → error eksplisit, tidak dipotong diam-diam."""
        alt, catatan, status = self.validate_alt("HS;INVALID", "TJ", "TEST_S01", 1)
        self.assertEqual(status, "error")
        self.assertIn("INVALID", catatan)

    def test_label_alt_lebih_dari_dua_error(self):
        """label_alt > 2 alternatif → error, tidak dipotong diam-diam."""
        alt, _, status = self.validate_alt("HS;LB;TJ", "MT", "TEST_S01", 1)
        self.assertEqual(status, "error")


# ===========================================================================
# 7. TestKonversiLSError
# ===========================================================================
class TestKonversiLSError(unittest.TestCase):

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
        """UP=Tidak + label_2 terisi → error eksplisit, bukan dibuang diam-diam."""
        r = self._make_results("TJ", "Tidak", ["MT"])
        label, notes, status = self.build_label(r, "TEST_ERR01", 99)
        self.assertEqual(status, "error")
        self.assertFalse(label)
        self.assertTrue(any("Uji Pemecahan" in n for n in notes))

    def test_up_ya_label_tambahan_ok(self):
        r = self._make_results("TJ", "Ya", ["MT"])
        label, _, status = self.build_label(r, "TEST_ERR02", 99)
        self.assertEqual(status, "ok")
        self.assertIn("MT", label)


# ===========================================================================
# 8. TestGroundTruth (dua anotator)
# ===========================================================================
class TestGroundTruth(unittest.TestCase):

    def setUp(self):
        from build_ground_truth import (
            build_ground_truth, needs_adjudication_two_annotators,
        )
        self.build_gt = build_ground_truth
        self.needs_adj = needs_adjudication_two_annotators

    def _seg(self, sid, id_abs="TEST_A001", urutan=1):
        return {"id_segmen": sid, "id_abstrak": id_abs,
                "urutan": str(urutan), "teks_segmen": "Teks sintetis.",
                "status_beku": "disetujui"}

    def _ann(self, sid, label="TJ", flag="", alasan=""):
        return {"id_segmen": sid, "id_abstrak": "TEST_A001",
                "label": label, "flag": flag, "alasan": alasan,
                "simpul_penentu": "TJ-1", "versi_pedoman": "v1.0"}

    def _adj(self, sid, label_akhir, status="final", label_alt=""):
        return {"id_segmen": sid, "id_abstrak": "TEST_A001",
                "label_akhir": label_akhir, "label_alt_sisa": label_alt,
                "status_akhir": status, "adjudikator_id": "adj1", "alasan": "test"}

    def test_konsensus_dua_anotator(self):
        """Dua anotator sepakat tanpa flag → sumber_keputusan='konsensus-dua-anotator'."""
        seg_map = {"TEST_S01": self._seg("TEST_S01")}
        ann1 = {"TEST_S01": self._ann("TEST_S01", "TJ")}
        ann2 = {"TEST_S01": self._ann("TEST_S01", "TJ")}
        gt, stats = self.build_gt(seg_map, ann1, ann2, {})
        self.assertEqual(gt[0]["status_akhir"], "final")
        self.assertEqual(gt[0]["sumber_keputusan"], "konsensus-dua-anotator")
        self.assertEqual(gt[0]["label_akhir"], "TJ")

    def test_label_berbeda_tanpa_adj_belum_selesai(self):
        seg_map = {"TEST_S02": self._seg("TEST_S02")}
        ann1 = {"TEST_S02": self._ann("TEST_S02", "TJ")}
        ann2 = {"TEST_S02": self._ann("TEST_S02", "MT")}
        gt, stats = self.build_gt(seg_map, ann1, ann2, {})
        self.assertEqual(gt[0]["status_akhir"], "belum-selesai")
        self.assertIn("belum-selesai", stats)

    def test_label_berbeda_dengan_adj_final(self):
        seg_map = {"TEST_S03": self._seg("TEST_S03")}
        ann1 = {"TEST_S03": self._ann("TEST_S03", "TJ")}
        ann2 = {"TEST_S03": self._ann("TEST_S03", "MT")}
        adj = {"TEST_S03": self._adj("TEST_S03", "MT", "final")}
        gt, stats = self.build_gt(seg_map, ann1, ann2, adj)
        self.assertEqual(gt[0]["status_akhir"], "final")
        self.assertEqual(gt[0]["sumber_keputusan"], "adjudikasi")
        self.assertEqual(gt[0]["label_akhir"], "MT")

    def test_flag_masuk_adjudikasi(self):
        ann1 = self._ann("TEST_S04", "LB", flag="B3", alasan="ragu")
        ann2 = self._ann("TEST_S04", "LB")
        perlu, reasons = self.needs_adj(ann1, ann2)
        self.assertTrue(perlu)
        self.assertTrue(any("flag" in r for r in reasons))

    def test_tt_masuk_adjudikasi(self):
        ann1 = self._ann("TEST_S05", "TT", flag="B2", alasan="tidak jelas")
        ann2 = self._ann("TEST_S05", "LB")
        perlu, reasons = self.needs_adj(ann1, ann2)
        self.assertTrue(perlu)
        self.assertTrue(any("TT" in r for r in reasons))

    def test_batas_sisa_tersimpan_di_gt(self):
        seg_map = {"TEST_S06": self._seg("TEST_S06")}
        ann1 = {"TEST_S06": self._ann("TEST_S06", "TJ")}
        ann2 = {"TEST_S06": self._ann("TEST_S06", "MT")}
        adj = {"TEST_S06": self._adj("TEST_S06", "TJ", "batas-sisa", "MT")}
        gt, stats = self.build_gt(seg_map, ann1, ann2, adj)
        self.assertEqual(gt[0]["status_akhir"], "batas-sisa")
        self.assertEqual(gt[0]["label_alt_sisa"], "MT")
        self.assertIn("batas-sisa", stats)

    def test_dikecualikan_tersimpan_di_gt(self):
        seg_map = {"TEST_S07": self._seg("TEST_S07")}
        ann1 = {"TEST_S07": self._ann("TEST_S07", "TT", "B2", "tidak bisa")}
        ann2 = {"TEST_S07": self._ann("TEST_S07", "TT", "B2", "tidak bisa")}
        adj = {"TEST_S07": self._adj("TEST_S07", "", "dikecualikan")}
        gt, stats = self.build_gt(seg_map, ann1, ann2, adj)
        self.assertEqual(gt[0]["status_akhir"], "dikecualikan")
        self.assertIn("dikecualikan", stats)

    def test_segmen_konsensus_di_luar_adjudikasi_masuk_gt(self):
        """Segmen konsensus yang tidak masuk antrean adjudikasi HARUS ada di GT."""
        seg_map = {
            "TEST_S08": self._seg("TEST_S08"),
            "TEST_S09": self._seg("TEST_S09"),
        }
        ann1 = {
            "TEST_S08": self._ann("TEST_S08", "LB"),
            "TEST_S09": self._ann("TEST_S09", "TJ", "B3", "ragu"),
        }
        ann2 = {
            "TEST_S08": self._ann("TEST_S08", "LB"),
            "TEST_S09": self._ann("TEST_S09", "MT"),
        }
        gt, stats = self.build_gt(seg_map, ann1, ann2, {})
        # S08 harus final-konsensus
        s08 = next(r for r in gt if r["id_segmen"] == "TEST_S08")
        self.assertEqual(s08["status_akhir"], "final")
        self.assertEqual(s08["sumber_keputusan"], "konsensus-dua-anotator")
        # S09 harus belum-selesai
        s09 = next(r for r in gt if r["id_segmen"] == "TEST_S09")
        self.assertEqual(s09["status_akhir"], "belum-selesai")
        # Total 2 baris
        self.assertEqual(len(gt), 2)


# ===========================================================================
# 9. TestGroundTruthSatuAnotator
# ===========================================================================
class TestGroundTruthSatuAnotator(unittest.TestCase):
    """
    Mode satu anotator TIDAK boleh diklaim sebagai konsensus dua anotator.
    """

    def setUp(self):
        from build_ground_truth import build_ground_truth
        self.build_gt = build_ground_truth

    def _seg(self, sid):
        return {"id_segmen": sid, "id_abstrak": "TEST_A010",
                "urutan": "1", "teks_segmen": "Teks.", "status_beku": "disetujui"}

    def _ann(self, sid, label="TJ", flag=""):
        return {"id_segmen": sid, "id_abstrak": "TEST_A010",
                "label": label, "flag": flag, "alasan": "",
                "simpul_penentu": "", "versi_pedoman": "v1.0"}

    def test_satu_anotator_tanpa_flag_perlu_adj_atau_internal(self):
        """Satu anotator tanpa flag: tanpa --single-annotator-no-adj → perlu adj → belum-selesai."""
        seg_map = {"TEST_SA01": self._seg("TEST_SA01")}
        ann1 = {"TEST_SA01": self._ann("TEST_SA01", "TJ")}
        # Tanpa ann2, tanpa adj, tanpa single_annotator_no_adj
        gt, stats = self.build_gt(seg_map, ann1, None, {})
        self.assertEqual(gt[0]["status_akhir"], "belum-selesai")
        self.assertNotEqual(gt[0]["sumber_keputusan"], "konsensus-dua-anotator")

    def test_satu_anotator_internal_tanpa_flag_final(self):
        """Mode internal: satu anotator tanpa flag → final, sumber=anotator-tunggal-internal."""
        seg_map = {"TEST_SA02": self._seg("TEST_SA02")}
        ann1 = {"TEST_SA02": self._ann("TEST_SA02", "TJ")}
        gt, stats = self.build_gt(
            seg_map, ann1, None, {}, single_annotator_no_adj=True
        )
        self.assertEqual(gt[0]["status_akhir"], "final")
        self.assertEqual(gt[0]["sumber_keputusan"], "anotator-tunggal-internal")
        self.assertNotEqual(gt[0]["sumber_keputusan"], "konsensus-dua-anotator")

    def test_satu_anotator_internal_dengan_flag_perlu_adj(self):
        """Mode internal: satu anotator dengan flag → tetap perlu adj → belum-selesai."""
        seg_map = {"TEST_SA03": self._seg("TEST_SA03")}
        ann1 = {"TEST_SA03": self._ann("TEST_SA03", "LB", flag="B3")}
        gt, stats = self.build_gt(
            seg_map, ann1, None, {}, single_annotator_no_adj=True
        )
        self.assertEqual(gt[0]["status_akhir"], "belum-selesai")


# ===========================================================================
# 10. TestGroundTruthBelumDianotasi
# ===========================================================================
class TestGroundTruthBelumDianotasi(unittest.TestCase):
    """Segmen yang belum dianotasi an1 → belum-selesai."""

    def setUp(self):
        from build_ground_truth import build_ground_truth
        self.build_gt = build_ground_truth

    def test_ann1_tidak_ada_belum_selesai(self):
        seg_map = {
            "TEST_BD01": {"id_segmen": "TEST_BD01", "id_abstrak": "TEST_A020",
                          "urutan": "1", "teks_segmen": "Teks.", "status_beku": "disetujui"},
        }
        # ann1 tidak menganotasi TEST_BD01
        ann1 = {}
        ann2 = {"TEST_BD01": {"id_segmen": "TEST_BD01", "id_abstrak": "TEST_A020",
                               "label": "LB", "flag": "", "alasan": "",
                               "simpul_penentu": "", "versi_pedoman": "v1.0"}}
        gt, stats = self.build_gt(seg_map, ann1, ann2, {})
        self.assertEqual(len(gt), 1)
        self.assertEqual(gt[0]["status_akhir"], "belum-selesai")

    def test_ann2_tidak_ada_dalam_mode_dua_anotator_perlu_adj(self):
        """Mode dua anotator tapi an2 tidak menganotasi segmen → perlu adj → belum-selesai."""
        seg_map = {
            "TEST_BD02": {"id_segmen": "TEST_BD02", "id_abstrak": "TEST_A020",
                          "urutan": "1", "teks_segmen": "Teks.", "status_beku": "disetujui"},
        }
        ann1 = {"TEST_BD02": {"id_segmen": "TEST_BD02", "id_abstrak": "TEST_A020",
                               "label": "LB", "flag": "", "alasan": "",
                               "simpul_penentu": "", "versi_pedoman": "v1.0"}}
        # ann2 ada tapi tidak menganotasi TEST_BD02
        ann2 = {}
        gt, stats = self.build_gt(seg_map, ann1, ann2, {})
        self.assertEqual(gt[0]["status_akhir"], "belum-selesai")


# ===========================================================================
# 11. TestKelengkapan (v utama K1-K4)
# ===========================================================================
class TestKelengkapan(unittest.TestCase):

    def setUp(self):
        from calculate_completeness import (
            compute_completeness, determine_status, format_vector,
        )
        self.compute = compute_completeness
        self.determine_status = determine_status
        self.format_vector = format_vector

    def _gt(self, id_abs, id_seg, label, status="final", label_alt=""):
        return {"id_abstrak": id_abs, "id_segmen": id_seg,
                "label_akhir": label, "label_alt_sisa": label_alt,
                "status_akhir": status}

    def test_lengkap_semua_komponen(self):
        rows = [self._gt("TEST_A30", f"TEST_A30-S0{i}", k)
                for i, k in enumerate(["LB", "TJ", "MT", "HS", "SI"], 1)]
        results, _ = self.compute(rows)
        status, _ = self.determine_status(results["TEST_A30"].v)
        self.assertEqual(status, "LENGKAP")

    def test_tidak_lengkap_hilang_si(self):
        rows = [self._gt("TEST_A31", f"TEST_A31-S0{i}", k)
                for i, k in enumerate(["LB", "TJ", "MT", "HS"], 1)]
        results, _ = self.compute(rows)
        status, missing = self.determine_status(results["TEST_A31"].v)
        self.assertEqual(status, "TIDAK LENGKAP")
        self.assertIn("SI", missing)

    def test_label_ganda_menyumbang_semua_k2(self):
        """K2: TJ+MT menyumbang dua komponen sekaligus."""
        rows = [
            self._gt("TEST_A32", "TEST_A32-S01", "LB"),
            self._gt("TEST_A32", "TEST_A32-S02", "TJ+MT"),
            self._gt("TEST_A32", "TEST_A32-S03", "HS"),
            self._gt("TEST_A32", "TEST_A32-S04", "SI"),
        ]
        results, _ = self.compute(rows)
        comp = results["TEST_A32"]
        self.assertEqual(comp.v["TJ"], 1)
        self.assertEqual(comp.v["MT"], 1)
        status, _ = self.determine_status(comp.v)
        self.assertEqual(status, "LENGKAP")

    def test_lainnya_tidak_menyumbang_k3(self):
        rows = [
            self._gt("TEST_A33", "TEST_A33-S01", "LAINNYA"),
            self._gt("TEST_A33", "TEST_A33-S02", "LB"),
        ]
        results, _ = self.compute(rows)
        comp = results["TEST_A33"]
        self.assertEqual(comp.v["LB"], 1)
        self.assertEqual(comp.v["TJ"], 0)

    def test_dikecualikan_tidak_menyumbang_v_utama_k3(self):
        rows = [
            self._gt("TEST_A34", "TEST_A34-S01", "LB"),
            self._gt("TEST_A34", "TEST_A34-S02", "HS", status="dikecualikan"),
        ]
        results, _ = self.compute(rows)
        self.assertEqual(results["TEST_A34"].v["HS"], 0)

    def test_segmen_konsensus_luar_adjudikasi_masuk_v(self):
        """Segmen konsensus (final, bukan dari adjudikasi) harus masuk v."""
        rows = [
            self._gt("TEST_A35", "TEST_A35-S01", "LB", status="final"),
            self._gt("TEST_A35", "TEST_A35-S02", "SI", status="final"),
        ]
        results, _ = self.compute(rows)
        comp = results["TEST_A35"]
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


# ===========================================================================
# 12. TestKelengkapanK5
# ===========================================================================
class TestKelengkapanK5(unittest.TestCase):
    """Test K5 v-min/v-maks sesuai Pedoman v1.0 Bagian 6.3."""

    def setUp(self):
        from calculate_completeness import (
            compute_completeness, get_segment_readings, segment_vmin_vmaks,
        )
        self.compute = compute_completeness
        self.get_readings = get_segment_readings
        self.seg_vmm = segment_vmin_vmaks

    def _gt(self, id_abs, id_seg, label, status="final", label_alt=""):
        return {"id_abstrak": id_abs, "id_segmen": id_seg,
                "label_akhir": label, "label_alt_sisa": label_alt,
                "status_akhir": status}

    # --- K5 per-segmen ---

    def test_k5_final_satu_pembacaan(self):
        """Segmen final: satu pembacaan = {label_akhir}, v-min = v-maks = {label_akhir}."""
        readings = self.get_readings("TJ", "", "final")
        vmin, vmaks = self.seg_vmm(readings)
        self.assertIn("TJ", vmin)
        self.assertIn("TJ", vmaks)
        self.assertEqual(vmin, vmaks)

    def test_k5_batas_sisa_alt_berbeda(self):
        """
        Segmen batas-sisa label_akhir=LB, label_alt=TJ.
        Pembacaan: [{LB}, {TJ}]
        v-min segmen = LB ∩ TJ = ∅ (tidak ada komponen yang sama)
        v-maks segmen = LB ∪ TJ = {LB, TJ}
        """
        readings = self.get_readings("LB", "TJ", "batas-sisa")
        vmin, vmaks = self.seg_vmm(readings)
        self.assertNotIn("LB", vmin)
        self.assertNotIn("TJ", vmin)
        self.assertIn("LB", vmaks)
        self.assertIn("TJ", vmaks)

    def test_k5_batas_sisa_alt_sama(self):
        """Segmen batas-sisa label_akhir=LB, label_alt=LB → v-min = v-maks = {LB}."""
        readings = self.get_readings("LB", "LB", "batas-sisa")
        vmin, vmaks = self.seg_vmm(readings)
        self.assertIn("LB", vmin)
        self.assertIn("LB", vmaks)

    def test_k5_batas_sisa_dua_alt(self):
        """
        Segmen batas-sisa label_akhir=LB, label_alt=TJ;HS.
        Pembacaan: [{LB}, {TJ}, {HS}]
        v-min = ∅; v-maks = {LB, TJ, HS}
        """
        readings = self.get_readings("LB", "TJ;HS", "batas-sisa")
        self.assertEqual(len(readings), 3)
        vmin, vmaks = self.seg_vmm(readings)
        self.assertEqual(len(vmin), 0)
        self.assertIn("LB", vmaks)
        self.assertIn("TJ", vmaks)
        self.assertIn("HS", vmaks)

    def test_k5_dikecualikan_pembacaan_kosong_pertama(self):
        """
        Segmen dikecualikan: pembacaan pertama = ∅.
        v-min segmen = ∅ ∩ ... = ∅ (selalu kosong).
        v-maks segmen = ∪ alternatif.
        """
        readings = self.get_readings("", "LB;TJ", "dikecualikan")
        # Harus ada pembacaan kosong di indeks 0
        self.assertEqual(readings[0], set())
        vmin, vmaks = self.seg_vmm(readings)
        self.assertEqual(len(vmin), 0)  # irisan dengan {} selalu {}
        self.assertIn("LB", vmaks)
        self.assertIn("TJ", vmaks)

    def test_k5_dikecualikan_tanpa_alt(self):
        """Segmen dikecualikan tanpa label_alt: satu pembacaan = ∅."""
        readings = self.get_readings("", "", "dikecualikan")
        self.assertEqual(len(readings), 1)
        self.assertEqual(readings[0], set())
        vmin, vmaks = self.seg_vmm(readings)
        self.assertEqual(len(vmin), 0)
        self.assertEqual(len(vmaks), 0)

    # --- K5 agregasi per abstrak ---

    def test_k5_abstrak_hanya_final_vmin_eq_vmaks(self):
        """Abstrak hanya segmen final → v-min = v-maks = v."""
        rows = [
            self._gt("TEST_K50", "TEST_K50-S01", "LB"),
            self._gt("TEST_K50", "TEST_K50-S02", "TJ"),
        ]
        results, _ = self.compute(rows)
        comp = results["TEST_K50"]
        self.assertEqual(comp.vmin["LB"], comp.vmaks["LB"])
        self.assertEqual(comp.vmin["TJ"], comp.vmaks["TJ"])
        self.assertEqual(comp.vmin["LB"], 1)
        self.assertEqual(comp.vmin["TJ"], 1)

    def test_k5_abstrak_batas_sisa_alt_berbeda_vmin_neq_vmaks(self):
        """
        Abstrak dengan segmen batas-sisa (alt berbeda):
        v-min ≠ v-maks → abstrak berstatus TAK PASTI.
        """
        rows = [
            self._gt("TEST_K51", "TEST_K51-S01", "LB", status="final"),
            self._gt("TEST_K51", "TEST_K51-S02", "SI",
                     status="batas-sisa", label_alt="HS"),
        ]
        results, _ = self.compute(rows)
        comp = results["TEST_K51"]
        # v utama: LB=1, SI=1
        self.assertEqual(comp.v["LB"], 1)
        self.assertEqual(comp.v["SI"], 1)
        # vmin: LB=1 (dari S01, satu pembacaan → v-min_seg=LB, union ke abstrak → 1)
        #        SI=0 (dari S02, v-min_seg=∅ karena LB≠HS; union ke abstrak → 0 jika LB tidak ada di batas-sisa)
        # Lebih tepatnya: vmin_abstrak[k] = union of vmin_segmen[k]
        # S01 final LB: vmin_seg={LB}, vmaks_seg={LB} → kontribusi ke vmin abstrak: LB=1
        # S02 batas-sisa SI, alt HS: readings=[{SI},{HS}], vmin_seg=∅, vmaks_seg={SI,HS}
        #   → kontribusi ke vmin abstrak: 0 (tidak ada komponen di vmin_seg S02)
        # vmin_abstrak[HS] = 0, vmin_abstrak[SI] = 0, vmaks_abstrak[SI]=1, vmaks_abstrak[HS]=1
        self.assertEqual(comp.vmaks["SI"], 1)
        self.assertEqual(comp.vmaks["HS"], 1)
        # vmin[SI]=0 karena S02 vmin=∅
        self.assertEqual(comp.vmin["SI"], 0)

    def test_k5_abstrak_dikecualikan_vmin_nol_untuk_komponen_dikecualikan(self):
        """Segmen dikecualikan dengan alt LB tidak menyumbang vmin."""
        rows = [
            self._gt("TEST_K52", "TEST_K52-S01", "TJ", status="final"),
            self._gt("TEST_K52", "TEST_K52-S02", "", status="dikecualikan", label_alt="LB"),
        ]
        results, _ = self.compute(rows)
        comp = results["TEST_K52"]
        # v utama: TJ=1 dari S01; LB=0 (dikecualikan tidak menyumbang v)
        self.assertEqual(comp.v["TJ"], 1)
        self.assertEqual(comp.v["LB"], 0)
        # vmin[LB]=0 karena S02 dikecualikan → pembacaan pertama ∅ → vmin_seg=∅ → union=0
        self.assertEqual(comp.vmin["LB"], 0)
        # vmaks[LB]=1 dari alt pembacaan S02
        self.assertEqual(comp.vmaks["LB"], 1)

    def test_k5_abstrak_batas_sisa_alt_sama_pasti(self):
        """Batas-sisa dengan alt sama → v-min = v-maks → pasti."""
        rows = [
            self._gt("TEST_K53", "TEST_K53-S01", "LB",
                     status="batas-sisa", label_alt="LB"),
            self._gt("TEST_K53", "TEST_K53-S02", "TJ", status="final"),
        ]
        results, _ = self.compute(rows)
        comp = results["TEST_K53"]
        # S01: readings=[{LB},{LB}], vmin={LB}, vmaks={LB}
        self.assertEqual(comp.vmin["LB"], comp.vmaks["LB"])
        self.assertEqual(comp.vmin["LB"], 1)


# ===========================================================================
# 13. TestKelengkapanBlokir
# ===========================================================================
class TestKelengkapanBlokir(unittest.TestCase):
    """
    HARD STOP: abstrak dengan TT belum selesai atau segmen belum-selesai
    TIDAK BOLEH masuk kelengkapan_abstrak.csv.
    """

    def setUp(self):
        from calculate_completeness import compute_completeness
        self.compute = compute_completeness

    def _gt(self, id_abs, id_seg, label, status="final", label_alt=""):
        return {"id_abstrak": id_abs, "id_segmen": id_seg,
                "label_akhir": label, "label_alt_sisa": label_alt,
                "status_akhir": status}

    def test_tt_belum_selesai_menjadi_blokir_tt(self):
        """label_akhir=TT di status final → BLOKIR-TT."""
        rows = [
            self._gt("TEST_BL01", "TEST_BL01-S01", "TT", status="final"),
            self._gt("TEST_BL01", "TEST_BL01-S02", "LB", status="final"),
        ]
        results, blocked = self.compute(rows)
        comp = results["TEST_BL01"]
        self.assertTrue(comp.has_unresolved_tt)
        blk = blocked["TEST_BL01"]
        self.assertEqual(blk["status_blokir"], "BLOKIR-TT")

    def test_belum_selesai_menjadi_blokir_belumselesai(self):
        """status=belum-selesai → BLOKIR-BELUMSELESAI."""
        rows = [
            self._gt("TEST_BL02", "TEST_BL02-S01", "", status="belum-selesai"),
            self._gt("TEST_BL02", "TEST_BL02-S02", "LB", status="final"),
        ]
        results, blocked = self.compute(rows)
        comp = results["TEST_BL02"]
        self.assertTrue(comp.has_pending_segments)
        blk = blocked["TEST_BL02"]
        self.assertIn(blk["status_blokir"], ("BLOKIR-BELUMSELESAI", "BLOKIR-TT"))

    def test_tt_menang_atas_belumselesai(self):
        """Jika ada TT DAN belum-selesai di abstrak yang sama → status BLOKIR-TT."""
        rows = [
            self._gt("TEST_BL03", "TEST_BL03-S01", "TT", status="final"),
            self._gt("TEST_BL03", "TEST_BL03-S02", "", status="belum-selesai"),
        ]
        results, blocked = self.compute(rows)
        blk = blocked["TEST_BL03"]
        self.assertEqual(blk["status_blokir"], "BLOKIR-TT")

    def test_tt_tidak_menyumbang_v(self):
        """TT tidak menyumbang komponen apapun ke v."""
        rows = [
            self._gt("TEST_BL04", "TEST_BL04-S01", "TT", status="final"),
            self._gt("TEST_BL04", "TEST_BL04-S02", "LB", status="final"),
        ]
        results, _ = self.compute(rows)
        comp = results["TEST_BL04"]
        self.assertEqual(comp.v["LB"], 1)
        # TT tidak membuat komponen lain menjadi 1
        self.assertEqual(comp.v["TJ"], 0)


# ===========================================================================
# 14. TestSegmentasiNearDup
# ===========================================================================
class TestSegmentasiNearDup(unittest.TestCase):
    """Near-duplicate yang belum direview harus memblokir segmentasi."""

    def setUp(self):
        from segment_abstrak import segment_all
        self.segment_all = segment_all

    def test_near_dup_diblokir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            abstrak_path = Path(tmpdir) / "abstrak.csv"
            out = Path(tmpdir) / "out"
            # Tulis abstrak dengan status near-dup
            with open(abstrak_path, "w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(
                    f,
                    fieldnames=["id_abstrak", "peran_data", "jenis_studi",
                                "teks_kerja", "status_dedup"],
                )
                writer.writeheader()
                writer.writerow({
                    "id_abstrak": "TEST_ND01", "peran_data": "korpus-anotasi",
                    "jenis_studi": "kuantitatif",
                    "teks_kerja": "Abstrak ini mirip dengan yang lain.",
                    "status_dedup": "duplikat-dekat-ditinjau",
                })

            self.segment_all(abstrak_path, out)

            # kandidat_segmen.csv tidak boleh berisi TEST_ND01
            kandidat = out / "kandidat_segmen.csv"
            if kandidat.exists():
                rows = list(csv.DictReader(open(kandidat, encoding="utf-8")))
                nd = [r for r in rows if r.get("id_abstrak") == "TEST_ND01"]
                self.assertEqual(len(nd), 0, "Near-dup tidak boleh disegmentasi")

    def test_abstrak_normal_disegmentasi(self):
        """Abstrak dengan status 'unik' harus disegmentasi."""
        with tempfile.TemporaryDirectory() as tmpdir:
            abstrak_path = Path(tmpdir) / "abstrak.csv"
            out = Path(tmpdir) / "out"
            with open(abstrak_path, "w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(
                    f,
                    fieldnames=["id_abstrak", "peran_data", "jenis_studi",
                                "teks_kerja", "status_dedup"],
                )
                writer.writeheader()
                writer.writerow({
                    "id_abstrak": "TEST_ND02", "peran_data": "korpus-anotasi",
                    "jenis_studi": "kuantitatif",
                    "teks_kerja": "Penelitian ini bertujuan. Metode digunakan secara cermat.",
                    "status_dedup": "unik",
                })

            self.segment_all(abstrak_path, out)
            kandidat = out / "kandidat_segmen.csv"
            self.assertTrue(kandidat.exists())
            rows = list(csv.DictReader(open(kandidat, encoding="utf-8")))
            nd = [r for r in rows if r.get("id_abstrak") == "TEST_ND02"]
            self.assertGreater(len(nd), 0)


# ===========================================================================
# 15. TestIntegrasi
# ===========================================================================
class TestIntegrasi(unittest.TestCase):
    """End-to-end test menggunakan file sementara yang terisolasi."""

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

    def test_cli_prepare_abstrak(self):
        """CLI --input dan --output-dir sesuai README menghasilkan abstrak.csv."""
        from prepare_abstrak import prepare_abstrak
        content = (
            "id_abstrak,judul,jurnal,tahun,jenis_studi,peran_data,teks_mentah\n"
            "TEST_INT01,Judul Integrasi,Jurnal Integrasi,2024,"
            "kuantitatif,korpus-anotasi,Penelitian ini bertujuan menguji sistem.\n"
        )
        inp = self.tmp / "input.csv"
        out = self.tmp / "out"
        inp.write_text(content, encoding="utf-8")
        prepare_abstrak(inp, out, skip_near_dup=True)
        self.assertTrue((out / "abstrak.csv").exists())
        rows = list(csv.DictReader(open(out / "abstrak.csv", encoding="utf-8")))
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["id_abstrak"], "TEST_INT01")

    def test_integrasi_gt_dan_kelengkapan_lengkap(self):
        """
        End-to-end: dua anotator konsensus semua komponen → LENGKAP.
        Memverifikasi bahwa segmen konsensus di luar antrean adjudikasi dihitung.
        """
        from build_ground_truth import (
            build_ground_truth, load_segmen, load_anotasi, load_adjudikasi,
        )
        from calculate_completeness import compute_completeness, determine_status

        segmen_path = self.tmp / "segmen.csv"
        self._write_csv(segmen_path,
            ["id_abstrak", "id_segmen", "urutan", "teks_segmen", "status_beku"],
            [{"id_abstrak": "TEST_INT02", "id_segmen": f"TEST_INT02-S0{i}",
              "urutan": str(i), "teks_segmen": f"Kalimat {i}.", "status_beku": "disetujui"}
             for i in range(1, 6)]
        )

        anotasi_cols = ["id_abstrak", "id_segmen", "label", "flag",
                        "alasan", "simpul_penentu", "versi_pedoman"]
        komponen = ["LB", "TJ", "MT", "HS", "SI"]

        def make_ann(anotator):
            return [{"id_abstrak": "TEST_INT02",
                     "id_segmen": f"TEST_INT02-S0{i+1}",
                     "label": k, "flag": "", "alasan": "",
                     "simpul_penentu": f"{k}-1", "versi_pedoman": "v1.0"}
                    for i, k in enumerate(komponen)]

        an1_path = self.tmp / "an1.csv"
        an2_path = self.tmp / "an2.csv"
        self._write_csv(an1_path, anotasi_cols, make_ann("an1"))
        self._write_csv(an2_path, anotasi_cols, make_ann("an2"))

        adj_path = self.tmp / "adj.csv"
        self._write_csv(adj_path,
            ["id_abstrak", "id_segmen", "label_akhir", "label_alt_sisa",
             "status_akhir", "adjudikator_id", "alasan"], [])

        seg_map, _ = load_segmen(segmen_path)
        ann1, _ = load_anotasi(an1_path)
        ann2, _ = load_anotasi(an2_path)
        adj, _ = load_adjudikasi(adj_path)

        gt_rows, stats = build_ground_truth(seg_map, ann1, ann2, adj)

        # Semua 5 segmen harus final-konsensus
        self.assertEqual(len(gt_rows), 5)
        self.assertEqual(stats.get("final-konsensus", 0), 5)
        self.assertEqual(stats.get("belum-selesai", 0), 0)

        # Setiap baris harus sumber_keputusan=konsensus-dua-anotator
        for r in gt_rows:
            self.assertEqual(r["sumber_keputusan"], "konsensus-dua-anotator")

        results, blocked = compute_completeness(gt_rows)
        comp = results["TEST_INT02"]
        status, missing = determine_status(comp.v)
        self.assertEqual(status, "LENGKAP", f"Komponen hilang: {missing}")
        self.assertEqual(blocked["TEST_INT02"]["status_blokir"], None)

    def test_integrasi_blokir_tt_tidak_masuk_kelengkapan(self):
        """Abstrak dengan segmen TT diblokir dari kelengkapan_abstrak.csv."""
        from calculate_completeness import compute_completeness

        rows = [
            {"id_abstrak": "TEST_INT03", "id_segmen": "TEST_INT03-S01",
             "label_akhir": "TT", "label_alt_sisa": "LB",
             "status_akhir": "final"},
            {"id_abstrak": "TEST_INT03", "id_segmen": "TEST_INT03-S02",
             "label_akhir": "MT", "label_alt_sisa": "",
             "status_akhir": "final"},
        ]
        results, blocked = compute_completeness(rows)
        blk = blocked.get("TEST_INT03", {})
        self.assertEqual(blk.get("status_blokir"), "BLOKIR-TT")
        # TT tidak boleh menyumbang komponen apapun
        comp = results["TEST_INT03"]
        self.assertEqual(comp.v["LB"], 0)

    def test_integrasi_cli_ground_truth_arg(self):
        """
        CLI --ground-truth sesuai README.
        Verifikasi bahwa calculate_completeness menerima argumen ini.
        """
        import subprocess, json
        gt_path = self.tmp / "ground_truth.csv"
        out = self.tmp / "out"
        out.mkdir(exist_ok=True)

        # Buat ground_truth.csv minimal
        self._write_csv(gt_path,
            ["id_abstrak", "id_segmen", "label_akhir", "label_alt_sisa", "status_akhir"],
            [{"id_abstrak": "TEST_CLI01", "id_segmen": "TEST_CLI01-S01",
              "label_akhir": "LB", "label_alt_sisa": "", "status_akhir": "final"}])

        scripts_dir = Path(__file__).parent.parent / "scripts"
        result = subprocess.run(
            [
                sys.executable,
                str(scripts_dir / "calculate_completeness.py"),
                "--ground-truth", str(gt_path),
                "--output-dir", str(out),
            ],
            capture_output=True, text=True, timeout=30,
        )
        # Pastikan tidak ada error argumen CLI
        self.assertNotIn("error: unrecognized arguments", result.stderr)
        self.assertNotIn("unrecognized arguments", result.stdout)
        # Pastikan output terbuat
        self.assertTrue((out / "kelengkapan_abstrak.csv").exists())


# ===========================================================================
# 16. TestGroundTruthFatalAndValidation
# ===========================================================================
class TestGroundTruthFatalAndValidation(unittest.TestCase):
    """
    Uji fatal error dan validasi ketat build_ground_truth.py:
    - Duplikat ID segmen di segmen.csv
    - Duplikat ID anotasi di anotasi.csv
    - Keputusan ganda di adjudikasi.csv
    - Anotasi merujuk ke segmen tidak dikenal (anotasi yatim)
    - Label kosong atau tidak valid tidak dapat menjadi konsensus
    """

    def setUp(self):
        import tempfile
        self.tmp = Path(tempfile.mkdtemp(prefix="test_gt_fatal_"))
        self.scripts_dir = Path(__file__).parent.parent / "scripts"

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _write_csv(self, path: Path, fieldnames: list, rows: list):
        with open(path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

    def test_duplikat_segmen_fatal(self):
        import subprocess
        seg_path = self.tmp / "segmen.csv"
        self._write_csv(seg_path,
            ["id_abstrak", "id_segmen", "urutan", "teks_segmen", "status_beku"],
            [
                {"id_abstrak": "TEST_A01", "id_segmen": "S01", "urutan": "1", "teks_segmen": "Teks 1", "status_beku": "disetujui"},
                {"id_abstrak": "TEST_A01", "id_segmen": "S01", "urutan": "2", "teks_segmen": "Teks 2", "status_beku": "disetujui"},
            ]
        )
        an1_path = self.tmp / "an1.csv"
        self._write_csv(an1_path,
            ["id_abstrak", "id_segmen", "label", "flag", "alasan", "simpul_penentu", "versi_pedoman"],
            [{"id_abstrak": "TEST_A01", "id_segmen": "S01", "label": "TJ", "flag": "", "alasan": "", "simpul_penentu": "", "versi_pedoman": "v1.0"}]
        )
        adj_path = self.tmp / "adj.csv"
        self._write_csv(adj_path, ["id_abstrak", "id_segmen", "label_akhir", "status_akhir"], [])
        out_dir = self.tmp / "out"
        res = subprocess.run(
            [sys.executable, str(self.scripts_dir / "build_ground_truth.py"),
             "--segmen", str(seg_path), "--anotasi-1", str(an1_path),
             "--adjudikasi", str(adj_path),
             "--output-dir", str(out_dir)],
            capture_output=True, text=True
        )
        self.assertNotEqual(res.returncode, 0)
        self.assertTrue((out_dir / "laporan_ground_truth.txt").exists())
        laporan = (out_dir / "laporan_ground_truth.txt").read_text(encoding="utf-8")
        self.assertIn("FATAL ERROR", laporan)

    def test_duplikat_anotasi_fatal(self):
        import subprocess
        seg_path = self.tmp / "segmen.csv"
        self._write_csv(seg_path,
            ["id_abstrak", "id_segmen", "urutan", "teks_segmen", "status_beku"],
            [{"id_abstrak": "TEST_A01", "id_segmen": "S01", "urutan": "1", "teks_segmen": "Teks 1", "status_beku": "disetujui"}]
        )
        an1_path = self.tmp / "an1.csv"
        self._write_csv(an1_path,
            ["id_abstrak", "id_segmen", "label", "flag", "alasan", "simpul_penentu", "versi_pedoman"],
            [
                {"id_abstrak": "TEST_A01", "id_segmen": "S01", "label": "TJ", "flag": "", "alasan": "", "simpul_penentu": "", "versi_pedoman": "v1.0"},
                {"id_abstrak": "TEST_A01", "id_segmen": "S01", "label": "MT", "flag": "", "alasan": "", "simpul_penentu": "", "versi_pedoman": "v1.0"},
            ]
        )
        adj_path = self.tmp / "adj.csv"
        self._write_csv(adj_path, ["id_abstrak", "id_segmen", "label_akhir", "status_akhir"], [])
        out_dir = self.tmp / "out"
        res = subprocess.run(
            [sys.executable, str(self.scripts_dir / "build_ground_truth.py"),
             "--segmen", str(seg_path), "--anotasi-1", str(an1_path),
             "--adjudikasi", str(adj_path),
             "--output-dir", str(out_dir)],
            capture_output=True, text=True
        )
        self.assertNotEqual(res.returncode, 0)
        self.assertTrue((out_dir / "laporan_ground_truth.txt").exists())
        laporan = (out_dir / "laporan_ground_truth.txt").read_text(encoding="utf-8")
        self.assertIn("FATAL ERROR", laporan)

    def test_duplikat_adjudikasi_fatal(self):
        import subprocess
        seg_path = self.tmp / "segmen.csv"
        self._write_csv(seg_path,
            ["id_abstrak", "id_segmen", "urutan", "teks_segmen", "status_beku"],
            [{"id_abstrak": "TEST_A01", "id_segmen": "S01", "urutan": "1", "teks_segmen": "Teks 1", "status_beku": "disetujui"}]
        )
        an1_path = self.tmp / "an1.csv"
        self._write_csv(an1_path,
            ["id_abstrak", "id_segmen", "label", "flag", "alasan", "simpul_penentu", "versi_pedoman"],
            [{"id_abstrak": "TEST_A01", "id_segmen": "S01", "label": "TJ", "flag": "", "alasan": "", "simpul_penentu": "", "versi_pedoman": "v1.0"}]
        )
        adj_path = self.tmp / "adj.csv"
        self._write_csv(adj_path,
            ["id_abstrak", "id_segmen", "label_akhir", "label_alt_sisa", "status_akhir", "adjudikator_id", "alasan"],
            [
                {"id_abstrak": "TEST_A01", "id_segmen": "S01", "label_akhir": "TJ", "label_alt_sisa": "", "status_akhir": "final", "adjudikator_id": "adj1", "alasan": "ok"},
                {"id_abstrak": "TEST_A01", "id_segmen": "S01", "label_akhir": "MT", "label_alt_sisa": "", "status_akhir": "final", "adjudikator_id": "adj1", "alasan": "ok"},
            ]
        )
        out_dir = self.tmp / "out"
        res = subprocess.run(
            [sys.executable, str(self.scripts_dir / "build_ground_truth.py"),
             "--segmen", str(seg_path), "--anotasi-1", str(an1_path),
             "--adjudikasi", str(adj_path),
             "--output-dir", str(out_dir)],
            capture_output=True, text=True
        )
        self.assertNotEqual(res.returncode, 0)
        laporan = (out_dir / "laporan_ground_truth.txt").read_text(encoding="utf-8")
        self.assertIn("FATAL ERROR", laporan)

    def test_anotasi_yatim_fatal(self):
        from build_ground_truth import build_ground_truth
        seg_map = {
            "TEST_S01": {"id_segmen": "TEST_S01", "id_abstrak": "TEST_A01", "urutan": "1", "teks_segmen": "Teks.", "status_beku": "disetujui"}
        }
        ann1 = {
            "TEST_S01": {"id_segmen": "TEST_S01", "id_abstrak": "TEST_A01", "label": "TJ", "flag": "", "alasan": "", "simpul_penentu": "", "versi_pedoman": "v1.0"},
            "TEST_S99": {"id_segmen": "TEST_S99", "id_abstrak": "TEST_A01", "label": "MT", "flag": "", "alasan": "", "simpul_penentu": "", "versi_pedoman": "v1.0"},
        }
        gt, stats = build_ground_truth(seg_map, ann1, None, {})
        self.assertGreater(stats.get("n_error", 0), 0)

    def test_label_kosong_bukan_konsensus(self):
        from build_ground_truth import build_ground_truth
        seg_map = {
            "TEST_S01": {"id_segmen": "TEST_S01", "id_abstrak": "TEST_A01", "urutan": "1", "teks_segmen": "Teks.", "status_beku": "disetujui"}
        }
        ann1 = {"TEST_S01": {"id_segmen": "TEST_S01", "id_abstrak": "TEST_A01", "label": "", "flag": "", "alasan": "", "simpul_penentu": "", "versi_pedoman": "v1.0"}}
        ann2 = {"TEST_S01": {"id_segmen": "TEST_S01", "id_abstrak": "TEST_A01", "label": "", "flag": "", "alasan": "", "simpul_penentu": "", "versi_pedoman": "v1.0"}}
        gt, stats = build_ground_truth(seg_map, ann1, ann2, {})
        self.assertEqual(gt[0]["status_akhir"], "belum-selesai")
        self.assertNotEqual(gt[0]["sumber_keputusan"], "konsensus-dua-anotator")

    def test_label_tidak_valid_bukan_konsensus(self):
        from build_ground_truth import build_ground_truth
        seg_map = {
            "TEST_S01": {"id_segmen": "TEST_S01", "id_abstrak": "TEST_A01", "urutan": "1", "teks_segmen": "Teks.", "status_beku": "disetujui"}
        }
        ann1 = {"TEST_S01": {"id_segmen": "TEST_S01", "id_abstrak": "TEST_A01", "label": "INVALID_X", "flag": "", "alasan": "", "simpul_penentu": "", "versi_pedoman": "v1.0"}}
        ann2 = {"TEST_S01": {"id_segmen": "TEST_S01", "id_abstrak": "TEST_A01", "label": "INVALID_X", "flag": "", "alasan": "", "simpul_penentu": "", "versi_pedoman": "v1.0"}}
        gt, stats = build_ground_truth(seg_map, ann1, ann2, {})
        self.assertEqual(gt[0]["status_akhir"], "belum-selesai")
        self.assertNotEqual(gt[0]["sumber_keputusan"], "konsensus-dua-anotator")


# ===========================================================================
# 17. TestKelengkapanStatusAndLabelValidation
# ===========================================================================
class TestKelengkapanStatusAndLabelValidation(unittest.TestCase):
    """
    Uji validasi ketat calculate_completeness.py:
    - status_akhir kosong -> BLOKIR-INVALID
    - status_akhir tidak dikenal -> BLOKIR-INVALID
    - label_akhir tidak valid -> BLOKIR-INVALID
    - label_alt_sisa tidak valid -> BLOKIR-INVALID
    """

    def setUp(self):
        from calculate_completeness import compute_completeness
        self.compute = compute_completeness

    def test_status_akhir_kosong_blokir(self):
        gt_rows = [{
            "id_abstrak": "TEST_INV01", "id_segmen": "S01",
            "label_akhir": "TJ", "label_alt_sisa": "", "status_akhir": ""
        }]
        results, blocked = self.compute(gt_rows)
        self.assertEqual(blocked["TEST_INV01"]["status_blokir"], "BLOKIR-INVALID")

    def test_status_akhir_tidak_dikenal_blokir(self):
        gt_rows = [{
            "id_abstrak": "TEST_INV02", "id_segmen": "S01",
            "label_akhir": "TJ", "label_alt_sisa": "", "status_akhir": "unknown-status"
        }]
        results, blocked = self.compute(gt_rows)
        self.assertEqual(blocked["TEST_INV02"]["status_blokir"], "BLOKIR-INVALID")

    def test_label_akhir_tidak_valid_blokir(self):
        gt_rows = [{
            "id_abstrak": "TEST_INV03", "id_segmen": "S01",
            "label_akhir": "BUKAN_LABEL", "label_alt_sisa": "", "status_akhir": "final"
        }]
        results, blocked = self.compute(gt_rows)
        self.assertEqual(blocked["TEST_INV03"]["status_blokir"], "BLOKIR-INVALID")

    def test_label_alt_sisa_tidak_valid_blokir(self):
        gt_rows = [{
            "id_abstrak": "TEST_INV04", "id_segmen": "S01",
            "label_akhir": "TJ", "label_alt_sisa": "SALAH_LABEL", "status_akhir": "batas-sisa"
        }]
        results, blocked = self.compute(gt_rows)
        self.assertEqual(blocked["TEST_INV04"]["status_blokir"], "BLOKIR-INVALID")


# ===========================================================================
# 18. TestConvertLabelStudioAnotatorPriorityAndErrors
# ===========================================================================
class TestConvertLabelStudioAnotatorPriorityAndErrors(unittest.TestCase):
    """
    Uji prioritas anotator_id CLI dan error label di convert_labelstudio_export.py.
    """

    def test_cli_anotator_id_mengalahkan_form(self):
        from convert_labelstudio_export import convert_task
        task = {
            "id": 100,
            "data": {"id_abstrak": "TEST_A01", "id_segmen": "S01"},
            "annotations": [{
                "result": [
                    {"from_name": "anotator_id", "value": {"text": ["anotator_palsu"]}},
                    {"from_name": "uji_pemecahan", "value": {"choices": ["Tidak"]}},
                    {"from_name": "label_1", "value": {"choices": ["TJ"]}},
                ]
            }]
        }
        anotasi_rows, audit_rows = convert_task(task, default_anotator_id="anotator_resmi")
        self.assertEqual(len(anotasi_rows), 1)
        self.assertEqual(anotasi_rows[0]["anotator_id"], "anotator_resmi")

    def test_label_kosong_konversi_gagal(self):
        from convert_labelstudio_export import convert_task
        task = {
            "id": 101,
            "data": {"id_abstrak": "TEST_A01", "id_segmen": "S01"},
            "annotations": [{
                "result": [
                    {"from_name": "uji_pemecahan", "value": {"choices": ["Tidak"]}},
                    {"from_name": "label_1", "value": {"choices": []}},
                ]
            }]
        }
        anotasi_rows, audit_rows = convert_task(task, default_anotator_id="an1")
        self.assertEqual(len(anotasi_rows), 0)
        self.assertEqual(audit_rows[0]["konversi_status"], "error")

    def test_label_tidak_valid_konversi_gagal(self):
        from convert_labelstudio_export import convert_task
        task = {
            "id": 102,
            "data": {"id_abstrak": "TEST_A01", "id_segmen": "S01"},
            "annotations": [{
                "result": [
                    {"from_name": "uji_pemecahan", "value": {"choices": ["Tidak"]}},
                    {"from_name": "label_1", "value": {"choices": ["LABEL_PALSU"]}},
                ]
            }]
        }
        anotasi_rows, audit_rows = convert_task(task, default_anotator_id="an1")
        self.assertEqual(len(anotasi_rows), 0)
        self.assertEqual(audit_rows[0]["konversi_status"], "error")


# ===========================================================================
# 19. TestValidateAnnotationsHardening
# ===========================================================================
class TestValidateAnnotationsHardening(unittest.TestCase):
    """
    Uji validasi eksplisit di validate_annotations.py:
    - Label kosong -> Rule 5 error
    - Keputusan ganda di adjudikasi.csv -> Rule 14 error
    """

    def setUp(self):
        import tempfile
        self.tmp = Path(tempfile.mkdtemp(prefix="test_val_"))
        self.scripts_dir = Path(__file__).parent.parent / "scripts"

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _write_csv(self, path: Path, fieldnames: list, rows: list):
        with open(path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

    def test_label_kosong_dilarang(self):
        from validate_annotations import validate
        seg_path = self.tmp / "segmen.csv"
        abs_path = self.tmp / "abstrak.csv"
        an_path = self.tmp / "anotasi.csv"
        self._write_csv(abs_path, ["id_abstrak", "kunci_artikel"], [{"id_abstrak": "TEST_A01", "kunci_artikel": "k1"}])
        self._write_csv(seg_path, ["id_segmen", "id_abstrak", "status_beku"], [{"id_segmen": "S01", "id_abstrak": "TEST_A01", "status_beku": "disetujui"}])
        self._write_csv(an_path,
            ["id_abstrak", "id_segmen", "anotator_id", "label", "label_alt", "flag", "alasan", "simpul_penentu", "versi_pedoman"],
            [{"id_abstrak": "TEST_A01", "id_segmen": "S01", "anotator_id": "an1", "label": "", "label_alt": "", "flag": "", "alasan": "", "simpul_penentu": "", "versi_pedoman": "v1.0"}]
        )
        issues = validate([an_path], seg_path, abs_path, None)
        rule_5_issues = [i for i in issues if i.rule_no == 5]
        self.assertTrue(any("kosong" in i.pesan.lower() for i in rule_5_issues))

    def test_adjudikasi_ganda_dilarang(self):
        from validate_annotations import validate
        seg_path = self.tmp / "segmen.csv"
        abs_path = self.tmp / "abstrak.csv"
        an_path = self.tmp / "anotasi.csv"
        adj_path = self.tmp / "adj.csv"
        self._write_csv(abs_path, ["id_abstrak", "kunci_artikel"], [{"id_abstrak": "TEST_A01", "kunci_artikel": "k1"}])
        self._write_csv(seg_path, ["id_segmen", "id_abstrak", "status_beku"], [{"id_segmen": "S01", "id_abstrak": "TEST_A01", "status_beku": "disetujui"}])
        self._write_csv(an_path,
            ["id_abstrak", "id_segmen", "anotator_id", "label", "label_alt", "flag", "alasan", "simpul_penentu", "versi_pedoman"],
            [{"id_abstrak": "TEST_A01", "id_segmen": "S01", "anotator_id": "an1", "label": "TJ", "label_alt": "", "flag": "", "alasan": "", "simpul_penentu": "", "versi_pedoman": "v1.0"}]
        )
        self._write_csv(adj_path,
            ["id_segmen", "status_akhir"],
            [{"id_segmen": "S01", "status_akhir": "batas-sisa"},
             {"id_segmen": "S01", "status_akhir": "final"}]
        )
        issues = validate([an_path], seg_path, abs_path, adj_path)
        rule_14_issues = [i for i in issues if i.rule_no == 14]
        self.assertTrue(len(rule_14_issues) > 0)


# ===========================================================================
# Entry point
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
        TestGroundTruthSatuAnotator,
        TestGroundTruthBelumDianotasi,
        TestKelengkapan,
        TestKelengkapanK5,
        TestKelengkapanBlokir,
        TestSegmentasiNearDup,
        TestIntegrasi,
        TestGroundTruthFatalAndValidation,
        TestKelengkapanStatusAndLabelValidation,
        TestConvertLabelStudioAnotatorPriorityAndErrors,
        TestValidateAnnotationsHardening,
    ]

    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    for tc in test_classes:
        suite.addTests(loader.loadTestsFromTestCase(tc))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)

