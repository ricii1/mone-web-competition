# Deployment Peta Pintar di Dokploy

Panduan ini mengikuti alur `panduan cara deploy di dokploy.pdf`: login,
hubungkan Git, pilih repository/branch, simpan, Deploy, periksa Deployments,
lalu buka Domains. **Perbedaannya ada pada jenis service:** contoh PDF memakai
Application + Nixpacks untuk Next.js saja. Peta Pintar memakai **Docker Compose**
karena API Python, worker arq, PostgreSQL + pgvector, dan Redis juga harus berjalan.
Stack, relasi database, dan alur aplikasi tidak berubah.

## 1. Akses dan repository

1. Login ke alamat Dokploy dari panitia memakai kredensial yang diberikan.
2. Buka **Settings → Git**, pilih GitHub (atau provider repository), lalu selesaikan
   autentikasi dan instalasi Git App sesuai PDF. Biarkan toggle berbagi provider
   **nonaktif**, sesuai peringatan PDF, agar tidak dibagikan kepada peserta lain.
3. Pastikan branch deployment sudah memuat perubahan aplikasi, seluruh migrasi,
   Dockerfile, dan `docker-compose.dokploy.yml`. Dokploy mengambil kode dari Git;
   perubahan lokal yang belum di-push tidak akan ikut deployment.
4. Di project yang disediakan panitia, gunakan service **Compose**, dengan
   **Compose Type: Docker Compose** (bukan Docker Stack).
   Jika yang tersedia hanya Application/Nixpacks dan akun tidak bisa membuat
   Compose, minta panitia menyediakan service Compose di project tersebut.
   Jangan men-deploy frontend saja lalu menganggap seluruh aplikasi sudah siap.

Pengaturan **General**:

| Isian | Nilai |
|---|---|
| Provider/account | Akun Git yang sudah dihubungkan |
| Repository | Repository Peta Pintar |
| Branch | Branch yang berisi perubahan siap deploy |
| Compose Path | `./docker-compose.dokploy.yml` |
| Build Path, jika tersedia | `/` (root repository) |
| Isolated Deployments | **Aktifkan** di pengaturan Compose/Advanced |

Simpan pengaturan. File Compose ini berdiri sendiri; tidak perlu digabung dengan
`docker-compose.yml` atau override production. Isolated Deployments menjaga
service di jaringan stack sendiri dan memungkinkan Dokploy menambahkan routing.
Tidak perlu menulis label Traefik atau `dokploy-network` manual.

## 2. Domain dan Environment

Siapkan **dua hostname** yang diizinkan panitia, satu untuk web dan satu untuk API.
Domain dalam tabel berikut hanya contoh, bukan domain yang sudah dialokasikan.
Di tab **Domains**, tambahkan:

| Contoh host | Service Name | Container Port | Path | HTTPS |
|---|---|---|---|---|
| `belajar.example.invalid` | `frontend` | `3000` | `/` | Aktif |
| `api.example.invalid` | `backend` | `8000` | `/` | Aktif |

Pastikan DNS kedua host mengarah ke server panitia dan sertifikat HTTPS tersedia.
Jika memakai domain sendiri, buat record sesuai IP yang diberikan panitia.
Pakai sertifikat yang dikelola panitia, atau Let's Encrypt jika tersedia.
WebSocket memakai host API yang sama dengan protokol **wss**.
Jangan menambahkan domain untuk postgres, redis, atau worker.

Di tab **Environment**, salin isi [`.env.dokploy.example`](../.env.dokploy.example),
lalu isi:

- `NEXT_PUBLIC_API_URL=https://<host-api>` dan `NEXT_PUBLIC_WS_URL=wss://<host-api>`.
  Tanpa `/api/v1`, tanpa `/ws`, dan tanpa garis miring di akhir: client sudah
  menambahkan path masing-masing.
- `CORS_ORIGINS=https://<host-web>`, tanpa path atau garis miring di akhir.
- `POSTGRES_PASSWORD` dan `JWT_SECRET`: dua nilai acak yang **berbeda**. Jalankan
  `openssl rand -hex 32` dua kali, lalu salin hasilnya ke dashboard.
  Password hex aman untuk URL database. JWT wajib minimal 32 byte.
- `LLM_MODE=openai`: isi `API_KEY_LITELLM`, `LLM_BASE_URL`, dan `LLM_MODEL` dari
  gateway yang digunakan. Untuk `groq`, isi `GROQ_API_KEY` dan `GROQ_MODEL` dengan
  model aktif di akun. Untuk demo offline, gunakan `LLM_MODE=mock` tanpa API key;
  embedding lokal tetap dipakai dan model tetap perlu diunduh.

Simpan Environment sebelum build. `DATABASE_URL`, `REDIS_URL`, `APP_ENV`, dan
`UPLOAD_DIR` disusun oleh Compose; tidak perlu menyalin `.env` development.
Secret LLM hanya diteruskan ke worker, dan frontend tidak menerima secret backend.
Nilai `NEXT_PUBLIC_*` ditanam saat build: perubahan domain API membutuhkan
**build ulang frontend**, bukan restart saja.

## 3. Validasi dan Deploy

Klik **Preview Compose** dan pastikan lima service muncul, domain menunjuk service
dan port yang benar, serta jaringan terisolasi diterapkan. Tidak ada pemetaan
port host `3000`, `8000`, `5432`, atau `6379` pada file ini.

Validasi lokal opsional, dengan file env deployment terpisah yang disimpan di luar
repository (misalnya `/tmp/edumap-dokploy.env`):

```bash
docker compose --env-file /tmp/edumap-dokploy.env -f docker-compose.dokploy.yml config -q
```

Jangan commit file env berisi secret atau membagikan output `config` tanpa `-q`.

Klik **Deploy**, lalu pantau **Deployments** dan log tiap service:

1. PostgreSQL dan Redis harus sehat.
2. Backend menjalankan `alembic upgrade head`, kemudian API di port 8000.
3. Worker arq dan frontend berjalan setelah backend sehat.
4. Periksa `https://<host-api>/health` menghasilkan `{"status":"ok"}` dan domain
   web menampilkan landing page. Status Done build perlu dilanjutkan pemeriksaan
   kesehatan service dan uji fungsi di bawah.

Build pertama memasang PyTorch CPU dan sentence-transformers; sediakan ruang
disk/memori serta akses internet server. Worker mengunduh model embedding pada
pemrosesan PDF pertama dan menyimpannya di volume cache. Jika server terbatas,
turunkan `WORKER_MAX_JOBS=1` sebelum mencoba proses PDF.

## 4. Uji fungsi setelah deployment

1. Daftar akun baru, masuk mode Guru, buat kelas, dan unggah PDF milik sendiri.
2. Pastikan progres pemrosesan bergerak sampai Siap; periksa log worker bila gagal.
3. Periksa pembagian sumber, buat level, tinjau artikel dan soal, lalu setujui
   materi setiap level serta minimal satu soal per level sebelum menerbitkan.
4. Dengan akun kedua, masuk sebagai Murid, ikuti kelas, buka PDF, kerjakan kuis,
   dan periksa level berikutnya serta leaderboard.
5. Mulai kuis bersama dari akun guru dan ikuti dari akun murid. Periksa WSS di
   browser; ketika koneksi WebSocket terputus, polling harus tetap memperbarui sesi.

Gunakan pendaftaran biasa untuk akun deployment. Seed development membuat akun
uji dengan password yang sudah didokumentasikan; tidak dijalankan otomatis.

## 5. Penyimpanan, pembaruan, dan pemecahan masalah

- Volume `postgres_data` menyimpan data utama, `uploads` menyimpan PDF bersama
  API/worker, `model_cache` menyimpan model, dan `redis_data` menyimpan antrean/state
  sementara dengan AOF. Hasil belajar tetap bersumber dari PostgreSQL.
- Siapkan backup PostgreSQL dan volume upload melalui fasilitas server/Dokploy.
  Jaga identitas project/service Compose saat redeploy agar volume lama digunakan.
  Jangan hapus volume atau memakai `down -v` untuk memperbaiki deployment.
- Sebelum update, tunggu job PDF/generate selesai dan akhiri sesi live. Push branch
  terbaru, buat backup sebelum migrasi, lalu Deploy ulang. Migrasi berjalan saat
  backend start; worker juga harus memakai build terbaru. Rollback image saja
  tidak membatalkan migrasi database: periksa kompatibilitas skema terlebih dahulu.
- **API gagal start:** periksa log migrasi, kekuatan JWT, dan password PostgreSQL.
  Mengganti env password tidak mengganti password akun di volume PostgreSQL lama.
- **Bad Gateway/404:** periksa service/port pada Domains, sertifikat, dan hasil
  Preview Compose. Pastikan Isolated Deployments aktif dan jaringan terpasang.
- **Halaman terbuka tetapi login gagal:** periksa URL API HTTPS hasil build dan
  `CORS_ORIGINS`; jangan memakai `localhost`, `backend:8000`, atau HTTP dari browser.
- **PDF/generate diam:** periksa worker, koneksi Redis, akses unduh model, kunci
  provider, dan log rate limit/timeout. Status frontend saja tidak cukup.
- **WebSocket gagal:** periksa `NEXT_PUBLIC_WS_URL`, sertifikat API, dan dukungan
  upgrade WebSocket proxy. Atur access log proxy agar query token disensor.
- **Permission denied pada volume lama:** volume yang dahulu dibuat root mungkin
  perlu diperbaiki kepemilikannya ke UID 10001 untuk upload/cache; backup dan
  pertahankan isinya, jangan hapus volume.

Rujukan tambahan resmi: [Docker Compose Dokploy](https://docs.dokploy.com/docs/core/docker-compose/example)
dan [Domains untuk Compose](https://docs.dokploy.com/docs/core/docker-compose/domains).
PDF panitia tetap menjadi acuan akses akun dan pembatasan project; jika izin
Compose/dua domain tidak tersedia, konfirmasikan fasilitas tersebut ke panitia.

## Verifikasi persiapan (15 Oktober 2026)

Konfigurasi diuji dengan Docker Compose 5.0.2 menggunakan nilai uji: lima service
valid, tanpa port host/bind mount, frontend tanpa secret backend, build production
non-root, dependensi startup sehat, dan volume persisten. Kelima variabel wajib
ditolak ketika kosong/tidak tersedia. Ruff dan ESLint lolos, serta tiga test
validasi konfigurasi production lolos secara terpisah tanpa database.
Suite backend lengkap dicoba tetapi terhalang PostgreSQL lokal port 5433 yang
tidak berjalan. Build image dan uji server Dokploy belum dilakukan; lakukan
langkah Deploy dan uji fungsi setelah domain, secret, serta akses Compose tersedia.
