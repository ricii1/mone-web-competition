# Peta Pintar

Platform belajar berbasis peta level untuk **guru SD dan murid SD**. Guru mengunggah materi PDF, sistem menyusunnya menjadi level (materi → rangkuman → kuis), dan murid membuka level satu per satu sambil mengumpulkan bintang. Ada leaderboard per class dan live class ala Kahoot.

> Nama final proyek: **Peta Pintar**. Aturan produk, arsitektur, dan konvensi kode ada di [`AGENTS.md`](AGENTS.md).

Instalasi lama tetap memakai kredensial database dan volume yang sudah ada di `.env`.
Jangan mengganti `POSTGRES_USER`, `POSTGRES_DB`, atau password database lama hanya
untuk menyesuaikan nama aplikasi. Jika environment conda lama memiliki nama lain,
jalankan API dengan `CONDA_ENV=<nama-environment-lama> ./run-uvicorn.sh`.
Branding baru memakai penyimpanan token browser baru; masuk kembali bila sebelumnya
sudah login. Akun, kelas, PDF, dan progres tetap berada di database yang sama.

## Isi

- [Prasyarat](#prasyarat)
- [Cara 1: Docker Compose](#cara-1-docker-compose)
- [Cara 2: Native dengan conda (lebih ringan)](#cara-2-native-dengan-conda-lebih-ringan)
- [Data demo dan akun uji](#data-demo-dan-akun-uji)
- [Mode LLM: mock atau Groq](#mode-llm-mock-atau-groq)
- [Test dan lint](#test-dan-lint)
- [Status perbaikan audit](docs/testing-fixes.md)
- [Deployment Dokploy](docs/deploy-dokploy.md)
- [Pemecahan masalah](#pemecahan-masalah)

## Prasyarat

| Kebutuhan | Cara 1 (Docker) | Cara 2 (conda) |
|---|---|---|
| Docker + Docker Compose | wajib | wajib (hanya untuk Postgres dan Redis) |
| Conda (Miniconda/Anaconda) | tidak perlu | wajib |
| Koneksi internet | build image dan unduh model | unduh paket dan model |

Model embedding (`intfloat/multilingual-e5-small`, sekitar 470 MB) diunduh otomatis oleh worker saat PDF pertama diproses.

## Cara 1: Docker Compose

Satu perintah menjalankan semuanya: Postgres + pgvector, Redis, API, worker, dan frontend. `docker compose down` mematikan semuanya.

```bash
cp .env.example .env            # sekali saja
docker compose up -d --build    # build pertama lama: memasang PyTorch CPU dan sentence-transformers
docker compose exec backend python -m app.db.seed   # data demo (opsional)
```

- Frontend: http://localhost:3000, API: http://localhost:8000 (dokumentasi di `/docs`).
- Migrasi database berjalan **otomatis** setiap backend start, jadi database baru langsung siap.
- Worker menunggu API sehat dulu, jadi urutan start sudah diatur.
- `.env` yang sama dipakai untuk Docker dan native. Nilai khusus container (host database, host Redis, folder upload) ditimpa di `docker-compose.yml`, sehingga `localhost` di `.env` tidak mengganggu.
- Port host bisa diganti lewat `API_PORT` dan `WEB_PORT` di `.env` (default `8000` dan `3000`). Kalau diganti, samakan juga `NEXT_PUBLIC_API_URL`, `NEXT_PUBLIC_WS_URL`, dan `CORS_ORIGINS`.
- Kode di `backend/` dan `frontend/` dipasang sebagai volume, jadi perubahan kode ikut ter-reload di API dan frontend. **Worker tidak reload otomatis**: jalankan `docker compose restart worker` setelah mengubah kode job atau prompt.

Perintah berguna:

```bash
docker compose ps                 # status semua service
docker compose logs -f worker     # log worker (pemrosesan PDF dan generate level)
docker compose restart worker     # muat ulang kode worker
docker compose down               # hentikan semua service (data tetap tersimpan)
docker compose down -v            # hentikan dan HAPUS data database, upload, dan cache model
```

Model embedding (sekitar 470 MB) diunduh worker saat PDF pertama diproses dan disimpan di volume `model_cache`, jadi tidak diunduh ulang setelah `down`.

> Jangan menjalankan Docker dan native (Cara 2) bersamaan. Keduanya memakai port 8000, 3000, 5433, dan 6379 yang sama, dan dua worker akan berebut antrean job.

## Cara 2: Native dengan conda (lebih ringan)

Backend, worker, dan frontend jalan langsung di mesin. Hanya Postgres dan Redis yang memakai Docker, sehingga tidak perlu membangun image PyTorch yang besar.

### 1. Siapkan environment

```bash
conda create -n petapintar python=3.11 nodejs=24 -y
conda activate petapintar

# PyTorch versi CPU dulu, agar sentence-transformers tidak menarik versi CUDA yang sangat besar
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install -e "backend[dev]"

cd frontend && npm install && cd ..
```

### 2. Siapkan `.env`

```bash
cp .env.example .env
```

Ubah nilai berikut agar mengarah ke service di host:

```env
DATABASE_URL=postgresql+psycopg://petapintar:petapintar@localhost:5433/petapintar
REDIS_URL=redis://localhost:6379/0
UPLOAD_DIR=/path/absolut/ke/repo/uploads
LLM_MODE=mock
```

Backend dan frontend membaca `.env` dari folder masing-masing, jadi buat tautannya:

```bash
mkdir -p uploads logs
ln -sf ../.env backend/.env
ln -sf ../.env frontend/.env.local
```

### 3. Jalankan database, Redis, dan migrasi

```bash
docker compose up -d postgres redis

cd backend
alembic upgrade head
python -m app.db.seed          # data demo (opsional)
```

### 4. Jalankan tiga proses aplikasi

Gunakan tiga terminal (masing-masing dengan `conda activate petapintar`).

```bash
# Terminal 1 - API (port 8000)
cd backend
uvicorn app.main:app --port 8000 --reload --timeout-graceful-shutdown 2

# Terminal 2 - worker (parsing PDF, embedding, panggilan LLM)
cd backend
arq app.worker.settings.WorkerSettings

# Terminal 3 - frontend (port 3000)
cd frontend
npm run dev
```

Buka http://localhost:3000. Dokumentasi API ada di http://localhost:8000/docs.

Untuk API tersedia skrip pintasan di root repo yang mengaktifkan env conda, mengosongkan `PYTHONPATH`, lalu menjalankan uvicorn dengan opsi yang benar:

```bash
./run-uvicorn.sh                  # reload aktif di 127.0.0.1:8000
PORT=8010 ./run-uvicorn.sh        # ganti port
HOST=0.0.0.0 ./run-uvicorn.sh     # bisa diakses dari perangkat lain di jaringan
RELOAD=0 ./run-uvicorn.sh         # tanpa auto-reload
CONDA_ENV=nama-lain ./run-uvicorn.sh
```

> Worker **tidak** me-reload otomatis. Setelah mengubah kode job, prompt, atau skema di `backend/app/rag` atau `backend/app/worker`, hentikan worker (Ctrl+C) dan jalankan lagi.

## Data demo dan akun uji

`python -m app.db.seed` membuat data uji (aman dijalankan berulang, dilewati jika sudah ada). Semua password: `password123`.

| Peran | Email |
|---|---|
| Guru | `guru@petapintar.id` |
| Murid | `murid1@petapintar.id` sampai `murid4@petapintar.id` |

- Class publik **IPA Kelas 4 - Siklus Air** dengan progres dan leaderboard contoh (murid1 sudah menyelesaikan beberapa level, murid4 masih baru). Seed baru memakai artikel dan soal tingkat SD; seed tidak menulis ulang kelas lama.
- Satu akun bisa jadi guru dan murid (seperti Kahoot): pakai tombol **Ganti ke Guru/Murid** di header. Pilihan peran saat daftar/masuk hanya menentukan halaman awal.
- Setiap akun yang mendaftar otomatis mendapat class referensi **"Contoh: IPA Kelas 4 - Siklus Air"** sebagai gambaran hasil akhir (materi, rangkuman, poin penting, soal). Class ini tidak bisa dipublish.
- Untuk akun yang sudah ada sebelum fitur class contoh: `python -m app.db.seed --examples`.

Alur uji cepat: masuk sebagai guru, buka class, unggah PDF, tunggu status `ready`, tekan **Generate level**, review materi dan soal, **Approve**, lalu **Publish**. Masuk sebagai murid, join class, dan mainkan level dari peta.

## Mode LLM: mock atau Groq

Variabel `LLM_MODE` di `.env` menentukan cara materi dan soal dibuat:

- `mock` (disarankan untuk pengembangan dan demo; nilai bawaan kode adalah `groq`): jawaban dibuat offline dari teks materi tanpa API key. Hasilnya kaku, tetapi seluruh alur (generate, progres real-time, review) bisa dicoba. `MOCK_LLM_DELAY_SECONDS` mengatur jeda tiruan agar progres terlihat.
- `openai`: memanggil gateway OpenAI-compatible (bawaan: `LLM_BASE_URL=https://senopati.its.ac.id/llm-gateway/v1`, model `LLM_MODEL`, mis. `qwen3:14b` atau `qwen3.5:9b`) dengan kunci `API_KEY_LITELLM`. Panggilan lewat `httpx`, tanpa dependency baru.
- `groq`: memanggil Groq API sungguhan. Isi `GROQ_API_KEY` dan `GROQ_MODEL` (cek nama model aktif di console Groq). Satu level memakai satu panggilan LLM untuk materi, rangkuman, dan poin penting, ditambah satu untuk soal. Hasil disimpan di database, dan murid tidak pernah memicu panggilan LLM.

## Test dan lint

```bash
# Backend (dari folder backend, environment conda aktif)
unset PYTHONPATH            # hindari plugin pytest dari paket lain (mis. ROS)
pytest -q
ruff check . && ruff format --check .

# Frontend (dari folder frontend)
npm run lint
npm run typecheck
npm run build
node --test tests/*.test.cjs
```

Test memakai database terpisah `<nama_database>_test` yang dibuat otomatis di server Postgres yang sama (default instalasi baru `petapintar_test`), jadi data pengembangan tidak ikut terhapus. Groq dan model embedding selalu di-mock; pub/sub Redis memakai `fakeredis`. Koneksi pool arq asli diblok pada test: test antrean harus memasang mock secara eksplisit, sehingga suite tidak memerlukan Redis development atau menghubunginya.

Hasil audit awal tersedia di [laporan testing](docs/testing-audit.md); status sesudah perbaikan ada di [docs/testing-fixes.md](docs/testing-fixes.md).

## Pemecahan masalah

| Gejala | Penyebab dan solusi |
|---|---|
| API tidak merespons setelah mengedit kode | `uvicorn --reload` menunggu koneksi WebSocket yang masih terbuka. Jalankan dengan `--timeout-graceful-shutdown 2` (sudah ada di perintah di atas) atau matikan prosesnya lalu jalankan ulang. |
| Generate level tidak jalan atau memakai kode lama | Worker belum dijalankan atau belum di-restart setelah perubahan kode. |
| Status materi tetap `pending` | Worker tidak berjalan, atau Redis belum menyala. Cek `docker compose ps` dan log worker. |
| Upload PDF pertama lama | Worker sedang mengunduh model embedding sekitar 470 MB. Tunggu sampai selesai. |
| Browser menampilkan CORS error | `localhost` dan `127.0.0.1` (port berapa pun) otomatis diizinkan. Kalau membuka lewat IP jaringan (mis. `192.168.x.x`) atau domain lain, tambahkan alamat itu ke `CORS_ORIGINS` di `.env` (pisahkan dengan koma), samakan `NEXT_PUBLIC_API_URL`, lalu restart API. |
| Muncul "Bukan pemilik class ini" | Token login milik akun lain tersimpan di browser. Keluar, lalu masuk lagi dengan akun pemilik class. |
| `pytest` gagal mengimpor plugin aneh | Jalankan `unset PYTHONPATH` sebelum `pytest`. |
| Ingin mengosongkan database dev | `docker compose down -v`, lalu `docker compose up -d` (Docker; migrasi otomatis) atau `docker compose up -d postgres redis` + `alembic upgrade head` (native), lalu seed. |
| Worker Docker langsung berhenti dengan `ConnectionError ... localhost:6379` | `REDIS_URL` dari `.env` (localhost) bocor ke container. Sudah ditimpa di `docker-compose.yml`; pastikan memakai file compose terbaru dan jalankan `docker compose up -d --force-recreate`. |


## Perbaikan keamanan dan menjalankan deployment

Mode development tetap memakai `docker compose up -d --build`. Port PostgreSQL
(5433) dan Redis (6379) sekarang hanya tersedia melalui loopback host. Pada native,
jalankan migrasi sebelum memakai kode baru:

```bash
cd backend
alembic upgrade head
```

Migrasi `0008` menambahkan identitas dan waktu permintaan generate. Worker baru
memeriksa job tertinggal saat startup; endpoint generate juga memeriksanya. Job
antre/berjalan tetap dipertahankan. Job yang hilang/selesai tetapi status class masih
`generating` dapat dicoba ulang setelah tenggat 30 menit ditambah 1 menit. Job lama
yang belum memiliki identitas diberi masa tenggang sejak migrasi. Restart worker
setelah job aktif selesai supaya ia memakai kode baru.

Untuk deployment, tersedia override terpisah (memerlukan Docker Compose yang
mendukung `!reset` dan `!override`; konfigurasi diverifikasi dengan versi 5.0.2):

```bash
docker compose -f docker-compose.yml -f docker-compose.production.yml config -q
docker compose -f docker-compose.yml -f docker-compose.production.yml up -d --build
```

Sebelum deployment, isi `JWT_SECRET` dengan nilai acak minimal 32 byte, gunakan
password database yang kuat, dan set URL API/WS serta CORS ke domain deployment.
`APP_ENV=production` otomatis diterapkan override dan menolak secret placeholder
serta password database contoh. Bila database sudah ada, password `.env` harus
sesuai password akun PostgreSQL yang sudah tersimpan; mengganti variabel tidak
mengganti password akun tersebut secara otomatis. Jangan hapus volume untuk
mengatasi perbedaan password.

Override menutup port DB/Redis, menonaktifkan reload dan bind mount kode,
menjalankan backend/worker/frontend sebagai pengguna non-root, dan memakai build
Next.js standalone. API/frontend hanya terbuka di loopback host untuk dilayani
reverse proxy dengan HTTPS/WSS. Atur proxy agar menyensor query token WebSocket
dalam access log. URL `NEXT_PUBLIC_*` ditanam saat build sehingga perubahan URL
memerlukan build frontend ulang. Frontend production tidak menerima `.env`
backend. Volume upload/model lama yang dibuat root mungkin memerlukan penyesuaian
kepemilikan ke UID 10001 sebelum digunakan dengan mode non-root; pertahankan isinya.

Batas request upload diterapkan sebelum multipart dibaca dan ukuran file diperiksa
lagi saat streaming. Login dibatasi 10 percobaan/menit dan register 20/jam per IP
serta email. Di sekolah dengan banyak pengguna melalui satu IP, batas registrasi
ini perlu dipertimbangkan saat menyiapkan akun bersama.

Kuis live menyimpan state/jawaban sementara 24 jam, terpisah dari deadline jawaban
20 detik. Snapshot REST dan polling 4 detik memulihkan soal, jawaban sendiri, daftar
peserta dan hasil akhir tanpa memerlukan WebSocket. Hasil akhir yang sudah ditutup
dibaca dari PostgreSQL; snapshot tidak membocorkan jawaban soal aktif.

Pemeriksaan realtime tanpa dependency tambahan:

```bash
cd frontend
node --test tests/realtime.test.cjs
```

Laporan awal: [audit DevOps](docs/devops-audit.md). Status implementasi dan batasan
ada di bagian akhir laporan tersebut.


### Pembaruan pemrosesan dan persetujuan materi

Migrasi `0009` menyimpan urutan chunk PDF, termasuk subbab pada halaman yang sama.
Pada native, jalankan `alembic upgrade head` sebelum memakai worker baru. Data lama
memakai urutan halaman dengan ID sebagai pemecah seri; urutan asli dalam halaman
lama yang tidak tersimpan belum tentu dapat dipulihkan dari backfill.

Sebelum menerbitkan kelas, guru harus menyetujui materi setiap level dan minimal
satu soalnya. Kelas tidak bisa terbit saat proses generate masih berjalan. Migrasi
tidak menulis ulang artikel, progres atau status kelas yang sudah terbit.

Sumber panjang sekarang dibuatkan catatan sumber bertahap sebelum artikel/soal,
sehingga bagian akhirnya ikut dibaca. Tahap tambahan hanya terjadi ketika konteks
melebihi 8.000 karakter dan dapat menambah waktu generate. Artikel dan soal tetap
perlu ditinjau guru. Subbab melebihi batas 128.000 karakter atau 16 bagian per
putaran ditolak dengan pesan meminta pemisahan, bukan dipotong tanpa pemberitahuan.

### Periksa sumber, tangani PDF gagal, dan hapus kelas

- Di halaman kelola kelas, PDF berstatus **Siap** punya tombol **Lihat pembagian
  materi**. Periksa judul, urutan, halaman dan teks sumber sebelum **Buat level**.
  Teks lengkap dimuat hanya saat diminta, dan daftar panjang memiliki navigasi halaman.
- PDF **Gagal** bisa **Coba proses lagi** tanpa unggah ulang atau **Hapus PDF gagal**.
  Materi yang sudah menjadi sumber level/soal tetap dilindungi. Proses ulang tidak
  tersedia saat pembuatan level berjalan; file asli harus masih tersedia.
- Di bawah peta kelas, **Hapus kelas** meminta nama kelas sebagai konfirmasi.
  Tindakan ini menghapus PDF, level, soal, progres murid dan hasil kuis secara permanen.
  Akhiri kuis bersama dan tunggu job materi/level selesai terlebih dahulu.
- Jalankan migrasi `alembic upgrade head` (termasuk `0010`) dan muat ulang worker
  setelah memperbarui kode. Penanda job mencegah retry lama menimpa hasil baru.
- Jika log mencatat kegagalan pembersihan file setelah commit, operator dapat
  memeriksa folder `.deleted-*` pada `UPLOAD_DIR`; folder itu tidak lagi dipakai
  metadata aktif. Penghapusan normal membersihkannya otomatis.

### Bantuan Bu Hoo

Tombol **Bantuan** di header membuka panduan interaktif untuk guru dan murid.
Pilih langkah (dropdown di HP, tombol nomor di layar lebar), gunakan
**Sebelumnya/Berikutnya**, tandai **Sudah paham**,
atau buka halaman terkait dari panduan. Masalah umum tersedia pada bagian
**Butuh bantuan lain?** dan bisa dibuka satu per satu. Panel mengikuti ukuran layar,
isi dapat digulir, dan tombol tutup serta navigasi tetap terlihat di HP.
Penanda panduan hanya berlaku selama halaman aktif; tidak mengubah nilai atau progres.
