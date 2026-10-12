# Pedoman Anotasi v1.0 (setelah uji mandiri): Fungsi Retoris Kalimat pada Abstrak Artikel Ilmiah Berbahasa Indonesia

*Skripsi Sarjana Terapan Manajemen Informatika, UNESA. Versi per 10 Oktober 2026.*

**Status dokumen.** Tahap 1 (kerangka) dan Tahap 2 (draf) selesai. Tahap 3(b) (uji adversarial sintetis) dan 3(c) (uji konsistensi) selesai pada Putaran 1 dari maksimal 2. Tahap 3(a) (uji pada empat abstrak, 28 segmen) selesai; hasilnya ada di Bagian B.1, dan Putaran 2 dari 2 sudah terpakai (Bagian B.3). Slot contoh nyata yang semula bertanda **\[SLOT-NYATA\]** di Bagian 3 telah diisi verbatim dari keempat abstrak beserta sumbernya, kecuali slot P-LN-1 yang tidak tersedia karena abstrak tidak memuat segmen LAINNYA. Tidak ada Putaran 3; sisa masalah menjadi kasus batas (Bagian B.4). Kriteria selesai terpenuhi menurut uji mandiri penyusun: tidak ada kontradiksi internal yang ditemukan, kasus batas sisa tercatat, dan keputusan untuk dosen terdaftar (Bagian C). Pedoman ini belum divalidasi: ukuran kesepakatan pertama baru dihasilkan Pilot 2 (Bagian 9). Versi 1.0 dibekukan pada 2026-10-11 setelah perbaikan pelaporan dan definisi pada B.3; berkas beku pedoman\_v1.0\_beku.md dan README\_versi.md disimpan terpisah, dan hash-nya dicatat pada paragraf Pembekuan di bawah.

Penanda: **\[PERLU VERIFIKASI\]** = rujukan belum dilampirkan atau belum diperiksa pada sumber primer. **\[KONFIRMASI DOSEN\]** = keputusan yang diambil penyusun dan perlu disetujui. **\[SINTETIS\]** = contoh buatan, hanya untuk kasus batas.

# BAGIAN A. PEDOMAN

## 1. Tujuan dan ruang lingkup

**1.1 Tujuan.** Pedoman ini menetapkan ground truth fungsi retoris per kalimat pada abstrak untuk melatih dan menguji tiga pendekatan (rule-based murni, IndoBERT murni, hybrid), lalu menurunkan vektor kehadiran lima komponen per abstrak. Pedoman harus dapat dipakai orang lain tanpa penjelasan lisan.

**1.2 Ruang lingkup.** Abstrak berbahasa Indonesia dari artikel jurnal ilmiah, untuk semua jenis studi (kuantitatif, kualitatif, pengembangan produk, studi literatur, konseptual). Di luar ruang lingkup: abstrak berbahasa lain, bagian artikel selain abstrak, penilaian kualitas isi, kebenaran klaim, dan mutu bahasa.

**1.3 Keputusan terkunci (ringkas).**

1. Kelas: LB (Latar Belakang), TJ (Tujuan), MT (Metode), HS (Hasil), SI (Simpulan/Implikasi), dan LAINNYA. SI mencakup simpulan dan saran/rekomendasi (alasan: move Conclusion pada Hyland (2000) disebut mencakup rekomendasi \[PERLU VERIFIKASI ke sumber primer\]).
2. Kelengkapan adalah vektor kehadiran LB-TJ-MT-HS-SI. LENGKAP jika dan hanya jika kelimanya hadir; komponen yang hilang disebut eksplisit. Ini definisi operasional penelitian ini, bukan norma universal, dan yang dinilai adalah kehadiran fungsi, bukan kualitas isi.
3. Definisi kelas berbasis fungsi. Daftar penanda leksikal dipisah ke dokumen lain dan hanya boleh diturunkan dari data pengembangan.
4. Multi-label hanya melalui uji pemecahan (Langkah 0).
5. Kasus batas tidak dipaksa selesai: ada flag “batas”, label alternatif, dan prosedur adjudikasi.
6. Lima kelas dipetakan ke kerangka IPMRC. Sumber lain hanya dipakai bila dilampirkan; selebihnya bertanda \[PERLU VERIFIKASI\].

**1.4 Kerangka (Tahap 1): pemetaan ke IPMRC.** Pemetaan berikut disusun sebelum penyusun melihat abstrak mana pun. Sumber primer IPMRC belum dilampirkan \[PERLU VERIFIKASI\].

| Label | Komponen IPMRC | Pertanyaan yang dijawab kalimat |
| --- | --- | --- |
| LB | Introduction | Apa konteks, masalah, atau kesenjangan di luar studi ini? |
| TJ | Purpose | Apa yang hendak dicapai atau dijawab studi ini? |
| MT | Method | Bagaimana studi ini dilakukan? |
| HS | Result | Apa yang diperoleh studi ini? |
| SI | Conclusion | Apa artinya, dan apa yang perlu dilakukan setelahnya? |
| LAINNYA | (tidak dipetakan) | Bukan salah satu dari lima fungsi di atas |

**1.5 Batasan: skala korpus dan beban anotasi.** Pedoman ini menuntut dua anotator independen pada Pilot 2 dan adjudikasi untuk setiap segmen yang berflag atau berbeda label, sehingga beban anotasi tumbuh lebih cepat daripada jumlah abstrak. Untuk N abstrak, beban kasarnya adalah 7N segmen (rata-rata 7 segmen per abstrak pada empat abstrak data pengembangan, rentang 4 sampai 10), dilabeli dua kali (14N pelabelan), ditambah adjudikasi atas sekitar 21% segmen (6 dari 28 segmen pengembangan berflag; batas bawah, karena ketidaksepakatan antaranotator belum terukur). Misalnya N = 100 menghasilkan sekitar 700 segmen, 1.400 pelabelan, dan 150 adjudikasi, sedangkan N = 300 menghasilkan sekitar 2.100 segmen, 4.200 pelabelan, dan 450 adjudikasi. Angka ini ilustrasi aritmetika dari sampel kecil, bukan perkiraan beban korpus; waktu per segmen belum diketahui dan dicatat pada Pilot 2 (Bagian 8). Jumlah abstrak yang dibutuhkan IndoBERT belum ditetapkan dan berada di luar lingkup pedoman. Keputusan skala dan skema anotasi ganda (penuh atau sebagian) ada di Bagian C.1 butir 3, dan urutan penyederhanaannya di butir 5.

**1.6 Prinsip kerja.**

- **P1.** Fungsi, bukan bentuk: label ditentukan oleh apa yang dilakukan proposisi dalam wacana abstrak, bukan oleh kata tertentu.
- **P2.** Setiap tes keputusan bersifat positif: label diberikan karena syaratnya terpenuhi, bukan karena label lain gugur.
- **P3.** Satu aturan berlaku sama untuk struktur yang sama.
- **P4.** Kasus batas dilaporkan, tidak dipaksa selesai.
- **P5.** Independensi dari sistem rule-based: anotator tidak membaca dan tidak memakai kamus penanda leksikal sistem.
- **P6.** Posisi kalimat dalam abstrak (awal, tengah, akhir) bukan kriteria.

**1.7 Istilah yang mudah tertukar.** Data pengembangan adalah empat abstrak yang dipakai menyusun dan menguji pedoman (`peran_data` = data-pengembangan); penelitian pengembangan adalah studi yang menghasilkan produk (`jenis_studi` = pengembangan-produk). Korpus anotasi adalah kumpulan abstrak yang dianotasi untuk melatih dan menguji sistem (`peran_data` = korpus-anotasi); korpus telaah adalah dokumen yang ditelaah sebuah studi literatur (A5). Kata korpus tanpa kata sifat berarti korpus telaah pada Bagian 3 dan 5, dan korpus anotasi pada bagian lain.

## 2. Satuan anotasi dan aturan segmentasi

**2.1 Satuan dokumen dan sumber teks.**

- Satu satuan adalah satu abstrak dalam satu bahasa. Versi 1.0 hanya mencakup abstrak bahasa Indonesia; abstrak bahasa Inggris pada artikel yang sama tidak dianotasi dan tidak diterjemahkan. Satu artikel menyumbang paling banyak satu abstrak.
- Satu abstrak berasal dari satu sumber teks. Urutan pilihan: (1) PDF versi terbit; (2) halaman artikel HTML bila PDF tidak tersedia atau tidak dapat diekstrak; (3) metadata Garuda hanya untuk menemukan artikel dan DOI, bukan sebagai sumber teks. Sumber dicatat, dan satu abstrak tidak boleh dirakit dari dua sumber.
- Setiap kutipan “verbatim” dalam pedoman diverifikasi karakter demi karakter terhadap teks mentah dari sumber kanonik yang sama. Hash teks mentah (SHA-256) dicatat. Verifikasi lintas sumber (misalnya PDF dibandingkan dengan halaman artikel) tidak dianggap verifikasi.

> **Keputusan (e) \[KONFIRMASI DOSEN\].** Abstrak diperlakukan per bahasa dan hanya bahasa Indonesia yang dicakup, karena pedoman dan kamus ditujukan ke bahasa Indonesia dan mencampur bahasa mengubah distribusi sintaksis serta menggandakan sampel dari artikel yang sama. PDF versi terbit dipilih sebagai sumber utama karena merupakan rekaman terbit yang tertaut ke DOI, sedangkan halaman HTML dan metadata Garuda adalah turunan yang dapat berbeda atau terpotong. Kebijakan satu sumber per abstrak mencegah kesalahan yang pernah terjadi, yaitu klaim verbatim yang diverifikasi terhadap sumber yang berbeda.

**2.2 Teks mentah dan teks kerja.** Teks mentah disalin persis dan tidak pernah diubah. Batas teks mentah seragam: dari karakter pertama kalimat pertama sampai karakter terakhir kalimat terakhir isi abstrak; label seksi, judul, dan kata kunci berada di luar batas. Teks mentah disimpan sebagai berkas teks UTF-8 per abstrak dengan satu baris baru akhir, dan hash dihitung pada berkas itu. Teks kerja adalah hasil normalisasi minimal: menyambung kata yang terpotong di akhir baris, menghapus pemisah baris, merapikan spasi ganda, dan menormalkan ligatur. Ejaan dan tata bahasa tidak diperbaiki, dan setiap perubahan dicatat dalam log normalisasi. Judul, kata kunci, dan subjudul seksi (misalnya pada abstrak terstruktur) bukan segmen; semuanya dipindah ke metadata, dan anotator melabeli teks kerja tanpa subjudul agar tidak terjangkar pada subjudul \[KONFIRMASI DOSEN\].

**2.3 Aturan segmentasi.**

Cuplikan teks dalam tabel ini adalah ilustrasi pola segmentasi \[SINTETIS\], bukan contoh nyata.

| Kasus | Aturan |
| --- | --- |
| Akhir kalimat | Batas adalah tanda . ? ! yang diikuti spasi lalu huruf kapital, angka, atau tanda kutip pembuka; atau akhir teks. |
| Singkatan bertitik (dkk., dsb., dst., dll., Prof., Dr., Ir., S.Pd., M.Kom., hlm., No.) | Titik bukan batas bila token berikutnya berupa kurung, huruf kecil, angka, atau nama/gelar yang melanjutkan frasa. Bila singkatan menutup klausa yang sudah berpredikat dan token berikutnya membuka klausa baru, titik adalah batas. Bila tidak dapat diputuskan: jangan dipecah dan beri flag B5. |
| Desimal koma dan ribuan titik (3,5; 0,05; 1.250) | Bukan batas. |
| Titik tanpa spasi (“...(p < 0,05).Hal ini ...”) | Batas bila titik langsung diikuti huruf kapital dan token sebelumnya bukan singkatan, inisial, URL, DOI, atau angka desimal. Dicatat sebagai artefak ekstraksi. |
| URL, DOI, surel, nama berkas | Titik di dalamnya bukan batas. |
| Daftar bernomor atau berhuruf dalam satu kalimat ((1), (a), a), 1)) | Penomor tidak membuat batas. Seluruh daftar bersama kalimat induknya adalah satu segmen. Butir yang masing-masing diakhiri tanda titik menjadi segmen sendiri, dan penomor “1.” di awal butir bukan batas. |
| Titik dua dan titik koma | Bukan batas kalimat. |
| Kutipan langsung | Tanda akhir di dalam tanda kutip bukan batas bila kalimat berlanjut. Bila kutipan ditutup lalu diikuti huruf kapital baru, batas ada setelah tanda kutip penutup. |
| Fragmen | Fragmen tanpa predikat tetapi memuat informasi (misalnya “Informan 12 guru.”) adalah segmen sendiri. Fragmen tanpa proposisi (penomor, label seksi, kata kunci) bukan segmen. |
| Kalimat dalam kurung | Segmen sendiri bila berdiri sendiri dan memuat proposisi; bila hanya rujukan seperti “(Tabel 2)”, bagian dari kalimat sebelumnya. |
| Elipsis | Diperlakukan sebagai satu titik. |

**2.4 Pembekuan segmentasi.** Segmentasi dikerjakan sebelum pelabelan, oleh skrip pemecah ditambah pemeriksa manual yang bukan anotator. Setelah dibekukan, anotator tidak mengubah batas segmen; keraguan ditandai flag B5, dan perubahan hanya dilakukan adjudikator serta dicatat. Akibatnya kesepakatan antaranotator dihitung pada segmen yang identik, dan kesepakatan segmentasi itu sendiri tidak diukur (dicatat sebagai keterbatasan di Bagian 10).

> **Keputusan (f) \[KONFIRMASI DOSEN\].** Segmentasi dikunci sebelum pelabelan karena batas kalimat memengaruhi semua metrik, dan ketidaksepakatan batas tidak boleh bercampur dengan ketidaksepakatan label. Daftar bernomor dalam satu kalimat tetap satu segmen agar tidak menghasilkan fragmen tanpa konteks; pemisahan fungsi antarbutir ditangani Langkah 0, bukan segmentasi. Kasus yang tidak dapat diputuskan aturan umum tidak dipecah dan diberi flag B5, bukan dibuatkan aturan khusus.

**2.5 Deduplikasi korpus.** Tujuannya agar setiap artikel dan setiap teks abstrak masuk korpus anotasi satu kali, dan tidak ada artikel yang berperan ganda, sehingga ukuran kesepakatan dan evaluasi model tidak menggelembung.

1. **Kunci artikel.** Kunci identitas adalah DOI yang dinormalkan (huruf kecil, tanpa awalan URL); bila tidak ada DOI, kuncinya judul ternormalisasi (huruf kecil, tanpa tanda baca, spasi tunggal) ditambah tahun dan nama jurnal. Dua entri berkunci sama adalah satu artikel.
2. **Duplikat persis.** Dua abstrak yang teks kerjanya, setelah normalisasi (huruf kecil, tanpa tanda baca, spasi tunggal), memiliki hash SHA-256 sama adalah duplikat walaupun kunci artikelnya berbeda, misalnya artikel yang diterbitkan ulang.
3. **Duplikat dekat.** Pasangan abstrak dengan kemiripan Jaccard atas 5-gram kata sekurang-kurangnya 0,90 ditandai dan ditinjau manual; hanya satu yang disimpan. Ambang ini pilihan penyusun tanpa rujukan \[KONFIRMASI DOSEN\].
4. **Entri yang disimpan.** Dipilih entri ber-DOI; bila sama, versi terbit paling awal. Entri lain dicatat pada log\_dedup.csv beserta alasan dan entri yang disimpan.
5. **Satu artikel satu peran.** Artikel pada data pengembangan tidak boleh masuk Pilot 2 atau korpus anotasi, dan artikel Pilot 2 tidak boleh masuk korpus anotasi.
6. **Bahasa.** Abstrak bahasa Indonesia dan bahasa Inggris dari artikel yang sama bukan duplikat satu sama lain; hanya bahasa Indonesia yang dianotasi (2.1).
7. **Waktu dan pencatatan.** Deduplikasi dijalankan sebelum segmentasi dan sebelum penarikan sampel Pilot 2, dan diulang setiap korpus bertambah. Hasilnya dicatat pada kolom kunci\_artikel, hash\_teks\_ternormalisasi, dan status\_dedup (Bagian 8).

## 3. Definisi label, tes positif, dan contoh

**3.0 Istilah kerja.**

- **Studi ini**: penelitian atau kajian yang dilaporkan artikel (disebut “penelitian ini”, “artikel ini”, “kami”, atau tanpa subjek).
- **Proposisi inti**: isi pernyataan setelah bingkai dikupas (Aturan Bingkai, 5.1) dan setelah Langkah 0.
- **Acuan**: D = dunia, literatur, atau situasi di luar studi; K = kegiatan studi (apa yang dituju atau dilakukan); X = keluaran studi (apa yang diperoleh atau diturunkan). Cara menentukan acuan: 5.2 (Uji Acuan).
- **Penanda pasca-penelitian (PP)**, daftar tertutup: PP-1 bingkai bersumber studi ini; PP-2 acuan anaforis atau konektor wacana eksplisit ke keluaran studi pada segmen sebelumnya (Aturan Kohesi, 5.2); PP-3 studi sebagai pelaku, atau acuan eksplisit ke subjek, produk, atau data studi, disertai pernyataan keluaran; PP-4 tindak anjuran (P3).
- **Penambat (A1–A5)**: A1 subjek, sampel, informan, lokasi, atau waktu pengambilan data studi; A2 produk, intervensi, model, sistem, atau kerangka yang dikembangkan, diterapkan, atau diusulkan studi; A3 hubungan, perbedaan, atau pengaruh antara dua variabel atau lebih, atau nilai, tingkat, atau perubahan satu variabel yang diukur; A4 angka, statistik, persentase, atau daftar/kategori hasil; A5 korpus, dokumen, atau kasus yang ditelaah studi, atau tema/pola yang ditemukan darinya.
- **Pelampauan (P1–P3)**: P1 generalisasi, yaitu perluasan keberlakuan yang disebut eksplisit ke pihak atau konteks di luar sampel atau produk studi, atau proposisi berstatus pasca yang tidak memuat penambat sama sekali; P2 makna, implikasi, atau kontribusi bagi teori, praktik, atau kebijakan; P3 anjuran, yaitu saran atau rekomendasi kepada penerima tertentu atau untuk penelitian lanjutan, dengan penerima dan tindakan yang dianjurkan. Pernyataan kebutuhan tanpa bentuk anjuran bukan P3.

**Peta keputusan** (ringkasan; tes lengkap di bawah dan di Bagian 4):

| Acuan | Status | Cakupan | Label |
| --- | --- | --- | --- |
| D | pra-penelitian | tidak relevan | LB |
| K, sasaran | tidak relevan | tidak relevan | TJ |
| K, cara, bahan, atau subjek | tidak relevan | tidak relevan | MT |
| X | pasca-penelitian | terikat (ada penambat, tanpa P1–P3) | HS |
| X | pasca-penelitian | melampaui (ada P1, P2, atau P3) | SI |
| bukan proposisi isi, di luar lima fungsi, atau rusak | tidak relevan | tidak relevan | LAINNYA |

Setiap tes di bawah dibaca “semua syarat harus terpenuhi”. Tidak ada label yang diberikan karena label lain gugur.

### 3.1 LB (Latar Belakang)

**Definisi fungsi.** Kalimat yang menempatkan studi dalam konteksnya: kondisi atau fenomena, masalah, pengetahuan atau temuan terdahulu, kesenjangan, kebutuhan, atau alasan topik penting, yang berlaku terlepas dari studi ini dilaksanakan atau tidak.

**Tes positif LB.**

- LB-1: acuan proposisi inti adalah D.
- LB-2: status pra-penelitian, yaitu bingkai bersumber literatur atau umum, atau status mengikuti antesedennya (5.2), atau tidak ada PP-1 sampai PP-4. Bila status pra hanya bertumpu pada ketiadaan PP dan tanda D-nya lemah (5.2), berlaku flag B3 (Bagian 7).
- LB-3: berfungsi memosisikan studi, yaitu menyatakan konteks, masalah, kesenjangan, kebutuhan, atau alasan.

**Contoh positif:** “Perkembangan teknologi terus mendorong penggunaan artificial intelligence (AI) pada cara pembelajaran mahasiswa di Indonesia.” (A1-S01; Supriyadi dkk., 2024), “Namun, di era digital dimana penggunaan artificial intelligence (AI) sudah semakin marak, para penggiat di industri kreatif mulai mendapat tantangannya tersendiri.” (A3-S04; Anwar dkk., 2024). **Contoh negatif:** “Yakni, AI dipergunakan sebagai sarana triangulasi, referensi untuk pengembangan ide orisinil, membaca trend terkini, serta sebagai alat bantu ketika dihadapkan pada kebutuhan dengan waktu yang terbatas.” (A3-S10; Anwar dkk., 2024) tampak seperti latar tentang kegunaan AI, tetapi berlabel HS: konektor ke segmen HS memberi status pasca, sehingga LB-2 gagal. Pola negatif: kalimat tentang apa yang dituju atau dilakukan studi (TJ, MT), apa yang diperoleh (HS), atau apa yang perlu dilakukan setelahnya (SI). **Contoh batas:** L-2 dan I-3 (Bagian B), serta A2-S05 (nyata, B.1).

### 3.2 TJ (Tujuan)

**Definisi fungsi.** Kalimat yang menyatakan sasaran studi secara keseluruhan: apa yang hendak diketahui, diuji, dijawab, dikembangkan, dideskripsikan, dibandingkan, atau dibahas. Hipotesis atau pertanyaan penelitian termasuk bila diajukan untuk diuji.

**Tes positif TJ.**

- TJ-1: acuan K, dengan studi sebagai pelaku.
- TJ-2: menyebut sasaran (objek, variabel, pertanyaan, hipotesis, atau produk yang dituju) tanpa memuat nilai, arah, tingkat, kategori hasil, atau ciri produk jadi. Uji pengetahuan: isinya dapat ditulis sebelum data ada.
- TJ-3: sasaran milik studi secara keseluruhan, bukan tujuan sebuah langkah atau alat (itu MT).

**Contoh positif:** “Penelitian ini bertujuan untuk mengungkap pengaruh teknologi artificial intelligence (AI) dan literasi digital terhadap hasil belajar mata kuliah Evaluasi Pembelajaran.” (A1-S03; Supriyadi dkk., 2024), “Penelitian ini hendak mengetahui bagaimana perkembangan AI mempengaruhi sikap pelaku di industri kreatif.” (A3-S06; Anwar dkk., 2024). **Contoh negatif:** “Melalui penelitian ini, peneliti berhasil untuk mengumpulkan, menganalisis, dan menjelaskan problematika dalam perkembangan Artificial Intelligence yang terjadi dalam dimensi Kekayaan Intelektual, seperti penggunaan tanpa hak suatu kekayaan intelektual dalam proses pembelajaran Artificial Intelligence, kaitannya dengan Kekayaan Intelektual sebagai data pribadi, dan kurangnya perlindungan dalam regulasi yang ada.” (A4-S03; Tullah dan Fakhsal, 2024) tampak seperti pernyataan tujuan, tetapi berlabel HS dengan flag B6: kategori hasil yang disebut menggugurkan TJ-2. Pola negatif: kalimat yang memuat hasil temuan (HS) atau desain dan teknik (MT). **Contoh batas:** T-3 (Bagian B), serta A2-S06 dan A4-S03 (nyata, B.1).

### 3.3 MT (Metode)

**Definisi fungsi.** Kalimat yang menyatakan bagaimana studi dilakukan: desain atau pendekatan, subjek, sampel, lokasi, waktu, sumber data atau korpus, bahan, alat, instrumen, prosedur pengumpulan atau pengembangan, perlakuan, teknik analisis, dan ukuran atau kriteria evaluasi yang dipakai.

**Tes positif MT.**

- MT-1: acuan K.
- MT-2: menyatakan cara, bahan, subjek, alat, prosedur, teknik, atau kriteria yang dipakai. Karakteristik sampel atau lokasi sebagai konteks pengambilan data termasuk. Untuk kajian konseptual: pendekatan analisis atau argumentasi.
- MT-3: tidak menyatakan nilai atau kategori hasil dari penerapan cara itu, dan bukan hanya sasaran.

**Contoh positif:** “Teknik pengambilan sampel menggunakan random sampling dengan jumlah sampel 155 mahasiswa Program Sarjana, Program Studi Pendidikan Ekonomi, Fakultas Ilmu Pendidikan, Universitas Panca Sakti Bekasi.” (A1-S05; Supriyadi dkk., 2024), “Metode campuran digunakan agar dapat memberikan asumsi secara menyeluruh atas akibat dari disrupsi AI, sekaligus juga bisa mendapatkan gambaran pemahaman secara holistik dari kacamata penggiat industri kreatif yang diwakili oleh beberapa responden dari berbagai bidang keahlian melalui wawancara terstruktur.” (A3-S08; Anwar dkk., 2024). **Contoh negatif:** “Studi ini mengkaji perancangan sistem otomatisasi laboratorium yang memanfaatkan AI untuk mengoptimalkan penggunaan sumber daya.” (A2-S02; Kurniawan dan Siswanto, 2024) memuat kata kerja analitis, tetapi berlabel TJ: kalimat menyatakan objek kajian, bukan cara, sehingga MT-2 gagal. Pola negatif: deskripsi produk jadi atau nilai hasil ukur (HS). **Contoh batas:** I-4 dan P-3 (Bagian B), serta A3-S07 dan A4-S03 (nyata, B.1).

### 3.4 HS (Hasil)

**Definisi fungsi.** Kalimat yang menyatakan apa yang diperoleh studi ini: keluaran yang terikat pada data, subjek, produk, korpus, atau kerangka milik studi.

**Tes positif HS.**

- HS-1: ada penanda pasca-penelitian (PP-1 sampai PP-3).
- HS-2: ada sekurang-kurangnya satu penambat (A1–A5) di dalam proposisi inti, dan proposisi menyatakan keluaran (nilai, perbedaan, hubungan, arah, signifikansi, tingkat, tema, ada atau tidaknya sesuatu, ciri atau mutu produk), bukan sasaran, bukan cara, dan bukan deskripsi bahan, subjek, atau korpus (siapa, berapa, dari mana, cara memilih).
- HS-3: tidak memuat pelampauan (P1–P3).

Catatan ambang: tidak memerlukan angka; modalitas (“dapat”, “sangat penting”) tidak dipakai sebagai kriteria; bingkai hanya memberi status, sedangkan penambat harus ada di dalam proposisi.

> **Keputusan (b) \[KONFIRMASI DOSEN\].** Ambang HS adalah keterikatan pada data, subjek, atau produk studi ini, diperiksa lewat penambat A1–A5, bukan modalitas. Modalitas menggambarkan sikap penulis, bukan relasi proposisi dengan data: kalimat bermodalitas “dapat” bisa sah terikat pada produk studi, dan kalimat tanpa modalitas bisa berupa klaim umum. Ambang tidak mensyaratkan angka sehingga studi kualitatif dan konseptual tidak dirugikan.

**Contoh positif:** “Responden wawancara yang bekerja di industri kreatif, menyatakan bahwa kehadiran AI banyak membantu proses kreatif mereka sampai pada tahapan tertentu.” (A3-S09; Anwar dkk., 2024), “Yakni, AI dipergunakan sebagai sarana triangulasi, referensi untuk pengembangan ide orisinil, membaca trend terkini, serta sebagai alat bantu ketika dihadapkan pada kebutuhan dengan waktu yang terbatas.” (A3-S10; Anwar dkk., 2024). **Contoh negatif:** “Simpulannya, teknologi artificial intelligence (AI) dalam pembelajaran memerlukan pengawasan oleh dosen serta kemampuan dan integritas mahasiswa dalam bentuk literasi digital mahasiswa.” (A1-S08; Supriyadi dkk., 2024) berbingkai studi, tetapi berlabel SI: tidak ada penambat, sehingga HS-2 gagal. Pola negatif: klaim umum tanpa penambat (LB atau SI), sasaran (TJ), cara (MT). **Contoh batas:** C-2, L-2, T-3 (Bagian B), serta A1-S07, A2-S04, dan A4-S03 (nyata, B.1).

### 3.5 SI (Simpulan/Implikasi)

**Definisi fungsi.** Proposisi pasca-penelitian yang melampaui data studi: generalisasi, makna atau implikasi atau kontribusi, atau anjuran (saran dan rekomendasi, termasuk untuk penelitian lanjutan). SI tidak mengandaikan adanya kalimat HS dalam abstrak yang sama.

**Tes positif SI.**

- SI-1 (jangkar): ada penanda pasca-penelitian (PP-1 sampai PP-4).
- SI-2: ada P1, P2, atau P3 sebagaimana didefinisikan di 3.0.
- SI-3: acuan proposisi inti adalah X (keluaran yang melampaui data, implikasi, atau kontribusi) atau tindak anjuran; bukan K dan bukan D.

> **Keputusan (c) \[KONFIRMASI DOSEN\].** Jangkar SI adalah status pasca-penelitian ditambah ciri pelampauan data, tanpa merujuk kalimat lain. Mengaitkan SI dengan kalimat HS membuat SI mustahil dikenali pada abstrak tanpa hasil seperti kajian konseptual. Konsekuensi yang harus dikonfirmasi: kalimat simpulan yang hanya mengulang temuan terikat data berlabel HS, bukan SI.

**Contoh positif:** “Disimpulkan juga bahwa perlindungan hukum yang diberikan oleh European Union Artificial Intelligence Act terhadap Kekayaan Intelektual semestinya dapat dijadikan acuan dalam penyusunan peraturan komprehensif sebagai solusi penyelesaian problematika yang muncul di Indonesia.” (A4-S04; Tullah dan Fakhsal, 2024), “Simpulannya, teknologi artificial intelligence (AI) dalam pembelajaran memerlukan pengawasan oleh dosen serta kemampuan dan integritas mahasiswa dalam bentuk literasi digital mahasiswa.” (A1-S08; Supriyadi dkk., 2024). **Contoh negatif:** “Responden wawancara yang bekerja di industri kreatif, menyatakan bahwa kehadiran AI banyak membantu proses kreatif mereka sampai pada tahapan tertentu.” (A3-S09; Anwar dkk., 2024) berbunyi seperti klaim umum tentang peran AI, tetapi berlabel HS: sumbernya subjek studi (PP-3) dan tidak ada generalisasi eksplisit, sehingga SI-2 gagal. Pola negatif: kalimat simpulan yang hanya mengulang temuan terikat data (HS) dan pernyataan kebutuhan umum tanpa penanda pasca (LB). **Contoh batas:** I-3, C-2, I-4 (Bagian B), serta A2-S05 dan A2-S06 (nyata, B.1).

### 3.6 LAINNYA

**Definisi fungsi.** Segmen yang tidak menjalankan salah satu dari lima fungsi karena bukan proposisi isi, berisi pernyataan administratif, atau rusak.

**Tes positif LAINNYA.**

- LN-1: memenuhi salah satu dari (a) bukan proposisi isi yang lolos segmentasi (judul, kata kunci, label seksi, nama, afiliasi, catatan penerbit); (b) pernyataan administratif atau di luar lima fungsi (pendanaan, ucapan terima kasih, hak cipta, rujukan ke tabel, gambar, atau bagian lain); (c) segmen rusak atau terpotong yang tidak memuat proposisi lengkap untuk dinilai atau yang acuannya tak dapat ditentukan, dengan bukti pada teks (tes label lain hanya dikenakan pada proposisi lengkap).
- LN-2: tidak lolos tes positif label lain.

LAINNYA tidak boleh dipakai untuk kalimat yang sulit atau tidak jelas; kalimat seperti itu diberi label TT dengan flag B2 (Bagian 4 dan 7).

> **Keputusan (g) \[KONFIRMASI DOSEN\].** LAINNYA dan LB sama-sama memiliki syarat positif sendiri, sehingga tidak ada yang menjadi tempat jatuh kalimat sisa. Kalimat yang tidak lolos satu pun tes tidak dipaksa masuk ke LAINNYA atau LB, melainkan diberi label sementara TT dan diselesaikan lewat adjudikasi. Dengan begitu perilaku LB yang menyerap kalimat Hasil, Simpulan, atau Saran, yang pernah terjadi, tidak terulang.

**Contoh positif:** Tidak tersedia: keempat abstrak tidak memuat segmen LAINNYA. Contoh batas sintetis O-3 dan O-4 (Bagian B) menjadi satu-satunya ilustrasi; pemeriksaan LAINNYA pada data nyata menunggu Pilot 2. **Contoh negatif:** “Berbanding terbalik dengan Uni Eropa yang telah diklaim mampu memberikan perlindungan terhadap permasalahan tersebut melalui pengaturan komprehensifnya terkait dengan Artificial Intelligence, European Union Artificial Intelligence Act.” (A4-S02; Tullah dan Fakhsal, 2024) tidak memiliki klausa utama tetapi memuat informasi, sehingga bukan segmen rusak (LN-1c gagal) dan berlabel LB. **Contoh batas:** O-3 dan O-4 (Bagian B).

## 4. Prosedur keputusan

Prosedur dijalankan untuk setiap segmen yang sudah dibekukan (2.4), dengan urutan: Langkah 0, Langkah 1, Langkah 2, Langkah 3.

&#91;embedded content: alur keputusan per segmen · 4 langkah, 2 percabangan\]

Setiap segmen dikupas, dipecah bila ada pemicu, diuji secara positif, lalu dicatat; hasil tanpa tes yang lolos adalah TT, bukan LB.

**Langkah 0. Kupas bingkai dan uji pemecahan.**

- **0a. Kupas bingkai.** Terapkan Aturan Bingkai (5.1) untuk memperoleh proposisi inti dan statusnya.
- **0b. Uji Pemecahan (UP).** UP hanya dijalankan pada struktur dalam daftar tertutup berikut.

| Kode | Pemicu UP (daftar tertutup) |
| --- | --- |
| U1 | Dua klausa atau predikat setara (koordinasi, atau dipisah titik koma atau tanda pisah), termasuk butir daftar bernomor dalam satu kalimat. |
| U2 | Adjunct tujuan pada klausa utama berupa kegiatan studi (K) yang menyatakan tujuan studi, yaitu relasi, pertanyaan, atau produk yang hendak dijawab, diuji, atau dikembangkan. Tujuan sebuah alat atau langkah (misalnya mengukur atau mengumpulkan data) bukan pemicu. |
| U3 | Adjunct cara, sarana, atau sumber data yang menyatakan desain, teknik, atau data studi. |
| U4 | Adjunct akibat atau turunan yang menyatakan makna atau anjuran. |
| U5 | Klausa sebab atau alasan yang berada di luar cakupan bingkai studi ini. |

**Bukan pemicu** (tidak pernah memecah; mengikuti label induk): klausa relatif; apositif dan keterangan dalam kurung (misalnya statistik); klausa syarat, konsesi, dan waktu; komplemen di dalam bingkai; klausa sebab di dalam cakupan bingkai studi ini.

**Prosedur UP.**

1. Tandai pemicu yang ada.
2. Tulis ulang tiap bagian sebagai kalimat mandiri hanya dengan membuang penghubung dan mengulang subjek atau anafora, tanpa menambah, mengurangi, atau mengubah informasi.
3. Terapkan tes positif (Bagian 3) pada tiap bagian.
4. Bagian yang tidak lolos tes mana pun bukan proposisi mandiri dan digabung ke bagian yang lolos.
5. Bagian dengan label sama digabung.
6. Bila tersisa dua label berbeda atau lebih, segmen berlabel ganda. Label dicatat berurutan sesuai kemunculan, misalnya TJ+MT.

Bila dua cara tulis ulang yang sama-sama sah menghasilkan jumlah atau jenis label yang berbeda, beri flag B4. Label utama adalah hasil penulisan ulang yang memuat label paling banyak (inklusif); hasil lainnya dicatat sebagai label alternatif. Segmen dengan tiga label atau lebih diberi flag B5 untuk memeriksa segmentasi. Multi-label tidak dapat diberikan lewat jalur lain selain UP.

**Langkah 1. Tes berurutan pada setiap proposisi inti.** Jalankan semua tes positif (Bagian 3) dalam urutan tetap: TJ, MT, HS, SI, LB, LAINNYA. Urutan dipilih dari label yang paling terikat pada studi ke yang paling umum. Urutan ini bukan rantai “bila tidak, maka”: setiap tes dinilai sendiri, dan urutan hanya berfungsi menetapkan label utama secara seragam bila lebih dari satu tes lolos.

**Langkah 2. Keluaran.**

| Hasil tes | Keputusan |
| --- | --- |
| Tepat satu tes lolos | Label itu; bila ambang tes dapat dibaca dua arah, beri flag B6 dan catat label alternatif. |
| Dua tes atau lebih lolos | Label utama adalah tes yang lolos paling awal menurut urutan; label alternatif adalah tes yang lolos berikutnya; flag B1. |
| Tidak ada tes yang lolos | Label TT (tidak terputuskan); flag B2; tulis label alternatif terdekat; diselesaikan lewat adjudikasi (Bagian 7). TT tidak boleh diganti LB atau LAINNYA oleh anotator. |

**Langkah 3. Catat.** Label (berurutan sesuai kemunculan, dipisah “+”), simpul penentu (tes atau aturan yang menentukan), flag, label alternatif, dan alasan satu kalimat yang wajib diisi bila ada flag.

## 5. Aturan khusus

Bagian ini memuat aturan yang dirujuk Bagian 3 dan 4. Rumus memakai tanda kurung siku sebagai tempat isi, bukan sebagai kalimat contoh. Kasus batas ditunjukkan dengan kode di Bagian B; contoh nyata diambil dari abstrak lampiran (Bagian B.1).

### 5.1 Bingkai dan cakupannya

**Definisi.** Bingkai adalah frasa atau klausa pembuka yang tidak membawa isi proposisi sendiri; ia hanya menyebut sumber dan sifat pernyataan yang menyusul (komplemen). Uji Buang: bila bingkai dibuang dan komplemen tetap menjadi klausa lengkap dengan proposisi yang sama, yang dibuang adalah bingkai. Predikat kegiatan studi (yang membawa sasaran atau cara) bukan bingkai, karena pembuangannya menghilangkan isi.

**Aturan Bingkai** (satu aturan, empat langkah):

1. **Sumber.** Tentukan sumber bingkai: (a) studi ini, yaitu pelaku atau korpus telaah studi ini disebut, atau kata kerja atau nomina temuan atau simpulan tanpa atribusi eksternal; (b) literatur atau pihak lain, yaitu ada atribusi eksternal (nama, tahun, kutipan, penelitian terdahulu) atau literatur disebut tanpa kaitan eksplisit ke korpus telaah studi ini; (c) pengetahuan umum.
2. **Status.** Sumber (a) memberi PP-1 (pasca-penelitian). Sumber (b) dan (c) memberi status pra. Tanpa bingkai tidak ada PP-1; status ditentukan oleh PP-2 sampai PP-4 atau diberlakukan pra-default bila tanda D kuat; pra-default dengan tanda D lemah berflag B3 (5.2).
3. **Cakupan.** Cakupan adalah komplemen langsung bingkai sampai batas segmen, termasuk semua klausa dependen yang melekat pada predikat di dalam komplemen (relatif, syarat, konsesi, waktu, sebab, cara). Cakupan berakhir lebih awal hanya pada bingkai baru atau tanda pisah kuat (titik koma, tanda pisah) yang membuka klausa baru. Bila bingkai menjadi induk daftar bernomor, cakupan meliputi seluruh butir (5.4). Semua proposisi dalam cakupan mewarisi status bingkai.
4. **Label.** Label ditentukan pada proposisi inti dengan tes Bagian 3. Bingkai bersumber studi hanya memenuhi syarat status (HS-1, SI-1); syarat penambat (HS-2) dan pelampauan (SI-2) harus dipenuhi isi komplemen sendiri.

**Klausa sebab dependen.** Di dalam cakupan, klausa sebab mewarisi status dan label proposisi induknya dan bukan pemicu UP. Di luar cakupan (kalimat tanpa bingkai bersumber studi, atau klausa setelah batas cakupan), klausa sebab adalah pemicu U5: ia dinilai sendiri, dan bagian lain yang tidak memuat proposisi mandiri digabung ke bagian yang lolos (Bagian 4, Langkah 0b).

**Akibat.** (i) Kata kerja bingkai tidak menentukan fungsi: bingkai simpulan tetap menghasilkan HS bila isinya terikat data. (ii) Bingkai studi tidak menjadikan kalimat HS bila isinya tanpa penambat atau melampaui data. (iii) Bingkai literatur menjadikan status pra. (iv) Kriteria “klausa utama” tidak dipakai.

> **Keputusan (a) \[KONFIRMASI DOSEN\].** Bingkai memberi status dan cakupan, bukan fungsi, karena bingkai yang sama membungkus proposisi berfungsi berbeda. Cakupan sampai batas segmen dipilih agar klausa sebab dependen dapat diputuskan secara sintaktis, tanpa menebak maksud penulis. Konsekuensinya, penjelasan sebab dari penulis di dalam cakupan tidak dipecah dan, bila bukan variabel terukur, ditandai B6.

### 5.2 Acuan, status, dan kohesi antarkalimat

**Uji Acuan.** Tentukan acuan proposisi inti dengan tiga pertanyaan berurutan (disebut Q1, Q2, dan Q3 menurut nomornya):

1. Apakah proposisi menyatakan apa yang dituju atau dilakukan studi ini? Pelakunya studi, peneliti, penulis, atau pelaku studi yang tersirat dalam kalimat pasif. Jika ya, acuannya **K**: sasaran menuju TJ; cara, bahan, subjek, alat, atau prosedur menuju MT.
2. Apakah proposisi menyatakan apa yang diperoleh studi atau diturunkan darinya (nilai, perubahan, perbedaan, hubungan, tema, produk jadi dan mutunya, makna, anjuran)? Tanda positif: bingkai atau pelaku studi; acuan eksplisit ke subjek, kelompok, produk, data, atau korpus studi; atau perubahan, perbedaan, dan perbandingan antarkelompok yang diukur. Jika ya, acuannya **X**.
3. Apakah proposisi menyatakan keadaan, pengetahuan, atau temuan di luar studi? Tanda positif: atribusi eksternal, atau pernyataan tentang kelas umum (populasi, fenomena, kebijakan, kebutuhan) yang berlaku terlepas dari studi, termasuk gambaran prevalensi tanpa kekhasan studi. Jika ya, acuannya **D**.

Bila pertanyaan 2 dan 3 sama-sama tidak mempunyai tanda positif, acuan tidak dapat ditentukan: LB-1 dan HS-1 tidak terpenuhi, dan bila tidak ada tes lain yang lolos hasilnya TT (flag B2). Bila keduanya mempunyai tanda positif, kedua tes dijalankan dan Langkah 2 (Bagian 4) berlaku (flag B1). Tanda D kuat: atribusi eksternal, atau pernyataan tentang fenomena, tren, atau keadaan umum yang berlaku terlepas dari studi. Tanda D lemah: pernyataan kebutuhan atau keharusan tindakan, prevalensi, atau angka tanpa atribusi eksternal; acuan D yang hanya bertanda lemah memberi flag B3 pada LB dan B6 dengan alternatif SI atau HS. Bila Q1 tidak terpenuhi dan segmen memuat PP-1, PP-2, PP-3, atau PP-4, acuannya X dan Q3 tidak dinilai.

**Aturan Kohesi.**

1. PP-2 diberikan kepada segmen tanpa bingkai bila (a) memuat acuan anaforis eksplisit (pronomina, demonstratif, atau frasa nomina definit) yang antesedennya proposisi berlabel HS atau SI, atau (b) diawali konektor wacana eksplisit yang menghubungkannya ke segmen sebelumnya berlabel HS atau SI.
2. Bila antesedennya berlabel LB, status segmen penerus adalah pra.
3. Antesedennya adalah segmen terdekat yang dirujuk; pada segmen berlabel ganda, bagian yang dirujuk. Bila tidak dapat ditentukan, status tidak diwarisi (flag B3).
4. Yang dipakai adalah label utama antesedennya. Bila antesedennya berflag batas, segmen penerus diberi flag B1 dan label alternatifnya dihitung dari label alternatif antesedennya.
5. Konektor atau anafora tidak mengubah acuan K: kalimat sasaran atau cara tetap TJ atau MT meskipun diawali konektor.
6. Segmen pertama abstrak tidak mempunyai antesedens, sehingga konektor di sana tidak memberi PP-2.
7. Segmen dinilai berurutan dari yang pertama; posisi sendiri bukan kriteria (P6).

### 5.3 Kalimat multi-fungsi

Tabel berikut memuat perlakuan seragam untuk struktur yang berulang. Tabel ini menerapkan daftar tertutup U1 sampai U5 dan tidak menambah pemicu.

| Struktur (rumus) | Pemicu | Perlakuan | Hasil khas |
| --- | --- | --- | --- |
| \[kegiatan studi: cara\] + \[adjunct tujuan: relasi, pertanyaan, atau produk yang dituju studi\] | U2 | pecah | MT+TJ |
| \[kegiatan studi: sasaran\] + \[adjunct cara: teknik, data, atau subjek studi\] | U3 | pecah | TJ+MT |
| \[alat, instrumen, atau langkah\] + \[adjunct tujuan: mengukur atau mengumpulkan sesuatu\] | bukan pemicu | satu proposisi | MT |
| \[bingkai studi\] \[temuan\] + \[adjunct akibat: implikasi atau anjuran\] | U4 | pecah | HS+SI |
| \[bingkai studi\] \[temuan\] + \[klausa sebab di dalam cakupan\] | bukan pemicu | satu proposisi | label temuan |
| \[kegiatan studi\] + \[klausa sebab: kondisi sebelum studi\] | U5 | pecah; bagian tanpa isi digabung | label bagian bermuatan |
| \[predikat 1\] dan \[predikat 2\] beracuan berbeda | U1 | pecah | gabungan label |
| \[proposisi\] + \[klausa relatif\], atau \[proposisi\] + \[statistik dalam kurung\] | bukan pemicu | satu proposisi | label induk |

**Pemilik tujuan (U2).** Tujuan dalam adjunct adalah tujuan studi bila klausa utama menyatakan kegiatan studi (K), subjeknya adalah studi (atau pelakunya), dan adjunct menyatakan relasi, pertanyaan, atau produk. Bila klausa utama menyatakan penegasan atau perolehan (acuan X), adjunct tujuan melekat pada isi penegasan itu dan bukan pemicu U2. Tujuan itu adalah tujuan alat bila subjek klausa utama adalah instrumen, teknik, atau langkah, atau adjunct hanya menyatakan pengukuran atau pengumpulan satu hal. Bila kedua pembacaan sah (misalnya tujuan berupa tingkat satu variabel dengan subjek studi), beri flag B4.

**Label ganda dan alternatif.** Segmen berlabel ganda menyumbang semua labelnya pada vektor (Bagian 6). Label alternatif pada B1 bukan label ganda. Kalimat yang memuat dua fungsi tanpa pemicu dalam daftar tertutup (misalnya fungsi kedua berada dalam klausa relatif) tidak dipecah; ia dinilai sebagai satu proposisi dan, bila dua tes lolos, berlaku B1.

### 5.4 Daftar bernomor

1. **Satu segmen.** Induk dan semua butir adalah satu segmen (2.3). Perlakukan sebagai U1: tulis ulang tiap butir dengan induk diulang, beri label per butir, dan gabungkan butir berlabel sama.
2. **Butir sebagai segmen sendiri.** Tiap butir dinilai sendiri. Bila induk berbingkai, cakupan bingkai meliputi semua butir dan butir mewarisi PP-1 (5.1, langkah 3). Butir berupa fragmen tanpa pelaku atau bingkai mewarisi acuan dan status induk; induk tanpa isi sendiri tidak diberi label.
3. **Tanpa induk.** Bila induk terpotong atau tidak ada, tiap butir dinilai sendiri menurut Uji Acuan (5.2), dapat berakhir TT, dan diberi flag B5 untuk memeriksa segmentasi.
4. **Penomor.** Penomor tidak menentukan fungsi.

### 5.5 Penelitian pengembangan produk

**Prinsip tunggal (berlaku juga untuk 5.6 dan 5.7).** Bahan, subjek, korpus, dan prosedur milik studi, termasuk cara memperolehnya, adalah MT. Apa yang diperoleh dari semuanya adalah HS, termasuk produk jadi dan mutunya.

- **TJ:** produk yang dituju dan, bila ada, jenis uji yang dituju, tanpa ciri produk jadi.
- **MT:** model atau tahap pengembangan, alat dan teknologi sebagai sarana pembuatan, subjek uji dan validator, instrumen penilaian, serta teknik analisis kelayakan atau efektivitas.
- **HS:** produk yang dihasilkan beserta ciri atau fitur produk jadi, serta hasil validasi, uji coba, uji teknis, kelayakan, kepraktisan, atau efektivitas yang terikat pada produk (A2) atau subjek uji (A1).
- **SI:** perluasan ke pengguna atau konteks lain, kontribusi, dan saran pengembangan.

**Uji Produk Jadi.** Ganti subjek kalimat dengan “produk yang telah selesai”. Bila kalimat menyatakan sesuatu yang baru dapat diketahui setelah produk selesai (ciri akhir, fitur akhir, hasil uji), acuannya X. Bila kalimat menyatakan langkah atau sarana untuk membuat atau menguji produk, acuannya K. Deskripsi produk yang tidak jelas sebagai rancangan maupun hasil dinilai X dan diberi flag B6 dengan alternatif MT. Kalimat yang hanya menyebut bahwa produk dikembangkan adalah TJ; bagian yang menyebut model, tahap, atau alat dipecah sebagai MT (U3).

### 5.6 Studi literatur

- **Korpus.** Artikel atau dokumen yang ditelaah studi adalah A5. Deskripsi korpus (jumlah, sumber, kriteria seleksi, rentang tahun, jumlah yang lolos seleksi) adalah MT, bukan HS.
- **HS.** Hasil telaah atas isi korpus: pola, tema, perbandingan, kesenjangan, tingkat bukti, atau kerangka hasil sintesis.
- **Bingkai.** Bingkai bersumber studi ini bila menyebut telaah atau korpus studi ini. Bingkai yang hanya menyebut literatur atau pihak lain tanpa kaitan eksplisit ke korpus studi ini bersumber literatur (status pra). Bila kedua pembacaan mungkin, beri flag B6 dengan alternatifnya.
- **SI.** Anjuran penelitian lanjutan dan implikasi bagi praktik atau teori yang melampaui korpus.

### 5.7 Penelitian kualitatif, konseptual, dan abstrak tanpa hasil

- **Kualitatif.** Pendekatan, informan, lokasi, teknik pengumpulan data, dan teknik analisis adalah MT. Tema, pola, atau temuan dari data adalah HS (A5).
- **Konseptual.** Pendekatan analisis atau argumentasi adalah MT. Keluaran konseptual yang dinyatakan isinya dan terikat pada kajian ini (kerangka, tipologi, argumen, proposisi, tema) adalah HS. Implikasi dan anjuran adalah SI.
- **Uji Parafrasa.** Tulis ulang kalimat menjadi “Yang diperoleh studi ini adalah …”. Bila makna tetap, predikat menyatakan perolehan (acuan X). Bila makna berubah karena kalimat hanya menyatakan apa yang dikerjakan atau dibahas, predikat menyatakan pelaksanaan (acuan K). Kalimat yang hanya mengumumkan topik atau lingkup keluaran tanpa menyatakan isinya adalah TJ. Uji ini hanya dipakai bila HS-2 dan MT-2 tidak memutuskan; data atau informasi mentah yang dikumpulkan (skor, jawaban, dokumen) adalah bahan (MT), bukan perolehan.
- **Hitungan keluaran.** Hitungan keluaran (jumlah faktor, tema, atau prinsip) adalah kategori hasil: ia menggugurkan TJ-2, dan kalimat dinilai HS bila HS-1 dan HS-2 terpenuhi, dengan flag B6 bila kalimat itu dapat dibaca sebagai pernyataan sasaran.
- **Abstrak tanpa hasil.** Bila tidak ada segmen yang memenuhi HS, komponen HS bernilai 0 (Bagian 6). HS tidak dipaksa, dan kalimat pengumuman tetap TJ.

> **Keputusan (d) \[KONFIRMASI DOSEN\].** Satu prinsip dipakai untuk semua tipe studi: yang dipakai studi (bahan, subjek, korpus, prosedur) adalah MT, dan yang diperoleh darinya (termasuk produk jadi dan mutunya) adalah HS. Prinsip ini menjaga kesamaan perlakuan antartipe studi dan mencegah HS selalu kosong pada penelitian pengembangan. Konsekuensinya, kelengkapan pada studi literatur dan konseptual bergantung pada ada tidaknya keluaran yang dinyatakan isinya, bukan pada jenis studinya.

## 6. Kelengkapan

**6.1 Definisi operasional.** Kelengkapan dalam penelitian ini adalah kehadiran lima fungsi retoris pada satu abstrak. Ia bukan penilaian mutu isi, kebenaran, atau kejelasan tulisan, dan bukan norma umum tentang abstrak yang baik.

**6.2 Vektor kehadiran.** Untuk abstrak a dengan himpunan segmen S(a), dan L(s) sebagai himpunan label akhir segmen s, vektor v(a) = (LB, TJ, MT, HS, SI) dihitung sebagai berikut.

```latex
v_k(a)=\begin{cases}1 & \exists\, s\in S(a):\ k\in L(s)\\ 0 & \text{jika tidak}\end{cases}\qquad \text{LENGKAP}(a)\iff \prod_{k} v_k(a)=1
```

**6.3 Aturan.**

1. **K1.** Yang dihitung adalah label akhir (data emas, setelah adjudikasi) atau label prediksi (sistem). Label alternatif tidak dihitung pada vektor utama; ia hanya dipakai sebagai pembacaan pembanding pada v-min dan v-maks (K5).
2. **K2.** Segmen berlabel ganda menyumbang semua labelnya.
3. **K3.** LAINNYA dan segmen yang dikecualikan tidak menyumbang komponen apa pun. Label TT harus sudah diselesaikan lewat adjudikasi sebelum vektor dihitung.
4. **K4.** Status LENGKAP jika dan hanya jika v = (1, 1, 1, 1, 1). Selain itu statusnya TIDAK LENGKAP, dengan komponen yang hilang disebut eksplisit, misalnya “TIDAK LENGKAP: hilang HS dan SI”. Tidak ada skor kelengkapan sebagian.
5. **K5.** Untuk setiap abstrak, hitung dua vektor secara simetris dari pembacaan tiap segmen. Segmen final hanya mempunyai satu pembacaan, yaitu label akhirnya. Segmen batas-sisa mempunyai satu pembacaan untuk label akhirnya dan satu untuk tiap label alternatifnya. Segmen dikecualikan mempunyai satu pembacaan tanpa label dan satu untuk tiap label kandidatnya (Bagian 7). v-min bernilai 1 pada komponen k bila ada segmen yang labelnya memuat k pada setiap pembacaannya; v-maks bernilai 1 pada komponen k bila ada segmen yang labelnya memuat k pada sekurang-kurangnya satu pembacaannya. Pada abstrak tanpa segmen batas-sisa atau dikecualikan, v-min dan v-maks sama dengan v. Sebelum adjudikasi, segmen berflag diperlakukan sebagai batas-sisa. Bila v-min sama dengan v-maks, statusnya pasti. Bila berbeda, abstrak berstatus TAK PASTI, dilaporkan terpisah, dan tidak masuk metrik utama; ia masuk analisis sensitivitas.
6. **K6.** Abstrak tanpa hasil memiliki HS = 0 menurut definisi, sehingga statusnya TIDAK LENGKAP: hilang HS. Laporan dipisah per tipe studi agar hasil ini tidak dibaca sebagai kegagalan penulis.
7. **K7.** Kehadiran tidak menilai ukuran: satu segmen cukup untuk satu komponen, tanpa ambang jumlah kalimat.
8. **K8.** Satuan adalah satu abstrak bahasa Indonesia (2.1).

**6.4 Tabel kebenaran.** Angka 1 berarti komponen hadir dan 0 berarti tidak hadir. Dari 32 kombinasi, hanya satu yang LENGKAP.

| LB | TJ | MT | HS | SI | Status | Komponen hilang |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 1 | 1 | 1 | 1 | LENGKAP | tidak ada |
| 0 | 1 | 1 | 1 | 1 | TIDAK LENGKAP | LB |
| 1 | 0 | 1 | 1 | 1 | TIDAK LENGKAP | TJ |
| 1 | 1 | 0 | 1 | 1 | TIDAK LENGKAP | MT |
| 1 | 1 | 1 | 0 | 1 | TIDAK LENGKAP | HS |
| 1 | 1 | 1 | 1 | 0 | TIDAK LENGKAP | SI |
| 0 | 0 | 1 | 1 | 1 | TIDAK LENGKAP | LB, TJ |
| 0 | 1 | 0 | 1 | 1 | TIDAK LENGKAP | LB, MT |
| 0 | 1 | 1 | 0 | 1 | TIDAK LENGKAP | LB, HS |
| 0 | 1 | 1 | 1 | 0 | TIDAK LENGKAP | LB, SI |
| 1 | 0 | 0 | 1 | 1 | TIDAK LENGKAP | TJ, MT |
| 1 | 0 | 1 | 0 | 1 | TIDAK LENGKAP | TJ, HS |
| 1 | 0 | 1 | 1 | 0 | TIDAK LENGKAP | TJ, SI |
| 1 | 1 | 0 | 0 | 1 | TIDAK LENGKAP | MT, HS |
| 1 | 1 | 0 | 1 | 0 | TIDAK LENGKAP | MT, SI |
| 1 | 1 | 1 | 0 | 0 | TIDAK LENGKAP | HS, SI |
| 1 | 1 | 0 | 0 | 0 | TIDAK LENGKAP | MT, HS, SI |
| 1 | 0 | 1 | 0 | 0 | TIDAK LENGKAP | TJ, HS, SI |
| 1 | 0 | 0 | 1 | 0 | TIDAK LENGKAP | TJ, MT, SI |
| 1 | 0 | 0 | 0 | 1 | TIDAK LENGKAP | TJ, MT, HS |
| 0 | 1 | 1 | 0 | 0 | TIDAK LENGKAP | LB, HS, SI |
| 0 | 1 | 0 | 1 | 0 | TIDAK LENGKAP | LB, MT, SI |
| 0 | 1 | 0 | 0 | 1 | TIDAK LENGKAP | LB, MT, HS |
| 0 | 0 | 1 | 1 | 0 | TIDAK LENGKAP | LB, TJ, SI |
| 0 | 0 | 1 | 0 | 1 | TIDAK LENGKAP | LB, TJ, HS |
| 0 | 0 | 0 | 1 | 1 | TIDAK LENGKAP | LB, TJ, MT |
| 1 | 0 | 0 | 0 | 0 | TIDAK LENGKAP | TJ, MT, HS, SI |
| 0 | 1 | 0 | 0 | 0 | TIDAK LENGKAP | LB, MT, HS, SI |
| 0 | 0 | 1 | 0 | 0 | TIDAK LENGKAP | LB, TJ, HS, SI |
| 0 | 0 | 0 | 1 | 0 | TIDAK LENGKAP | LB, TJ, MT, SI |
| 0 | 0 | 0 | 0 | 1 | TIDAK LENGKAP | LB, TJ, MT, HS |
| 0 | 0 | 0 | 0 | 0 | TIDAK LENGKAP | semua komponen |

**6.5 Evaluasi sistem terhadap data emas.** Evaluasi dilakukan pada dua tingkat. Pada tingkat segmen: presisi, recall, dan F1 per kelas, F1 makro, serta kappa terhadap data emas; untuk segmen berlabel ganda, evaluasi per kelas memakai kehadiran biner tiap label. Pada tingkat abstrak: kecocokan penuh vektor, serta presisi, recall, dan F1 per komponen. Abstrak berstatus TAK PASTI dikeluarkan dari metrik utama dan dilaporkan dengan v-min dan v-maks pada analisis sensitivitas.

## 7. Kasus batas dan adjudikasi

**7.1 Flag batas.** Setiap segmen yang memenuhi syarat salah satu flag wajib diberi flag itu, label alternatif (bila ada), dan alasan satu kalimat.

| Flag | Nama | Syarat | Yang dicatat |
| --- | --- | --- | --- |
| B1 | Dua tes lolos | Dua tes positif atau lebih lolos (Bagian 4, Langkah 2); juga segmen penerus dari antesedens berflag (5.2) | label utama menurut urutan, label alternatif |
| B2 | Tidak ada tes lolos | Tidak ada tes positif yang lolos; label TT | alternatif terdekat, tes yang gagal |
| B3 | Status default atau tak pasti | LB-2 lolos hanya karena ketiadaan PP dengan tanda D lemah (kebutuhan, prevalensi, angka tanpa atribusi), atau status dari antesedens tidak dapat ditentukan | alasan dan antesedens yang dirujuk |
| B4 | Dua penulisan ulang sah | UP menghasilkan label berbeda pada dua penulisan ulang yang sama-sama sah | kedua hasil; label utama inklusif |
| B5 | Keraguan segmentasi | Segmen berlabel tiga atau lebih, segmen terpotong, daftar tanpa induk, atau fragmen yang batasnya meragukan | usulan batas |
| B6 | Ambang dapat dibaca dua arah | Satu tes lolos, tetapi ambang (penambat, pelampauan, kekhasan, perolehan atau pelaksanaan) tidak tegas | label alternatif |

Flag dapat berganda (misalnya B3 dan B6) dan dipisah titik koma (Bagian 8). Setiap flag mengantre adjudikasi.

**7.2 Label alternatif.** Paling banyak dua alternatif per segmen, berurutan menurut kedekatan. Alternatif bukan label ganda dan tidak masuk vektor utama; ia dipakai sebagai pembacaan pembanding pada v-min dan v-maks (6.3, K5). Alternatif dipakai untuk adjudikasi dan analisis sensitivitas.

**7.3 Prosedur adjudikasi.**

1. **Antrean.** Segmen masuk antrean bila (a) kedua anotator memberi label atau himpunan label berbeda, (b) salah satu memberi flag apa pun, atau (c) salah satu memberi TT.
2. **Adjudikator.** Adjudikator adalah orang ketiga yang bukan anotator, memakai versi pedoman yang sama, membaca seluruh abstrak, dan tidak mengetahui identitas anotator.
3. **Penentuan.** Adjudikator memeriksa penerapan tes oleh kedua anotator pada simpul yang disebut, lalu menentukan label akhir menurut tes pedoman. Bila tes menghasilkan dua label atau tidak ada, ia mengikuti Langkah 2 (Bagian 4) dan mencatat label alternatif.
4. **Konteks pada B2 dan B3.** Untuk flag B2 dan B3, adjudikator boleh memakai konteks seluruh abstrak sebagai bukti tambahan. Pemakaiannya dicatat, dan posisi saja tidak cukup (P6).
5. **Sisa.** Bila tetap tak terputuskan, segmen berstatus batas-sisa (label akhir sama dengan label utama menurut urutan tes; alternatif dicatat) atau dikecualikan (tidak ada label yang dapat dipertanggungjawabkan). Untuk segmen TT, label akhir diambil dari label alternatif terdekat bila adjudikator menilai satu alternatif lebih dapat dipertanggungjawabkan (status batas-sisa); bila tidak, segmen dikecualikan.
6. **Larangan.** Adjudikator tidak membuat aturan baru, tidak mengubah segmentasi (kecuali pada B5, dengan pencatatan), dan tidak memakai prediksi sistem.

**7.4 Status akhir segmen.**

| Status | Arti | Pemakaian |
| --- | --- | --- |
| final | Label akhir pasti, disepakati atau diputuskan oleh tes | data emas |
| batas-sisa | Label akhir dipilih, alternatif tetap tercatat | data emas dan dilaporkan; analisis sensitivitas tanpa segmen ini |
| dikecualikan | Tidak ada label akhir | tidak dipakai melatih atau menguji; jumlahnya dilaporkan |

**7.5 Pola berulang tanpa mengubah pedoman.** Pedoman dibekukan selama satu putaran anotasi. Pola berulang dicatat pada Daftar Usulan Revisi (Bagian 8). Usulan menjadi perubahan hanya bila (a) berpola struktural, bukan kata tertentu, (b) muncul pada sekurang-kurangnya tiga segmen dari dua abstrak, (c) berlaku untuk semua kalimat bergaya sama, dan (d) tidak membuat tes lain bertentangan. Perubahan dilakukan setelah Pilot 2, dalam versi baru dengan catatan perubahan. Perbaikan pertentangan antaraturan yang dapat ditunjukkan tanpa data tidak memerlukan syarat (b), tetapi dicatat sebagai perbaikan konsistensi.

**7.6 Pelaporan.** Laporkan jumlah dan proporsi segmen per flag dan per status akhir; kesepakatan sebelum adjudikasi (Bagian 9); serta subset data emas ketat (segmen tanpa flag yang disepakati kedua anotator) untuk analisis sensitivitas. Daftar kasus batas sisa dari uji mandiri ada di Bagian B.4.

## 8. Format berkas anotasi

**8.1 Berkas dan konvensi.** Semua berkas berformat CSV, UTF-8 tanpa BOM, pemisah koma; teks yang memuat koma atau baris baru diapit tanda kutip ganda. Dalam satu sel, label ganda dipisah tanda + menurut urutan kemunculan, sedangkan alternatif, flag, dan simpul dipisah titik koma.

| Berkas | Satu baris mewakili | Diisi oleh |
| --- | --- | --- |
| abstrak.csv | satu abstrak | pengumpul teks |
| segmen.csv | satu segmen terbekukan | skrip pemecah dan pemeriksa segmentasi |
| anotasi.csv | satu segmen oleh satu anotator | anotator |
| adjudikasi.csv | satu segmen dalam antrean | adjudikator |
| log\_normalisasi.csv | satu perubahan dari teks mentah ke teks kerja | pengumpul teks |
| usulan\_revisi.csv | satu pola berulang | adjudikator dan peneliti |
| README\_versi.md | satu versi pedoman | peneliti |
| log\_dedup.csv | satu entri artikel yang dibuang atau ditinjau pada deduplikasi (2.5) | pengumpul teks |

**8.2 Kolom abstrak.csv.** `id_abstrak` (kode unik), `bahasa` (id), `peran_data` (data-pengembangan, pilot2, atau korpus-anotasi), `jenis_studi` (kuantitatif, kualitatif, campuran, pengembangan-produk, literatur, atau konseptual; diisi dari pernyataan artikel sendiri sebelum anotasi), `judul`, `jurnal`, `tahun`, `volume_nomor`, `doi` (kosong bila tidak ada), `url`, `jenis_sumber` (pdf\_terbit atau halaman\_artikel; 2.1), `versi_dokumen` (versi terbit, naskah diterima, atau pracetak, sesuai keterangan sumber), `tanggal_akses` (YYYY-MM-DD), `teks_mentah` (verbatim, tidak pernah ditimpa), `hash_teks_mentah` (SHA-256 dari teks mentah), `teks_kerja` (hasil normalisasi minimal tanpa subjudul; 2.2), `lisensi` (sesuai keterangan artikel; \[PERLU VERIFIKASI\] per artikel), kunci\_artikel (kunci identitas; 2.5), hash\_teks\_ternormalisasi (SHA-256 teks kerja ternormalisasi; 2.5), dan status\_dedup (unik, duplikat-dibuang, atau duplikat-dekat-ditinjau; 2.5).

**8.3 Kolom segmen.csv.** `id_abstrak`, `id_segmen`, `urutan`, `teks_segmen`, `asal_segmentasi` (skrip atau manual), `catatan_segmentasi`.

**8.4 Kolom anotasi.csv.** `id_abstrak`, `id_segmen`, `anotator_id`, `label` (LB, TJ, MT, HS, SI, LAINNYA, atau TT; ganda dengan tanda +), `label_alt` (paling banyak dua), `simpul_penentu` (tes atau aturan yang menentukan, misalnya TJ-1;TJ-2;U3), `flag` (B1 sampai B6), `alasan` (wajib bila ada flag), `versi_pedoman`, `urutan_penyajian`, `waktu_mulai`, `waktu_selesai` (ISO 8601 dengan zona waktu), `durasi_detik`.

**8.5 Kolom adjudikasi.csv.** `id_abstrak`, `id_segmen`, `label_anotator_1`, `label_anotator_2`, `label_akhir`, `label_alt_sisa`, `status_akhir` (final, batas-sisa, atau dikecualikan), `konteks_dipakai` (ya atau tidak; ya hanya pada B2 atau B3), `alasan`, `adjudikator_id`, `versi_pedoman`, `waktu_selesai`.

**8.6 Kolom log\_normalisasi.csv dan usulan\_revisi.csv.** Log normalisasi: `id_abstrak`, `posisi_karakter`, `teks_asal`, `teks_baru`, `jenis` (sambung\_kata, hapus\_baris, spasi, ligatur, atau lainnya). Usulan revisi: `id_usulan`, `pola`, `id_segmen_terkait`, `simpul_terkait`, `usulan_umum`, `status` (diajukan, diterima, atau ditolak), `versi_target`.

**8.7 Skema baris anotasi.** Berikut kerangka kolom dengan isian pengganti dalam kurung sudut; ini skema, bukan data.

```csv
id_abstrak,id_segmen,anotator_id,label,label_alt,simpul_penentu,flag,alasan,versi_pedoman,urutan_penyajian,waktu_mulai,waktu_selesai,durasi_detik
<A001>,<A001-S01>,<an1>,<TJ+MT>,<>,<TJ-1;TJ-2;U3>,<B6>,<alasan satu kalimat>,<v1.0>,<3>,<2026-10-12T09:00:00+07:00>,<2026-10-12T09:01:10+07:00>,<70>
```

**8.8 Aturan berkas.**

1. Setiap baris anotasi dan adjudikasi memuat versi pedoman.
2. Berkas anotasi tidak memuat prediksi sistem maupun kamus penanda leksikal.
3. Berkas tiap anotator disimpan terpisah dan tidak dibuka oleh anotator lain sebelum adjudikasi.
4. Teks mentah tidak pernah ditimpa; hash diperiksa setiap kali berkas dibuka.
5. Tanggal akses dan jenis sumber dicatat per abstrak, bukan per kumpulan.

## 9. Protokol validasi (Pilot 2)

**9.1 Tujuan dan kedudukan.** Pilot 2 mengestimasi reliabilitas antaranotator pedoman v1.0 pada abstrak yang belum dipakai menyusun aturan, dan mengidentifikasi aturan yang menghasilkan ketidaksepakatan. Pilot 1 adalah uji mandiri empat abstrak (Bagian B); ia data pengembangan, bukan bukti validasi. Prosedur dan ambang di bawah ditetapkan sebelum data Pilot 2 dilihat dan tidak diubah sesudahnya.

**9.2 Sampel.**

- Sepuluh abstrak bahasa Indonesia dari sekurang-kurangnya lima jurnal berbeda, paling banyak tiga abstrak per jurnal, satu abstrak per artikel.
- Tidak ada artikel yang sama dengan empat abstrak data pengembangan, dan deduplikasi (2.5) dijalankan sebelum penarikan sampel.
- Agar aturan khusus teruji, sekurang-kurangnya satu abstrak untuk tiap jenis studi (kuantitatif, kualitatif, pengembangan produk, literatur, konseptual); sisanya bebas.
- Dipilih acak dalam strata dari kerangka sampel yang dicatat (misalnya penelusuran metadata Garuda untuk menemukan artikel); teks diambil dari sumber kanonik (2.1). Benih acak dan tanggal penarikan dicatat.
- Panjang 4 sampai 15 segmen setelah segmentasi. Rentang ini pilihan penyusun \[KONFIRMASI DOSEN\].

**9.3 Anotator dan adjudikator.**

- Dua anotator independen, penutur asli bahasa Indonesia berpendidikan sarjana, bukan penyusun pedoman.
- Adjudikator adalah orang ketiga yang bukan anotator \[KONFIRMASI DOSEN: siapa orangnya\].
- Pelatihan satu sesi: membaca pedoman, melabeli empat abstrak pengembangan, lalu membahas kuncinya. Lama pelatihan dicatat. Abstrak Pilot 2 tidak dipakai untuk pelatihan.
- Anotasi independen: tanpa komunikasi, urutan abstrak diacak per anotator, tanpa akses ke kamus penanda leksikal atau prediksi sistem.
- Segmentasi dibekukan sebelum anotasi (2.4).

**9.4 Ukuran kesepakatan.** Semua dihitung pada label sebelum adjudikasi, pada segmen yang identik.

| Kode | Ukuran | Dasar hitung |
| --- | --- | --- |
| M1 | Kappa Cohen | label utama per segmen; TT diperlakukan sebagai kategori, dengan analisis sensitivitas tanpa TT |
| M2 | Kappa per kelas | kehadiran biner tiap label (LB, TJ, MT, HS, SI, LAINNYA) pada segmen, sehingga segmen berlabel ganda tidak hilang |
| M3 | Kesepakatan himpunan | proporsi segmen dengan himpunan label identik, dan alpha Krippendorff dengan jarak antarhimpunan, misalnya MASI \[PERLU VERIFIKASI\] |
| M4 | Persentase kesepakatan | kecocokan label utama, dilaporkan bersama distribusi kelas dan flag |
| M5 | Vektor kelengkapan | kappa per komponen dan proporsi abstrak bervektor identik; pada 10 abstrak dilaporkan sebagai hitungan |

Interval kepercayaan memakai bootstrap persentil 95% dengan pengambilan ulang pada tingkat abstrak (bukan segmen), 1.000 kali; ini pilihan penyusun. Kesepakatan segmentasi tidak diukur karena segmentasi dibekukan (Bagian 10).

**9.5 Ambang penerimaan.** Rujukan kandidat, semuanya belum dilampirkan dan wajib diperiksa pada sumber primer \[PERLU VERIFIKASI\]: skala interpretasi kappa oleh Landis dan Koch (1977); konvensi Krippendorff (2004) bahwa alpha sekurang-kurangnya 0,800 dapat diandalkan sedangkan 0,667 sampai 0,800 hanya untuk kesimpulan tentatif; dan tinjauan Artstein dan Poesio (2008) bahwa tidak ada ambang tunggal untuk semua tujuan.

| Hasil M1 | Keputusan |
| --- | --- |
| Titik sekurang-kurangnya 0,80 dan batas bawah CI 95% sekurang-kurangnya 0,67 | Terima: v1.0 dibekukan untuk anotasi korpus |
| Titik 0,67 sampai 0,80, atau titik memenuhi tetapi batas bawah di bawah 0,67 | Terima bersyarat: revisi umum (v1.1) pada aturan penyebab ketidaksepakatan, lalu Pilot 3 dengan abstrak baru; korpus belum dianotasi |
| Titik di bawah 0,67 | Tolak: tinjau rancangan label dan aturan, bukan menambal kalimat; ulangi dengan abstrak baru |

Kelas yang muncul pada sekurang-kurangnya lima segmen (menurut salah satu anotator) dilaporkan kappa per kelasnya, dan kelas dengan kappa di bawah 0,67 dibahas sebagai sumber ketidaksepakatan. Proporsi TT dan tiap flag dilaporkan tanpa ambang karena tidak ada rujukan untuk menetapkannya.

> **Keputusan ambang \[KONFIRMASI DOSEN\].** Angka 0,80 dan 0,67 dipinjam dari konvensi alpha dan dipakai pada kappa sebagai pendekatan; keduanya mengukur kesepakatan yang dikoreksi kebetulan tetapi tidak identik. Dengan sekitar 70 segmen, batas bawah CI akan jauh di bawah titik, sehingga hasil “terima” menuntut kesepakatan sangat tinggi; hal ini disengaja agar pedoman tidak diterima berdasarkan sampel kecil. Dosen dapat memilih meniadakan syarat batas bawah, dengan konsekuensi keputusan lebih longgar.

**9.6 Analisis ketidaksepakatan.** Setiap ketidaksepakatan dipetakan ke simpul aturan (tes atau aturan) yang diterapkan berbeda. Keluarannya matriks konfusi antaranotator dan tabel ketidaksepakatan per simpul. Pola yang memenuhi syarat 7.5 menjadi usulan revisi umum.

**9.7 Pembekuan dan pelaporan.**

1. Pedoman, ambang, dan prosedur dibekukan (hash berkas pedoman dicatat) sebelum anotasi dimulai.
2. Abstrak Pilot 2 tidak dipakai menyusun aturan; bila kemudian dipakai merevisi pedoman, ia tidak dapat menjadi bukti validasi versi yang direvisi.
3. Laporan memuat M1 sampai M5 beserta CI, jumlah segmen per kelas, proporsi flag dan status akhir, serta keterbatasan di Bagian 10.
4. Empat abstrak pengembangan tidak dilaporkan sebagai bukti validasi.

## 10. Ancaman validitas dan keterbatasan

Ancaman terbesar adalah bahwa pedoman ini baru diuji oleh penyusunnya sendiri dan belum menyentuh data nyata; ukuran reliabilitas pertama baru muncul dari Pilot 2. Ambiguitas sisa dari uji mandiri tercatat di Bagian B.4.

| Ancaman | Uraian | Mitigasi dan sisa risiko |
| --- | --- | --- |
| Konstruk: kelengkapan sebagai kehadiran | Lima komponen dan pemetaan IPMRC belum diperiksa pada sumber primer; LENGKAP tidak berarti abstrak baik | Definisi operasional eksplisit (6.1) dan laporan per tipe studi; sisa risiko: disalahbaca sebagai penilaian mutu |
| Konstruk: SI menggabungkan simpulan dan saran | Alasan bertumpu pada Hyland (2000) \[PERLU VERIFIKASI\]; vektor tidak membedakan abstrak yang hanya bersaran | Keputusan terkunci; pemisahan memerlukan versi pedoman baru |
| Sirkularitas dengan sistem rule-based | Definisi berbasis fungsi dan kamus dipisah (P5), tetapi satu orang menyusun keduanya; beberapa bentuk rujukan diri muncul sebagai ilustrasi di 3.0 | Kamus hanya diturunkan dari data pengembangan dan tidak dilihat anotator; sisa risiko: intuisi penyusun yang sama |
| Penguji tidak independen | Uji adversarial, uji konsistensi, dan pelabelan empat abstrak dikerjakan oleh penyusun aturan | Seluruh hasil Bagian B perlu ditinjau orang kedua; Pilot 2 adalah uji independen pertama |
| Data pengembangan kecil dan sempit | Empat abstrak (28 segmen) mencakup satu studi kuantitatif, satu studi literatur, satu studi campuran, dan satu studi hukum normatif; tidak ada penelitian pengembangan produk, kalimat LAINNYA, TT, atau B1. Putaran 2 mengubah aturan setelah melihat data, sehingga ada risiko overfitting | Perubahan berbasis data hanya untuk pola yang muncul pada tiga segmen dari dua abstrak (satu perubahan, R2-1); dua usulan dari satu segmen ditarik (B.3); aturan 5.5, LAINNYA, B1, dan TT hanya teruji sintetis, sehingga Pilot 2 wajib mencakupnya |
| Reliabilitas pada sampel kecil | Sekitar 70 segmen, satu pasang anotator, CI lebar; kappa peka terhadap distribusi kelas | Laporkan persentase, CI, dan kappa per kelas; ambang tidak dipakai mekanis (9.5) |
| Segmentasi dibekukan | Kesepakatan segmentasi tidak diukur; kesalahan batas merambat ke label dan vektor | Pemeriksa manual dan flag B5; sisa risiko tidak terukur |
| Sumber teks | PDF dan halaman artikel dapat berbeda (ligatur, pemenggalan kata, karakter khusus); tata letak tabel dua kolom (A2) mengacaukan urutan baca dan menuntut ekstraksi per kolom; laman jurnal A1 memuat dua rumusan abstrak yang berbeda (metadata dan tampilan), sehingga hanya PDF yang dipakai | Satu sumber kanonik dan hash; verifikasi verbatim hanya terhadap sumber yang sama |
| Kerangka sampel | Metadata Garuda hanya mencakup jurnal yang terindeks; lima sampai sepuluh jurnal tidak mewakili semua jurnal Indonesia | Generalisasi dibatasi pada jurnal serupa; kerangka sampel dilaporkan |
| Subjudul dibuang (2.2) | Abstrak terstruktur kehilangan petunjuk seksi; bila sistem kelak menerima teks bersubjudul, distribusinya berbeda dari data latih | Dicatat sebagai keputusan untuk dosen; sisa risiko pada penerapan sistem |
| Kalimat tanpa penanda status | Kalimat seperti H-1, H-2, dan I-3 berakhir TT atau LB berflag B3; keempat abstrak tidak memuat satu pun, sehingga proporsinya pada korpus belum diketahui | Flag B3, konteks wacana pada adjudikasi (7.3), analisis sensitivitas; sisa risiko LB menyerap saran tanpa penanda |
| Label utama pada B1 | Ditentukan urutan tes, bukan klaim prioritas fungsi; model yang dilatih pada label utama saja dapat mewarisi urutan itu | Label alternatif disimpan; analisis sensitivitas pada segmen berflag B1 |
| Multi-label | UP menambah kerumitan dan dapat melipatgandakan ketidaksepakatan | M2 dan M3 mengukur kesepakatan per label dan per himpunan |
| Cakupan bahasa dan genre | Hanya bahasa Indonesia dan abstrak artikel jurnal | Tidak berlaku untuk abstrak skripsi, prosiding, atau bahasa Inggris tanpa validasi ulang |
| Hak cipta dan lisensi | Abstrak dilindungi hak cipta penerbit atau penulis; lisensi berbeda per artikel \[PERLU VERIFIKASI\] | Simpan hash dan tautan; bila teks tidak boleh dibagikan, bagikan label dan ID tanpa teks |
| Kelelahan dan urutan | Mutu anotasi dapat turun seiring waktu atau dipengaruhi urutan abstrak | Urutan diacak per anotator; waktu anotasi dicatat (Bagian 8) |

## 11. Daftar keputusan yang perlu konfirmasi dosen pembimbing

Dua puluh sembilan keputusan menunggu konfirmasi; lima di antaranya diringkas untuk dosen di Bagian C.1, dan nomor yang sama dipakai di Bagian C.2 yang memuat pilihan dalam draf, alternatif, dan dampaknya. Butir (a) sampai (g) adalah keputusan yang diminta untuk diputuskan penyusun; butir 8 sampai 29 muncul selama penyusunan dan pengujian.

1. (a) Aturan Bingkai, cakupan, dan klausa sebab dependen (5.1).
2. (b) Ambang HS berbasis penambat, bukan modalitas (3.4).
3. (c) Jangkar SI: pasca-penelitian dan pelampauan; SI tidak mengandaikan HS (3.5).
4. (d) Perlakuan HS dan MT pada penelitian pengembangan, studi literatur, kualitatif, dan konseptual (5.5 sampai 5.7).
5. (e) Satuan teks: abstrak bahasa Indonesia dan kebijakan satu sumber teks (2.1).
6. (f) Segmentasi dibekukan sebelum pelabelan dan perlakuan daftar bernomor (2.3, 2.4, 5.4).
7. (g) LAINNYA, TT, dan larangan LB menyerap kalimat sisa (3.6).
8. Judul dan subjudul seksi dikeluarkan dari teks kerja (2.2).
9. Daftar tertutup pemicu UP (U1 sampai U5) dan label utama inklusif pada B4 (4).
10. Urutan tes dan penetapan label utama pada B1 (4).
11. Pra-default pada LB-2 (B3) dan TT untuk kalimat bermuatan data tanpa penanda status (3.1, 5.2).
12. Definisi P1 sampai P3, anjuran sebagai penerima ditambah tindakan, dan SI-3 (3.0, 3.5).
13. Flag B6 dan pemakaian konteks wacana pada adjudikasi B2 dan B3 (7).
14. Definisi simetris v-min dan v-maks serta status TAK PASTI (6.3).
15. Abstrak tanpa hasil berstatus TIDAK LENGKAP: hilang HS (6.3).
16. Verifikasi rujukan IPMRC dan Hyland (2000) pada sumber primer (1.3, 1.4).
17. Komposisi sampel Pilot 2 dan rentang 4 sampai 15 segmen (9.2).
18. Anotator dan adjudikator Pilot 2 (9.3).
19. Ukuran kesepakatan dan ambang penerimaan (9.4, 9.5).
20. Tafsir “setiap aturan” pada uji adversarial sebagai kelompok aturan (B.2).
21. Lisensi dan penyimpanan teks abstrak (8.2, 10).
22. Aturan Kohesi dan pewarisan status antarkalimat (5.2).
23. Dua tingkat tanda D (kuat dan lemah) dan B3 yang dipersempit pada tanda D lemah (3.1, 5.2, 7.1).
24. Penarikan dua usulan Putaran 2 yang hanya bertumpu pada satu segmen, dan pencatatannya sebagai kasus batas (B.3, B.4).
25. Pengecualian perbaikan pertentangan antaraturan pada ambang perubahan aturan (7.5, B.3).
26. Pelabelan empat abstrak oleh penyusun tanpa anotator kedua sebagai dasar contoh nyata (B.1).
27. Ambang duplikat dekat pada deduplikasi korpus (2.5).
28. Tangga penyederhanaan (C.1 butir 5).
29. Skala korpus dan beban anotasi (1.5).

# BAGIAN B. HASIL UJI MANDIRI

Bagian B memuat hasil Tahap 3. Uji pada empat abstrak (3a) belum dapat dikerjakan; uji adversarial (3b) dan uji konsistensi (3c) selesai pada Putaran 1.

## B.1 Uji pada empat abstrak (Tahap 3a)

Empat abstrak berbahasa Indonesia dari PDF yang diunggah (28 segmen) dianotasi oleh penyusun menurut pedoman setelah Putaran 2. Segmentasi dikerjakan skrip menurut 2.3 dan diperiksa manual. Ini bukan anotasi independen: tidak ada anotator kedua, adjudikasi, atau pencatatan waktu. Abstrak bahasa Inggris pada A1, A2, dan A4 tidak dianotasi (2.1); PDF A3 tidak memuat abstrak bahasa Inggris. Kolom Label memuat label utama dan, dalam kurung, alternatif.

### B.1.1 Sumber dan teks mentah

| Kode | Penulis dan tahun | Jurnal, volume, nomor, halaman awal | DOI artikel | Jenis studi | Ekstraksi teks | Versi dan riwayat | Tanggal akses |
| --- | --- | --- | --- | --- | --- | --- | --- |
| A1 | Supriyadi, Nasution, dan Amalia (2024) | Jurnal TEKNODIK 28(2), hlm. 113 | 10.32550/teknodik.vi.1185 (laman jurnal) | kuantitatif (survei asosiatif) | pdftotext, halaman 1 | PDF berkop jurnal; diterima 05 Des 2024, direvisi 05 Des 2024, disetujui 06 Feb 2025 | PDF 2026-10-10; ekstraksi ulang dan laman 2026-10-11 |
| A2 | Kurniawan dan Siswanto (2024) | PELASTEK 4(1), hlm. 17 | 10.33369/pelastek.v4i1.41760 (PDF) | literatur (tinjauan literatur) | pdfplumber, kolom Abstrak (tata letak tabel dua kolom mengacaukan urutan baca pdftotext) | PDF berkop jurnal; diterima 08 Mei 2025, revisi 18 Jun 2025, diterima 29 Jun 2025 (tidak konsisten dengan kop Juni 2024; dicatat apa adanya) | PDF 2026-10-10; ekstraksi ulang 2026-10-11 |
| A3 | Anwar, Caroline, Kornarius, Gusti, dan Gunawan (2024) | eCo-Buss 7(1), hlm. 226 | 10.32877/eb.v7i1.1284 (laman jurnal) | campuran (survei dan wawancara terstruktur) | pdftotext, halaman 1 | PDF berkop jurnal; unggah 10 Mei 2024, revisi 11 Mei 2024, diterima 11 Mei 2024, tersedia daring 10 Agu 2024 | PDF 2026-10-10; ekstraksi ulang dan laman 2026-10-11 |
| A4 | Tullah dan Fakhsal (2024) | Jurnal Yuridis 11(2), hlm. 394 | 10.35586/jyur.v11i2.9649 (laman jurnal) | yuridis normatif (kepustakaan) | pdftotext, halaman 1 | PDF berkop jurnal Desember 2024; laman artikel ada di situs jurnal | PDF 2026-10-10; ekstraksi ulang dan laman 2026-10-11 |

Hash SHA-256 dihitung pada berkas PDF dan pada berkas teks mentah yang disimpan (A1\_teks\_mentah.txt sampai A4\_teks\_mentah.txt; batas seragam menurut 2.2, baris baru apa adanya, satu baris baru akhir). Hash teks mentah A1 dan A2 dihitung ulang setelah batasnya diseragamkan; hash lama (A1 be36b6433a32… dan A2 984242632cee…) tidak berlaku.

```csv
kode,sha256_berkas_pdf,sha256_teks_mentah
A1,4bd57189079fdae3324895539fbfe2bb22bf7d243f2413c758140aafb547b0c0,ebacb01c42c7c0ef8d2afbe590f2cea0da043483c0d76b368980bbbda116d94d
A2,4d3060bbcc1f5e6c7f01ab46213417935379e88faab095c380ad73a0b48fea2e,f15a3c4baf3b8705974341aa3afe3371cbf5f97240f32c7a52ddc157d574c911
A3,f1a30b0ab4b1997de1ea25b566db585f5d46680fa985433eb0dbe78d6008de53,4ffcbf54adc909aa05ae3bfecfee65d2a6f72df3a4a9230ec0d7aeb81af875db
A4,0b8281b208974d8d8402a0eac7c6d5a2fee9cdb3cf673a43354f45a3df549077,0e30ae799640b6bbdab8945545f328aa1b150b3a98bfbfd3f0ff7b374c5b56b5
```

Batas teks mentah seragam (2.2): dari karakter pertama kalimat pertama sampai karakter terakhir kalimat terakhir isi abstrak; label seksi (“ABSTRAK:” pada A1, “Abstrak” pada A2 dan A4), judul, dan kata kunci berada di luar batas. Teks mentah disimpan sebagai berkas teks UTF-8 per abstrak dan hash-nya dihitung pada berkas itu. Teks kerja: baris baru diganti spasi (A1 26, A2 15, A3 19, A4 13 pergantian); ejaan tidak diperbaiki. Pada keempat abstrak tidak ada kata terpenggal di akhir baris, ligatur, atau karakter non-ASCII.

**Tautan laman jurnal (diperiksa 2026-10-11).** DOI dan URL A1, A3, dan A4 tidak tercantum pada PDF; keduanya diambil dari laman artikel di situs jurnal. Laman hanya dipakai untuk metadata dan pemeriksaan silang; teks tetap berasal dari PDF (2.1).

| Kode | DOI | URL laman jurnal | Lisensi | Catatan pemeriksaan laman |
| --- | --- | --- | --- | --- |
| A1 | https://doi.org/10.32550/teknodik.vi.1185 | https://jurnalteknodik.kemendikdasmen.go.id/index.php/jurnalteknodik/article/view/1185 | CC BY-NC-SA 4.0 (metadata artikel) | Laman mencantumkan dua penulis (PDF: tiga), terbit 2024-12-31, dan terbitan diterbitkan 2025-05-14. Metadata laman memuat redaksi abstrak yang berbeda dari abstrak yang ditampilkan; abstrak tampil sama dengan PDF. |
| A2 | https://doi.org/10.33369/pelastek.v4i1.41760 | tidak dicari | CC BY-SA (PDF) | DOI dari PDF. |
| A3 | https://doi.org/10.32877/eb.v7i1.1284 | https://jurnal.kdi.or.id/index.php/eb/article/view/1284 | tidak ditemukan pada laman | Terbit 2024-08-10. Abstrak laman sama dengan PDF. |
| A4 | https://doi.org/10.35586/jyur.v11i2.9649 | https://ejournal.upnvj.ac.id/Yuridis/article/view/9649 | CC BY 4.0 (laman) | Abstrak laman sama dengan PDF. Cuplikan halaman terbitan (tidak dapat dibuka langsung) mencantumkan terbit daring 2025-11-28, sedangkan kop PDF Desember 2024. |

### B.1.2 A1: Supriyadi, Nasution, dan Amalia (2024), kuantitatif

| Segmen | Kalimat (verbatim) | Label (alternatif) | Simpul penentu | Flag | Catatan |
| --- | --- | --- | --- | --- | --- |
| A1-S01 | Perkembangan teknologi terus mendorong penggunaan artificial intelligence (AI) pada cara pembelajaran mahasiswa di Indonesia. | LB | Uji Acuan Q3 (kelas umum); LB-1 sampai LB-3 | tidak ada | Fenomena umum tanpa atribusi; tidak ada PP, sehingga status pra (LB-2). |
| A1-S02 | Keberadaan artificial intelligence (AI) telah memberikan dampak signifikan bagi dunia pendidikan. | LB | Uji Acuan Q3; LB-1 sampai LB-3 | tidak ada | Pernyataan umum tentang dunia pendidikan. |
| A1-S03 | Penelitian ini bertujuan untuk mengungkap pengaruh teknologi artificial intelligence (AI) dan literasi digital terhadap hasil belajar mata kuliah Evaluasi Pembelajaran. | TJ | TJ-1, TJ-2, TJ-3 | tidak ada | Predikat kegiatan, bukan bingkai; relasi variabel dicari tanpa nilai. |
| A1-S04 | Metode penelitian yang digunakan adalah metode kuantitatif asosiatif dengan pendekatan survei. | MT | MT-1 sampai MT-3; U3 (kedua bagian MT, digabung) | tidak ada | Desain dan pendekatan. |
| A1-S05 | Teknik pengambilan sampel menggunakan random sampling dengan jumlah sampel 155 mahasiswa Program Sarjana, Program Studi Pendidikan Ekonomi, Fakultas Ilmu Pendidikan, Universitas Panca Sakti Bekasi. | MT | MT-1 sampai MT-3; HS-2 gagal (deskripsi subjek) | tidak ada | Angka 155 menjelaskan sampel, bukan keluaran. |
| A1-S06 | Data penelitian diperoleh dari instrumen teknologi artificial intelligence (AI) dan instrumen literasi digital yang valid dan reliabel; data hasil belajar mata kuliah Evaluasi Pembelajaran Pendidikan Ekonomi diperoleh dari nilai ujian akhir semester gasal. | MT | U1 (titik koma; kedua bagian MT, digabung); MT-1 sampai MT-3; HS-2 gagal (deskripsi bahan) | tidak ada | Predikat “diperoleh” menyatakan sumber data, bukan perolehan hasil (perbaikan R2-2). |
| A1-S07 | Hasil penelitian mengungkapkan bahwa teknologi artificial intelligence berpengaruh positif terhadap hasil belajar mata kuliah Evaluasi Pembelajaran; kedua, terdapat pengaruh literasi digital terhadap hasil belajar mata kuliah Evaluasi Pembelajaran; teknologi artificial intelligence (AI) dan literasi digital secara bersama-sama dan simultan berpengaruh terhadap hasil belajar mata kuliah Evaluasi Pembelajaran Pendidikan Ekonomi. | HS+LB (HS) | U1 (tiga butir); dua penulisan ulang sah: butir 2 dan 3 digabung ke butir 1 (HS), atau berdiri sendiri dengan tanda D positif (LB); PP-1; A3; HS-1 sampai HS-3 | B4 | B4: label utama inklusif HS+LB, alternatif HS (Bagian 4). Tanpa tanda D positif, butir 2 dan 3 tidak lolos tes mana pun sebagai proposisi mandiri dan digabung ke butir 1; pewarisan bingkai lewat titik koma tidak diatur eksplisit (B.4). |
| A1-S08 | Simpulannya, teknologi artificial intelligence (AI) dalam pembelajaran memerlukan pengawasan oleh dosen serta kemampuan dan integritas mahasiswa dalam bentuk literasi digital mahasiswa. | SI | 5.1 langkah 1(a) (perbaikan R2-4); PP-1; P1, P2; SI-1 sampai SI-3; HS-2 gagal (tanpa penambat) | tidak ada | Kebutuhan pengawasan oleh dosen; melampaui data. |

### B.1.3 A2: Kurniawan dan Siswanto (2024), studi literatur

| Segmen | Kalimat (verbatim) | Label (alternatif) | Simpul penentu | Flag | Catatan |
| --- | --- | --- | --- | --- | --- |
| A2-S01 | Otomatisasi laboratorium berbasis Artificial Intelligence (AI) menjadi tren yang semakin penting dalam upaya meningkatkan efisiensi dan produktivitas penelitian ilmiah. | LB | Uji Acuan Q3 (tren umum); LB-1 sampai LB-3 | tidak ada | Tren umum tanpa atribusi. |
| A2-S02 | Studi ini mengkaji perancangan sistem otomatisasi laboratorium yang memanfaatkan AI untuk mengoptimalkan penggunaan sumber daya. | TJ | TJ-1, TJ-2, TJ-3 | tidak ada | Klausa relatif memuat tujuan sistem, bukan tujuan studi, dan bukan pemicu (5.3). |
| A2-S03 | Melalui tinjauan literatur komprehensif dan analisis studi kasus terkini, penelitian ini mengeksplorasi komponen kunci, tantangan implementasi, dan potensi dampak dari sistem otomatisasi berbasis AI dalam setting laboratorium. | MT+TJ | U3; MT-1 sampai MT-3 (bagian “Melalui ...”); TJ-1 sampai TJ-3 (bagian “penelitian ini mengeksplorasi ...”) | tidak ada | Satu-satunya sumber komponen MT pada abstrak ini; tanpa pemecahan U3 komponen itu hilang. Bagian kedua mengumumkan topik keluaran tanpa isi (5.7), sehingga TJ. |
| A2-S04 | Hasil menunjukkan bahwa integrasi AI dalam otomatisasi laboratorium dapat secara signifikan meningkatkan efisiensi penggunaan sumber daya, meminimalkan limbah, dan meningkatkan akurasi hasil penelitian. | HS (SI) | PP-1; A3; HS-1 sampai HS-3 | B6 | Subjek generik tanpa perluasan eksplisit, sehingga P1 tidak terpenuhi, tetapi dapat dibaca sebagai generalisasi (SI); modalitas tidak dipakai. Seragam dengan C-2. |
| A2-S05 | Namun, implementasi yang efektif memerlukan pendekatan holistik yang mempertimbangkan aspek teknis, ekonomi, dan etika. | SI (LB) | PP-2 (konektor ke A2-S04 berlabel HS), sehingga acuan X (perbaikan R2-6); P1, P2; SI-1 sampai SI-3; HS-2 gagal | B6 | Tanpa penambat, sehingga bukan HS; status pasca hanya bertumpu pada konektor (PP-2), dan tanpa konektor kalimat ini LB. |
| A2-S06 | Studi ini menyoroti pentingnya kolaborasi multidisiplin dan adaptasi berkelanjutan terhadap perkembangan teknologi AI untuk mencapai sistem otomatisasi laboratorium yang optimal dan berkelanjutan. | SI (HS; TJ) | PP-3; P1, P2; SI-1 sampai SI-3; Uji Parafrasa (5.7); U2 tidak berlaku (perbaikan R2-3) | B6 | Predikat dapat dibaca sebagai pelaksanaan (TJ) atau perolehan (HS); klausa utama dibaca sebagai penegasan, sehingga adjunct tujuan bukan pemicu U2. Padanan sintetis: T-2. |

### B.1.4 A3: Anwar dkk. (2024), campuran

| Segmen | Kalimat (verbatim) | Label (alternatif) | Simpul penentu | Flag | Catatan |
| --- | --- | --- | --- | --- | --- |
| A3-S01 | Revolusi pada big data dan perkembangan kapasitas komputasi membawa dampak terhadap berbagai industri, termasuk pada industri kreatif. | LB | Uji Acuan Q3; LB-1 sampai LB-3 | tidak ada | Pernyataan umum tentang industri. |
| A3-S02 | Industri kreatif mempunyai dampak yang cukup signifikan terhadap laju Produk Domestik Bruto (PDB) yang merupakan faktor yang berkontribusi secara signifikan terhadap pertumbuhan ekonomi negara. | LB | Uji Acuan Q3; LB-1 sampai LB-3 | tidak ada | Klausa relatif tidak dipecah. |
| A3-S03 | Hal ini membuat industri kreatif menjadi salah satu alternatif kuat untuk membangun kerajaan bisnis maupun sebagai pilihan sektor yang menarik untuk digeluti di dunia profesional. | LB | Kohesi (anafora ke A3-S02 berlabel LB, status pra); LB-1 sampai LB-3 | tidak ada | Status pra diwarisi dari antesedens. |
| A3-S04 | Namun, di era digital dimana penggunaan artificial intelligence (AI) sudah semakin marak, para penggiat di industri kreatif mulai mendapat tantangannya tersendiri. | LB | Kohesi (konektor ke A3-S03 berlabel LB); LB-1 sampai LB-3 | tidak ada | Menyatakan masalah. |
| A3-S05 | Hal ini dikarenakan para penggiat di industri kreatif dihadapkan pada kenyataan bahwa teknologi dapat menjadi ancaman untuk pekerjaan mereka juga dapat menjadi alat bantu yang dapat mendukung pekerjaan mereka. | LB | Kohesi (anafora ke A3-S04 berlabel LB); U5 (bagian “Hal ini” tanpa isi, digabung); LB-1 sampai LB-3 | tidak ada | Alasan bagi masalah. |
| A3-S06 | Penelitian ini hendak mengetahui bagaimana perkembangan AI mempengaruhi sikap pelaku di industri kreatif. | TJ | TJ-1, TJ-2, TJ-3 | tidak ada | Pertanyaan relasi tanpa nilai. |
| A3-S07 | Theory of Planned Behavior digunakan sebagai dasar untuk memahami perilaku yang muncul akibat disrupsi AI. | MT (LB) | MT-1, MT-2 (pendekatan teoretis); U2 tidak berlaku (subjek klausa utama adalah teori sebagai alat) | B6 | Definisi MT tidak menyebut kerangka teori secara eksplisit; dibaca sebagai pendekatan (3.3). Alternatif LB bila teori dibaca sebagai pengetahuan latar. |
| A3-S08 | Metode campuran digunakan agar dapat memberikan asumsi secara menyeluruh atas akibat dari disrupsi AI, sekaligus juga bisa mendapatkan gambaran pemahaman secara holistik dari kacamata penggiat industri kreatif yang diwakili oleh beberapa responden dari berbagai bidang keahlian melalui wawancara terstruktur. | MT | MT-1 sampai MT-3; tujuan adjunct milik metode (5.3) | tidak ada | Desain campuran, subjek, dan teknik; klausa relatif tidak dipecah. |
| A3-S09 | Responden wawancara yang bekerja di industri kreatif, menyatakan bahwa kehadiran AI banyak membantu proses kreatif mereka sampai pada tahapan tertentu. | HS | PP-3 (responden wawancara sebagai subjek studi); A1; HS-1 sampai HS-3 | tidak ada | Sumber pernyataan adalah subjek studi, bukan pihak eksternal. |
| A3-S10 | Yakni, AI dipergunakan sebagai sarana triangulasi, referensi untuk pengembangan ide orisinil, membaca trend terkini, serta sebagai alat bantu ketika dihadapkan pada kebutuhan dengan waktu yang terbatas. | HS | PP-2 (konektor elaboratif ke A3-S09 berlabel HS); A5; HS-1 sampai HS-3 | tidak ada | Daftar kegunaan AI adalah pola dari data wawancara. |

### B.1.5 A4: Tullah dan Fakhsal (2024), yuridis normatif (kepustakaan)

| Segmen | Kalimat (verbatim) | Label (alternatif) | Simpul penentu | Flag | Catatan |
| --- | --- | --- | --- | --- | --- |
| A4-S01 | Penelitian ini didasari atas dinamika perkembangan teknologi Artificial Intelligence di Indonesia yang tidak diikuti dengan perkembangan regulasi yang mumpuni yang pada akhirnya melahirkan problematika multidimensional khususnya dalam kaitannya dengan Kekayaan Intelektual. | LB | Uji Acuan Q3; LB-1 sampai LB-3 (alasan) | tidak ada | Klausa utama “Penelitian ini didasari” tidak memuat sasaran atau cara; isinya kondisi di luar studi. |
| A4-S02 | Berbanding terbalik dengan Uni Eropa yang telah diklaim mampu memberikan perlindungan terhadap permasalahan tersebut melalui pengaturan komprehensifnya terkait dengan Artificial Intelligence, European Union Artificial Intelligence Act. | LB | Uji Acuan Q3 (atribusi eksternal tersirat); Kohesi (kontras ke A4-S01 berlabel LB); LB-1 sampai LB-3 | tidak ada | Fragmen tanpa klausa utama tetapi memuat informasi, sehingga segmen sendiri (2.3). |
| A4-S03 | Melalui penelitian ini, peneliti berhasil untuk mengumpulkan, menganalisis, dan menjelaskan problematika dalam perkembangan Artificial Intelligence yang terjadi dalam dimensi Kekayaan Intelektual, seperti penggunaan tanpa hak suatu kekayaan intelektual dalam proses pembelajaran Artificial Intelligence, kaitannya dengan Kekayaan Intelektual sebagai data pribadi, dan kurangnya perlindungan dalam regulasi yang ada. | HS (MT; TJ) | U1; PP-3; A5; HS-1 sampai HS-3; TJ-2 gagal (kategori hasil); MT-3 gagal | B6 | Predikat “mengumpulkan, menganalisis” (cara) dan “menjelaskan problematika seperti ...” (hasil) berbagi satu objek yang memuat kategori hasil, sehingga semua bagian HS. Abstrak ini tidak punya kalimat TJ atau MT lain. |
| A4-S04 | Disimpulkan juga bahwa perlindungan hukum yang diberikan oleh European Union Artificial Intelligence Act terhadap Kekayaan Intelektual semestinya dapat dijadikan acuan dalam penyusunan peraturan komprehensif sebagai solusi penyelesaian problematika yang muncul di Indonesia. | SI | 5.1 langkah 1(a); PP-1; P2, P3; SI-1 sampai SI-3; HS-3 gagal | tidak ada | Anjuran kebijakan. |

### B.1.6 Vektor kelengkapan

| Abstrak | v-min (LB, TJ, MT, HS, SI) | v-maks (LB, TJ, MT, HS, SI) | Status | Penyebab ketidakpastian |
| --- | --- | --- | --- | --- |
| A1 | 1, 1, 1, 1, 1 | 1, 1, 1, 1, 1 | LENGKAP (pasti) | A1-S07 berflag B4, tetapi HS hadir pada kedua pembacaan. |
| A2 | 1, 1, 1, 0, 0 | 1, 1, 1, 1, 1 | TAK PASTI | HS hanya berasal dari A2-S04 (B6); SI hanya dari A2-S05 dan A2-S06 (B6). MT hanya berasal dari A2-S03 lewat pemecahan U3. |
| A3 | 1, 1, 1, 1, 0 | 1, 1, 1, 1, 0 | TIDAK LENGKAP: hilang SI (pasti) | A3-S07 berflag B6, tetapi MT dan LB hadir pada segmen lain. |
| A4 | 1, 0, 0, 0, 1 | 1, 1, 1, 1, 1 | TAK PASTI | HS, MT, dan TJ bergantung pada A4-S03 (B6). |

### B.1.7 Verifikasi dan batas data

Ke-28 segmen dan 16 kutipan contoh di Bagian 3 (13 kalimat berbeda) dicocokkan dengan berkas teks mentah yang disimpan (A1\_teks\_mentah.txt sampai A4\_teks\_mentah.txt, diekstrak dari PDF yang sama), hanya dengan menyamakan spasi dan baris baru; seluruhnya cocok. Abstrak pada laman jurnal A1, A3, dan A4 juga sama dengan PDF setelah spasi dinormalkan; itu pemeriksaan silang, bukan verifikasi (2.1). Tidak ada kutipan yang dicocokkan terhadap halaman artikel atau sumber lain. Keempat abstrak tidak memuat penelitian pengembangan produk (5.5), segmen LAINNYA, TT, maupun B1, sehingga bagian aturan itu hanya teruji secara sintetis (B.2). Karena belum ada adjudikasi, semua segmen berflag (B4 dan B6) diperlakukan sebagai batas-sisa pada v-min dan v-maks (6.3, K5).

## B.2 Uji adversarial (Tahap 3b)

Aturan dikelompokkan menjadi sebelas kelompok, dan tiap kelompok diuji dengan sekurang-kurangnya tiga kalimat \[SINTETIS\] yang dirancang paling mungkin membuat dua anotator berbeda (tafsir ini perlu konfirmasi, butir 20). Penerapan dilakukan manual oleh penyusun pada aturan Bagian 3 sampai 6 setelah perbaikan Putaran 1 dan 2; hasilnya belum ditinjau orang kedua. Kolom Label memuat label utama dan, dalam kurung, alternatif. Semua kalimat bertanda \[SINTETIS\] dan hanya berfungsi sebagai kasus batas.

| Kode | Kelompok aturan | Bagian |
| --- | --- | --- |
| S | Segmentasi | 2.3 |
| C | Cakupan bingkai dan klausa sebab | 5.1 |
| I | Implikasi dan kohesi antarkalimat | 3.5, 5.2 |
| U | Uji Pemecahan | 4, 5.3 |
| D | Daftar bernomor | 5.4 |
| P | Penelitian pengembangan | 5.5 |
| L | Studi literatur | 5.6 |
| T | Abstrak tanpa hasil, kualitatif, konseptual | 5.7 |
| H | Kalimat bermuatan data tanpa penanda status | 5.2 |
| O | LAINNYA | 3.6 |
| K | Kelengkapan | 6 |

### B.2.1 Kelompok S: segmentasi

| ID | Teks mentah \[SINTETIS\] | Segmentasi menurut 2.3 | Flag | Catatan |
| --- | --- | --- | --- | --- |
| S-1 | Data dianalisis dengan uji-t (p < 0,05).Hasil menunjukkan bahwa kelas eksperimen lebih tinggi. | Dua segmen, dipisah setelah tanda kurung dan titik | tidak ada | Titik tanpa spasi; token sebelumnya bukan singkatan atau desimal, sehingga batas. Dicatat sebagai artefak ekstraksi. |
| S-2 | Metode ini dikembangkan oleh Rahmat dkk. Metode tersebut diuji pada 30 siswa. | Dua segmen, dipisah setelah “dkk.” | tidak ada | Klausa sebelum “dkk.” sudah berpredikat dan token berikutnya membuka klausa baru. Ambiguitas sisa: bila anotator tidak yakin, B5. |
| S-3 | Sampel penelitian meliputi 1.250 responden. Sebanyak 62,5 persen berusia di bawah 30 tahun. | Dua segmen | tidak ada | Titik ribuan dan koma desimal bukan batas. |
| S-4 | Penelitian ini menggunakan tiga instrumen: 1. angket; 2. wawancara; 3. observasi. Data dianalisis secara deskriptif. | Dua segmen: induk beserta seluruh daftar, lalu kalimat berikutnya | tidak ada | Penomor, titik dua, dan titik koma bukan batas. |
| S-5 | Informan: 12 guru. Lokasi: SMPN 1. | Dua segmen, masing-masing fragmen informatif | B5 bila diragukan | Awalan berbentuk label dapat dibaca sebagai label seksi (bukan segmen); aturan memberi segmen karena fragmen memuat informasi. Ambiguitas sisa. |

### B.2.2 Kelompok C, I, dan U: label

| ID | Kalimat \[SINTETIS\] | Label (alternatif) | Simpul penentu | Flag | Catatan |
| --- | --- | --- | --- | --- | --- |
| C-1 | Hasil penelitian menunjukkan bahwa kemampuan menulis siswa rendah karena kurangnya latihan. | HS (SI) | 5.1 langkah 1 sampai 3; PP-1; HS-1, HS-2, HS-3 | B6 | Klausa sebab berada di dalam cakupan, tidak dipecah. “Kurangnya latihan” bukan variabel terukur, sehingga dapat dibaca sebagai penafsiran penulis (P2). |
| C-2 | Berdasarkan hasil penelitian dapat disimpulkan bahwa pelatihan berbasis proyek efektif meningkatkan kompetensi guru. | HS (SI) | PP-1; A3; HS-1, HS-2, HS-3 | B6 | Kata kerja bingkai tidak menentukan fungsi. “Guru” tanpa batas dapat dibaca sebagai sampel atau sebagai generalisasi. |
| C-3 | Penelitian ini dilakukan karena rendahnya minat baca siswa. | LB | U5; LB-1, LB-2, LB-3 | tidak ada | Tanpa bingkai studi, klausa sebab di luar cakupan. Bagian “Penelitian ini dilakukan” tidak lolos tes mana pun lalu digabung. Hasil deterministik, tetapi anotator dapat memilih TJ. |
| C-4 | Dapat disimpulkan bahwa program mentoring efektif karena melibatkan peserta secara aktif. | SI (HS) | PP-1; P1; SI-1, SI-2, SI-3 | B6 | HS-2 gagal: “efektif” bukan hubungan atau nilai terukur dan intervensi studi tidak disebut eksplisit; klausa sebab dapat dibaca sebagai hubungan dua variabel (A3), sehingga HS tetap menjadi alternatif. Berbeda dari C-2 karena C-2 memuat hubungan dua variabel. |
| I-1 | \[antesedens berlabel HS\] Oleh karena itu, pelatihan serupa perlu diterapkan di sekolah lain. | SI | PP-2; P1; SI-1, SI-2, SI-3 | tidak ada | Konektor ke segmen HS memberi status pasca; “sekolah lain” adalah generalisasi eksplisit, sehingga HS-3 gagal. |
| I-2 | \[antesedens berlabel LB\] Oleh karena itu, penelitian ini bertujuan mengembangkan modul pelatihan. | TJ | TJ-1, TJ-2, TJ-3 | tidak ada | Konektor tidak mengubah acuan K (5.2 butir 5). |
| I-3 | Pelatihan literasi digital bagi guru perlu dilakukan secara berkelanjutan. | LB (SI) | LB-1, LB-2 (pra-default), LB-3 | B3; B6 | Tanpa bingkai atau konektor. “Bagi guru” adalah penerima manfaat, bukan penerima anjuran, sehingga bukan P3. Bila berada setelah segmen HS, adjudikator boleh memakai konteks (7.3). |
| I-4 | Studi ini menawarkan kerangka analisis lima tahap yang dapat diadopsi oleh peneliti lain. | MT (SI) | MT-1, MT-2, MT-3; SI-1, SI-2, SI-3 | B1 | HS gagal di HS-3 (P2) dan TJ gagal di TJ-2 (ciri produk jadi). Klausa relatif tidak dipecah, sehingga unsur SI hanya tercatat sebagai alternatif. Label utama MT berasal dari urutan tes. |
| U-1 | Penelitian ini menggunakan metode survei untuk mengetahui tingkat kepuasan pengguna. | MT+TJ (MT) | U2; MT-1 sampai MT-3; TJ-1 sampai TJ-3 | B4 | Tujuan berupa tingkat satu variabel dapat dibaca sebagai tujuan studi (dipecah) atau tujuan alat (tidak dipecah). Label utama inklusif. |
| U-2 | Wawancara mendalam digunakan untuk menggali pengalaman guru. | MT | MT-1, MT-2, MT-3 | tidak ada | Subjek klausa utama adalah teknik, sehingga tujuan adalah tujuan alat dan bukan pemicu U2 (5.3). Risiko: anotator memecah menjadi MT+TJ. |
| U-3 | Kami menganalisis pengaruh gaya kepemimpinan terhadap kinerja guru dengan regresi linear berganda. | TJ+MT | U3; TJ-1 sampai TJ-3; MT-1 sampai MT-3 | tidak ada | Bagian pertama menyatakan sasaran tanpa nilai; adjunct cara memuat teknik analisis. |
| U-4 | Hasil menunjukkan bahwa model kooperatif meningkatkan hasil belajar siswa kelas VIII sehingga dapat diterapkan di sekolah lain. | HS+SI | U4; HS-1 sampai HS-3 (bagian 1); PP-1, P1, SI-1 sampai SI-3 (bagian 2) | tidak ada | Bagian kedua mewarisi status bingkai tetapi memuat generalisasi eksplisit. |
| U-5 | Hasil menunjukkan bahwa siswa yang mengikuti program memperoleh skor lebih tinggi (rata-rata 82 dibanding 71). | HS | PP-1; A1, A3, A4; HS-1 sampai HS-3 | tidak ada | Klausa relatif dan statistik dalam kurung bukan pemicu (5.3), sehingga tidak dipecah. |

### B.2.3 Kelompok D, P, L, T, H, dan O: label

| ID | Kalimat \[SINTETIS\] | Label (alternatif) | Simpul penentu | Flag | Catatan |
| --- | --- | --- | --- | --- | --- |
| D-1 | Penelitian ini bertujuan (1) mengetahui pengaruh X terhadap Y dan (2) menguji efektivitas model Z. | TJ | 5.4 butir 1; U1; TJ-1 sampai TJ-3 | tidak ada | Satu segmen; kedua butir berlabel TJ lalu digabung. |
| D-2 | Hasil penelitian: (1) motivasi meningkat 12%; (2) prestasi meningkat; (3) guru disarankan mengikuti pelatihan. | HS+SI | 5.4 butir 1; U1; PP-1; HS-1 sampai HS-3 (butir 1 dan 2); P3, SI-1 sampai SI-3 (butir 3) | tidak ada | Induk berbingkai hanya memberi status. Butir 3 memuat penerima dan tindakan (P3), sehingga SI walaupun berada dalam cakupan bingkai. |
| D-3 | Hasil analisis menunjukkan bahwa: 1. Motivasi siswa meningkat. 2. Prestasi siswa meningkat. | HS (segmen 1) dan HS (segmen 2) | 5.1 langkah 3; 5.4 butir 2; PP-1; HS-1 sampai HS-3 | tidak ada | Segmen kedua mewarisi PP-1 dari induk. Tanpa aturan cakupan daftar, segmen kedua berakhir TT (lihat D-4). |
| D-4 | 1. Motivasi siswa meningkat. 2. Prestasi siswa meningkat. | TT (HS) pada kedua segmen | 5.4 butir 3; Uji Acuan (5.2) | B2; B5 | Tanpa bingkai, pelaku, atau antesedens tidak ada PP, sehingga HS-1 gagal; LB-1 gagal karena perubahan terukur bukan keadaan umum. Induk mungkin terpotong, sehingga segmentasi diperiksa. |
| P-1 | Produk yang dihasilkan berupa modul digital berisi lima bab dan latihan interaktif. | HS | 5.5 Uji Produk Jadi; PP-3; A2; HS-1 sampai HS-3 | tidak ada | Ciri produk jadi dihitung HS (keputusan d). TJ gagal di TJ-2 dan MT gagal di MT-1 karena bukan kegiatan studi. |
| P-2 | Media dikembangkan dengan model ADDIE dan dibangun menggunakan Unity. | TJ+MT (MT) | U3, U1; TJ-1 sampai TJ-3 (bagian “media dikembangkan”); MT-1 sampai MT-3 (model dan alat) | B6 | Bagian pertama hanya menyebut produk yang dituju (TJ-2); sebagian anotator menilainya prosedur pengembangan (MT). |
| P-3 | Aplikasi ini berbasis Android dan memiliki fitur kuis serta penilaian otomatis. | HS (MT) | 5.5 Uji Produk Jadi; PP-3; A2; HS-1 sampai HS-3 | B6 | Deskripsi stativ produk dinilai X; MT-1 gagal karena bukan kegiatan studi, tetapi kalimat dapat dibaca sebagai deskripsi rancangan. |
| P-4 | Produk ini layak digunakan oleh guru di sekolah lain. | SI (HS) | PP-3; P1; SI-1 sampai SI-3 | B6 | HS-3 gagal karena generalisasi eksplisit ke sekolah lain. Unsur kelayakan (mutu produk) hanya tercatat sebagai alternatif; tidak ada pemicu U4, sehingga tidak dipecah. |
| L-1 | Hasil telaah terhadap 25 artikel menunjukkan bahwa sebagian besar studi memakai pendekatan kuantitatif. | HS | 5.6; PP-1; A4, A5; HS-1 sampai HS-3 | tidak ada | Bingkai menyebut korpus telaah studi ini. Proposisi inti adalah pola dari isi korpus, bukan deskripsi korpus. |
| L-2 | Literatur menunjukkan bahwa pembelajaran kooperatif meningkatkan hasil belajar. | LB (HS) | 5.1 langkah 1(b); 5.6; LB-1, LB-2 (status dari bingkai literatur), LB-3 | B6 | Pada abstrak studi literatur, bingkai generik dapat merujuk korpus telaah. Aturan memberi LB karena tidak ada kaitan eksplisit ke korpus. |
| L-3 | Sebanyak 25 artikel dari basis data Scopus memenuhi kriteria inklusi. | MT | 5.6 korpus; MT-1 sampai MT-3; HS-2 gagal (deskripsi korpus) | tidak ada | Jumlah dan seleksi adalah deskripsi bahan (perbaikan R1-2). Risiko: sebagian anotator membacanya sebagai HS. |
| L-4 | Berdasarkan telaah tersebut, perlu penelitian lanjutan mengenai kontekstualisasi model di Indonesia. | SI | PP-1, PP-2 (anafora ke telaah studi); P3; SI-1 sampai SI-3 | tidak ada | Anjuran untuk penelitian lanjutan termasuk P3. |
| T-1 | Artikel ini membahas peran arsiparis dalam transformasi digital. | TJ | 5.7 Uji Parafrasa (makna berubah, acuan K); TJ-1 sampai TJ-3 | tidak ada | Kalimat pengumuman topik tanpa isi. Pada abstrak tanpa hasil, anotator dapat membacanya sebagai ringkasan isi (HS), tetapi Uji Parafrasa menolak. |
| T-2 | Kajian ini menegaskan pentingnya literasi informasi di era disinformasi. | SI (LB; HS) | PP-3; P1 (pasca tanpa penambat); SI-1 sampai SI-3; LB-2 gagal | B6 | Tanpa penambat, sehingga HS-2 gagal. Dapat dibaca sebagai latar (LB) atau argumen konseptual (HS). |
| T-3 | Studi ini mengidentifikasi tiga faktor penghambat adopsi sistem arsip digital. | HS (TJ) | 5.7 Uji Parafrasa (makna tetap, acuan X); hitungan keluaran (TJ-2 gagal); PP-3; A4; HS-1 sampai HS-3 | B6 | Predikat lazim dipakai untuk sasaran, tetapi hitungan keluaran menandai perolehan. |
| T-4 | Ditemukan bahwa guru memanfaatkan grup pesan instan untuk berbagi materi dan menjaga komunikasi dengan wali murid. | HS | 5.1 langkah 1(a); PP-1; A5; HS-1 sampai HS-3 | tidak ada | Dua tujuan koordinatif di bawah satu predikat bukan U1; keduanya HS. |
| H-1 | Rata-rata nilai siswa meningkat dari 65 menjadi 82. | TT (HS) | Uji Acuan (5.2); HS-1 gagal; LB-1 gagal | B2 | Besar kemungkinan HS menurut anotator manusia, tetapi tanpa bingkai, pelaku, atau antesedens status tidak dapat diturunkan, dan posisi bukan kriteria (P6). Diselesaikan lewat adjudikasi dengan konteks (7.3). |
| H-2 | Sebanyak 60% siswa memiliki minat baca rendah. | LB (HS) | Uji Acuan (prevalensi tanpa kekhasan studi, acuan D); LB-1, LB-2 (pra-default), LB-3 | B3; B6 | Angka tanpa atribusi eksternal dapat berasal dari data studi. HS-1 gagal karena tanpa bingkai atau acuan eksplisit ke sampel. |
| H-3 | Skor rata-rata kelas eksperimen 82, sedangkan kelas kontrol 71. | HS | U1 (kedua bagian HS, digabung); PP-3; A1, A4; HS-1 sampai HS-3 | tidak ada | Kelompok eksperimen dan kontrol adalah acuan eksplisit ke kelompok studi. |
| O-1 | Penelitian ini didanai oleh Hibah Penelitian Dasar tahun 2024. | LAINNYA | LN-1(b), LN-2 | tidak ada | TJ-2 dan MT-2 gagal: pendanaan bukan sasaran maupun cara. |
| O-2 | Terima kasih kepada seluruh guru yang berpartisipasi. | LAINNYA | LN-1(b), LN-2 | tidak ada | Menyebut partisipan tetapi tidak menyatakan karakteristik subjek sebagai konteks pengambilan data. |
| O-3 | Rincian hasil disajikan pada Tabel 2. | LAINNYA (HS) | LN-1(b); HS-2 gagal (tanpa penambat) | B6 | Rujukan ke tabel; proposisi tidak menyatakan keluaran. |
| O-4 | Hasil analisis menunjukkan bahwa pengaruh \[terpotong akibat ekstraksi\] | LAINNYA (HS) | LN-1(c) (perbaikan R1-3) | B5 | Tidak ada proposisi lengkap untuk dinilai. Periksa apakah segmen berikutnya melengkapi (kesalahan segmentasi atau ekstraksi). |

### B.2.4 Kelompok K: kelengkapan

| ID | Label akhir per segmen \[SINTETIS\] | Vektor (LB, TJ, MT, HS, SI) | Status | Aturan |
| --- | --- | --- | --- | --- |
| K-1 | LB; TJ; MT; HS | 1, 1, 1, 1, 0 | TIDAK LENGKAP: hilang SI | K4 |
| K-2 | LB; TJ+MT; HS+SI | 1, 1, 1, 1, 1 | LENGKAP | K2: segmen berlabel ganda menyumbang semua labelnya |
| K-3 | LB; TJ; MT; HS (batas-sisa, alternatif SI) | v-min 1, 1, 1, 0, 0; v-maks 1, 1, 1, 1, 1 | TAK PASTI | K5 |
| K-4 | LB; TJ; MT (pendekatan analisis); SI (tanpa HS) | 1, 1, 1, 0, 1 | TIDAK LENGKAP: hilang HS | K6; SI tidak mengandaikan HS (3.5) |

## B.3 Uji konsistensi (Tahap 3c) dan log perubahan Putaran 1

Uji konsistensi memeriksa sebelas hal. Sembilan terpenuhi penuh atau dengan pengecualian yang tercatat; dua hanya sebagian; tidak ada yang tidak dapat diuji.

| Pemeriksaan | Hasil | Catatan |
| --- | --- | --- |
| Semua simpul tes bersifat positif, tanpa simpul “bila tidak, maka label” | Terpenuhi dengan satu pengecualian | LB-2 menerima status pra tanpa PP (berflag B3 bila tanda D-nya lemah) bila LB-1 dan LB-3 terpenuhi secara positif. Ini satu-satunya syarat berbasis ketiadaan penanda; dipertahankan karena tanpa itu LB hanya mengenali bingkai literatur eksplisit (butir 11). |
| SI tidak mengandaikan HS | Terpenuhi | SI-1 sampai SI-3 tidak merujuk segmen HS; PP-2 hanya memberi status. K-4 dan T-2 menunjukkan SI tanpa HS. |
| Bingkai tidak menentukan fungsi; kriteria “klausa utama” tidak dipakai | Terpenuhi | 5.1 langkah 4; C-1 sampai C-4; nyata: A1-S07, A1-S08, A2-S04, A4-S04. |
| Modalitas bukan pembeda HS | Terpenuhi | HS-2 memakai penambat; P3 memakai penerima dan tindakan, bukan kata modal (I-3); nyata: A2-S04 memuat kata modal tetapi berlabel HS. |
| Multi-label hanya lewat UP | Terpenuhi | Alternatif pada B1 tidak masuk vektor utama (hanya pembacaan pembanding pada v-min dan v-maks); label ganda hanya dari UP (U-1 sampai U-4, D-2); nyata: A2-S03 (MT+TJ). |
| Struktur yang sama diperlakukan sama | Sebagian | Terpenuhi untuk struktur pada tabel 5.3; ketidaktegasan tersisa pada U2 (U-1) dan dicatat sebagai B4. Data nyata (A2-S06) menunjukkan pertentangan Bagian 4 dan 5.3 pada U2, yang diperbaiki (R2-3). |
| Tidak ada aturan khusus demi satu kalimat | Terpenuhi | Putaran 1 dikerjakan sebelum ada abstrak. Putaran 2 menghasilkan satu perubahan berbasis data yang memenuhi ambang (R2-1: enam segmen dari empat abstrak) empat perbaikan konsistensi, dan satu perubahan skema; dua usulan yang hanya bertumpu pada satu segmen (A1-S07 dan A3-S07) ditarik dan dicatat sebagai kasus batas. |
| Contoh, tes, dan definisi tidak bertentangan | Sebagian | Enam belas contoh nyata di Bagian 3 konsisten dengan tes (B.1). Slot P-LN-1 kosong karena tidak ada segmen LAINNYA pada data, sehingga LAINNYA hanya teruji sintetis. |
| Rujukan silang valid (ID kasus batas, kode flag, nomor bagian) | Terpenuhi | Diperiksa ulang setelah Putaran 2: ID A1-S01 sampai A4-S04, R1-1 sampai R1-10, R2-1 sampai R2-5, flag B1 sampai B6, dan nomor bagian. |
| Independensi leksikal dari kamus rule-based (P5) | Terpenuhi dengan pengecualian | Definisi memakai kategori fungsi dan tata bahasa; ilustrasi rujukan diri di 3.0 dicatat sebagai risiko (Bagian 10). |
| Kutipan verbatim cocok dengan sumber | Terpenuhi | 28 segmen dan 16 kutipan contoh dicocokkan dengan teks mentah PDF yang sama (hanya normalisasi spasi dan baris baru); semuanya cocok. |

**Log perubahan Putaran 1.** Semua perubahan berupa aturan umum.

| No | Cacat yang ditemukan | Perubahan | Bagian |
| --- | --- | --- | --- |
| R1-1 | Kalimat beracuan K yang diawali konektor ke segmen HS lolos SI lewat P1 (pasca tanpa penambat) | Tambah SI-3: acuan X atau anjuran | 3.5 |
| R1-2 | Deskripsi sampel, subjek, atau korpus lolos MT dan HS sekaligus pada semua tipe studi (B1 massal) | HS-2: deskripsi bahan, subjek, atau korpus bukan keluaran | 3.4 |
| R1-3 | Segmen terpotong berbingkai lolos SI lewat P1 dan bertabrakan dengan LN-2 | LN-1(c): tes label lain hanya untuk proposisi lengkap | 3.6 |
| R1-4 | B4 tidak punya label utama yang deterministik | Label utama adalah penulisan ulang yang paling inklusif | 4 |
| R1-5 | Hasil tunggal yang dapat dibaca dua arah tidak punya flag | Tambah flag B6 | 4, 7 |
| R1-6 | Bingkai pasif tanpa pelaku tidak punya sumber | Kata kerja temuan atau simpulan pasif tanpa atribusi eksternal bersumber studi | 5.1 |
| R1-7 | Butir daftar yang menjadi segmen sendiri kehilangan status bingkai | Cakupan bingkai meliputi seluruh butir daftar | 5.1, 5.4 |
| R1-8 | Acuan D, K, dan X tidak punya uji penentu | Tambah Uji Acuan | 5.2 |
| R1-9 | TT dan B2 tidak punya jalur menuju label akhir (H-1) | Konteks wacana dibolehkan pada B2 dan B3; label akhir TT diambil dari alternatif terdekat atau dikecualikan | 7.3 |
| R1-10 | Contoh batas MT hanya mencakup satu kasus | Tambah P-3 sebagai contoh batas | 3.3 |

**Putaran 2 (terpakai).** Putaran 2 memakai temuan Tahap 3(a). Perubahan berbasis data hanya sah bila berpola struktural, berlaku untuk semua kalimat bergaya sama, tidak membuat tes lain bertentangan, dan muncul pada sekurang-kurangnya tiga segmen dari dua abstrak; perbaikan pertentangan antaraturan yang dapat ditunjukkan tanpa data dibolehkan dan dicatat sebagai perbaikan konsistensi. Dua usulan yang semula dibuat dari satu segmen (cakupan bingkai melewati titik koma, dari A1-S07; kerangka teori dalam MT, dari A3-S07) ditarik karena berada di bawah ambang dan karena aturan yang ada sudah menghasilkan label; keduanya menjadi kasus batas (B.4). Tidak ada Putaran 3.

**Log perubahan Putaran 2.**

| No | Temuan pada data nyata | Perubahan | Bagian | Segmen pemicu | Jenis |
| --- | --- | --- | --- | --- | --- |
| R2-1 | Enam segmen LB tanpa antesedens akan berflag B3 dan masuk antrean adjudikasi walaupun acuan D-nya jelas | Tanda D dibedakan kuat dan lemah; B3 hanya pada ketiadaan PP dengan tanda D lemah | 3.1, 5.1, 5.2, 7.1 | A1-S01, A1-S02, A2-S01, A3-S01, A3-S02, A4-S01 | berbasis data (memenuhi ambang) |
| R2-2 | Uji Parafrasa memberi acuan X pada kalimat sumber data, sehingga gagal di MT-1 dan HS-2 lalu berakhir TT | Uji hanya dipakai bila HS-2 dan MT-2 tidak memutuskan; data mentah adalah bahan; sementara, diuji ulang pada Pilot 2 | 5.7 | A1-S06 | perbaikan pertentangan antaraturan |
| R2-3 | Definisi U2 di Bagian 4 lebih longgar daripada tabel 5.3 dan memecah kalimat penegasan | U2 hanya pada klausa utama berupa kegiatan studi | 4, 5.3 | A2-S06 | perbaikan pertentangan antaraturan |
| R2-4 | Rumusan sumber bingkai menyebut kata kerja pasif, padahal definisi bingkai mencakup nomina | Sumber bingkai: kata kerja atau nomina temuan atau simpulan | 5.1 | A1-S08 | penyelarasan dengan definisi bingkai |
| R2-5 | Skema jenis\_studi tidak memuat tipe campuran | Tambah nilai campuran | 8.2 | A3 | skema berkas, bukan aturan label |
| R2-6 | Uji Acuan tidak memetakan PP-2 ke acuan X, sehingga kalimat kebutuhan yang terhubung ke segmen HS lewat konektor (A2-S05; padanan sintetis I-1) beracuan D lemah, gagal di LB-2 dan SI-3, lalu berakhir TT | Segmen non-K yang memuat PP-1 sampai PP-4 beracuan X; Q3 hanya untuk segmen tanpa PP; sementara, diuji ulang pada Pilot 2 | 5.2 | A2-S05 | perbaikan pertentangan antaraturan |

R2-2 dan R2-6 berstatus sementara: keduanya berlaku pada pembekuan v1.0, tetapi wajib diuji ulang pada Pilot 2 karena dibuat dari satu segmen dan memakai pengecualian perbaikan konsistensi.

**Perbaikan sebelum pembekuan (bukan Putaran 3).** (1) Flag B4 pada A1-S07 serta B6 pada A2-S04 dan A2-S05 diterapkan sesuai catatan B.4, dan vektor dihitung ulang (B.1.6). (2) K5 dibuat simetris: v-min adalah irisan dan v-maks gabungan pembacaan tiap segmen (6.3); ini satu-satunya perubahan definisi label atau vektor pada tahap ini. (3) Batas teks mentah diseragamkan (2.2), berkas teks mentah disimpan, dan hash dihitung ulang (B.1.1). (4) Aturan deduplikasi korpus ditambahkan (2.5); ia mengatur tata kelola korpus dan tidak mengubah label. Istilah yang mudah tertukar dibedakan (1.7) dan batasan skala korpus dicatat (1.5). (5) DOI dan URL laman jurnal A1, A3, dan A4 dilengkapi (B.1.1), dan lima butir untuk dosen disusun (Bagian C.1).

## B.4 Ambiguitas sisa

Daftar ini tidak menyatakan bahwa ambiguitas lain tidak ada; ia memuat yang sudah teridentifikasi.

1. **Pelampauan pada klaim tanpa batas sampel** (C-2, C-4, P-4, T-2): batas antara HS terikat dan generalisasi bergantung pada ada atau tidaknya batas yang disebut eksplisit.
2. **Penjelasan sebab dari penulis di dalam cakupan** (C-1): tidak dipecah; bila bukan variabel terukur, tetap HS dengan flag B6.
3. **Kalimat tanpa penanda status** (H-1, H-2, I-3, D-4): berakhir TT, atau LB berflag B3 bila tanda D-nya lemah. Proporsinya pada korpus belum diketahui karena keempat abstrak tidak memuat TT maupun B3 (B.1); LB dapat menyerap saran tanpa penanda bila konteks tidak dipakai pada adjudikasi.
4. **Klausa relatif yang memuat implikasi** (I-4): tidak dipecah, sehingga SI hanya menjadi alternatif; vektor dapat kehilangan SI bila itu satu-satunya kalimat SI (v-maks mencatatnya).
5. **Tujuan studi dan tujuan alat** (U-1, U-2): bergantung pada pemilik tujuan; tujuan berupa tingkat satu variabel tetap ambigu (B4).
6. **Pengembangan produk** (P-2, P-3): “dikembangkan” sebagai sasaran atau prosedur, dan deskripsi stativ produk sebagai rancangan atau hasil. Aturan 5.5 belum pernah diuji pada data nyata.
7. **Bingkai literatur pada studi literatur** (L-2): rujukan generik atau rujukan ke korpus telaah.
8. **Pengumuman dan perolehan** (T-1, T-3): Uji Parafrasa membantu, tetapi hitungan keluaran dengan predikat sasaran tetap dapat dibaca dua arah.
9. **Deskripsi korpus atau subjek** (L-3): aturan memberi MT; sebagian anotator akan membacanya HS.
10. **Batas LAINNYA dengan label isi** (O-3, O-4): rujukan ke tabel dan segmen terpotong; belum ada segmen LAINNYA nyata.
11. **Segmentasi** (S-2, S-5): singkatan bertitik sebelum huruf kapital dan fragmen berawalan label. Keempat abstrak tersegmentasi tanpa kasus ambigu.
12. **Urutan tes pada B1**: hanya penentu label utama (tie-breaker), bukan klaim prioritas fungsi; belum ada B1 pada data nyata.
13. **Butir komplemen sesudah titik koma** (A1-S07): pewarisan bingkai lewat titik koma tidak diatur eksplisit. A1-S07 berflag B4: dua penulisan ulang sah, yaitu bagian yang tidak lolos tes mana pun digabung ke butir pertama (HS; Bagian 4, Langkah 0b) atau butir berdiri sendiri dengan tanda D positif (LB); label utama inklusif HS+LB, alternatif HS. Usulan Putaran 2 yang menutup celah ini ditarik (B.3).
14. **Kerangka teori sebagai MT** (A3-S07): definisi MT tidak menyebut kerangka teori; kalimat dibaca sebagai pendekatan dengan flag B6 dan alternatif LB. Usulan Putaran 2 yang menambah kategori ini ditarik (B.3).
15. **Hasil dan cara dalam satu predikat majemuk** (A4-S03): objek bersama memuat kategori hasil, sehingga semua bagian HS; TJ dan MT hanya tercatat sebagai alternatif, dan vektor A4 berstatus TAK PASTI.
16. **Penegasan oleh studi tanpa penambat** (A2-S06; padanan sintetis T-2): SI dengan alternatif HS dan TJ; bergantung pada tafsir predikat sebagai pelaksanaan atau perolehan.
17. **Subjek generik pada temuan studi literatur** (A2-S04): HS berflag B6 (alternatif SI): tidak ada perluasan eksplisit, tetapi subjek generik dapat dibaca sebagai generalisasi; seragam dengan C-2.
18. **Komponen yang bergantung pada pemecahan U3** (A2-S03): komponen MT pada A2 hanya muncul lewat pemecahan U3; tanpa pemecahan vektor A2 kehilangan MT.
19. **Status pasca dari konektor kontras** (A2-S05): kalimat umum tanpa penambat menjadi SI hanya karena konektor ke segmen HS (PP-2) dan berflag B6 (alternatif LB); tanpa konektor ia LB. Acuan X berasal dari PP-2 (R2-6), bukan dari isi kalimat.
20. **Status pengujian**: butir sintetis diuji oleh penyusun sendiri dan belum ditinjau orang kedua; butir 13 sampai 19 berasal dari empat abstrak yang juga dilabeli penyusun sendiri, tanpa anotator kedua.

# BAGIAN C. KEPUTUSAN UNTUK DOSEN PEMBIMBING

Bagian C memuat lima butir yang perlu diputuskan dosen (C.1) dan, sebagai rujukan, daftar lengkap keputusan bernomor (C.2). Keputusan di luar kelima butir berlaku sebagai bawaan draf sampai ada keberatan.

## C.1 Lima butir untuk dosen

Kelima butir berikut membutuhkan keputusan sebelum Pilot 2.

**1. Anotator dan adjudikator Pilot 2** (9.3; C.2 butir 18). **Pertanyaan:** siapa dua anotator independen (bukan penyusun) dan siapa adjudikatornya? **Usul penyusun:** dua penutur asli berpendidikan sarjana yang belum membaca kamus penanda, dan adjudikator orang ketiga (dosen pembimbing atau pemeriksa senior). **Dasar:** semua label di B.1 dibuat penyusun sendiri, sehingga kesepakatan belum terukur; 6 dari 28 segmen (21%) berflag dan akan masuk antrean adjudikasi. **Bila orangnya belum ada:** Rung 2 pada butir 5.

**2. Ambang penerimaan** (9.5; C.2 butir 19). **Pertanyaan:** terapkan kappa sekurang-kurangnya 0,80 dengan batas bawah CI 95% sekurang-kurangnya 0,67, atau lebih longgar? **Usul penyusun:** pertahankan. **Dasar:** Pilot 2 menghasilkan sekitar 70 segmen, sehingga batas bawah CI berada jauh di bawah titik dan hasil “terima” menuntut kesepakatan sangat tinggi; rujukan Landis dan Koch (1977), Krippendorff (2004), serta Artstein dan Poesio (2008) belum diperiksa pada sumber primer \[PERLU VERIFIKASI\]. **Konsekuensi:** tanpa syarat batas bawah, pedoman dapat diterima dengan bukti yang lebih lemah.

**3. Skala korpus versus beban anotasi** (Batasan 1.5; C.2 butir 29). **Pertanyaan:** berapa jumlah abstrak (N) yang ditargetkan, dan anotasi ganda penuh atau sebagian? **Usul penyusun:** jangan menjanjikan N sebelum waktu per segmen terukur pada Pilot 2; tetapkan N dan skema ganda sesudahnya. **Dasar:** beban kasar 7N segmen, 14N pelabelan, dan sekitar 1,5N adjudikasi; N = 100 berarti sekitar 700 segmen, 1.400 pelabelan, dan 150 adjudikasi, sedangkan N = 300 berarti 2.100, 4.200, dan 450. Angka ini ilustrasi dari empat abstrak; kebutuhan data IndoBERT belum ditetapkan. **Konsekuensi:** N besar menuntut Rung 1 dan 2 pada butir 5.

**4. Definisi SI** (keputusan c; 3.5; C.2 butir 3). **Pertanyaan:** setujukah SI didefinisikan sebagai pasca-penelitian ditambah pelampauan data, sehingga kalimat simpulan yang hanya mengulang temuan terikat data berlabel HS? **Usul penyusun:** pertahankan dan uji pada Pilot 2. **Dasar:** keputusan ini belum teruji data. Keempat abstrak tidak memuat simpulan yang mengulang temuan, dan tidak ada abstrak yang memuat SI tanpa HS (A3 tanpa SI; A1, A2, dan A4 memuat HS dan SI), sehingga klaim bahwa SI tidak mengandaikan HS hanya teruji sintetis (K-4, T-2). Dari empat segmen SI nyata, dua bersih (A1-S08, A4-S04) dan dua berflag B6 (A2-S05, A2-S06). **Konsekuensi:** abstrak yang bagian simpulannya mengulang hasil akan tercatat tanpa SI dan TIDAK LENGKAP; mengubahnya membuka keputusan terkunci (c) dan memerlukan versi baru. **Usul uji:** sertakan sekurang-kurangnya dua abstrak bersimpulan pengulang temuan pada sampel Pilot 2 (usul ini tidak mengubah 9.2).

**5. Tangga penyederhanaan** (C.2 butir 28). **Pertanyaan:** setujukah urutan berikut dipakai bila beban atau kesepakatan gagal? **Usul penyusun:** setujui; tiap rung hanya berlaku dengan persetujuan dosen dan dicatat sebagai perubahan versi.

| Rung | Pemicu | Perubahan | Biaya bagi konstruk | Uji ulang |
| --- | --- | --- | --- | --- |
| 0 | bawaan | Pedoman v1.0 apa adanya | tidak ada | tidak ada |
| 1 | Waktu adjudikasi pada Pilot 2 melampaui kapasitas adjudikator | Antrean adjudikasi hanya untuk ketidaksepakatan dan flag B1, B2, B4; segmen berflag B3 atau B6 yang disepakati kedua anotator berstatus final | Ketidakpastian B3 dan B6 yang disepakati tidak lagi dibuka, sehingga K5 tidak menangkapnya | tidak perlu |
| 2 | Beban total (1.5) masih melampaui kapasitas pada Rung 1 | Dua anotator hanya pada Pilot 2, subset acak korpus (ukuran ditetapkan dosen), dan semua abstrak berflag; sisanya satu anotator | Reliabilitas hanya diestimasi pada subset; label di luar subset berasal dari satu anotator | kesepakatan pada subset |
| 3 | Kappa pada satu jenis studi rendah, atau aturan 5.5 tidak teruji pada Pilot 2 | Jenis studi itu (misalnya pengembangan produk) dikeluarkan dari korpus dan dinyatakan di 1.2 | Sistem tidak diklaim berlaku untuk jenis itu | tidak perlu |
| 4 | Ketidaksepakatan Uji Pemecahan (M3) menjadi penyebab terbesar | U2, U3, dan U5 tidak memecah; kalimatnya berlabel tunggal dengan alternatif (B4); U1 dan U4 tetap | Komponen TJ atau MT dapat turun menjadi alternatif; pada A2-S03, tanpa pemecahan MT hanya menjadi alternatif sehingga A2 kehilangan MT pada v-min | Pilot 3 |
| 5 | Pemakaian flag tidak konsisten antaranotator | B3 dan B6 digabung menjadi satu flag B6 | Informasi sumber ketidaktegasan (status atau ambang) hilang | tidak perlu |

Kelas, definisi SI, dan vektor kelengkapan adalah keputusan terkunci dan tidak termasuk tangga; membukanya memerlukan keputusan tertulis tersendiri.

**Tiga hal lain yang masih terbuka.** (i) Istilah `peran_data` sudah diselesaikan dengan nilai data-pengembangan dan korpus-anotasi, serta `jenis_studi` pengembangan-produk (1.7; 8.2). (ii) R2-2 dan R2-6 berstatus sementara dan wajib diuji ulang pada Pilot 2 (B.3). (iii) Keputusan (c) belum teruji data (butir 4).

## C.2 Rujukan: daftar lengkap keputusan

Tabel berikut memuat semua keputusan bernomor (nomor sama dengan Bagian 11) beserta pilihan dalam draf, alternatif, dan dampaknya. Ia dapat diserahkan terpisah dan tidak perlu diputuskan sekarang kecuali butir yang tercantum di C.1.

| No | Keputusan | Pilihan dalam draf | Alternatif | Dampak | Bagian |
| --- | --- | --- | --- | --- | --- |
| 1 | (a) Bingkai, cakupan, klausa sebab | Bingkai memberi status dan cakupan sampai batas segmen; label dari proposisi inti; sebab di dalam cakupan tidak dipecah | Cakupan hanya komplemen langsung; semua klausa sebab dipecah | Alternatif menambah pemecahan dan ketidaksepakatan U5; pilihan sekarang menandai penjelasan sebab penulis dengan B6 | 5.1 |
| 2 | (b) Ambang HS | Penambat A1 sampai A5 di dalam proposisi inti, bukan modalitas | Ambang berupa angka atau statistik | Alternatif merugikan studi kualitatif dan konseptual; pilihan sekarang menuntut penilaian atas penambat yang eksplisit | 3.4 |
| 3 | (c) Jangkar SI | Pasca-penelitian ditambah pelampauan (P1 sampai P3, SI-3); tidak mengandaikan HS | SI didefinisikan relatif terhadap HS | Simpulan yang hanya mengulang temuan terikat data berlabel HS; abstrak konseptual dapat memiliki SI tanpa HS | 3.5 |
| 4 | (d) HS dan MT lintas tipe studi | Bahan, subjek, korpus, dan prosedur adalah MT; perolehan, termasuk produk jadi dan mutunya, adalah HS | Produk jadi dihitung MT; deskripsi korpus dihitung HS | HS dapat kosong pada pengembangan bila alternatif dipilih; kelengkapan studi literatur dan konseptual bergantung pada keluaran yang dinyatakan isinya | 5.5 sampai 5.7 |
| 5 | (e) Satuan teks dan sumber | Abstrak bahasa Indonesia saja; satu sumber kanonik (PDF terbit, lalu halaman artikel; Garuda hanya untuk menemukan artikel) | Menyertakan abstrak bahasa Inggris; halaman artikel sebagai sumber utama | Sampel dari artikel yang sama tidak digandakan; ekstraksi PDF dapat bermasalah | 2.1 |
| 6 | (f) Segmentasi | Dibekukan sebelum pelabelan; daftar dalam satu kalimat tetap satu segmen | Anotator boleh mengubah batas; tiap butir dipecah | Kesepakatan dihitung pada segmen identik, tetapi kesepakatan segmentasi tidak terukur | 2.3, 2.4, 5.4 |
| 7 | (g) LAINNYA dan TT | Tes positif sendiri; kalimat sulit diberi TT dan diadjudikasi | LAINNYA sebagai tempat jatuh kalimat sisa | Mencegah LB dan LAINNYA menyerap kalimat, tetapi menambah beban adjudikasi | 3.6 |
| 8 | Judul dan subjudul seksi | Dikeluarkan dari teks kerja | Dipertahankan sebagai petunjuk | Anotasi tidak terjangkar pada subjudul, tetapi teks bersubjudul pada penerapan sistem berbeda dari data latih | 2.2 |
| 9 | Pemicu UP | Daftar tertutup U1 sampai U5; label utama inklusif pada B4 | Pemicu terbuka; label utama konservatif | Keseragaman terjaga; struktur di luar daftar dinilai sebagai satu proposisi | 4 |
| 10 | Urutan tes | TJ, MT, HS, SI, LB, LAINNYA menentukan label utama pada B1 | Urutan lain (misalnya SI sebelum MT) atau tanpa label utama sampai adjudikasi | Pada I-4 label utama MT melepas unsur SI; alternatif tetap tersimpan | 4 |
| 11 | Pra-default dan TT untuk kalimat tanpa penanda | LB-2 menerima status pra tanpa PP; B3 hanya bila tanda D lemah; kalimat bermuatan data tanpa penanda berakhir TT | Tanpa pra-default (semua tanpa penanda TT); atau PP-3 otomatis untuk angka hasil ukur | Pra-default mengurangi TT tetapi berisiko LB menyerap saran; TT memperbesar adjudikasi | 3.1, 5.2 |
| 12 | Definisi P1 sampai P3 dan SI-3 | Anjuran adalah penerima ditambah tindakan; kebutuhan tanpa penerima bukan anjuran | Semua kalimat kebutuhan berstatus pasca dihitung SI | Kalimat kebutuhan tanpa penanda (I-3) jatuh ke LB dengan B3, bukan SI | 3.0, 3.5 |
| 13 | Flag B6 dan konteks wacana | B6 untuk ambang dua arah; konteks seluruh abstrak boleh dipakai pada adjudikasi B2 dan B3 | Tanpa B6; konteks tidak dipakai | B6 mencatat keraguan tetapi dapat dipakai berlebihan; konteks membantu H-1 dan I-3 tetapi melonggarkan P6 | 7 |
| 14 | Ketidakpastian vektor | v-min (irisan pembacaan) dan v-maks (gabungan pembacaan), simetris; status TAK PASTI bila berbeda | Hanya label akhir | Sensitivitas terhadap kasus batas terukur; abstrak TAK PASTI keluar dari metrik utama | 6.3 |
| 15 | Abstrak tanpa hasil | TIDAK LENGKAP: hilang HS | Abstrak konseptual dikecualikan dari penilaian | Konsisten dengan definisi operasional; dilaporkan terpisah per tipe studi | 6.3 |
| 16 | Rujukan IPMRC dan Hyland (2000) | Ditandai \[PERLU VERIFIKASI\] karena sumber belum dilampirkan | Melampirkan sumber primer | Pemetaan 1.4 dan alasan SI belum bersandar pada rujukan yang terverifikasi | 1.3, 1.4 |
| 17 | Sampel Pilot 2 | 10 abstrak, sekurang-kurangnya 5 jurnal, paling banyak 3 per jurnal, strata jenis studi, 4 sampai 15 segmen | Sampel lebih besar; tanpa strata | Sekitar 70 segmen dengan CI lebar; strata menguji aturan khusus | 9.2 |
| 18 | Anotator dan adjudikator | Dua anotator bukan penyusun; adjudikator orang ketiga | Penyusun sebagai adjudikator | Independensi lebih terjaga, tetapi perlu orang yang ditunjuk dosen | 9.3 |
| 19 | Kesepakatan dan ambang | M1 sampai M5; terima bila kappa sekurang-kurangnya 0,80 dan batas bawah CI 95% sekurang-kurangnya 0,67; bersyarat 0,67 sampai 0,80; tolak di bawah 0,67 | Tanpa syarat batas bawah; ambang 0,70 | Pilihan sekarang ketat untuk sampel kecil; rujukan \[PERLU VERIFIKASI\] | 9.4, 9.5 |
| 20 | Tafsir “setiap aturan” | Sebelas kelompok aturan, sekurang-kurangnya tiga kasus per kelompok | Tiga kasus untuk setiap aturan individual | Cakupan lebih sempit; dapat diperluas pada Putaran 2 | B.2 |
| 21 | Lisensi dan penyimpanan teks | Simpan hash dan tautan; bagikan label dan ID bila teks tidak boleh dibagikan | Menyimpan dan membagikan salinan teks penuh | Reproduksibilitas berhadapan dengan hak cipta; \[PERLU VERIFIKASI\] per artikel | 8.2, 10 |
| 22 | Aturan Kohesi | Status diwariskan dari antesedens lewat anafora atau konektor eksplisit | Tiap kalimat dinilai berdiri sendiri | Pewarisan mengurangi TT tetapi membuat label bergantung pada segmen sebelumnya | 5.2 |
| 23 | Dua tingkat tanda D | Tanda D kuat (atribusi eksternal, fenomena atau keadaan umum) dan lemah (kebutuhan, prevalensi, angka tanpa atribusi); B3 hanya pada tanda lemah | B3 untuk setiap LB tanpa PP, atau tanpa B3 sama sekali | Tanpa pembedaan, enam dari sepuluh segmen LB nyata berflag B3 dan masuk antrean adjudikasi; tanpa B3, LB dapat menyerap saran tanpa jejak | 3.1, 5.2, 7.1 |
| 24 | Penarikan usulan dari satu segmen | Dua usulan Putaran 2 (cakupan bingkai melewati titik koma; kerangka teori dalam MT) ditarik dan dicatat sebagai kasus batas | Menerima kedua usulan sebagai aturan umum | Pedoman tetap sesuai ambang tiga segmen dari dua abstrak; dua celah (A1-S07, A3-S07) terbuka sampai Pilot 2 | B.3, B.4 |
| 25 | Pengecualian perbaikan konsistensi | Pertentangan antaraturan yang dapat ditunjukkan tanpa data diperbaiki tanpa syarat tiga segmen dari dua abstrak, dan dicatat terpisah | Semua perubahan wajib memenuhi ambang data | Empat perbaikan Putaran 2 (R2-2, R2-3, R2-4, dan R2-6) memakai pengecualian ini; tanpanya pertentangan itu bertahan sampai Pilot 2 | 7.5, B.3 |
| 26 | Pelabelan empat abstrak oleh penyusun | Label B.1 dibuat penyusun tanpa anotator kedua dan dipakai sebagai contoh nyata di Bagian 3 | Menunda contoh nyata sampai ada anotasi dua orang | Contoh nyata belum berstatus kesepakatan; bias penyusun belum terukur | B.1 |
| 27 | Ambang duplikat dekat | Kemiripan Jaccard atas 5-gram kata sekurang-kurangnya 0,90 ditinjau manual | Ambang lain, atau hanya duplikat persis | Ambang rendah membuang abstrak serupa yang sah; ambang tinggi meloloskan duplikat; tanpa rujukan | 2.5 |
| 28 | Tangga penyederhanaan | Rung 0 sampai 5 (C.1 butir 5); kelas, definisi SI, dan vektor kelengkapan tidak masuk tangga | Tanpa tangga; penyederhanaan diputuskan ad hoc | Urutan disepakati lebih dulu, tetapi tiap rung tetap memerlukan persetujuan dosen | C.1 |
| 29 | Skala korpus dan beban anotasi | N ditetapkan setelah waktu per segmen terukur pada Pilot 2 | Menetapkan N sekarang | Penetapan dini berisiko melampaui kapasitas anotasi; penetapan lambat menunda perencanaan | 1.5 |

# BAGIAN D. PROTOKOL PILOT 2

Bagian ini menjabarkan Bagian 9 menjadi langkah kerja; ia tidak mengubah ukuran maupun ambang di sana.

## D.1 Prasyarat

- [x] Pedoman v1.0 dibekukan dan hash berkasnya dicatat (paragraf Pembekuan pada status dokumen).
- [ ] Ukuran, ambang, dan prosedur Bagian 9 disetujui dosen (butir 17 sampai 19).
- [ ] Anotator, adjudikator, dan pemeriksa segmentasi ditetapkan (butir 18).
- [x] Empat abstrak data pengembangan dan kuncinya siap untuk pelatihan (Tahap 3a selesai; kunci di B.1).
- [ ] Templat berkas Bagian 8 siap dipakai.
- [ ] Skrip pemecah segmen dan skrip penghitung kesepakatan sudah diuji pada data sintetis.
- [ ] Deduplikasi (2.5) sudah dijalankan pada kerangka sampel sebelum penarikan.

## D.2 Langkah kerja

| Langkah | Pelaku | Keluaran | Kriteria selesai |
| --- | --- | --- | --- |
| 1. Penarikan sampel | peneliti | daftar 10 artikel, benih acak, tanggal penarikan | sekurang-kurangnya 5 jurnal, paling banyak 3 per jurnal, semua strata terisi, tidak ada artikel pengembangan |
| 2. Pengambilan teks | peneliti | abstrak.csv dengan teks mentah dan hash | satu sumber kanonik per abstrak (2.1) |
| 3. Normalisasi minimal | peneliti | teks kerja dan log\_normalisasi.csv | hanya perubahan menurut 2.2; tanpa subjudul |
| 4. Segmentasi dan pembekuan | skrip dan pemeriksa | segmen.csv | 4 sampai 15 segmen per abstrak; keraguan B5 awal diselesaikan; segmentasi dibekukan |
| 5. Pelatihan anotator | peneliti | catatan pelatihan dan durasinya | kedua anotator melabeli dan membahas kunci empat abstrak pengembangan; tanpa abstrak Pilot 2 |
| 6. Anotasi independen | dua anotator | anotasi.csv per anotator | semua segmen berlabel; flag dan alasan terisi; waktu tercatat; urutan diacak |
| 7. Penghitungan kesepakatan | peneliti | M1 sampai M5 beserta CI | dihitung sebelum adjudikasi |
| 8. Adjudikasi | adjudikator | adjudikasi.csv | semua segmen dalam antrean berstatus akhir (7.4) |
| 9. Analisis ketidaksepakatan | peneliti | tabel ketidaksepakatan per simpul dan usulan revisi | tiap ketidaksepakatan terpeta ke simpul aturan |
| 10. Keputusan | peneliti dan dosen | terima, terima bersyarat, atau tolak | sesuai tabel 9.5 |
| 11. Pelaporan | peneliti | laporan Pilot 2 | memuat butir 9.7 nomor 3 |

Bila keputusannya terima bersyarat atau tolak, Pilot 3 memakai abstrak baru dengan prosedur yang sama; abstrak Pilot 2 tidak dipakai lagi.

## D.3 Templat laporan hasil

Tabel ini formulir; nilainya diisi setelah Pilot 2.

| Ukuran | Nilai | CI 95% (bootstrap pada abstrak) |
| --- | --- | --- |
| M1 kappa label utama |  |  |
| M2 kappa per kelas (LB, TJ, MT, HS, SI, LAINNYA) |  |  |
| M3 kesepakatan himpunan dan alpha |  |  |
| M4 persentase kesepakatan |  |  |
| M5 vektor kelengkapan |  |  |
| Jumlah segmen, per kelas, dan per flag |  |  |
| Status akhir (final, batas-sisa, dikecualikan) |  |  |

## D.4 Daftar periksa integritas

- [ ] Teks verbatim cocok dengan sumber yang sama (hash diperiksa).
- [ ] Anotator tidak berkomunikasi; kronologi berkas menunjukkan independensi.
- [ ] Pedoman tidak berubah selama anotasi (hash sama).
- [ ] Anotator tidak melihat prediksi sistem maupun kamus penanda.
- [ ] Semua ketidaksepakatan terpeta, dan usulan revisi memenuhi syarat 7.5.
- [ ] Empat abstrak pengembangan tidak dilaporkan sebagai bukti validasi.
- [ ] Keterbatasan Bagian 10 dicantumkan, termasuk ukuran sampel.
