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
| LLM | Groq API, nama model dari env `GROQ_MODEL` |
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
├── .env.example
├── frontend/                 # Next.js
│   ├── app/
│   │   ├── (auth)/           # login, register
│   │   ├── teacher/          # dashboard guru, kelola class, review level & soal
│   │   └── student/          # daftar class, map level, halaman level
│   ├── components/
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
| `LLM_MODE` | `groq` (default) atau `mock`: jawaban offline dari konteks materi untuk demo/dev tanpa API key; `MOCK_LLM_DELAY_SECONDS` mengatur jeda tiruan |
| `EMBEDDING_MODEL` | Default `intfloat/multilingual-e5-small` |
| `EMBEDDING_DIM` | Default `384`, harus sama dengan dimensi kolom `vector` |
| `UPLOAD_DIR` | Folder penyimpanan PDF (volume Docker) |
| `MAX_UPLOAD_MB` | Batas ukuran PDF, default `20` |
| `NEXT_PUBLIC_API_URL` | URL backend untuk frontend |

---

## 6. Model data

Mengikuti ERD yang disepakati. Tambahan kolom boleh, tetapi perubahan relasi harus ditanyakan dulu.

| Tabel | Kolom penting |
|---|---|
| `users` | `id`, `name`, `email` (unik), `password_hash`, `role` (`teacher` \| `student`; hanya halaman awal default, bukan pembatas akses, lihat bagian 11) |
| `classes` | `id`, `teacher_id`, `title`, `description`, `visibility` (`public` \| `private`), `invite_code` (hanya private), `status` (`draft` \| `published`) |
| `materials` | `id`, `class_id`, `file_name`, `file_path`, `vector_status` (`pending` \| `processing` \| `ready` \| `failed`), `error_message` |
| `material_chunks` | `id`, `material_id`, `class_id`, `section_title`, `content`, `page_start`, `page_end`, `embedding vector(384)` |
| `levels` | `id`, `class_id`, `prerequisite_id` (nullable, self-FK), `title`, `type` (`lesson_quiz` \| `boss`), `order_index`, `summary`, `status` (`draft` \| `approved`) |
| `level_chunks` | relasi level ↔ chunk sumber (`level_id`, `chunk_id`) |
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
   - Embedding di CPU secara batch. **Model e5 wajib memakai prefix**: `"passage: "` untuk isi chunk, `"query: "` untuk query retrieval. Muat model sekali (singleton), jangan per request.
3. Selesai → `ready`. Error → `failed` + `error_message` yang bisa dibaca guru. Pipeline harus idempoten (memproses ulang material menghapus chunk lama dulu).

Retrieval:

- Selalu filter berdasarkan `class_id` (dan `level_chunks` bila konteks level). Tidak boleh ada retrieval lintas class.
- Similarity cosine di pgvector, default top-k = 5.

Prompt dan LLM:

- Semua prompt disimpan sebagai template di `backend/app/rag/prompts/`, tidak ditulis inline di route.
- System prompt wajib menegaskan: jawab hanya dari konteks yang diberikan, dalam Bahasa Indonesia, dan akui jika konteks tidak cukup.
- Output terstruktur (level, soal) diminta dalam JSON lalu **divalidasi dengan Pydantic**. Jika gagal parse, retry maksimal 2 kali lalu tandai gagal.
- Tangani rate limit Groq (HTTP 429) dengan exponential backoff dan fitur retry `arq`. Batasi jumlah panggilan Groq global per menit memakai counter di Redis. Jangan panggil LLM di dalam loop tanpa batas.
- Generate level dan generate soal juga berjalan sebagai job `arq`, dengan event progres yang sama.
- Jangan panggil LLM saat murid membuka halaman level. Ringkasan dan soal dibuat saat generate/review guru, lalu disimpan di DB.

---

## 8. Level dan kuis

Generate level:

- Satu section materi = satu level (`lesson_quiz`). Setiap 3–5 level, sisipkan satu level `boss` yang soalnya menggabungkan level-level sebelumnya.
- Graph dibuat **linear dengan sedikit percabangan**: setiap level punya paling banyak satu `prerequisite_id`. Level pertama tanpa prasyarat. Jangan membuat skill-tree kompleks.
- Hasil generate berstatus `draft`. Guru bisa mengubah judul, urutan, prasyarat, menggabung/memisah level, lalu publish class.

Soal (hybrid):

- AI membuat draft soal pilihan ganda (default 5 per level, 4 opsi) dari chunk level tersebut, lengkap dengan penjelasan dan `source_chunk_id`.
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
