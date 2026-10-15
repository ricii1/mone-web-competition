# AGENTS.md

Panduan untuk coding agent (dan anggota tim) yang bekerja di repo ini. Baca seluruh file ini sebelum mengubah kode. Jika instruksi di sini bertentangan dengan permintaan di task, ikuti task tetapi sebutkan konfliknya.

> Nama proyek masih sementara: **EduMap**. Ganti semua kemunculan `EduMap` / `edumap` saat nama final sudah ditentukan.

---

## 1. Ringkasan proyek

EduMap adalah platform web pembelajaran untuk lomba *"Innovating Education Through Technology"*.

- **Guru** membuat *class* (public/private), mengunggah materi PDF.
- Sistem memproses PDF dengan **RAG** dan menghasilkan **peta level** bergaya game (graph).
- **Murid** membuka level satu per satu: materi detail → rangkuman → kuis → level berikutnya terbuka. Ada leaderboard per class.

**Pengguna: guru SD dan murid SD** (kira-kira usia 7–12 tahun). Semua keputusan UI dan konten harus mengikuti ini:

- Teks UI dan konten AI memakai Bahasa Indonesia yang sederhana: kalimat pendek, istilah sulit dijelaskan, nada ramah dan menyemangati.
- Tampilan murid dibuat menyenangkan dan ramah anak: warna cerah, ikon dan ilustrasi ringan (SVG inline), tombol besar (target sentuh ≥ 48px), huruf besar dan mudah dibaca, umpan balik positif (bintang, selamat). Hindari istilah teknis dan layar yang padat.
- Tampilan guru tetap rapi dan efisien, tetapi memakai bahasa visual yang sama agar konsisten.
- Konten contoh (class contoh, seed) memakai topik tingkat SD, bukan SMP/SMA.

**Satu akun, dua peran (seperti Kahoot).** Email yang sama bisa membuat class (mode Guru) dan mengikuti class orang lain (mode Murid). Tidak ada akun "khusus guru" atau "khusus murid"; pengguna berpindah mode lewat tombol di header. `users.role` hanya menentukan halaman awal (default saat daftar/pilihan saat masuk), bukan hak akses.

**Halaman awal (`/`) adalah landing page promosi**, bukan sekadar tombol masuk: hero, fitur (grid bento berwarna dengan adegan mini), "Cara kerja" (peta game tiga pemberhentian), demo interaktif **"Coba sekarang"** sebagai murid dan sebagai guru, CTA, dan footer. Demo murni di browser (state lokal, tanpa backend, tanpa akun, tanpa localStorage) dan dimuat lazy lewat `next/dynamic`. Identitas visual: maskot burung hantu "Bu Hoo" (`Mascot.tsx`, juga ikon tab lewat `app/icon.svg`), lompat dengan bayangan di panel login/register dan landing, awan latar yang bergerak kiri ke kanan.

Prinsip produk yang tidak boleh dilanggar:

1. **Driven by guru dan kurikulum.** Semua konten AI (ringkasan, soal, jawaban tutor) harus berasal dari materi yang diunggah guru melalui retrieval. AI tidak boleh mengarang dari pengetahuan umum. Jika konteks tidak cukup, AI harus bilang tidak tahu.
2. **AI membantu guru, bukan menggantikan.** Struktur level dan soal yang dihasilkan AI berstatus *draft* sampai guru menyetujui.
3. **Ringan untuk murid.** Halaman murid harus cepat di HP low-end dan koneksi lambat. Semua komputasi berat (parsing, embedding, LLM) terjadi di backend.
4. **Cocok untuk anak SD.** Materi level berupa artikel pendek (±450–650 kata, bacaan 2–3 menit) yang disusun dari materi guru, diikuti rangkuman dan poin penting; bahasa dan tampilan harus bisa dipahami murid SD.

---

## 2. Tech stack (sudah diputuskan, jangan diganti tanpa persetujuan)

| Lapisan | Pilihan |
|---|---|
| Frontend | Next.js (App Router) + TypeScript (strict) + Tailwind CSS |
| Graph/map level | React Flow (`@xyflow/react`) |
| Backend | Python 3.11+ + FastAPI + Pydantic v2 |
| ORM & migrasi | SQLAlchemy 2.x + Alembic |
| Database | PostgreSQL 16 + ekstensi `pgvector` (data relasional dan vektor dalam satu DB) |
| Embedding | Model lokal di CPU via `sentence-transformers`, default `intfloat/multilingual-e5-small` (dimensi 384) |
| LLM | Groq API (`GROQ_MODEL`) atau gateway OpenAI-compatible LiteLLM ITS (`LLM_MODE=openai`, `LLM_BASE_URL`, `LLM_MODEL`, `API_KEY_LITELLM`) |
| PDF parsing | `pymupdf` (fitz) |
| Auth | JWT dibuat oleh FastAPI (email + password, hash `bcrypt`/`argon2`) |
| Queue & worker | Redis 7 + `arq` (worker async terpisah dari API) |
| Real-time | Redis pub/sub + WebSocket FastAPI; fallback polling |
| Menjalankan | Docker Compose |
| Test | `pytest` (backend), Vitest (frontend, bila perlu) |
| Lint/format | `ruff` (lint + format) untuk Python; ESLint + Prettier untuk TS |

Jangan menambah dependency besar (Celery, LangChain, ORM lain, UI kit berat, three.js, library real-time selain yang di atas, dll.) tanpa bertanya dulu. Semua pekerjaan berat (parsing PDF, embedding, panggilan LLM) **wajib** berjalan di worker `arq`, bukan di proses API dan bukan lewat `BackgroundTasks`.

---

## 3. Struktur repo

```
.
├── AGENTS.md
├── docker-compose.yml
├── run-uvicorn.sh            # menjalankan API native (conda)
├── README.md                 # cara start Docker dan conda, akun seed, troubleshooting
├── conversation.md
├── .env.example
├── frontend/                 # Next.js
│   ├── app/
│   │   ├── (auth)/           # login, register
│   │   ├── teacher/          # dashboard guru, kelola class, review level & soal
│   │   └── student/          # daftar class, map level, halaman level
│   ├── components/           # termasuk landing/ (landing page dan demo) dan Mascot, CloudSky, AuthHero
│   ├── app/icon.svg          # ikon tab (maskot)
│   ├── lib/                  # api client, auth helper, types
│   └── ...
└── backend/                  # FastAPI
    ├── app/
    │   ├── main.py
    │   ├── core/             # config, security (JWT), deps
    │   ├── db/               # session, base
    │   ├── models/           # SQLAlchemy models
    │   ├── schemas/          # Pydantic request/response
    │   ├── api/routes/       # router per domain
    │   ├── services/         # business logic (progress, leaderboard, class, live session)
    │   ├── rag/              # parsing, chunking, embedding, retrieval, llm, prompts
    │   ├── realtime/         # WebSocket endpoints, pub/sub helper, event schemas
    │   └── worker/           # arq WorkerSettings dan job functions
    ├── alembic/
    └── tests/
```

Aturan: route tipis, logika di `services/` atau `rag/`. Model LLM dan embedding hanya dipanggil dari `app/rag/`, dan `app/rag/` hanya dijalankan dari job di `app/worker/`. Model embedding dimuat di worker, bukan di proses API.

---

## 4. Perintah

```bash
# Menjalankan semua service (frontend, backend, worker, postgres, redis)
cp .env.example .env
docker compose up --build

# Log worker
docker compose logs -f worker

# Migrasi database
docker compose exec backend alembic upgrade head
docker compose exec backend alembic revision --autogenerate -m "pesan"

# Test & lint backend
docker compose exec backend pytest
docker compose exec backend ruff check . && docker compose exec backend ruff format --check .

# Lint & build frontend
cd frontend && npm run lint && npm run build
```

Alternatif tanpa membangun image PyTorch (lebih ringan, memakai conda; detail di `README.md`): `docker compose up -d postgres redis`, lalu `./run-uvicorn.sh`, `arq app.worker.settings.WorkerSettings`, dan `npm run dev`. Jangan menjalankan mode Docker dan native bersamaan (port 8000/3000/5433/6379 sama). Mode Docker penuh: `docker compose up -d` menjalankan semuanya (migrasi otomatis), `docker compose down` mematikan semuanya; worker tidak reload otomatis (`docker compose restart worker` setelah mengubah kode job/prompt). Data demo: `python -m app.db.seed` (`--examples` untuk memberi class contoh ke akun lama).

Sebelum menyatakan task selesai: jalankan test backend, `ruff check`, dan `npm run lint` untuk bagian yang disentuh.

---

## 5. Environment variables

Semua config lewat env (lihat `.env.example`). Jangan pernah hardcode secret atau commit `.env`.

| Variabel | Keterangan |
|---|---|
| `DATABASE_URL` | URL Postgres (`postgresql+psycopg://...`) |
| `REDIS_URL` | URL Redis (`redis://redis:6379/0`) |
| `WORKER_MAX_JOBS` | Jumlah job paralel di worker, default `2` (embedding memakai CPU) |
| `NEXT_PUBLIC_WS_URL` | URL WebSocket backend untuk frontend |
| `JWT_SECRET`, `JWT_EXPIRES_MINUTES` | Konfigurasi token |
| `GROQ_API_KEY` | API key Groq |
| `GROQ_MODEL` | Nama model Groq; cek daftar model aktif di console Groq, jangan hardcode di kode |
| `LLM_MODE` | `groq` (default), `openai` (gateway OpenAI-compatible; memakai `LLM_BASE_URL`, `LLM_MODEL`, `API_KEY_LITELLM`), atau `mock`: jawaban offline dari konteks materi untuk demo/dev tanpa API key; `MOCK_LLM_DELAY_SECONDS` mengatur jeda tiruan |
| `EMBEDDING_MODEL` | Default `intfloat/multilingual-e5-small` |
| `EMBEDDING_DIM` | Default `384`, harus sama dengan dimensi kolom `vector` |
| `UPLOAD_DIR` | Folder penyimpanan PDF (volume Docker) |
| `MAX_UPLOAD_MB` | Batas ukuran PDF, default `20` |
| `NEXT_PUBLIC_API_URL` | URL backend untuk frontend |
| `CORS_ORIGINS` | Origin frontend yang diizinkan (pisahkan dengan koma). `localhost` dan `127.0.0.1` di port mana pun selalu diizinkan; alamat lain (IP jaringan, domain) harus ditambahkan di sini |
| `API_PORT`, `WEB_PORT` | Port host untuk API dan frontend di Docker Compose (default `8000` dan `3000`) |

---

## 6. Model data

Mengikuti ERD yang disepakati. Tambahan kolom boleh, tetapi perubahan relasi harus ditanyakan dulu.

| Tabel | Kolom penting |
|---|---|
| `users` | `id`, `name`, `email` (unik), `password_hash`, `role` (`teacher` \| `student`; hanya halaman awal default, bukan pembatas akses, lihat bagian 11) |
| `classes` | `id`, `teacher_id`, `title`, `description`, `visibility` (`public` \| `private`), `invite_code` (hanya private), `status` (`draft` \| `published`), `is_example` (class contoh: tidak bisa dipublish), `generation_status`/`generation_error` (status job generate level) |
| `materials` | `id`, `class_id`, `file_name`, `file_path`, `vector_status` (`pending` \| `processing` \| `ready` \| `failed`), `error_message` |
| `material_chunks` | `id`, `material_id`, `class_id`, `section_title`, `content`, `page_start`, `page_end`, `embedding vector(384)` |
| `levels` | `id`, `class_id`, `prerequisite_id` (nullable, self-FK), `title`, `type` (`lesson_quiz` \| `boss`), `order_index`, `content` (artikel Markdown), `summary`, `key_points` (JSONB), `source_note` (teks sumber bebas yang diisi guru), `status` (`draft` \| `approved`) |
| `level_chunks` | relasi level ↔ chunk sumber (`level_id`, `chunk_id`); jejak retrieval AI, dibuat pipeline dan hanya dibaca guru (tidak diedit manual) |
| `questions` | `id`, `level_id`, `question_text`, `question_type` (`multiple_choice`), `options` (JSONB), `correct_answer`, `explanation`, `source_chunk_id`, `status` (`draft` \| `approved`) |
| `enrollments` | `id`, `user_id`, `class_id`, `joined_at`; unik (`user_id`, `class_id`) |
| `progress` | `id`, `user_id`, `level_id`, `status` (`locked` \| `unlocked` \| `completed`), `best_score`, `completed_at`; unik (`user_id`, `level_id`) |
| `attempts` | `id`, `user_id`, `question_id`, `user_answer`, `is_correct`, `created_at`, `live_session_id` (nullable) |
| `live_sessions` | `id`, `class_id`, `level_id` (level `boss` atau level pilihan guru), `host_id`, `join_code`, `status` (`waiting` \| `running` \| `finished`), `current_question_index`, `started_at`, `ended_at` |
| `live_participants` | `id`, `live_session_id`, `user_id`, `score`, `joined_at`; unik (`live_session_id`, `user_id`) |

Semua ID memakai UUID. Semua perubahan skema lewat migrasi Alembic, jangan edit tabel manual.

---

## 7. Pipeline RAG

Alur saat guru mengunggah PDF:

1. Validasi: hanya `application/pdf`, ukuran ≤ `MAX_UPLOAD_MB`. Simpan file, buat `materials` dengan `vector_status=pending`, enqueue job `arq`, kembalikan respons segera.
2. Worker memproses (`processing`) dan mengirim event progres per tahap (lihat bagian 9):
   - Ekstrak teks per halaman dengan `pymupdf`.
   - **Chunking per section**: pakai heading/bookmark PDF (ToC) jika ada; jika tidak, deteksi heading dari ukuran font; jika tetap gagal, fallback ke chunk ukuran tetap (~500 token, overlap ~50).
   - Simpan `section_title`, `page_start`, `page_end` di tiap chunk.
   - Embedding di CPU secara batch. **Model e5 wajib memakai prefix**: `"passage: "` untuk isi chunk, `"query: "` untuk query retrieval. Muat model sekali (singleton), jangan per request. Panggil `encode(..., convert_to_numpy=True)` lalu `.tolist()`: dengan `convert_to_numpy=False`, sentence-transformers 6.x mengembalikan list tensor untuk input batch sehingga `.tolist()` gagal.
3. Selesai → `ready`. Error → `failed` + `error_message` yang bisa dibaca guru. Pipeline harus idempoten (memproses ulang material menghapus chunk lama dulu).

Retrieval:

- Selalu filter berdasarkan `class_id` (dan `level_chunks` bila konteks level). Tidak boleh ada retrieval lintas class.
- Similarity cosine di pgvector, default top-k = 5.

Prompt dan LLM:

- Semua prompt disimpan sebagai template di `backend/app/rag/prompts/`, tidak ditulis inline di route.
- System prompt wajib menegaskan: jawab hanya dari konteks yang diberikan, dalam Bahasa Indonesia, dan akui jika konteks tidak cukup.
- Output terstruktur (level, soal) diminta dalam JSON lalu **divalidasi dengan Pydantic**. Jika gagal parse, retry maksimal 2 kali lalu tandai gagal.
- Tangani rate limit Groq (HTTP 429) dengan exponential backoff dan fitur retry `arq`. Batasi jumlah panggilan Groq global per menit memakai counter di Redis. Jangan panggil LLM di dalam loop tanpa batas.
- Mode `LLM_MODE=openai` (gateway OpenAI-compatible, mis. LiteLLM ITS) memakai jalur yang sama: `httpx` ke `{LLM_BASE_URL}/chat/completions`, kesalahan HTTP dibungkus `LlmHttpError` (punya `status_code` sehingga backoff 429 tetap jalan), blok `<think>` model penalaran (qwen3) dibuang sebelum JSON divalidasi. Model yang tersedia di gateway ITS: `qwen3:14b` (default), `qwen3.5:9b`. Satu generate PDF kecil sekitar 3 menit.
- Generate level dan generate soal juga berjalan sebagai job `arq`, dengan event progres yang sama. `WorkerSettings.job_timeout = 1800` (bawaan arq 300 detik terlalu pendek untuk PDF panjang); jika job dibatalkan karena timeout, `generation_status` harus menjadi `failed` (tangkap `asyncio.CancelledError`, bukan hanya `Exception`).
- Jangan panggil LLM saat murid membuka halaman level. Ringkasan dan soal dibuat saat generate/review guru, lalu disimpan di DB.

---

## 8. Level dan kuis

Generate level:

- Satu section materi = satu level (`lesson_quiz`). Setiap 3–5 level, sisipkan satu level `boss` yang soalnya menggabungkan level-level sebelumnya. Implementasi: boss disisipkan setiap `LEVELS_PER_BOSS = 4` level (`services/level_service.py`) dan tidak setelah level terakhir, sehingga class dengan 4 section atau kurang tidak punya boss; untuk 8 section ada boss setelah level ke-4; untuk 9 section ada boss setelah level ke-4 dan ke-8.
- Graph dibuat **linear dengan sedikit percabangan**: setiap level punya paling banyak satu `prerequisite_id`. Level pertama tanpa prasyarat. Jangan membuat skill-tree kompleks.
- Setiap level lesson berisi artikel (`content`), rangkuman, poin penting, dan sumber. Guru bisa mengedit semuanya di tab "Materi" (layout satu kolom lebar, tombol Simpan menempel di dasar layar). **Sumber** ada dua: `source_note` (teks bebas yang diketik guru, mis. "Buku IPA Kelas 4 hal. 12-15") dan bagian PDF yang dipakai AI (`level_chunks`, hanya tampil read-only). Jangan mengubah kembali ke checklist chunk: tidak skala untuk PDF asli.
- Hasil generate berstatus `draft`. Guru bisa mengubah judul, urutan, prasyarat, menggabung/memisah level, lalu publish class.

Soal (hybrid):

- AI membuat draft soal pilihan ganda (default 5 per level, 4 opsi) dari chunk level tersebut, lengkap dengan penjelasan dan `source_chunk_id`. Skema `GeneratedQuestion` menolak opsi kembar (dibandingkan tanpa spasi dan huruf besar/kecil) dan jawaban benar yang bukan salah satu opsi; output seperti itu memicu retry JSON.
- Guru bisa edit, hapus, tambah manual, dan approve. **Murid hanya melihat soal `approved`**.
- Class tidak bisa di-publish jika ada level tanpa soal `approved`.

Aturan progres (implementasi di `services/`, wajib ada test):

- Saat murid join class: level tanpa prasyarat → `unlocked`, sisanya `locked`.
- Level `completed` jika skor ≥ 70% (konstanta `PASSING_SCORE`, satu tempat saja). Setelah itu level yang prasyaratnya level ini menjadi `unlocked`.
- Murid boleh mengulang level; simpan `best_score` tertinggi.
- **Penilaian dilakukan di server.** Jawaban benar tidak pernah dikirim ke client sebelum murid submit.

Leaderboard:

- Per class, skor = jumlah `best_score` semua level. Seri diurutkan berdasarkan waktu `completed_at` terakhir yang lebih awal.
- Tampilkan nama murid dan skor saja, tanpa email.
- Sumber kebenaran tetap Postgres. Redis sorted set (`leaderboard:{class_id}`) dipakai sebagai cache ranking dan diperbarui setiap `best_score` berubah. Jika key hilang, bangun ulang dari Postgres.

---

## 9. Real-time

Fitur real-time adalah bagian utama demo. Tiga pemakaiannya:

1. **Progres pemrosesan materi** untuk guru: tahap `reading` → `chunking` → `embedding` → `generating_levels` → `generating_questions` → `done` / `failed`, dengan angka progres (misal "level 3 dari 8"). Di frontend, node level muncul satu per satu saat event `level_created` diterima.
2. **Leaderboard live** per class.
3. **Live class** (bagian 10).

Aturan:

- Channel pub/sub: `class:{class_id}:events`, `material:{material_id}:progress`, `live:{session_id}`. Nama channel didefinisikan di satu modul (`app/realtime/channels.py`).
- Setiap event adalah JSON dengan skema Pydantic di `app/realtime/events.py`: `{ "type": ..., "payload": ..., "ts": ... }`. Tipe TypeScript yang sama didefinisikan di `frontend/lib/realtime.ts`.
- WebSocket wajib diautentikasi dengan JWT (dikirim saat handshake) dan dicek aksesnya ke class/sesi terkait.
- Event hanya pemberitahuan. State penting (status material, progres, skor) selalu disimpan ke Postgres dulu, baru event dikirim. Client yang tersambung ulang harus mengambil state terbaru lewat REST.
- **Fallback wajib:** jika WebSocket gagal atau terputus, frontend beralih ke polling endpoint REST setiap beberapa detik dan mencoba reconnect dengan backoff. Demo tidak boleh macet karena WebSocket.
- Halaman murid biasa (map, level) tidak membuka WebSocket kecuali untuk leaderboard dan live class, supaya tetap ringan.

---

## 10. Live class

Sesi kuis serentak ala Kahoot yang dipimpin guru.

- Guru memulai sesi dari sebuah level (umumnya `boss`) di class miliknya. Sistem membuat `join_code` pendek. Status awal `waiting`.
- Murid yang sudah join class masuk ke sesi dengan `join_code` dan tampil di lobi guru secara real-time.
- Guru mengontrol alur: mulai, lanjut ke soal berikutnya, akhiri. Setiap soal punya batas waktu (default 20 detik, konstanta di satu tempat).
- Penilaian di server. Skor per soal: benar mendapat poin dasar ditambah bonus kecepatan berdasarkan waktu server, bukan waktu dari client. Jawaban setelah batas waktu atau jawaban ganda ditolak.
- Jawaban benar dan distribusi jawaban hanya dikirim setelah waktu soal habis atau guru menutup soal.
- State sesi yang sedang berjalan (soal aktif, deadline, jawaban masuk) disimpan di Redis dengan TTL. Hasil akhir (`live_participants.score`, `attempts`) disimpan ke Postgres saat soal ditutup.
- Hasil live class tidak mengubah `progress` murid; ini sesi terpisah dari jalur belajar mandiri.
- Jika guru terputus, sesi tetap berada di status terakhir dan bisa dilanjutkan saat guru tersambung lagi.

---

## 11. Auth dan otorisasi

- JWT dikirim sebagai header `Authorization: Bearer <token>`. Password di-hash, tidak pernah dikembalikan di respons.
- Satu akun boleh bertindak sebagai guru dan murid. Hak akses ditentukan **per resource di backend**, bukan oleh `users.role`: aksi guru (ubah class, upload, review, live host) hanya untuk pemilik class (`classes.teacher_id`); aksi murid (lihat level published, kuis, leaderboard, ikut live) hanya untuk yang ter-enroll. Dependency `require_teacher`/`require_student` hanya memastikan pengguna sudah masuk; pengecekan kepemilikan/enrollment tetap wajib di service/route, jangan hanya menyembunyikan tombol di frontend.
- Setiap akun baru mendapat class contoh (karena bisa jadi guru kapan saja).
- Guru hanya bisa mengubah class miliknya sendiri.
- Class `private` hanya bisa di-join dengan `invite_code` yang benar; kode dibuat acak dan cukup panjang.
- Murid hanya bisa melihat level/soal dari class yang sudah ia join dan yang berstatus `published`.
- Hanya guru pemilik class yang bisa membuat dan mengontrol live session; hanya murid yang ter-enroll yang bisa masuk.

---

## 12. Konvensi kode

Bahasa:

- Dokumen proyek dan **teks UI**: Bahasa Indonesia.
- **Nama variabel, fungsi, file, komentar kode, pesan commit**: Bahasa Inggris.

Backend:

- Type hints di semua fungsi. Pydantic schema terpisah untuk request dan response.
- Endpoint diawali `/api/v1/`, nama resource jamak (`/api/v1/classes/{class_id}/levels`).
- Error memakai `HTTPException` dengan pesan yang jelas; jangan membocorkan stack trace ke client.

Frontend:

- TypeScript strict, hindari `any`.
- Halaman murid (map dan level) utamakan ringan: Server Components bila memungkinkan, tanpa animasi berat (awan latar `CloudSky variant="page"` boleh: hanya `transform`, maksimal 4 awan, 2 di HP, mati saat `prefers-reduced-motion`), gambar dioptimasi, dan pastikan tampil baik di lebar 360px. React Flow hanya dimuat di halaman map (dynamic import).
- Animasi hanya `transform`/`opacity`, CSS murni atau komponen kecil tanpa dependency (tidak ada framer-motion, GSAP, atau lib ikon), dan wajib mati saat `prefers-reduced-motion`. Landing page boleh lebih kaya (`Reveal` dengan varian up/left/right/zoom/flip, `ScrollProgress`, `Parallax`, garis yang tergambar saat scroll, `scroll-behavior: smooth` untuk tautan `#`), tetapi tidak boleh ada konten yang tersembunyi tanpa JS.
- Peta level (`LevelMap`) punya tombol "Tampilan awal" di kiri bawah (murid, guru, dan preview) yang mengembalikan viewport ke tampilan awal, untuk kasus peta tergeser atau ter-zoom. Logika tampilan awal dan tombol harus memakai hook yang sama (`useDefaultView`).
- Latar halaman (warna dan titik matahari) berada di `html`, bukan `body`, supaya layer `fixed` dengan `z-index` negatif (awan) terlihat.
- Saat memformat, jangan menjalankan `prettier --write` pada file lama (mengubah gaya seluruh file); cukup ikuti gaya file di sekitarnya.
- Semua panggilan API lewat satu client di `frontend/lib/api.ts`.
- Tampilkan state loading/empty/error, termasuk status pemrosesan PDF untuk guru.

Git:

- Commit kecil dan fokus, format Conventional Commits (`feat:`, `fix:`, `refactor:`, `test:`, `docs:`).

---

## 13. Testing (wajib untuk logika inti)

Wajib ada test `pytest` untuk:

- Chunking (PDF dengan heading, tanpa heading, PDF kosong/rusak).
- Parsing & validasi output LLM (JSON valid, JSON rusak, retry).
- Aturan unlock level, `PASSING_SCORE`, dan `best_score`.
- Perhitungan leaderboard.
- Otorisasi (guru lain tidak bisa edit class, murid tidak bisa akses class yang tidak di-join, invite code salah ditolak, WebSocket tanpa token ditolak).
- Job worker: status material berubah benar saat sukses, gagal, dan retry; job idempoten jika dijalankan ulang.
- Live class: skor dan bonus kecepatan, penolakan jawaban terlambat/ganda, jawaban benar tidak bocor sebelum soal ditutup.
- Leaderboard Redis bisa dibangun ulang dari Postgres dan hasilnya sama.

Test memakai database terpisah `edumap_test` (dibuat otomatis di server Postgres yang sama) supaya data development tidak terhapus. Test yang menegaskan perilaku lama harus diganti dengan test untuk aturan baru, bukan dilemahkan (contoh: akun ganda guru+murid).

Dalam test, **mock Groq dan model embedding**; test tidak boleh memanggil jaringan atau mengunduh model. Gunakan `fakeredis` atau Redis dari Docker khusus test; jangan memakai Redis development. Job `arq` diuji dengan memanggil fungsi job langsung. Test UI tidak wajib.

---

## 14. Ruang lingkup

MVP (kerjakan dulu, urut prioritas):

1. Auth & role, class public/private.
2. Upload PDF + worker RAG + progres pemrosesan real-time.
3. Generate level & soal, review guru, publish.
4. Map level, halaman penjelasan + kuis, progres/unlock.
5. Leaderboard live.
6. Live class.

Nice-to-have (jangan dikerjakan kecuali diminta): level Tutor Sokratik (chat streaming), tema naratif "wilayah berkabut", peta kelas sosial, notifikasi proaktif, analitik guru lanjutan. Desain kode agar fitur ini bisa ditambahkan nanti (misalnya `levels.type` bisa diperluas, channel event bisa ditambah), tetapi jangan membuat kerangkanya sekarang.

### Backlog perbaikan (hasil uji generate dengan `qwen3:14b`, 11 Oktober 2026)

Temuan dari uji nyata: PDF 4 section selesai sekitar 3 menit, PDF 9 section sekitar 5,5 menit (11 level, 55 soal valid). Daftar ini **usulan**, bukan kesepakatan; kerjakan hanya jika diminta, urut dari yang paling berdampak:

1. **Job macet di "generating".** Selain timeout (sudah diperbaiki), worker yang mati atau di-restart saat job berjalan (SIGTERM, crash) juga meninggalkan `generation_status=generating` selamanya, dan `POST .../levels/generate` lalu ditolak. Usulan: saat worker start (atau saat endpoint dipanggil) tandai class yang `generating` lebih lama dari `job_timeout` sebagai `failed`. Tambahkan test untuk kasus timeout dan restart.
2. **Artikel pendek jika section PDF pendek.** Prompt meminta 450-650 kata "jika konteks cukup"; section ±120-150 kata menghasilkan artikel 218-346 kata. Itu perilaku benar (AI tidak mengarang), tetapi guru perlu tahu. Usulan: beri peringatan di UI guru ("materi sumber pendek, artikel mungkin singkat") dan/atau gabungkan section bertetangga yang sangat pendek menjadi satu level. Jangan menyuruh model menambah isi dari pengetahuan umum.
3. **Boss tidak adil untuk ekor.** Boss disisipkan setiap 4 level dan tidak setelah level terakhir, jadi class 4 section tidak punya boss dan sisa level setelah boss terakhir tidak ditutup boss. Usulan: jika sisa ≥ 3 level di akhir, tambahkan satu boss penutup; selaraskan konstanta dengan teks "3-5 level".
4. **Kecepatan.** Level dan soal dibuat berurutan (±2 panggilan LLM per level, ±30 detik per panggilan). Usulan: jalankan beberapa level paralel dengan batas kecil (2-3) tetap di bawah counter rate limit Redis. Jangan menaikkan paralelisme tanpa menjaga batas itu.
5. **Token terbuang pada model penalaran.** Gateway mengembalikan `reasoning_content` panjang untuk qwen3. Perlu dicoba (belum diverifikasi) mematikan mode berpikir lewat parameter gateway agar lebih cepat dan murah; pastikan JSON tetap valid.
6. **Kualitas soal.** Opsi kembar sudah ditolak skema. Usulan tambahan yang murah: tolak soal yang pertanyaannya sama dengan soal lain di level itu, dan pastikan `explanation` merujuk isi chunk. Guru tetap meninjau semua soal `draft`.
7. **Material gagal tertinggal.** Material `failed` tetap tampil sebagai duplikat setelah upload ulang. Usulan: tombol "Coba proses lagi" (job idempoten sudah ada) dan "Hapus" untuk material.
8. **Nama yang menyesatkan.** `call_groq_structured`, `call_groq_with_backoff`, `_call_groq_sync`, `GROQ_MAX_CALLS_PER_MINUTE`, dan key Redis `groq:calls:*` kini melayani semua provider. Usulan rename ke nama netral (`call_llm_*`) dalam satu commit `refactor:` tersendiri beserta test.
9. **Fixture uji.** Tidak ada PDF contoh di repo (dan PDF pihak lain tidak boleh di-commit). Usulan: skrip kecil yang membuat PDF uji dengan `pymupdf` (beberapa section, panjang bervariasi) agar uji generate bisa diulang.

---

## 15. Jangan lakukan

- Jangan mengganti stack, menambah service/dependency besar, atau mengubah relasi skema tanpa bertanya.
- Jangan membuat konten AI tanpa retrieval dari materi class.
- Jangan mengirim jawaban benar ke client sebelum submit (atau sebelum soal live ditutup).
- Jangan menjalankan parsing, embedding, atau panggilan LLM di proses API.
- Jangan menjadikan Redis satu-satunya penyimpanan data yang harus bertahan; Postgres adalah sumber kebenaran.
- Jangan membuat fitur yang hanya jalan jika WebSocket tersambung; selalu ada fallback polling.
- Jangan commit secret, file `.env`, PDF contoh milik orang lain, atau bobot model.
- Jangan menghapus atau melemahkan test agar lolos.
- Jika ragu tentang keputusan produk, tanya dulu daripada menebak.

---

## 16. Dokumentasi percakapan

Lomba ini mewajibkan dokumentasi lengkap prompt awal–akhir (termasuk debugging). Jadi:

- Setiap sesi kerja dengan coding agent, update `conversation.md` di root repo dengan entri baru, format:

  ```
  **HH:MM**
  user: "prompt asli pengguna (diringkas kalau panjang)"

  agent: "ringkasan singkat apa yang dikerjakan/ditemukan/diperbaiki"
  ```

- Kelompokkan entri per tanggal dengan heading `## <tanggal>`. Timestamp pakai jam saat prompt/respons terjadi.
- Debugging **wajib** dicatat sebagai entri tersendiri: apa masalahnya, kenapa terjadi, dan apa perbaikannya — bukan cuma "fixed bug".
- Tulis entri di akhir setiap tugas yang selesai (bukan ditunda ke akhir sesi), supaya tidak ada yang terlewat kalau sesi terputus.
- `conversation.md` ikut di-stage/commit bersama perubahan kode terkait.


## 17. Perbaikan audit DevOps (11 Oktober 2026)

- Development memakai port DB/Redis loopback. Override `docker-compose.production.yml`
  menutup keduanya, menjalankan service non-root tanpa watcher/bind mount, serta memakai
  frontend standalone. Production memerlukan secret JWT minimal 32 byte dan menolak
  password database contoh; frontend production tidak menerima env backend.
- Upload mempunyai batas body sebelum multipart parsing, baca bertahap, signature PDF
  ringan dan cleanup ketika gagal. Parsing PDF tetap di worker. Kegagalan enqueue material
  menjadi `failed`; kegagalan enqueue generate menjadi `failed` dan respons 503.
- Migrasi `0008` menambahkan `classes.generation_job_id` dan `generation_requested_at`.
  Worker startup dan endpoint generate memulihkan job yang hilang/selesai setelah tenggat;
  job antre/deferred/berjalan tetap sah. Job lama diberi masa tenggang saat migrasi.
  Permintaan generate diserialkan dengan lock baris; worker menolak identitas job lama.
- Kuota LLM diperoleh untuk setiap percobaan HTTP termasuk retry 429; setelah menunggu
  pergantian menit wajib mengambil slot lagi. Retry tersembunyi SDK Groq dimatikan.
- Auth dibatasi per IP dan email (login 10/menit, register 20/jam); password maksimal
  72 byte agar bcrypt tidak memotong diam-diam. Field nama dibatasi 100 karakter.
- WebSocket menutup session DB setelah otorisasi, sebelum streaming. Live WebSocket
  hanya untuk host/peserta sesi, selaras dengan REST.
- Submit live memakai `HSETNX` dalam transaksi yang mengawasi soal aktif; close/start/end
  diserialkan dengan lock kontrol Redis dan lock baris Postgres. Close tidak menilai ulang
  soal yang sudah tersimpan. Tombol next mengirim ID soal untuk menolak permintaan lama.
  Retensi state/jawaban live 24 jam; deadline tetap 20 detik. Akhiri menyimpan jawaban
  sebelum cleanup. Kegagalan notifikasi pub/sub tidak menggagalkan state yang tersimpan.
- REST sesi live menyediakan soal aktif tanpa jawaban benar, jawaban sendiri, peserta
  (nama/skor), dan hasil akhir. Frontend mengambil snapshot saat connect/reconnect dan
  polling 4 detik, juga ketika event masuk. Timer reconnect/polling dibersihkan saat keluar.
- Leaderboard memakai penggantian cache atomik dan versi untuk retry ketika skor berubah
  saat rebuild; integer score dan urutan leksikografis mempertahankan tie waktu mikrodetik.
  Format cache lama dibangun ulang otomatis. Pemeriksaan publish memakai dua query tetap.
- `docs/devops-audit.md` menyimpan bukti audit dan status perbaikannya;
  `docs/backlog-solutions.md` menyimpan usulan produk/optimasi yang belum semuanya diterapkan.


## 18. PDF asli untuk guru dan murid (12 Oktober 2026)

- Guru membuka PDF asli dari daftar materi di halaman kelola class melalui tombol
  "Lihat PDF". Murid membuka bagian "Materi PDF dari guru" pada halaman peta kelas.
- File diambil lewat client API dengan header Bearer, bukan token dalam URL.
  Endpoint `GET /api/v1/classes/{class_id}/materials/{material_id}/file` mengizinkan
  pemilik kelas atau murid yang ter-enroll di kelas published. Material harus milik
  kelas tersebut dan file harus berada di direktori upload kelas; file hilang memberi 404.
- Viewer menggunakan PDF bawaan browser (iframe dari object URL), dimuat hanya
  ketika diminta. Request dibatalkan dan object URL dilepas saat viewer ditutup/unmount.
  Sediakan tombol "Unduh PDF" untuk perangkat yang tidak mendukung tampilan PDF inline.
  Respons memakai `application/pdf`, inline disposition dan `private, no-store`.
- Tips format Markdown pada editor artikel guru diletakkan sebelum kotak artikel;
  pertahankan `aria-describedby` yang menghubungkan kotak dengan tips.


## 19. Hasil uji batas subbab PDF (12 Oktober 2026)

Enam fixture asli dibuat melalui
`backend/scripts/generate_pdf_layout_fixtures.py`; hasil rinci di
`docs/pdf-layout-test.md`. Parser/chunker belum diubah pada sesi pengujian ini.

- Jalur bookmark benar untuk satu subbab per halaman, tetapi tidak memisahkan
  dua bookmark pada halaman yang sama dan salah menempatkan kelanjutan subbab.
- Jalur font-heading memasukkan halaman heading berikut sebagai akhir inklusif:
  bahkan PDF rapi tanpa bookmark ikut tercampur; pada subbab di tengah halaman,
  potongan bisa mencakup beberapa subbab sekaligus.
- PDF tanpa heading yang bisa dikenali memakai fallback 500 kata/overlap 50;
  jumlah level kemudian mengikuti jumlah chunk, bukan selalu jumlah subbab.
- Pipeline worker dengan parsing asli dan embedding/LLM mock menghasilkan
  16 level/80 soal dari enam fixture, tetapi artikel bisa ikut tercampur karena
  sumber chunk salah. Status done dan jumlah level saja tidak membuktikan kualitas.
- Usulan perbaikan: simpan posisi heading dalam teks dan potong sampai sebelum
  heading berikutnya; gunakan lokasi/pencocokan heading untuk bookmark di halaman
  yang sama. Tambahkan test penanda isi per subbab dan kelanjutan lintas halaman.


## 20. Perbaikan batas subbab PDF (12 Oktober 2026)

Bug pada bagian 19 sudah diperbaiki: `HeadingSpan.offset` dan `ParsedPdf.toc_headings`
menyimpan posisi dalam teks halaman. Teks dan offset berasal dari aliran baris yang
sama; heading multi-span/dua baris dalam satu blok digabung. Bookmark dicocokkan
ke judul atau lokasi tujuan. Batas chunk berakhir sebelum heading berikutnya,
termasuk pada halaman yang sama; metadata halaman memakai isi aktual. Pengantar
sebelum heading pertama dipertahankan di chunk pertama. Bookmark bertingkat dengan
posisi sama tidak menggandakan materi; bookmark ambigu memakai fallback yang aman.

Test `test_pdf_section_boundaries.py` wajib menjaga isi subbab, kelanjutan,
metadata halaman, heading/gaya huruf, bookmark dan sumber artikel/soal pada worker.
Hasil lama tidak diubah otomatis; perbaikan berlaku saat PDF diproses dengan worker
baru. Dokumen tanpa struktur yang dapat dikenali tetap memakai fallback 500 kata
(overlap 50). Semua test memakai embedding/LLM mock dan database test terpisah.


## 21. Urutan, persetujuan, dan sumber panjang (12 Oktober 2026)

- Migrasi `0009` menambahkan `material_chunks.order_index` dan index
  `(material_id, order_index)`. Worker menyimpan urutan hasil chunking; generate
  dan tampilan sumber mengurutkan material lalu `order_index`. Nomor halaman
  tidak cukup untuk dua subbab pada halaman yang sama.
- Data lama di-backfill dengan urutan halaman dan ID sebagai pemecah seri.
  Urutan asli beberapa subbab di halaman yang sama pada chunk lama tidak dapat
  dipastikan hanya dari data tersebut; jangan mengklaim backfill memulihkan offset
  yang sebelumnya tidak tersimpan. Artikel/progres/relasi sumber lama dipertahankan.
- Publish membutuhkan setiap level berstatus `approved` dan minimal satu soal
  `approved` per level. Publish saat generate masih berjalan ditolak. UI guru
  menampilkan jumlah materi yang masih perlu ditinjau. Kelas kosong tetap mengikuti
  perilaku sebelumnya; kelas yang sudah terbit tidak diubah otomatis oleh migrasi.
- Konteks lebih dari 8.000 karakter dibaca seluruhnya dalam bagian maksimal 8.000,
  dengan batas kalimat jika memungkinkan. Template `source_notes.txt` menghasilkan
  catatan Pydantic `GeneratedSourceNotes` maksimal 2.000 karakter per bagian;
  catatan direduksi bertahap hingga muat, tanpa mengambil awalan sumber saja.
  Artikel dan soal memakai konteks siap yang sama, termasuk boss; semua tetap draft.
- Semua panggilan catatan memakai jalur LLM/limiter/retry yang sama, hanya dari worker.
  Batas 16 bagian per putaran, 4 putaran reduksi, dan maksimal 128.000 karakter input
  mencegah pekerjaan tanpa batas. Jika melewati batas, job gagal dengan pesan meminta
  subbab dipisah; jangan membuang bagian akhir diam-diam. Catatan tetap perlu review
  guru; membaca semua bagian tidak menjamin model mempertahankan setiap detail.
- Test menjaga urutan insert/UUID yang berbeda, sumber artikel/soal awal–tengah–akhir,
  batas panggilan, publish draft/generating, serta backfill yang menjaga data guru.


## 22. Pratinjau sumber, proses ulang, soal unik, dan hapus kelas (12 Oktober 2026)

- Guru dapat melihat pembagian PDF sebelum generate: judul, urutan, rentang halaman,
  cuplikan, dan teks lengkap. Endpoint `materials/{id}/sections` dibatasi maksimal
  50 bagian per request; teks lengkap dimuat terpisah saat dibuka. Semua hanya untuk
  pemilik kelas dan material `ready`, tanpa parsing atau embedding di proses API.
- Materi `failed` memiliki tindakan "Coba proses lagi" dan "Hapus PDF gagal".
  Keduanya ditolak saat generate aktif atau jika chunk dipakai oleh `level_chunks`
  atau `questions.source_chunk_id`. Retry memakai file asli dan job worker yang sama.
- Migrasi `0010` menambah `materials.processing_job_id` nullable. Upload/retry baru
  menetapkan UUID job baru; worker memeriksa token dan melakukan claim status atomik.
  Job dengan token lama atau job yang sudah selesai tidak mengganti hasil baru.
  Material lama dengan token null tetap mendukung job lama; material ready yang
  sudah dipakai sebagai sumber dilewati agar job legacy tidak merusak hasil review.
  Pembatalan worker
  menjadi `failed`; kegagalan pub/sub hanya dicatat dan tidak membalik status sukses.
- Pertanyaan satu level harus unik setelah whitespace dinormalisasi dan huruf
  dibandingkan dengan `casefold`. Output AI duplikat memicu retry JSON terbatas;
  tambah/edit manual ditolak dengan pesan jelas. Data lama tidak dihapus otomatis.
- "Hapus kelas" ada di bagian bawah halaman kelola kelas. Guru harus mengetik nama
  kelas tepat; backend juga memeriksa nama, kepemilikan, job materi/generate dan sesi
  live. Sesi `waiting`/`running` harus diakhiri dahulu. Akun tidak ikut dihapus.
- Penghapusan kelas membersihkan file pada folder UUID kelas, level/soal/sumber,
  enrollment/progres/attempt dan sesi beserta peserta. Cache terkait dibersihkan
  setelah commit. Hubungan sumber/prasyarat lintas kelas yang tidak valid ditolak,
  bukan diam-diam mengubah kelas lain. Symlink keluar folder kelas ditolak.
- File/folder dipindah sementara sebelum transaksi delete dan dikembalikan bila
  transaksi gagal. Setelah commit, pembersihan file/cache dilakukan; kegagalan
  filesystem atau Redis dicatat untuk operator. Kegagalan penghapusan filesystem
  setelah commit dapat menyisakan folder `.deleted-*`, bukan metadata aktif.
- `test_resource_management.py` menjaga izin, batas payload, referensi sumber,
  identitas job, pemulihan file/data, penghapusan lengkap, dan retry soal duplikat.


## 23. Bantuan interaktif dan dialog layar penuh (12 Oktober 2026)

- Panel bantuan memakai `<dialog>.showModal()` agar masuk lapisan modal browser.
  Jangan menaruh kembali overlay `fixed` biasa di dalam header `backdrop-blur`:
  filter header menjadi containing block dan membuat overlay hanya setinggi header.
- Batas panel mengikuti `100dvh` dan safe area. Isi bisa digulir; judul/tutup dan
  tombol Sebelumnya/Berikutnya tetap terlihat. Buka ulang/ganti mode mengembalikan
  guliran ke awal. Escape, klik latar, tombol tutup dan pemulihan fokus tetap bekerja.
- Panduan guru/murid punya langkah yang bisa dipilih (pilihan dropdown di HP,
  tombol nomor di layar lebar), penanda "Sudah paham", tautan
  menuju halaman terkait dan masalah umum yang bisa dibuka. Penanda hanya state
  lokal komponen, bukan progres belajar dan tidak disimpan ke backend/localStorage.
- Tab mode mendukung tombol panah/Home/End, roving tabindex dan ARIA panel; kontrol
  bantuan berukuran minimal 48px. Panduan guru harus mengikuti aturan publish terbaru
  (materi level approved serta minimal satu soal approved), bukan hanya soal approved.
- Uji browser memeriksa guru/murid pada 320×568, 360×640, 800×360 dan 1280×800,
  geometri panel/judul, overflow, kontrol langkah, FAQ, tab keyboard, tutup/Escape,
  pemulihan fokus/scroll dan posisi awal saat dibuka lagi. Rincian di
  `docs/help-ui-check.md`. Tidak ada dependency UI baru atau panggilan AI tambahan.
