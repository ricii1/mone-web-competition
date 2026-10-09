# EduMap

Platform belajar berbasis peta level untuk **guru SD dan murid SD**. Guru mengunggah materi PDF, sistem menyusunnya menjadi level (materi → rangkuman → kuis), dan murid membuka level satu per satu sambil mengumpulkan bintang. Ada leaderboard per class dan live class ala Kahoot.

> Nama proyek masih sementara. Aturan produk, arsitektur, dan konvensi kode ada di [`AGENTS.md`](AGENTS.md).

## Isi

- [Prasyarat](#prasyarat)
- [Cara 1: Docker Compose](#cara-1-docker-compose)
- [Cara 2: Native dengan conda (lebih ringan)](#cara-2-native-dengan-conda-lebih-ringan)
- [Data demo dan akun uji](#data-demo-dan-akun-uji)
- [Mode LLM: mock atau Groq](#mode-llm-mock-atau-groq)
- [Test dan lint](#test-dan-lint)
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
conda create -n edumap python=3.11 nodejs=20 -y
conda activate edumap

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
DATABASE_URL=postgresql+psycopg://edumap:edumap@localhost:5433/edumap
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

Gunakan tiga terminal (masing-masing dengan `conda activate edumap`).

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
| Guru | `guru@edumap.id` |
| Murid | `murid1@edumap.id` sampai `murid4@edumap.id` |

- Class publik **Biologi Sel Kelas XI** dengan progres dan leaderboard contoh (murid1 sudah menyelesaikan beberapa level, murid4 masih baru).
- Setiap guru yang mendaftar otomatis mendapat class referensi **"Contoh: IPA Kelas 4 - Siklus Air"** sebagai gambaran hasil akhir (materi, rangkuman, poin penting, soal). Class ini tidak bisa dipublish.
- Untuk guru yang sudah ada sebelum fitur class contoh: `python -m app.db.seed --examples`.

Alur uji cepat: masuk sebagai guru, buka class, unggah PDF, tunggu status `ready`, tekan **Generate level**, review materi dan soal, **Approve**, lalu **Publish**. Masuk sebagai murid, join class, dan mainkan level dari peta.

## Mode LLM: mock atau Groq

Variabel `LLM_MODE` di `.env` menentukan cara materi dan soal dibuat:

- `mock` (disarankan untuk pengembangan dan demo; nilai bawaan kode adalah `groq`): jawaban dibuat offline dari teks materi tanpa API key. Hasilnya kaku, tetapi seluruh alur (generate, progres real-time, review) bisa dicoba. `MOCK_LLM_DELAY_SECONDS` mengatur jeda tiruan agar progres terlihat.
- `groq`: memanggil Groq API sungguhan. Isi `GROQ_API_KEY` dan `GROQ_MODEL` (cek nama model aktif di console Groq). Satu level memakai satu panggilan LLM untuk materi, rangkuman, dan poin penting, ditambah satu untuk soal. Hasil disimpan di database, dan murid tidak pernah memicu panggilan LLM.

## Test dan lint

```bash
# Backend (dari folder backend, environment conda aktif)
unset PYTHONPATH            # hindari plugin pytest dari paket lain (mis. ROS)
pytest -q
ruff check . && ruff format --check .

# Frontend (dari folder frontend)
npm run lint
npx tsc --noEmit
npm run build
```

Test memakai database terpisah `edumap_test` yang dibuat otomatis di server Postgres yang sama, jadi data pengembangan tidak ikut terhapus. Groq dan model embedding selalu di-mock, dan Redis memakai `fakeredis`.

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
