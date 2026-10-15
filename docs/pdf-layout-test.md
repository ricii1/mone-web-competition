# Uji PDF dengan batas subbab yang tidak mengikuti halaman

Tanggal: 12 Oktober 2026. Enam PDF buatan sendiri, topik SD (air, tumbuhan,
energi), dibuat dengan PyMuPDF. Tidak memakai PDF pihak lain atau mengubah kelas
development. File PDF dan hasil JSON ada di `/tmp/edumap-pdf-layout-checks/`.

## Hasil

| Tata letak | Halaman | Chunk / level | Soal draft | Hasil batas materi |
|---|---:|---:|---:|---|
| Satu subbab per halaman, dengan bookmark | 3 | 3 | 15 | Benar: air, tumbuhan, dan energi terpisah. |
| Satu subbab per halaman, tanpa bookmark; font judul lebih besar | 3 | 3 | 15 | Bug: chunk Air mencakup halaman 1–2; chunk Tumbuhan mencakup 2–3. Halaman subbab berikut ikut masuk. |
| Dua subbab di halaman 1; Tumbuhan berlanjut di halaman 2, lalu Energi mulai di tengah halaman 2 | 2 | 3 | 15 | Bug: Air berisi air+tumbuhan; Tumbuhan berisi air+tumbuhan+energi; Energi berisi tumbuhan+energi. |
| Tata letak campur yang sama, dengan bookmark | 2 | 3 | 15 | Bug: Air dan Tumbuhan memakai isi halaman 1 yang sama. Kelanjutan Tumbuhan di halaman 2 masuk ke Energi. |
| Judul dan isi berukuran font sama, tanpa bookmark | 2 | 1 | 5 | Fallback sesuai implementasi: tidak ada heading terdeteksi, seluruh 275 kata masuk satu chunk. Bukan tiga subbab semantik. |
| Teks panjang tanpa struktur, 1.005 kata | 5 | 3 | 15 | Fallback membentuk chunk 500, 500, 105 kata dengan overlap 50 kata. |

Pipeline menghasilkan total **16 level dan 80 soal draft**. Semua job mencapai
status selesai, tetapi itu tidak membuktikan pembagian materi benar.

Pada artikel level Tumbuhan untuk `mixed_pages.pdf`, pemeriksaan menemukan ketiga
penanda sumber: `penampungan air`, `Akar tumbuhan`, dan `Lampu belajar`. Artinya
konteks yang salah batas benar-benar diteruskan ke artikel hasil generate, bukan
hanya masalah angka halaman di metadata.

## Akar masalah

- `backend/app/rag/parsing.py:11`: `HeadingSpan` menyimpan halaman, teks dan ukuran
  font, tanpa posisi heading dalam teks/halaman.
- `backend/app/rag/chunking.py:55`: jalur font-heading memakai halaman heading
  berikut sebagai **akhir inklusif**, sehingga halaman subbab berikut ikut diambil.
- `backend/app/rag/chunking.py:34`: jalur bookmark menyesuaikan akhir berdasarkan
  nomor halaman saja. Dua bookmark pada halaman yang sama menghasilkan potongan
  halaman yang sama; tidak dapat memisahkan awal subbab di tengah halaman.
- Pipeline generate memakai satu chunk sebagai satu lesson. Karena itu jumlah
  level bisa terlihat benar sementara konteks tiap level salah.

## Cara mengulang

Dari root repo dengan environment backend aktif:

```bash
python backend/scripts/generate_pdf_layout_fixtures.py /tmp/edumap-pdf-layout-checks
```

Enam fixture dihasilkan: `one_section_per_page.pdf`,
`one_section_per_page_toc.pdf`, `mixed_pages.pdf`, `mixed_pages_toc.pdf`,
`flat_headings.pdf`, dan `unstructured_long.pdf`.

Probe pipeline sementara disimpan di
`/tmp/edumap-pdf-layout-checks/pipeline_probe.py`. Untuk mengulang dengan fixture
pytest repo, salin sementara ke `backend/tests/_pdf_layout_probe.py`, jalankan
`pytest -q -s tests/_pdf_layout_probe.py` dari backend, lalu hapus salinan tersebut.
Probe memakai database test terpisah dan fakeredis, fungsi job worker asli,
parsing/chunking asli, embedding tiruan dan `LLM_MODE=mock` dengan delay nol.

Enam pemeriksaan probe lulus untuk **kelancaran pipeline, jumlah level, dan jumlah
soal**, bukan untuk kebenaran batas subbab. Pemeriksaan isi menghasilkan bug dalam
tabel di atas. Tidak ada panggilan gateway/Groq atau unduhan model. Kualitas
jawaban model nyata, OCR PDF hasil scan, tabel/kolom ganda, dan bookmark bertingkat
belum diuji pada sesi ini.

## Perbaikan yang diperlukan

Simpan posisi heading dalam aliran teks, lalu potong mulai heading sekarang hingga
**sebelum** heading berikutnya, termasuk ketika keduanya berada di halaman yang
sama. Untuk bookmark, gunakan lokasi tujuan atau pencocokan judul pada halaman
sumber; jangan mengandalkan nomor halaman saja. Pertahankan metadata rentang
halaman dan fallback untuk dokumen tanpa struktur yang dapat dikenali.

Test regresi perlu memastikan setiap chunk hanya memuat penanda subbabnya,
kelanjutan subbab tidak hilang, dan teks subbab berikut tidak masuk. Sekadar
mengubah akhir halaman menjadi `next_page - 1` hanya memperbaiki PDF rapi; kasus
subbab di tengah halaman tetap memerlukan posisi heading.

Pada sesi pengujian awal, parser/chunker belum diubah. Perbaikannya dicatat di bawah.


## Perbaikan dan tes ulang — 12 Oktober 2026

Parser kini membangun teks halaman dan offset judul dari aliran baris yang sama.
Heading multi-span/gaya huruf dan heading yang terbungkus dalam satu blok tetap
menjadi satu judul. Bookmark dicocokkan ke teks judul; bila nama bookmark berbeda,
lokasi tujuan digunakan. Bookmark bertingkat pada posisi sama tidak menggandakan
isi. Bookmark ambigu kembali ke heading/fallback, bukan menduplikasi halaman.

Chunking memotong dari posisi heading sampai tepat sebelum heading berikutnya.
Rentang halaman dihitung dari teks yang benar-benar masuk ke chunk, dan pengantar
sebelum heading pertama dipertahankan pada chunk pertama.

| Fixture berstruktur | Sumber Air | Sumber Tumbuhan | Sumber Energi |
|---|---|---|---|
| Rapi, tanpa bookmark | Air saja, hal. 1 | Tumbuhan saja, hal. 2 | Energi saja, hal. 3 |
| Rapi, dengan bookmark | Air saja, hal. 1 | Tumbuhan saja, hal. 2 | Energi saja, hal. 3 |
| Campur, tanpa bookmark | Air saja, hal. 1 | Tumbuhan saja, hal. 1–2 | Energi saja, hal. 2 |
| Campur, dengan bookmark | Air saja, hal. 1 | Tumbuhan saja, hal. 1–2 | Energi saja, hal. 2 |

Fallback font seragam/tanpa struktur tetap memakai ukuran teks. Hasil chunk sesudah
perbaikan disimpan sebagai `*.chunks-after.json` di direktori fixture `/tmp` yang sama.

Test regresi baru `backend/tests/test_pdf_section_boundaries.py` memeriksa penanda
sumber tiap subbab, isi lengkap, rentang halaman, kelanjutan lintas halaman,
bookmark dengan nama berbeda, heading multi-span/dua baris, pengantar, dan bookmark
bertingkat. Dua test worker memakai parsing/chunking asli, embedding mock dan LLM
mock untuk memastikan artikel, soal dan relasi chunk sumber tidak bercampur.
Test heading lama juga diperkuat agar memeriksa isi dan akhir halaman.

Sebelum patch, lima test regresi gagal dan dua kontrol lolos. Sesudah patch,
12 test regresi baru lolos dan **138 test backend** lolos. Ruff lint/format bersih.
Worker diaktifkan ulang sesudah pemeriksaan tidak ada job aktif. Tidak ada perubahan
skema/dependency, pemanggilan LLM nyata, atau perubahan otomatis pada artikel/soal
kelas lama. Materi yang sudah tersimpan sebelum perbaikan tidak otomatis dipecah ulang.
