# Solusi backlog Peta Pintar

Tanggal: 11 Oktober 2026. Tinjauan kode, tanpa perubahan perilaku aplikasi. Audit keamanan dan infrastruktur ada di [devops-audit.md](devops-audit.md).

## Prioritas implementasi

1. **Pemulihan generate macet.** `backend/app/services/level_service.py:141` menolak semua permintaan ketika status masih `generating`. `backend/app/api/routes/levels.py:25` menyimpan status sebelum enqueue, sehingga kegagalan Redis juga dapat membuat status tertinggal. Tambahkan waktu antre dan waktu mulai khusus melalui Alembic; bedakan waktu menunggu antrean dari waktu eksekusi. Simpan identitas job, cegah permintaan bersamaan dengan pembaruan status bersyarat/lock baris, dan lakukan kompensasi status bila enqueue gagal. Pemulihan perlu memeriksa status job/lease serta tenggat eksekusi; jangan memakai umur `updated_at` saja atau menggagalkan job yang masih sah di antrean. Uji enqueue gagal, pembatalan, worker mati, dua permintaan bersamaan, dan job lama yang selesai setelah percobaan baru.

2. **Perbaiki limiter sebelum paralelisme.** `backend/app/rag/llm.py:41` hanya menunggu pergantian menit ketika kuota habis, tanpa mengambil slot baru. `:95` mengambil slot sekali sebelum loop retry 429. Ambil slot untuk setiap percobaan HTTP dan ulangi pemeriksaan sesudah menunggu; buat kenaikan counter dan expiry atomik di Redis. Pastikan retry internal SDK ikut dihitung atau dimatikan agar hanya satu lapisan mengendalikan retry. Uji konkurensi, pergantian menit, serta 429 dengan jam dan sleep tiruan.

3. **Optimasi query murah.** `backend/app/services/level_service.py:99` menjalankan satu query soal per level saat memeriksa publish. Ambil semua ID level yang punya soal approved dalam satu query, lalu hitung penghalang dari hasilnya. Ukur jumlah query pada 1, 10, dan 50 level; target jumlah query tetap. Jangan menambah cache sebelum dibutuhkan.

4. **Generate paralel terbatas sesudah langkah 1–2.** `backend/app/worker/jobs/generate_content.py` saat ini mengerjakan artikel dan soal per level secara berurutan. Mulai dengan dua tugas LLM independen, gunakan semaphore, dan pertahankan penulisan DB serta penyambungan prasyarat secara berurutan. Jangan membagikan satu SQLAlchemy Session ke tugas konkuren. Ukur median/p95 durasi, 429, konsumsi token, dan kegagalan JSON memakai fixture yang sama. Belum ada bukti besarnya peningkatan kecepatan.

## Solusi untuk sisa backlog

| Masalah | Solusi minimal | Bukti keberhasilan |
|---|---|---|
| Artikel pendek | Tampilkan pemberitahuan sumber pendek kepada guru; pertahankan prompt yang membolehkan artikel singkat. Penggabungan section memerlukan keputusan guru. | Materi singkat tidak menghasilkan fakta tambahan; pemberitahuan tampil. |
| Boss untuk ekor | Tentukan aturan produk sebelum mengubah kode. Dokumen bagian 8 mengatakan boss tidak setelah level terakhir, tetapi contoh 8 section mengatakan ada boss setelah ke-8; kode `generate_content.py:169` menghasilkan hanya satu boss untuk 8 section. Usulan backlog: boss penutup bila sisa minimal 3 lesson. | Test jumlah/urutan/prasyarat untuk 3, 4, 5, 7, 8, dan 9 section sesuai aturan yang disepakati. |
| Reasoning panjang | Uji opsi non-thinking hanya jika gateway benar-benar mendukungnya, pada materi dan model yang sama. Jangan mengasumsikan parameter provider. | JSON valid, grounding tetap, durasi dan token terukur. |
| Soal berulang | Tambahkan validasi pertanyaan duplikat setelah normalisasi whitespace dan huruf. Pemeriksaan keterkaitan penjelasan tetap memerlukan tinjauan guru; pencocokan teks saja tidak membuktikan grounding. | Duplikat ditolak dan memicu retry terbatas. |
| Material gagal | Tambahkan retry dan hapus khusus pemilik class; tolak saat job aktif dan tangani referensi chunk sebelum menghapus. | Otorisasi, enqueue gagal, idempotensi, dan sumber level tetap konsisten. |
| Nama Groq untuk semua provider | Rename fungsi/konstanta ke LLM dalam perubahan terpisah. Perubahan key Redis harus mempertahankan satu kuota bersama selama transisi worker. | Test semua provider dan limiter tetap lolos. |
| PDF fixture | Buat generator PDF memakai PyMuPDF yang sudah tersedia: section pendek/panjang, heading, tanpa heading, dan teks kosong. | Reproduksi chunking dan generate mock tanpa jaringan atau PDF pihak lain. |

## Batasan

Usulan ini belum diterapkan. Tidak ada perubahan stack, dependency, atau relasi data. Pengukuran performa nyata dan verifikasi opsi gateway belum dilakukan. Perubahan pengguna yang sudah ada sebelum audit dipertahankan.


## Pembaruan implementasi — 11 Oktober 2026

Pelacakan/pemulihan job, kompensasi enqueue, limiter per retry, dan query publish
sudah diterapkan dengan test regresi. Runtime aman dan perbaikan live/leaderboard
tercatat di laporan DevOps. Artikel singkat, aturan boss, paralelisme, reasoning,
fitur retry/hapus material, rename provider dan generator PDF tetap usulan, bukan
perubahan yang diterapkan. Contoh boss di AGENTS.md telah dikoreksi sesuai kode:
8 section mempunyai boss setelah ke-4; 9 section setelah ke-4 dan ke-8.


## Eksekusi tiga prioritas utama — 12 Oktober 2026

1. Urutan chunk tersimpan lewat migrasi `0009`, lalu dipakai worker generate dan
   penyajian sumber. Test memakai insert terbalik pada halaman sama. Backfill lama
   mempertahankan data, tetapi tie halaman lama memakai ID karena offset asli tidak
   tersedia; hal ini tidak otomatis memperbaiki semua urutan dokumen lama.
2. Publish menolak materi draft dan level tanpa soal approved, dengan alasan per
   level. Publish saat generate ditolak. UI mengarahkan guru meninjau materi dulu.
3. `rag/context.py` membaca semua bagian sumber panjang, membuat catatan terstruktur
   lalu mereduksi hingga muat 8.000 karakter. Konteks yang sama dipakai artikel/soal;
   boss juga memakai konteks semua sumber kelompoknya. Tidak ada `[:8000]` yang
   membuang akhir sumber. Input terlalu besar ditolak dengan pesan jelas. Pemrosesan
   tambahan memakai limiter yang sama dan menambah durasi/panggilan untuk materi
   panjang; benchmark model nyata belum dilakukan.

Verifikasi: 152 pytest lolos; Ruff lint/format, ESLint, TypeScript dan build Next.js
lolos. Test migration downgrade/upgrade menggunakan DB test dan memeriksa artikel
serta FK sumber yang tetap utuh. Test LLM memakai mock. Migrasi lokal diterapkan dan
worker diperbarui sesudah pemeriksaan tidak ada job aktif.

Pratinjau pembagian, retry/hapus material dan validasi soal duplikat tetap rekomendasi
lanjutan; sesi eksekusi ini mengikuti urutan tiga prioritas pertama yang disarankan.


## Eksekusi rekomendasi 4–6 dan penghapusan kelas — 12 Oktober 2026

Pratinjau chunk sekarang tersedia untuk pemilik sebelum generate: judul/urutan/
halaman/cuplikan berpaginasi dan teks lengkap yang dimuat saat dibuka. Semua membaca
hasil worker yang tersimpan; tidak ada parsing atau embedding dalam API.

PDF gagal dapat diproses ulang atau dihapus selama tidak dipakai sebagai sumber
level/soal dan generate tidak aktif. Token job pada migrasi `0010` menjaga enqueue
baru dari job lama/duplikat. Pertanyaan berulang dengan beda spasi atau kapital
memicu retry JSON yang dibatasi; tambah/edit manual juga menolaknya.

Penghapusan kelas memakai konfirmasi nama dan izin pemilik, menolak job/sesi live
aktif, membersihkan graph data dan folder UUID kelas, serta menjaga akun/kelas lain.
Transaksi gagal memulihkan file/folder; cache dibersihkan sesudah commit. Cleanup
filesystem sesudah commit yang gagal dicatat dan dapat meninggalkan `.deleted-*`
untuk ditangani operator. Tidak mengubah relasi atau menambah dependency.

Verifikasi: 175 pytest, Ruff lint/format, ESLint/TypeScript, build produksi Next.js
dan empat test frontend lolos. Seluruh uji LLM/embedding memakai mock dan database
terpisah. Status lama pada bagian sebelumnya adalah riwayat saat audit tersebut,
bukan status implementasi terbaru.


Pemeriksaan lanjutan menambahkan perlindungan job legacy tanpa token: material
ready yang sumbernya sudah dipakai tetap ready dan tidak diparsing/ditimpa.
Suite akhir menjadi **176 test backend**; Ruff lint/format, ESLint/TypeScript dan
build Next.js tetap lolos. Bantuan interaktif dan uji delapan kombinasi browser
tercatat di `help-ui-check.md`.
