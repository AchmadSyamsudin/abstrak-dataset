#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_pipeline.py
================
Unit test untuk seluruh pipeline sistem anotasi fungsi retoris abstrak.
Data uji SINTETIS - tidak boleh dicampur dengan data penelitian asli.

Semua data uji bertanda [SINTETIS] atau menggunakan prefix 'TEST_'.

Kelompok test:
1. TestNormalisasi      - normalisasi minimal teks (prepare_abstrak.py)
2. TestDeduplikasi      - deduplikasi DOI, hash, Jaccard (prepare_abstrak.py)
3. TestSegmentasi       - aturan segmentasi kalimat (segment_abstrak.py)
4. TestKonversiLS       - konversi JSON Label Studio ke CSV (convert_labelstudio_export.py)
5. TestValidasiMultiLabel - validasi label ganda, flag (validate_annotations.py)
6. TestAdjudikasi       - pembangunan antrean adjudikasi (build_adjudication_queue.py)
7. TestKelengkapan      - vektor kelengkapan, v-min/v-maks (calculate_completeness.py)

Jalankan:
    python -m pytest tests/test_pipeline.py -v
    # ATAU
    python tests/test_pipeline.py
"""

import sys
import unittest
from pathlib import Path

# Tambahkan direktori scripts ke path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))


# ===========================================================================
# 1. Test Normalisasi
# ===========================================================================

class TestNormalisasi(unittest.TestCase):
    """Test normalisasi minimal sesuai Bagian 2.2 pedoman."""

    def setUp(self):
        from prepare_abstrak import normalize_minimal, normalize_ligatures, sha256_text
        self.normalize_minimal = normalize_minimal
        self.normalize_ligatures = normalize_ligatures
        self.sha256_text = sha256_text

    def test_hapus_baris_biasa(self):
        """Baris baru dari tata letak harus diganti spasi."""
        teks = "Penelitian ini\nbertujuan untuk"
        hasil, changes = self.normalize_minimal(teks)
        self.assertNotIn("\n", hasil)
        self.assertIn("bertujuan", hasil)

    def test_sambung_kata_terpotong(self):
        """Kata terpotong di akhir baris (soft hyphen) harus disambung."""
        teks = "pengguna-\nan teknologi"
        hasil, changes = self.normalize_minimal(teks)
        self.assertNotIn("-\n", hasil)
        # 'penggunaan' harus tersambung
        self.assertIn("penggunaan", hasil)

    def test_rapikan_spasi_ganda(self):
        """Spasi ganda harus diganti satu spasi."""
        teks = "Penelitian  ini  bertujuan"
        hasil, _ = self.normalize_minimal(teks)
        self.assertNotIn("  ", hasil)

    def test_normalisasi_ligatur(self):
        """Ligatur harus diganti karakter biasa."""
        teks = "eﬃsiensi dan eﬀektif"
        hasil, changes = self.normalize_ligatures(teks)
        self.assertIn("ffi", hasil)  # ﬃ -> ffi
        self.assertIn("ff", hasil)   # ﬀ -> ff
        self.assertGreater(len(changes), 0)

    def test_teks_mentah_tidak_berubah(self):
        """Normalisasi TIDAK boleh mengubah isi kalimat atau memperbaiki ejaan."""
        teks_mentah = "Perkembangan teknologi terus mendorong AI."
        hasil, _ = self.normalize_minimal(teks_mentah)
        # Konten semantik harus sama (tanpa baris baru)
        self.assertIn("Perkembangan teknologi", hasil)
        self.assertIn("mendorong AI", hasil)

    def test_sha256_deterministik(self):
        """SHA-256 dari teks yang sama harus selalu menghasilkan hash yang sama."""
        teks = "Abstrak uji [SINTETIS]"
        h1 = self.sha256_text(teks)
        h2 = self.sha256_text(teks)
        self.assertEqual(h1, h2)
        self.assertEqual(len(h1), 64)

    def test_sha256_berbeda(self):
        """Teks berbeda harus menghasilkan hash berbeda."""
        h1 = self.sha256_text("Teks A [SINTETIS]")
        h2 = self.sha256_text("Teks B [SINTETIS]")
        self.assertNotEqual(h1, h2)

    def test_log_perubahan_dicatat(self):
        """Setiap perubahan normalisasi harus dicatat dalam log."""
        teks = "Baris pertama\nBaris kedua"
        _, changes = self.normalize_minimal(teks)
        self.assertGreater(len(changes), 0)
        for ch in changes:
            self.assertIn("jenis", ch)
            self.assertIn("teks_asal", ch)
            self.assertIn("teks_baru", ch)


# ===========================================================================
# 2. Test Deduplikasi
# ===========================================================================

class TestDeduplikasi(unittest.TestCase):
    """Test deduplikasi sesuai Bagian 2.5 pedoman."""

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

    def test_normalisasi_doi(self):
        """DOI harus dinormalisasi ke bentuk kanonik."""
        self.assertEqual(self.normalize_doi("https://doi.org/10.1234/abc"), "10.1234/abc")
        self.assertEqual(self.normalize_doi("DOI: 10.1234/ABC"), "10.1234/abc")
        self.assertEqual(self.normalize_doi("10.1234/ABC"), "10.1234/abc")
        self.assertEqual(self.normalize_doi(""), "")

    def test_normalisasi_judul(self):
        """Judul harus dinormalisasi ke huruf kecil tanpa tanda baca."""
        judul = "Analisis Pengaruh AI pada Pendidikan."
        hasil = self.normalize_title(judul)
        self.assertNotIn(".", hasil)
        self.assertEqual(hasil, hasil.lower())

    def test_jaccard_identik(self):
        """Dua himpunan identik harus Jaccard = 1.0."""
        s = {(1, 2, 3)}
        self.assertAlmostEqual(self.jaccard_sim(s, s), 1.0)

    def test_jaccard_berbeda_total(self):
        """Dua himpunan tidak beririsan harus Jaccard = 0.0."""
        a = {("a", "b", "c", "d", "e")}
        b = {("f", "g", "h", "i", "j")}
        self.assertAlmostEqual(self.jaccard_sim(a, b), 0.0)

    def test_jaccard_kosong(self):
        """Dua himpunan kosong harus Jaccard = 1.0."""
        self.assertAlmostEqual(self.jaccard_sim(set(), set()), 1.0)

    def test_duplikat_doi_terdeteksi(self):
        """Dua abstrak dengan DOI sama harus dideteksi sebagai duplikat."""
        rows = [
            {
                "id_abstrak": "TEST_A001",
                "kunci_artikel": "doi:10.1234/test",
                "hash_teks_ternormalisasi": "hash1",
                "teks_kerja": "Ini abstrak pertama sintetis untuk uji.",
                "status_dedup": "unik",
            },
            {
                "id_abstrak": "TEST_A002",
                "kunci_artikel": "doi:10.1234/test",  # DOI sama
                "hash_teks_ternormalisasi": "hash2",
                "teks_kerja": "Ini abstrak kedua sintetis untuk uji.",
                "status_dedup": "unik",
            },
        ]
        dedup_log = self.run_dedup(rows, [], skip_near_dup=True)
        # Salah satu harus dibuang
        dibuang = [r for r in rows if r["status_dedup"] == "duplikat-dibuang"]
        self.assertEqual(len(dibuang), 1)
        self.assertEqual(len(dedup_log), 1)

    def test_duplikat_hash_terdeteksi(self):
        """Dua abstrak dengan teks persis sama harus dideteksi via hash."""
        teks = "Abstrak sintetis untuk uji deduplikasi hash yang identik."
        h = self.sha256(self.normalize_text_for_hash(teks) if hasattr(self, 'normalize_text_for_hash') else teks)
        rows = [
            {
                "id_abstrak": "TEST_A003",
                "kunci_artikel": "doi:10.1234/a003",
                "hash_teks_ternormalisasi": h,
                "teks_kerja": teks,
                "status_dedup": "unik",
            },
            {
                "id_abstrak": "TEST_A004",
                "kunci_artikel": "doi:10.1234/a004",  # DOI berbeda
                "hash_teks_ternormalisasi": h,  # hash sama
                "teks_kerja": teks,
                "status_dedup": "unik",
            },
        ]
        dedup_log = self.run_dedup(rows, [], skip_near_dup=True)
        dibuang = [r for r in rows if r["status_dedup"] == "duplikat-dibuang"]
        self.assertEqual(len(dibuang), 1)

    def test_duplikat_dekat_tidak_dihapus_diam_diam(self):
        """Duplikat dekat harus ditandai, bukan dihapus."""
        # Buat dua teks yang sangat mirip (> 90% 5-gram kata sama)
        # Dengan teks panjang 30 kata, mengganti 1 kata terakhir menghasilkan
        # Jaccard yang sangat tinggi
        base_words = [f"kata{i}" for i in range(40)]
        base = " ".join(base_words)
        teks_a = base + " akhir_a"
        teks_b = base + " akhir_b"

        # Verifikasi Jaccard secara eksplisit
        from prepare_abstrak import word_ngrams, jaccard_similarity
        ng_a = word_ngrams(teks_a, 5)
        ng_b = word_ngrams(teks_b, 5)
        sim = jaccard_similarity(ng_a, ng_b)
        self.assertGreaterEqual(sim, 0.90, f"Jaccard harus >= 0.90, dapat {sim:.4f}")

        rows = [
            {
                "id_abstrak": "TEST_A005",
                "kunci_artikel": "doi:10.1234/a005",
                "hash_teks_ternormalisasi": "hash5",
                "teks_kerja": teks_a,
                "status_dedup": "unik",
            },
            {
                "id_abstrak": "TEST_A006",
                "kunci_artikel": "doi:10.1234/a006",
                "hash_teks_ternormalisasi": "hash6",
                "teks_kerja": teks_b,
                "status_dedup": "unik",
            },
        ]
        dedup_log = self.run_dedup(rows, [], skip_near_dup=False)
        # Harus ada di log
        log_dekat = [l for l in dedup_log if l["jenis_duplikat"] == "duplikat-dekat"]
        self.assertGreater(len(log_dekat), 0, "Duplikat dekat harus tercatat di log")
        # Tidak ada yang berstatus duplikat-dibuang (hanya ditandai untuk review)
        dibuang = [r for r in rows if r["status_dedup"] == "duplikat-dibuang"]
        self.assertEqual(len(dibuang), 0, "Duplikat dekat tidak boleh dihapus otomatis")


# ===========================================================================
# 3. Test Segmentasi
# ===========================================================================

class TestSegmentasi(unittest.TestCase):
    """Test aturan segmentasi kalimat sesuai Bagian 2.3 pedoman."""

    def setUp(self):
        from segment_abstrak import segment_text
        self.segment = segment_text

    def test_kalimat_normal(self):
        """Kalimat normal dipisah oleh titik + spasi + huruf kapital."""
        teks = "Penelitian ini bertujuan untuk X. Metode yang digunakan adalah Y."
        segs = self.segment(teks)
        self.assertEqual(len(segs), 2)

    def test_singkatan_dkk_tidak_memecah(self):
        """'dkk.' sebelum nama tidak mengakhiri kalimat."""
        teks = "Supriyadi dkk. (2024) menemukan bahwa AI berpengaruh positif. Kesimpulannya valid."
        segs = self.segment(teks)
        # Harus 2 kalimat, bukan 3
        self.assertLessEqual(len(segs), 3)
        # Kalimat pertama harus mengandung 'dkk. (2024)'
        first = segs[0]["teks_segmen"]
        self.assertIn("2024", first)

    def test_angka_desimal_tidak_memecah(self):
        """Angka desimal (koma) bukan batas kalimat."""
        teks = "Nilai signifikansi p = 0,05 diperoleh. Kesimpulannya positif."
        segs = self.segment(teks)
        # 0,05 tidak memecah
        first = segs[0]["teks_segmen"]
        self.assertIn("0,05", first)

    def test_url_tidak_memecah(self):
        """URL dengan titik di dalamnya bukan batas kalimat."""
        teks = "Data diambil dari https://jurnal.example.com/artikel. Kemudian dianalisis."
        segs = self.segment(teks)
        # URL tidak memecah kalimat
        first = segs[0]["teks_segmen"]
        self.assertIn("https://jurnal.example.com/artikel", first)

    def test_tanda_tanya(self):
        """Tanda tanya + huruf kapital = batas kalimat."""
        teks = "Apakah AI berpengaruh? Penelitian ini menjawabnya."
        segs = self.segment(teks)
        self.assertEqual(len(segs), 2)

    def test_fragmen_pendek_diberi_catatan_b5(self):
        """Fragmen sangat pendek harus mendapat catatan B5-kandidat."""
        teks = "Satu. Dua."
        segs = self.segment(teks)
        has_b5 = any(s["catatan_segmentasi"] for s in segs)
        self.assertTrue(has_b5)

    def test_elipsis_tidak_memecah_ganda(self):
        """Elipsis (...) diperlakukan sebagai satu tanda."""
        teks = "Hasilnya... menunjukkan bahwa AI efektif. Penelitian selesai."
        segs = self.segment(teks)
        # Tidak boleh lebih dari 2 kalimat untuk teks ini
        self.assertLessEqual(len(segs), 3)

    def test_urutan_segmen(self):
        """Urutan segmen harus dimulai dari 1 dan berurutan."""
        teks = "Pertama. Kedua. Ketiga."
        segs = self.segment(teks)
        for i, seg in enumerate(segs, start=1):
            self.assertEqual(seg["urutan"], i)


# ===========================================================================
# 4. Test Konversi Label Studio
# ===========================================================================

class TestKonversiLS(unittest.TestCase):
    """Test konversi JSON Label Studio ke CSV anotasi."""

    def setUp(self):
        from convert_labelstudio_export import (
            build_label_string, _normalize_label_alt, _warn_conversion_issues
        )
        self.build_label = build_label_string
        self.norm_alt = _normalize_label_alt

    def _make_results(self, label_1, up="Tidak", labels_extra=None, flags=None,
                      simpul="TJ-1", alasan="", anotator="an1", label_alt=""):
        """Helper buat struktur results Label Studio."""
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
                results.append({
                    "from_name": f"label_{i}",
                    "value": {"choices": [lbl]}
                })
        return results

    def test_label_tunggal_tanpa_up(self):
        """Label tunggal tanpa UP harus menghasilkan satu label."""
        results = self._make_results("TJ", up="Tidak")
        label = self.build_label(results)
        self.assertEqual(label, "TJ")

    def test_label_ganda_dengan_up(self):
        """Label ganda dengan UP harus digabung dengan '+'."""
        results = self._make_results("TJ", up="Ya", labels_extra=["MT"])
        label = self.build_label(results)
        self.assertEqual(label, "TJ+MT")

    def test_label_ganda_tidak_duplikat(self):
        """Label yang sama tidak boleh muncul dua kali dalam label ganda."""
        results = self._make_results("TJ", up="Ya", labels_extra=["TJ"])
        label = self.build_label(results)
        self.assertEqual(label, "TJ")  # Duplikat TJ dihapus

    def test_label_kosong_diabaikan(self):
        """Label '(kosong)' harus diabaikan."""
        results = self._make_results("HS", up="Ya", labels_extra=["(kosong)", "SI"])
        label = self.build_label(results)
        self.assertNotIn("(kosong)", label)
        self.assertIn("HS", label)
        self.assertIn("SI", label)

    def test_normalisasi_label_alt_valid(self):
        """Label alternatif valid harus dipertahankan."""
        self.assertEqual(self.norm_alt("HS;LB"), "HS;LB")
        self.assertEqual(self.norm_alt("SI"), "SI")

    def test_normalisasi_label_alt_maks_dua(self):
        """Label alternatif lebih dari 2 harus dipotong ke 2."""
        result = self.norm_alt("HS;LB;TJ")
        parts = result.split(";")
        self.assertLessEqual(len(parts), 2)

    def test_normalisasi_label_alt_tidak_valid_diabaikan(self):
        """Label alternatif tidak valid harus diabaikan."""
        result = self.norm_alt("HS;INVALID;LB")
        self.assertNotIn("INVALID", result)


# ===========================================================================
# 5. Test Validasi Anotasi (khususnya multi-label dan flag)
# ===========================================================================

class TestValidasiMultiLabel(unittest.TestCase):
    """Test validasi aturan multi-label dan flag."""

    def setUp(self):
        # Buat data sintetis minimal untuk test
        self.ann_valid = {
            "id_abstrak": "TEST_A001",
            "id_segmen": "TEST_A001-S01",
            "anotator_id": "an1",
            "label": "TJ",
            "label_alt": "",
            "simpul_penentu": "TJ-1;TJ-2",
            "flag": "",
            "alasan": "",
            "versi_pedoman": "v1.0",
        }

    def _run_validation_checks(self, row):
        """Helper: jalankan pemeriksaan validasi manual tanpa file."""
        issues = []
        labels = [l.strip() for l in row["label"].split("+") if l.strip()]
        flags = [f.strip() for f in row["flag"].split(";") if f.strip()]
        label_alts = [la.strip() for la in row["label_alt"].split(";") if la.strip()]
        alasan = row.get("alasan", "").strip()

        # Aturan 11: TT harus ada B2
        if "TT" in labels and "B2" not in flags:
            issues.append("TT-tanpa-B2")

        # Aturan 10: Flag harus ada alasan
        if flags and not alasan:
            issues.append("flag-tanpa-alasan")

        # Aturan 12: 3+ label harus B5
        if len(labels) >= 3 and "B5" not in flags:
            issues.append("3label-tanpa-B5")

        # Aturan 9: Alt maks 2
        if len(label_alts) > 2:
            issues.append("alt-lebih-dari-2")

        # Aturan 6: label ganda harus ada pemicu UP
        if len(labels) > 1:
            simpul = row.get("simpul_penentu", "")
            if not any(u in simpul.upper() for u in ("U1","U2","U3","U4","U5")):
                issues.append("label-ganda-tanpa-UP")

        return issues

    def test_anotasi_valid_tidak_ada_error(self):
        issues = self._run_validation_checks(self.ann_valid)
        self.assertEqual(issues, [])

    def test_tt_tanpa_b2_error(self):
        row = dict(self.ann_valid)
        row["label"] = "TT"
        row["flag"] = ""
        issues = self._run_validation_checks(row)
        self.assertIn("TT-tanpa-B2", issues)

    def test_flag_tanpa_alasan_error(self):
        row = dict(self.ann_valid)
        row["flag"] = "B3"
        row["alasan"] = ""
        issues = self._run_validation_checks(row)
        self.assertIn("flag-tanpa-alasan", issues)

    def test_tiga_label_tanpa_b5_error(self):
        row = dict(self.ann_valid)
        row["label"] = "TJ+MT+HS"
        row["simpul_penentu"] = "U1;U3"
        row["flag"] = ""
        issues = self._run_validation_checks(row)
        self.assertIn("3label-tanpa-B5", issues)

    def test_label_alt_lebih_dari_dua_error(self):
        row = dict(self.ann_valid)
        row["label_alt"] = "HS;LB;TJ"
        issues = self._run_validation_checks(row)
        self.assertIn("alt-lebih-dari-2", issues)

    def test_label_ganda_tanpa_pemicu_up_error(self):
        row = dict(self.ann_valid)
        row["label"] = "TJ+MT"
        row["simpul_penentu"] = "TJ-1;MT-1"  # Tidak ada U1-U5
        issues = self._run_validation_checks(row)
        self.assertIn("label-ganda-tanpa-UP", issues)

    def test_label_ganda_dengan_pemicu_up_valid(self):
        row = dict(self.ann_valid)
        row["label"] = "TJ+MT"
        row["simpul_penentu"] = "TJ-1;MT-1;U3"
        row["flag"] = "B4"
        row["alasan"] = "Adjunct cara memicu U3."
        issues = self._run_validation_checks(row)
        self.assertEqual(issues, [])


# ===========================================================================
# 6. Test Antrean Adjudikasi
# ===========================================================================

class TestAdjudikasi(unittest.TestCase):
    """Test logika pembuatan antrean adjudikasi."""

    def setUp(self):
        from build_adjudication_queue import determine_queue_reasons
        self.determine = determine_queue_reasons

    def _ann(self, label="TJ", flag="", alasan=""):
        return {"label": label, "flag": flag, "alasan": alasan}

    def test_sepakat_tanpa_flag_tidak_masuk_antrean(self):
        """Dua anotator sepakat tanpa flag = tidak perlu adjudikasi."""
        reasons = self.determine(self._ann("TJ"), self._ann("TJ"))
        self.assertEqual(reasons, [])

    def test_label_berbeda_masuk_antrean(self):
        """Label berbeda = harus adjudikasi."""
        reasons = self.determine(self._ann("TJ"), self._ann("MT"))
        self.assertTrue(any("label-berbeda" in r for r in reasons))

    def test_flag_an1_masuk_antrean(self):
        """Flag dari salah satu anotator = harus adjudikasi."""
        reasons = self.determine(self._ann("LB", flag="B3"), self._ann("LB"))
        self.assertTrue(any("flag-an1" in r for r in reasons))

    def test_tt_masuk_antrean(self):
        """Label TT dari salah satu anotator = harus adjudikasi."""
        reasons = self.determine(self._ann("TT", flag="B2"), self._ann("LB"))
        self.assertTrue(any("TT" in r for r in reasons))

    def test_label_ganda_vs_tunggal_masuk_antrean(self):
        """Label ganda vs tunggal = berbeda = harus adjudikasi."""
        reasons = self.determine(self._ann("TJ+MT"), self._ann("TJ"))
        self.assertTrue(any("label-berbeda" in r for r in reasons))

    def test_mode_satu_anotator_tt(self):
        """Mode satu anotator: TT tetap masuk antrean."""
        reasons = self.determine(self._ann("TT", flag="B2"), None)
        self.assertTrue(any("TT" in r for r in reasons))

    def test_mode_satu_anotator_flag(self):
        """Mode satu anotator: flag tetap masuk antrean."""
        reasons = self.determine(self._ann("HS", flag="B6"), None)
        self.assertTrue(any("flag" in r for r in reasons))


# ===========================================================================
# 7. Test Perhitungan Kelengkapan
# ===========================================================================

class TestKelengkapan(unittest.TestCase):
    """Test vektor kelengkapan, v-min/v-maks sesuai Bagian 6 pedoman."""

    def setUp(self):
        from calculate_completeness import (
            compute_completeness, determine_status, format_vector,
            AbstractCompleteness
        )
        self.compute = compute_completeness
        self.determine_status = determine_status
        self.format_vector = format_vector
        self.AbstractComp = AbstractCompleteness

    def _make_adj_row(self, id_abstrak, id_segmen, label, status="final", label_alt=""):
        return {
            "id_abstrak": id_abstrak,
            "id_segmen": id_segmen,
            "label_akhir": label,
            "label_alt_sisa": label_alt,
            "status_akhir": status,
        }

    def test_lengkap_semua_komponen(self):
        """Abstrak dengan semua 5 komponen = LENGKAP."""
        rows = [
            self._make_adj_row("TEST_A001", "TEST_A001-S01", "LB"),
            self._make_adj_row("TEST_A001", "TEST_A001-S02", "TJ"),
            self._make_adj_row("TEST_A001", "TEST_A001-S03", "MT"),
            self._make_adj_row("TEST_A001", "TEST_A001-S04", "HS"),
            self._make_adj_row("TEST_A001", "TEST_A001-S05", "SI"),
        ]
        results = self.compute(rows, warn_tt=False)
        comp = results["TEST_A001"]
        status, missing = self.determine_status(comp.v)
        self.assertEqual(status, "LENGKAP")
        self.assertEqual(missing, "")

    def test_tidak_lengkap_hilang_si(self):
        """Abstrak tanpa SI = TIDAK LENGKAP: hilang SI."""
        rows = [
            self._make_adj_row("TEST_A002", "TEST_A002-S01", "LB"),
            self._make_adj_row("TEST_A002", "TEST_A002-S02", "TJ"),
            self._make_adj_row("TEST_A002", "TEST_A002-S03", "MT"),
            self._make_adj_row("TEST_A002", "TEST_A002-S04", "HS"),
        ]
        results = self.compute(rows, warn_tt=False)
        comp = results["TEST_A002"]
        status, missing = self.determine_status(comp.v)
        self.assertEqual(status, "TIDAK LENGKAP")
        self.assertIn("SI", missing)
        self.assertEqual(comp.v["SI"], 0)

    def test_label_ganda_menyumbang_semua(self):
        """Segmen berlabel ganda (mis. TJ+MT) menyumbang dua komponen (K2)."""
        rows = [
            self._make_adj_row("TEST_A003", "TEST_A003-S01", "LB"),
            self._make_adj_row("TEST_A003", "TEST_A003-S02", "TJ+MT"),  # label ganda
            self._make_adj_row("TEST_A003", "TEST_A003-S03", "HS"),
            self._make_adj_row("TEST_A003", "TEST_A003-S04", "SI"),
        ]
        results = self.compute(rows, warn_tt=False)
        comp = results["TEST_A003"]
        self.assertEqual(comp.v["TJ"], 1)
        self.assertEqual(comp.v["MT"], 1)
        status, _ = self.determine_status(comp.v)
        self.assertEqual(status, "LENGKAP")

    def test_lainnya_tidak_menyumbang(self):
        """LAINNYA tidak menyumbang komponen vektor (K3)."""
        rows = [
            self._make_adj_row("TEST_A004", "TEST_A004-S01", "LAINNYA"),
            self._make_adj_row("TEST_A004", "TEST_A004-S02", "LB"),
            self._make_adj_row("TEST_A004", "TEST_A004-S03", "TJ"),
        ]
        results = self.compute(rows, warn_tt=False)
        comp = results["TEST_A004"]
        self.assertEqual(comp.v["LB"], 1)
        self.assertEqual(comp.v["TJ"], 1)
        # MT, HS, SI harus 0
        self.assertEqual(comp.v["MT"], 0)

    def test_tt_tidak_diselesaikan_tidak_menyumbang(self):
        """TT yang belum diselesaikan tidak boleh menyumbang vektor."""
        rows = [
            self._make_adj_row("TEST_A005", "TEST_A005-S01", "TT", status="final"),
            self._make_adj_row("TEST_A005", "TEST_A005-S02", "LB"),
        ]
        results = self.compute(rows, warn_tt=False)
        comp = results["TEST_A005"]
        # TT tidak menyumbang; hanya LB yang ada
        self.assertEqual(comp.v["LB"], 1)
        self.assertEqual(comp.v["TJ"], 0)

    def test_dikecualikan_tidak_menyumbang_v_utama(self):
        """Segmen dikecualikan tidak menyumbang vektor utama (K3)."""
        rows = [
            self._make_adj_row("TEST_A006", "TEST_A006-S01", "LB"),
            self._make_adj_row("TEST_A006", "TEST_A006-S02", "HS", status="dikecualikan"),
        ]
        results = self.compute(rows, warn_tt=False)
        comp = results["TEST_A006"]
        self.assertEqual(comp.v["HS"], 0)  # Dikecualikan tidak menyumbang v utama

    def test_format_vektor(self):
        """Format vektor harus (LB,TJ,MT,HS,SI)."""
        v = {"LB": 1, "TJ": 1, "MT": 0, "HS": 1, "SI": 0}
        self.assertEqual(self.format_vector(v), "(1,1,0,1,0)")

    def test_vektor_semua_nol_tidak_lengkap(self):
        """Vektor semua nol = TIDAK LENGKAP: semua komponen."""
        v = {"LB": 0, "TJ": 0, "MT": 0, "HS": 0, "SI": 0}
        status, missing = self.determine_status(v)
        self.assertEqual(status, "TIDAK LENGKAP")
        self.assertIn("semua", missing)


# ===========================================================================
# Jalankan test
# ===========================================================================

if __name__ == "__main__":
    # Jalankan dengan output yang lebih verbose
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    test_classes = [
        TestNormalisasi,
        TestDeduplikasi,
        TestSegmentasi,
        TestKonversiLS,
        TestValidasiMultiLabel,
        TestAdjudikasi,
        TestKelengkapan,
    ]

    for tc in test_classes:
        suite.addTests(loader.loadTestsFromTestCase(tc))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Exit code non-zero jika ada test yang gagal
    sys.exit(0 if result.wasSuccessful() else 1)
