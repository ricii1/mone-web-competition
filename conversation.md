# Dokumentasi Percakapan — EduMap

Rekap percakapan dengan AI coding agent (Claude Code) untuk lomba *"Innovating Education Through Technology"*. Format: prompt pengguna dan ringkasan respons agent, urut dari awal sampai akhir dengan timestamp, termasuk proses debugging.

## 6 Oktober

**09:02**
user: "Bangun EduMap sesuai AGENTS.md — Next.js + FastAPI + Postgres/pgvector + Redis/arq, auth guru/murid, upload PDF yang diproses jadi peta level lewat RAG, kuis, leaderboard, dan live class ala Kahoot."

agent: "Membuat skema database (users, classes, materials, material_chunks, levels, questions, enrollments, progress, attempts, live_sessions, live_participants) lewat Alembic; pipeline RAG (parsing PyMuPDF → chunking per section → embedding `intfloat/multilingual-e5-small` → generate level & soal via Groq, semua berjalan di worker `arq`); endpoint REST per domain; WebSocket + Redis pub/sub untuk progres upload, leaderboard live, dan live class; frontend Next.js untuk auth, dashboard guru/murid, peta level (`@xyflow/react`), kuis, leaderboard, live class. Menyertakan suite `pytest` untuk auth, otorisasi, aturan unlock level, dan leaderboard, dengan Groq dan model embedding di-mock."

**11:47**
user: "Jalankan sekarang."

agent: "Menjalankan `docker compose up --build`. Ditemukan: `alembic upgrade head` gagal dengan `DuplicateObject: type "user_role" already exists` — migrasi memanggil `.create(checkfirst=True)` manual untuk tiap enum Postgres, lalu `op.create_table` mencoba membuat ulang enum yang sama secara implisit tanpa `checkfirst`. Tidak ketahuan test sebelumnya karena test pakai `Base.metadata.create_all`, bukan migrasi asli. Diperbaiki dengan menambahkan `create_type=False` pada semua `postgresql.ENUM(...)` yang dipakai sebagai tipe kolom di migrasi `0001_initial.py` dan `0002_domain_tables.py`."

**12:20**
user: "Memang besar sekali kah memori yang dibutuhkan oleh dockernya?"

agent: "Image backend ~6.6 GB karena `sentence-transformers` menarik PyTorch build CUDA penuh, padahal embedding hanya dijalankan di CPU. Diperbaiki dengan install `torch` dari index CPU-only (`--index-url https://download.pytorch.org/whl/cpu`) sebelum install dependency lain di `backend/Dockerfile`. Image turun ke ~1.9 GB, build jauh lebih cepat, test tetap 38/38 lulus. Juga ditemukan bentrok port host (5432, 8000, 3000 sudah dipakai proses lain di mesin dev) — diperbaiki dengan remap port host di `docker-compose.yml` (5433, 8001, 3001) tanpa mengubah port internal container maupun `.env.example`."

## Styling frontend

**14:05**
user: "Kasih styling di FE nya biar bagus, di halaman login kasih opsi untuk daftar jika akun belum ada. Lalu di halaman register kasih opsi register sebagai guru atau sebagai murid."

agent: "Merancang identitas visual 'buku tulis / papan tulis' — warna `ink` (navy), `paper`, `highlight` (kuning mustard), `correct` (hijau), `alert` (merah), font Fraunces (judul) + Work Sans (body), input bergaris bawah ala kertas bergaris. Menambahkan token di `tailwind.config.ts` + `globals.css`, komponen `AuthHero` dengan ilustrasi peta level, link daftar di halaman login, dan pilihan role di halaman register."

**14:38**
user: "Eh masuk juga kasih opsi deh masuk sebagai guru dan masuk sebagai murid, menurut anda handler yang baik gimana?"

agent: "Role tidak bisa dipilih saat login karena sudah tetap di akun sejak registrasi, jadi pilihan itu diperlakukan sebagai validasi, bukan parameter: jika role yang dipilih tidak cocok dengan role akun sebenarnya, tampilkan pesan jelas ('Akun ini terdaftar sebagai Murid, bukan Guru') dengan tombol lanjut eksplisit, bukan diam-diam dialihkan ke dashboard yang tidak diminta. Dibuat komponen `RoleChooser` yang dipakai bersama di login dan register."

**14:52**
user: "Bagian masukkan password kasih tombol opsi peek."

agent: "Menambahkan komponen `PasswordField` dengan tombol mata untuk toggle `type=\"password\"`/`\"text\"`, dipakai di login dan register."

**15:30**
user: "Saya penasaran ketika pindah dari halaman login ke register, text di bawah gambar kanan berubah mendadak — mungkinkah transisinya halus, dan pakai teknologi apa?"

agent: "Karena login dan register adalah route terpisah di Next.js, halaman di-remount penuh termasuk panel hero. Direkomendasikan: pindahkan `AuthHero` ke shared layout `app/(auth)/layout.tsx` supaya panel tidak remount saat navigasi, lalu crossfade tagline dengan CSS keyframe biasa (tanpa dependency baru). Setelah diimplementasikan, diverifikasi dengan browser headless: elemen DOM panel hero terbukti tidak di-remount saat klik link 'Daftar', hanya teks tagline yang berganti dengan animasi fade."

**15:33**
user: "Ya, implementasikan."

agent: "Selesai — shared layout dibuat, tagline crossfade dengan `prefers-reduced-motion` dihormati, diverifikasi lewat tes DOM-identity di browser headless."

**16:10**
user: "Coba juga halaman teacher dan student stylingnya."

agent: "Menerapkan design token yang sama ke seluruh halaman guru dan murid (dashboard, detail class, review soal, live class, peta level, kuis, leaderboard), menambahkan `AppHeader` bersama (logout + nama user) lewat layout guru/murid, dan menyamakan warna node di `LevelMap` (hijau=completed, kuning=unlocked, abu=locked, border merah=boss) dengan sistem warna yang sama."

**16:44**
agent (lanjutan, ditemukan lewat uji browser sungguhan): "Dua bug nyata ditemukan saat menjalankan alur asli lewat browser headless, bukan cuma baca kode: (1) CORS belum diaktifkan di backend — semua fetch dari frontend ke backend diblokir browser sejak awal, tidak ketahuan sebelumnya karena pengujian sebelumnya lewat `curl`/pytest langsung ke backend. Diperbaiki dengan `CORSMiddleware` + env `CORS_ORIGINS`. (2) Dashboard guru memfilter endpoint publik `/api/v1/classes` yang hanya mengembalikan class berstatus `published`, jadi class yang baru dibuat (`draft`) tidak pernah muncul di 'Class Saya' — guru tidak punya jalan membuka classnya sendiri. Diperbaiki dengan endpoint baru `GET /api/v1/classes/mine` khusus guru + test otorisasi. Alur register → create class → publish → join → map → leaderboard → live class → login role-mismatch diverifikasi ulang lewat browser headless dan semua berjalan benar."

**17:02**
agent (insiden kecil): "Saat menyiapkan data uji manual untuk screenshot, satu command shell multi-baris tergabung salah dan mengirim `DROP SCHEMA public CASCADE` yang nyangkut menunggu lock dari sesi lain, ikut memblokir semua query berikutnya selama beberapa menit. Terdeteksi lewat `pg_stat_activity`, dibatalkan dengan `pg_cancel_backend` sebelum benar-benar jalan, sesi macet lainnya dibersihkan dengan `pg_terminate_backend`. Tidak ada data yang hilang."

**17:25**
user: "Init git dan stage perubahan yang telah dilakukan, lalu buatlah file conversation.md berisi rekap percakapan penting untuk keperluan dokumentasi submission lomba."

agent: "Menjalankan `git init`, menambahkan `.claude/` ke `.gitignore`, staging seluruh file proyek (kode backend, frontend, `AGENTS.md`, `docker-compose.yml`, `.env.example`) tanpa menyertakan `.env` atau file lokal lainnya, dan membuat `conversation.md` ini."

**17:31**
user: "Sama timestamp waktunya bisakah?"

agent: "Menambahkan timestamp di setiap entri percakapan pada `conversation.md`"

## 2026-10-08

**22:35**
user: "pelajari repo ini dan AGENTS.md lalu setup agar bisa dijalankan di sini" (lalu: "jangan pakai venv tapi pakai conda, agar hemat memori")

agent: "Setup native memakai conda env `edumap` (python 3.11 + nodejs 20, torch CPU); hanya postgres (pgvector) dan redis lewat Docker. `.env` disesuaikan untuk host localhost (DB port 5433), backend/frontend `.env` di-symlink. Migrasi alembic dijalankan, 42 test lolos, API :8000, worker arq, frontend :3000 berjalan."

**22:36**
agent (debugging): "`pip install -e backend` gagal: 'Multiple top-level packages discovered in a flat-layout: app, alembic' karena setuptools menemukan dua paket di root backend. Build Docker akan gagal dengan sebab yang sama. Diperbaiki dengan `[tool.setuptools.packages.find] include = [\"app*\"]` di `pyproject.toml`. Selain itu pytest crash di luar Docker karena `PYTHONPATH` ROS memuat plugin pytest `launch` yang butuh `lark`; diatasi dengan `unset PYTHONPATH`. Dua test CORS awalnya gagal karena `CORS_ORIGINS` sempat saya set ke port 3001 (mengikuti mapping compose); dikembalikan ke 3000 karena port 3000/8000 kosong di mesin ini."

**22:58**
user: "buatkan seeder nya terlebih dahulu"

agent: "Dibuat `backend/app/db/seed.py` (`python -m app.db.seed`, idempotent): 1 guru, 4 murid (password `password123`), class publik 'Biologi Sel Kelas XI' (3 level + boss, soal `approved`, progres murid disimpan lewat `record_quiz_result` agar aturan unlock/best_score konsisten, cache leaderboard Redis dibangun ulang) dan 1 class privat draft. Chunk/embedding tidak di-seed karena butuh model embedding di worker."

**23:05**
agent (debugging): "Seeder gagal: `relation \"users\" does not exist` padahal migrasi sudah jalan. Penyebab: `tests/conftest.py` memakai `settings.database_url` (DB development) lalu `drop_all` di akhir sesi dan `delete` di tiap test, jadi setiap `pytest` menghapus seluruh tabel dev sementara `alembic_version` tetap di head (sehingga `alembic upgrade head` tidak melakukan apa-apa). Perbaikan: test sekarang memakai DB terpisah `<nama>_test` (dibuat otomatis) dan `SessionLocal` di-rebind ke DB test agar job worker/WebSocket tidak menyentuh DB dev. DB dev dipulihkan dengan `alembic stamp base` + `upgrade head`, lalu di-seed. 42 test lolos."

**23:30**
user: "sidebar di login dan register itu apa gabisa dibuat kek semacam motion graphic animation"

agent: "`AuthHero` diubah dari SVG statis menjadi motion graphic loop 10 detik berbasis CSS murni (tanpa dependency/JS): jalur emas tergambar, titik pemain bergerak di sepanjang jalur (`offset-path`), node Mulai → Bab 1 → Bab 2 muncul berurutan dengan efek '+100', node Boss terbuka dengan ring burst, plus partikel melayang. Panel tetap berada di layout bersama sehingga tidak remount. Di `prefers-reduced-motion` animasi mati dan peta ditampilkan dalam keadaan selesai. Diverifikasi di browser dengan membekukan animasi pada detik ke-7,5. `npm run lint` bersih."

**23:55**
user: "[screenshot dashboard guru kosong] kok kesannya kosong banget ya, apa bagusnya kita kasih example class ya?" → setelah ditanya, user memilih: "Setiap guru baru tidak perlu muat class contoh tapi lgsg ada kelas referensi atau template ... Tujuannya itu memberi guru gambaran"

agent: "Setiap guru yang register otomatis mendapat class referensi 'Contoh: Biologi Sel Kelas XI' (private, draft, kolom baru `classes.is_example` lewat migrasi 0003). Level pertama + soalnya `approved`, sisanya `draft` agar guru melihat alur review. Class contoh tidak bisa di-publish (400) dan tidak muncul di daftar publik. Konten dipindah ke `services/example_class.py` dan dipakai bersama seeder; `python -m app.db.seed --examples` mengisi guru lama (akun Junathan dan guru seed). Dashboard guru sekarang menampilkan daftar class di atas form, dengan badge 'Contoh' dan deskripsi. Test baru: guru dapat contoh/murid tidak, contoh tidak bisa publish dan tidak publik; satu test lama diperbarui karena guru baru kini punya 1 class bawaan (bukan dilemahkan). 44 test lolos, ruff dan lint bersih."
