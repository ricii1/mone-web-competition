# Audit DevOps: keamanan dan performa

Tanggal: 11 Oktober 2026. Audit sumber lokal; tidak mengubah kode aplikasi, membaca `.env`, mengirim permintaan ke layanan eksternal, atau melakukan pemindaian jaringan. Prioritas P1 berarti perlu ditangani sebelum aplikasi dipakai melalui jaringan publik; P2 berarti pengerasan atau optimasi berikutnya. Temuan terkonfirmasi berarti terlihat di kode/config; keterjangkauan layanan dari Internet dan besarnya dampak performa belum diukur.

## Temuan prioritas

| Prioritas | Bukti terkonfirmasi | Dampak | Solusi minimal dan verifikasi |
|---|---|---|---|
| P1 | `docker-compose.yml:19` dan `:31` mempublikasikan PostgreSQL/Redis tanpa alamat loopback. Redis tidak dikonfigurasi autentikasi; password PostgreSQL memiliki fallback contoh di `:16`. | Host jaringan yang dapat menjangkau port berpotensi mengubah antrean, state kuis, atau cache; risiko DB bila fallback dipakai. Firewall aktual belum diperiksa. | Bind `127.0.0.1:5433:5432` dan `127.0.0.1:6379:6379` untuk native development; hilangkan port DB/Redis pada deployment Docker penuh. Wajibkan password produksi. Uji koneksi dari jaringan yang seharusnya ditolak. |
| P1 | `backend/app/realtime/ws.py:65` membuka session DB, melakukan query, lalu baru menutupnya di `:82` setelah forwarding berakhir. Pola sama di `:42` dan `:87`. | Transaksi baca menahan koneksi DB sepanjang WebSocket; kumpulan koneksi dapat habis saat satu kelas tersambung. `SessionLocal` memakai pool default (`backend/app/db/session.py:8`). | Selesaikan auth/otorisasi dalam scope DB pendek, simpan ID/nilai yang diperlukan, tutup DB sebelum `accept`/forwarding. Uji banyak koneksi idle dan ukur checkout pool, bukan menaikkan pool sebagai perbaikan utama. |
| P1 | `frontend/app/student/live/page.tsx:67` dan `frontend/app/teacher/classes/[classId]/live/page.tsx:43` memanggil `connectRealtime` tanpa callback `poll`. `backend/app/schemas/live_session.py:12` hanya mengembalikan metadata sesi. | Kuis bergantung pada WebSocket; koneksi gagal atau event terlewat membuat murid kehilangan soal. Reconnect juga tidak mengambil soal aktif/deadline. Bertentangan dengan fallback wajib AGENTS.md. | Tambahkan snapshot REST berotorisasi: soal aktif tanpa jawaban benar, deadline server, status jawaban sendiri, hasil soal yang sudah ditutup. Berikan callback polling dan ambil snapshot setelah connect/reconnect. Uji dengan WebSocket dinonaktifkan dan reconnect di tengah soal. |
| P1 | `backend/app/services/live_session_service.py:159` memakai `HEXISTS`, kemudian `HSET` di `:165` sebagai dua operasi. Reproduksi offline menerima dua submit serentak untuk murid/soal yang sama. | Jawaban pertama bisa ditimpa dan aturan penolakan jawaban ganda gagal. | Minimal gunakan `HSETNX` dan tolak jika hasilnya false; untuk pergantian soal/deadline gunakan operasi atomik Redis yang juga memeriksa ID soal aktif. Tambahkan test konkurensi, termasuk submit bersamaan dengan penutupan soal. |
| P1 | `backend/app/services/material_service.py:18` membaca seluruh file sebelum pengecekan batas ukuran di `:20`; `:30` menulis disk secara sinkron dalam fungsi async. | Upload besar memakan RAM sebelum ditolak, sementara penulisan disk dapat menahan event loop API. MIME dari client menjadi satu-satunya pemeriksaan awal. | Baca bertahap dengan akumulasi ukuran dan hentikan di batas; gunakan temporary file, cleanup saat gagal, offload I/O blocking. Tambahkan batas body di ingress. Validasi signature PDF ringan; parsing tetap di worker. Uji file melebihi batas tanpa mengalokasikan isi penuh. |
| P1 | `backend/app/services/live_session_service.py:23` menetapkan TTL 50 detik; soal aktif disimpan dengan TTL tersebut di `:114`. `close_current_question` menolak ketika key hilang (`:175`). `end_session` menghapus jawaban tanpa menyimpannya (`:256`). | Guru kembali setelah >50 detik tidak dapat melanjutkan lewat `next`; jawaban yang belum ditutup hilang karena TTL atau tombol akhiri. Ini tidak memenuhi aturan sesi dapat dilanjutkan setelah guru terputus dan hasil disimpan saat soal ditutup. | Pisahkan deadline jawab 20 detik dari masa simpan state sesi; simpan jawaban sebelum akhir sesi. Gunakan penutupan idempoten, simpan hasil ke Postgres sebelum cleanup, dengan retensi Redis yang cukup untuk reconnect. Uji jeda guru melebihi TTL dan tombol akhiri sebelum `next`. |
| P2 | `backend/app/api/routes/auth.py:44` tidak memiliki throttle login; register juga tanpa throttle. `backend/app/schemas/auth.py:8` tidak memberi batas nama/password. Tidak ditemukan middleware pembatas request di `backend/app/main.py`. | Percobaan password berulang dan registrasi massal membebani hashing serta membuat class contoh. String password sangat panjang juga perlu ditangani sesuai batas bcrypt. | Gunakan counter Redis yang sudah tersedia untuk batas per IP dan akun, respons 429, batas panjang field dan validasi password. Uji threshold dan reset; pastikan pembatasan tidak memakai pesan yang membuka apakah akun ada. Tidak dilakukan brute force terhadap akun nyata. |
| P2 | `backend/app/services/leaderboard_service.py:85` membangun ulang ranking seluruh kelas setiap best score berubah. Rebuild melakukan `DELETE` lalu `ZADD` di `:59`–`:65`. | Pekerjaan agregasi tumbuh dengan peserta/progres; request paralel dapat melihat cache kosong atau berlomba menulis snapshot lama. Belum ada pengukuran latency. | Mulai dengan penggantian cache atomik dan test concurrent read/rebuild. Ukur SQL/query duration sebelum optimasi inkremental satu murid; pertahankan tie-break dan rebuild dari Postgres. |
| P2 | `docker-compose.yml:56` menjalankan `uvicorn --reload`, `:90` memakai `npm run dev`, bind mount kode aktif; Dockerfile menjalankan default root dan backend memasang dependency dev. | Konfigurasi development bukan baseline deployment: overhead watcher/kompilasi, permukaan tooling, dan hak proses lebih besar. | Pertahankan Compose development; buat konfigurasi deployment tanpa reload/bind mount, frontend build+start, user non-root, dependency runtime. Jangan mengganti stack. Ukur cold/warm response serta bundle produksi sesudah build. |

## Pengerasan tambahan yang perlu diverifikasi

- `frontend/lib/auth.ts:4` menyimpan JWT dalam localStorage dan `frontend/lib/realtime.ts:94` memasukkannya dalam query URL WebSocket. Ini memperbesar dampak XSS dan potensi token tercatat di access log. **Belum ditemukan exploit XSS**; renderer Markdown memakai elemen React dan pencarian tidak menemukan `dangerouslySetInnerHTML`. Solusi awal: redaksi query/token di logging ingress, TLS/WSS produksi, header keamanan dan evaluasi CSP (`frontend/next.config.js:1` belum menetapkan header). Perpindahan cookie HttpOnly memerlukan desain auth/CSRF yang eksplisit, bukan perubahan diam-diam.
- Live WebSocket (`backend/app/realtime/ws.py:96`) mengizinkan semua anggota kelas, sedangkan REST snapshot (`backend/app/api/routes/live_sessions.py:62`) mensyaratkan peserta sesi. Pertimbangkan menyelaraskan akses peserta dan host supaya event sesi tidak bisa diamati anggota yang belum masuk sesi. JWT diverifikasi saat handshake saja; tidak ada revalidasi expiry sepanjang koneksi. Kebutuhan pembatalan sesi/token perlu disepakati sebelum implementasi.
- `backend/app/services/live_session_service.py:183` mengambil jawaban lalu memperbarui poin sebelum menghapus Redis. Dua permintaan `next` bersamaan berpotensi menggandakan attempts/poin; ini **dugaan berdasarkan urutan operasi, belum direproduksi**. Gunakan klaim penutupan atomik per soal dan operasi persistence idempoten; uji dua penutupan serentak dan retry setelah crash.

## Pemeriksaan yang dilakukan

- Membaca seluruh AGENTS.md dan meninjau Compose/Dockerfile, auth, upload, WebSocket/pubsub, live class, leaderboard, frontend realtime serta konfigurasi frontend.
- `/home/ricii/miniconda3/envs/edumap/bin/ruff check .` di backend: **lulus**.
- `npm run lint` di frontend: **lulus**.
- Reproduksi race jawaban: script `/tmp/devops-race-check.py` memanggil fungsi `submit_answer` asli dengan fakeredis dan barrier pada `HEXISTS`. Hasil: `Concurrent submissions accepted: 2`, `Stored answers: 1`. Tidak memakai Postgres/Redis development, API eksternal, atau model embedding.
- Suite pytest penuh dijalankan agent utama: **89 passed, 81 warnings, 29,89 detik**. Percobaan pertama terhalang koneksi DB oleh sandbox; rerun dengan eskalasi berhasil. Test memakai DB terpisah sesuai fixture. Ada peringatan key HMAC JWT runtime test berukuran 23 byte, lebih pendek dari rekomendasi library 32 byte; nilai secret tidak dicatat. Verifikasi bahwa deployment memakai key acak minimal 32 byte, tanpa menyimpulkan konfigurasi production dari warning test.
- Audit ini tidak menjalankan benchmark/load test, audit CVE jaringan, atau pengujian penetrasi production. Tidak ada klaim aplikasi sudah aman hanya karena lint dan test lulus.

## Urutan implementasi dan kriteria selesai

1. Tutup eksposur DB/Redis dan lepaskan koneksi DB sebelum streaming WebSocket.
2. Perbaiki lifecycle kuis: snapshot REST + fallback, submit atomik, retensi/penutupan idempoten dan persistence sebelum cleanup.
3. Batasi upload serta request auth; siapkan konfigurasi deployment yang terpisah dari development.
4. Ukur p95 API/DB, jumlah koneksi DB, RAM upload, bundle dan waktu interaksi murid pada perangkat lambat; baru optimalkan cache/generate berdasarkan hasilnya.

Perubahan logika inti harus dibuktikan dengan pytest ber-DB terpisah dan fakeredis/mock model, ruff, serta lint frontend untuk area yang disentuh. Temuan di sini berupa hasil audit dan solusi yang dapat dikerjakan; kode aplikasi belum diperbaiki oleh agent audit.


## Status perbaikan — 11 Oktober 2026

Perubahan kode untuk temuan terkonfirmasi sudah diterapkan: loopback port DB/Redis,
penutupan DB sebelum streaming WebSocket, pembatas body/upload bertahap, submit
live atomik dengan pemeriksaan pergantian soal, retensi state 24 jam, persistence
saat mengakhiri sesi, snapshot REST + polling/reconnect, serta serialisasi kontrol
dan pencegahan penilaian ulang. Login/register dibatasi, input password/nama dibatasi.

Cache leaderboard kini diganti atomik dengan versi untuk menolak snapshot lama;
tie mikrodetik tidak lagi dicampur ke floating-point score. Pemeriksaan publish
menghindari query per level. Limiter LLM menghitung semua retry dan mengambil slot
lagi setelah menunggu. Generate mempunyai pelacakan job, kompensasi enqueue gagal,
dan pemulihan job tertinggal melalui migrasi 0008.

Override production dan Dockerfile menyediakan runtime non-root, build frontend
standalone, tanpa reload/bind mount kode/port DB-Redis. Production menolak secret
JWT pendek/placeholder serta password DB contoh. Header nosniff, anti-framing dan
referrer policy ditambahkan. Token localStorage/query WebSocket tetap memakai
kontrak auth sebelumnya; deployment perlu HTTPS/WSS dan redaksi log query token.

Verifikasi: 120 pytest lolos; Ruff lint/format, ESLint, TypeScript, dua test realtime,
dan build Next.js lolos. Server standalone diuji pada port sementara: HTTP 200
untuk halaman live dan header keamanan benar. Konfigurasi Compose production
valid; migrasi 0008 diterapkan pada database lokal. Image Docker production penuh
belum dibangun dan tidak ada load test atau pengujian penetrasi production.

Batasan: state live yang belum ditutup masih mengikuti TTL 24 jam dan memerlukan
Redis; lock kontrol Redis memiliki lease 60 detik untuk operasi singkat, dengan
lock baris Postgres melindungi persistence. Deployment production belum diaktifkan. Port loopback development sudah diterapkan
pada container DB/Redis dengan volume database dipertahankan; API dan worker direstart
setelah pemeriksaan tidak ada job aktif. API sehat dan schema snapshot baru tersedia. Usulan perubahan
aturan boss, paralelisme LLM dan fitur baru pada backlog tetap menunggu keputusan
produk atau pengukuran, sesuai AGENTS.md.
