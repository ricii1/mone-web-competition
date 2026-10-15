# Pengujian backend dan integrasi — 15 Oktober 2026

Pengujian dilakukan pada commit aplikasi `b77ec6c`, tanpa memperbaiki kode aplikasi.
Kode audit/test dan laporan ditambahkan secara terpisah. Model embedding dan LLM
tidak diunduh atau dipanggil ke jaringan.

## Hasil

| Pemeriksaan | Hasil |
|---|---|
| Suite pytest awal, PostgreSQL aktif tetapi Redis development tidak berjalan | 175 lulus, 1 gagal |
| Suite pytest dengan Redis test terpisah pada port 16379, database Redis 1 | **176 lulus**, 1 peringatan deprecation TestClient/httpx |
| Ruff check | Lulus |
| Ruff format --check | 109 file awal sesuai format; pemeriksaan tambahan harness dilakukan terpisah |
| Migrasi database audit kosong | Alembic `0001 → 0010` berhasil |
| Integrasi HTTP + job worker dipanggil langsung | 75 pemeriksaan tercatat; alur lengkap berhasil |
| Repro kebocoran penjelasan melalui HTTP nyata | Terbukti: 4 dari 5 penjelasan soal fixture memuat teks jawaban benar sebelum submit |
| Repro mock LLM dengan kalimat sumber berulang | Terbukti gagal validasi soal duplikat |
| WebSocket nyata pada API audit | Event Redis diterima pada channel class, material, dan live; handshake tanpa token/tanpa enrollment ditolak |

Peringatan deprecation berasal dari FastAPI/Starlette TestClient dengan versi httpx
yang terpasang, bukan kegagalan assertion. Pengujian ulang menggunakan JWT test
minimal 32 byte agar peringatan secret development tidak menutupi hasil utama.

Perintah suite dari direktori `backend`, memakai environment Python `edumap`:

```bash
REDIS_URL=redis://127.0.0.1:16379/1 \
JWT_SECRET=edumap-test-only-secret-with-at-least-32-bytes \
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONPATH=. \
python -m pytest -p pytest_asyncio.plugin -q
ruff check .
ruff format --check .
```

Variabel `DATABASE_URL` lokal mengarah ke PostgreSQL pada port 5433; conftest
membuat/memakai database **`edumap_test`**. Plugin autoload dimatikan untuk menghindari
plugin ROS dari environment global. Fixture fakeredis menangani pub/sub; alasan
masih memerlukan Redis test nyata untuk satu jalur antrean dibahas di bawah.

## Isolasi data

- PostgreSQL container repo yang sebelumnya berhenti diaktifkan agar test dapat
  dijalankan. Data database development tidak dimigrasi, dihapus, atau di-seed.
- Suite pytest memakai `edumap_test`, terpisah dari database development.
- API audit memakai database **`edumap_audit_20261015`**, dimigrasi dari kosong,
  upload di `/tmp/edumap-full-audit/uploads`, dan hanya bind `127.0.0.1:18000`.
- Redis audit memakai container `edumap-audit-redis-20261015`, bind loopback port
  **16379**. API/browser/integrasi memakai Redis DB 0; suite memakai Redis DB 1.
  Redis development port 6379 tidak dinyalakan atau dipakai menyimpan hasil test.
- Dua akun audit, kelas IPA SD, dan PDF milik sendiri dibuat hanya pada database
  audit. Kredensial/token disimpan di file `/tmp` mode 0600 dan tidak disertakan
  dalam laporan atau repository.
- Audit kode menggunakan database terpisah lagi,
  **`edumap_audit_review_20261015`**, agar reproduksi relasi invalid/race tidak
  merusak fixture untuk pengujian browser.

## Alur integrasi yang berhasil

Harness `/tmp/edumap-full-audit/integration.py` menggunakan HTTP ke API audit asli,
PostgreSQL/Redis audit nyata, parsing/chunking PDF asli, embedding palsu berukuran
384, dan `LLM_MODE=mock`. Job dijalankan langsung dengan identitas job yang
di-enqueue; tidak menjalankan proses worker arq atau mengambil antrean development.

1. Guru membuat kelas; murid ditolak bergabung sebelum published.
2. Guru mengunggah PDF asli buatan sendiri, lima halaman dengan lima bookmark.
   Endpoint menerima upload, menyimpan material, dan membuat job antrean.
3. Job material dengan identitas enqueue memproses PDF menjadi lima bagian dan
   material `ready`. Pratinjau sumber mengembalikan kelima bagian.
4. Endpoint generate membuat identitas job. Job membuat **5 lesson + 1 boss** dan
   **30 soal**, seluruhnya draft. Publish sebelum persetujuan ditolak.
5. Guru menyetujui materi setiap level dan semua soal melalui API, lalu publish.
   Murid belum enrolled ditolak; setelah join, hanya level pertama unlocked.
6. Submit level terkunci ditolak. Submit level pertama dengan jawaban benar
   menghasilkan 100%, level kedua terbuka. Pengulangan dengan nilai 0 tidak
   menurunkan best_score 100 pada eksekusi serial. Leaderboard bernilai 100 dan
   tidak mengandung email.
7. Murid mengunduh PDF melalui Bearer. Isi berawal signature PDF yang benar.
8. Guru membuat sesi live; murid join; guru start; snapshot soal aktif tidak
   memiliki field `correct_answer`; jawaban pertama diterima dan duplikat ditolak.
   Guru menutup soal lalu mengakhiri sesi; skor peserta tersimpan. Progres mandiri
   sebelum/sesudah sesi sama.

Alur ini membuktikan integrasi pada jalur sukses, bukan bahwa semua kontrak aman.
Penjelasan soal murid masih bocor dan race best_score tetap terkonfirmasi pada
audit terpisah. Embedding palsu tidak membuktikan kualitas retrieval model nyata;
LLM mock tidak membuktikan ketepatan generasi provider sesungguhnya.

## Temuan tambahan

Pengujian WebSocket tambahan memakai client Python nyata terhadap API audit:
ketiga endpoint `/ws/classes/{id}`, `/ws/materials/{id}`, dan `/ws/live/{id}`
berhasil handshake dengan JWT pada query sesuai protokol aplikasi dan menerima
JSON event dari channel Redis masing-masing. Koneksi class tanpa token serta murid
ke kelas private yang tidak diikuti ditolak HTTP 403 pada handshake. Bukti tersimpan
di `/tmp/edumap-full-audit/websocket-results.json`. Ini melengkapi uji browser yang
sengaja memblokir WebSocket untuk menguji polling.

### P2 — Penolakan generate kelas contoh bergantung pada Redis

Lokasi: `backend/app/api/routes/levels.py:27`,
`backend/tests/test_owned_classes.py:111`.

Endpoint mengambil pool arq dan melakukan recovery sebelum menjalankan
`request_generation`, yang menolak kelas contoh. Ketika Redis tidak tersedia,
endpoint mengembalikan 503, padahal kelas contoh selalu tidak boleh digenerate
dan test mengharapkan 400. Suite pertama gagal tepat pada kasus tersebut.

Fixture fakeredis untuk pub/sub tidak menggantikan pool arq. Karena itu, suite
yang tampak memakai mock tetap mencoba terhubung ke URL Redis environment lokal.
Suite ulang menunjuk Redis test khusus DB 1 dan seluruh 176 assertion lulus.

Usulan: validasi penolakan yang tidak membutuhkan antrean sebelum menghubungi
Redis, serta mock pool arq secara eksplisit pada test yang tidak menguji antrean.
Jangan mengubah expected status test hanya agar suite hijau.

### P2 — Mode mock gagal membuat soal dari kalimat sumber berulang

Lokasi: `backend/app/rag/mock_llm.py:48`, `:162`,
`backend/app/rag/llm.py:118`.

Reproduksi minimum tanpa jaringan:

```python
from app.rag.mock_llm import _questions

context = (
    "Panas matahari membuat air laut menguap menjadi uap air. "
    "Uap air kemudian naik ke langit dan menjadi dingin. "
) * 4
_questions(context, 5)
```

Hasil: `GeneratedQuestionsOutput` menolak `question texts must be nonblank and
different within a level`. `_sentences` mempertahankan kalimat duplikat dan
perputaran target baru terjadi setelah seluruh list kalimat, sehingga lima soal
pertama dapat mengulang pertanyaan yang sama. Jalur mock berada sebelum loop
retry provider; validasi ini langsung menggagalkan job.

Bug ditemukan pada percobaan integrasi pertama dengan paragraf PDF berulang.
Percobaan kedua memakai setidaknya lima kalimat berbeda untuk membuktikan jalur
sukses secara terpisah; kode mock dan test lama tidak diubah untuk menutupi bug.

Usulan: deduplikasi kandidat kalimat/pertanyaan dan pilih target berbeda secara
terbatas; jika sumber tidak memungkinkan lima soal unik, beri pesan kegagalan yang
jelas. Pertahankan validasi soal unik dan grounding sumber.

Enam masalah lain dengan bukti PostgreSQL, termasuk tiga P1, ada di
[audit kode](testing-code-audit.md).

### P2 — Seed development masih memakai materi SMA

Lokasi: `backend/app/db/seed.py:36`, `:81`, dan
`backend/app/services/example_class.py:33`.

Seeder default membuat kelas `Biologi Sel Kelas XI` serta draft `Hukum Newton`,
bertentangan dengan ketentuan konten contoh/seed tingkat SD di AGENTS.md.
Kelas contoh otomatis saat daftar sudah memakai Siklus Air SD; masalah ini khusus
jalur seed development. Audit tidak menjalankan seed lama, sehingga seluruh fixture
browser/integrasi tetap memakai IPA SD. Usulan: ganti konten seed ke topik SD dan
selaraskan README pada perubahan terpisah; data development tidak ditulis ulang
secara otomatis.

## Batas pengujian

Belum menguji provider LLM/embedding asli, beban murid serentak skala sekolah,
build/run image Docker production, restart worker arq nyata ketika sedang memproses,
backup/restore volume deployment, ngrok/Cloudflare, DNS/TLS, atau server panitia.
Uji timer/duplikat/otorisasi/cache Redis terdapat pada suite pytest; alur integrasi
di atas tidak menggantikan seluruh test gangguan tersebut.
