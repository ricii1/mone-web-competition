# Audit kode backend dan deployment — 15 Oktober 2026

Audit read-only pada kode aplikasi, terutama perubahan `4ffb6d9` dan `b77ec6c`.
Tidak ada perubahan kode aplikasi, migrasi, dependency, data development, atau database
`edumap_test`. Laporan ini melengkapi hasil suite dan uji browser yang dijalankan agent lain.

## Metode dan batas bukti

- Telusur route → service → schema/model dan test terkait: otorisasi, upload/PDF,
  worker/RAG, progres, leaderboard, sesi live, penghapusan, serta konfigurasi Docker.
- Harness awal memakai SQLite di memori dengan FK aktif. Seluruh skenario kemudian
  diulang terhadap PostgreSQL pada database baru **`edumap_audit_review_20261015`**,
  dimigrasikan Alembic `0001 → 0010`. Database development dan `edumap_test` tidak disentuh.
- Harness reusable: `backend/scripts/audit_regressions.py`; menolak menulis bila nama
  database tidak diawali `edumap_audit_review_`. Gunakan `DATABASE_URL` database audit
  yang sudah dimigrasikan dan `PYTHONPATH=backend`, lalu jalankan skrip dengan Python
  environment backend. Akun/kelas bukti sengaja ditinggalkan di database audit tersebut.
- Tidak ada embedding, panggilan LLM, atau service Redis development. Uji notifikasi
  worker menggunakan mock database/LLM dan kegagalan pub/sub terkendali.
- Race skor dibuktikan dua cara: dua session dengan instance lama, kemudian dua thread
  request PostgreSQL yang benar-benar tumpang tindih. Barrier dipasang setelah pembacaan
  asli `get_or_create_progress`; request skor 80 baru dilanjutkan setelah request 100
  commit. Ini menjadwalkan interleaving yang mungkin terjadi, tanpa mengubah logika
  perhitungan maupun UPDATE aplikasi. Nilai akhir kedua skenario adalah 80.
- Semua skenario di bawah berhasil direproduksi. Tingkat P1 = integritas/isolasi atau
  kebocoran jawaban; P2 = perilaku gagal pada alur normal atau pemulihan gangguan.

## Temuan terkonfirmasi

### P1 — Penjelasan jawaban dikirim sebelum submit

Lokasi: `backend/app/schemas/question.py:14`,
`backend/app/api/routes/questions.py:42`.

Respons murid `GET /api/v1/levels/{id}/questions` memang menghilangkan
`correct_answer`, tetapi masih menyertakan `explanation`. Prompt soal secara eksplisit
meminta penjelasan mengapa jawaban benar. Dengan soal contoh jawaban B, serializer
menghasilkan `"explanation": "Karena B."` sebelum submit. Murid dapat membaca jawaban
melalui respons jaringan, termasuk soal yang sedang dipakai kuis live melalui endpoint
soal biasa jika sudah ter-enroll.

Perbaikan minimum: keluarkan penjelasan dari respons soal murid; pertahankan untuk guru
dan `QuestionResult` setelah submit. Tambahkan test yang memeriksa kedua field jawaban
**dan penjelasan** tidak bocor. Test saat ini di `test_level_lesson.py` hanya melarang
field `correct_answer`.

### P1 — Prasyarat lintas kelas dan siklus diterima

Lokasi: `backend/app/services/level_service.py:69`,
`backend/app/services/progress_service.py:44`.

PATCH level memeriksa pemilik level yang diedit, tetapi langsung menyimpan UUID
prasyarat tanpa memastikan kelas, menolak self-reference, atau mendeteksi siklus.
Harness berhasil menyimpan level kelas A yang bergantung pada level kelas B, lalu
mengubahnya menjadi bergantung pada dirinya sendiri. FK hanya memastikan ID ada.

Dampak: jalur belajar dapat terkunci permanen; `unlock_dependents` mengambil seluruh
kelas sehingga dapat membuat progres di kelas lain. Lebih jauh, guru bisa mengaitkan
level miliknya ke level kelas lain, lalu pemilik kelas lain ditolak menghapus kelas
karena pemeriksaan referensi lintas kelas di `resource_deletion.py`. Guard penghapusan
menahan kerusakan, tetapi tidak mencegah pembentukan hubungan invalid dari API.

Perbaikan minimum: validasi prasyarat ada di kelas yang sama, bukan diri sendiri dan
bukan keturunan; pastikan query unlock juga dibatasi kelas. Tambahkan test PATCH lintas
pemilik/kelas, self-reference, siklus, dan pembatasan unlock.

### P1 — Submit bersamaan dapat menurunkan best_score

Lokasi: `backend/app/services/progress_service.py:53`.

`max(progress.best_score, score_percent)` dihitung di Python tanpa row lock/UPDATE
atomik. Dua request bisa memegang instance ORM dengan nilai awal 70. Harness dua
session memuat nilai tersebut, session A menyimpan 100, session B menyimpan hasil
80 dari instance lamanya; nilai akhir database **80**, bukan 100. Repro lanjutan pada
dua thread PostgreSQL menghasilkan nilai akhir yang sama dengan pembacaan kedua
request disinkronkan sebelum commit request 100. Ini bukti race, bukan hanya perkiraan
berdasarkan kode.

Dampak: melanggar aturan skor terbaik dan menurunkan leaderboard. Test
`test_best_score_keeps_highest` hanya memeriksa dua panggilan serial dalam satu session.

Perbaikan minimum: serialkan pembacaan/perubahan progress dengan row lock, atau UPDATE
atomik `greatest(best_score, :score)` beserta transisi status/timestamp yang konsisten.
Tambahkan regresi dua session PostgreSQL dan pastikan unlock tetap idempoten.

### P2 — Hapus level/soal yang sudah dipakai menghasilkan 500

Lokasi: `backend/app/services/level_service.py:101`,
`backend/app/services/question_service.py:78`.

`delete_question` langsung DELETE tanpa menangani `attempts.question_id`.
`delete_level` juga tidak menangani `progress.level_id`, `attempts`, prasyarat level
lain, dan relasi `live_sessions.level_id`. Semua FK tersebut tidak memakai cascade.
Harness membuktikan `IntegrityError` ketika menghapus soal dengan satu attempt serta
level dengan satu progress. Exception tidak diterjemahkan menjadi pesan HTTP yang jelas.

Dampak: tombol hapus berhenti bekerja setelah kelas dipakai; kegagalan juga terjadi
pada level draft di tengah rantai level karena prasyarat level berikutnya.

Perbaikan minimum: tentukan aturan aman untuk resource yang sudah punya riwayat—tolak
409 dengan pesan jelas; untuk draft yang boleh dihapus, tangani prasyarat/relasi dalam
satu transaksi. Hindari menghapus riwayat nilai diam-diam. Tambahkan test level rantai,
progres, attempt, serta sesi live. Test penghapusan kelas lengkap tidak menguji endpoint
hapus level/soal ini.

### P2 — Soal approved dapat memiliki jawaban yang tidak ada di opsi

Lokasi: `backend/app/schemas/question.py:24`,
`backend/app/services/question_service.py:66`.

Validasi AI lebih ketat daripada tambah/edit guru. Schema manual menerima list opsi
kosong/duplikat atau jawaban yang bukan opsi. Harness mengubah soal approved
`options=[A,B,C,D], correct_answer=B` menjadi `options=[C,D]` dan tetap approved.

Dampak: murid tidak dapat menjawab benar; pada live, endpoint answer menolak jawaban
di luar opsi, sehingga poin benar benar-benar tidak mungkin didapat. Pemeriksaan publish
hanya menghitung soal approved dan tidak memeriksa konsistensi opsi-jawaban.

Perbaikan minimum: validasi gabungan nilai sesudah PATCH (bukan hanya field yang dikirim)
serta saat create/approve: empat opsi nonkosong unik dan jawaban termasuk di dalamnya.
Tambahkan test edit opsi tanpa mengirim correct_answer dan sebaliknya.

### P2 — Gangguan notifikasi dapat mengubah generate sukses menjadi gagal

Lokasi: `backend/app/worker/jobs/generate_content.py:231`,
`backend/app/worker/jobs/generate_content.py:243`.

Notifikasi generate tidak memiliki perlindungan seperti job material dan sesi live.
Harness menjalankan satu chunk dengan LLM/database mock, lalu membuat hanya event
`generation_progress:done` gagal. Urutan perubahan status yang tercatat adalah
`generating → done → failed` karena exception pub/sub masuk handler kegagalan job.
Gangguan event sebelumnya juga menghentikan generate padahal data sudah disimpan.

Dampak: status UI salah, pekerjaan terhenti karena fitur notifikasi, dan percobaan ulang
bisa mengganti draft yang sebenarnya sudah selesai. Polling tidak menyelamatkan pipeline
karena status sumber kebenaran justru diubah menjadi failed.

Perbaikan minimum: pengiriman semua event generate bersifat best-effort dengan logging,
termasuk event `level_created`; status gagal hanya untuk kegagalan pekerjaan sebenarnya.
Tambahkan test sukses saat publish gagal pada awal/tengah/akhir pipeline.

## Temuan integrasi suite yang dikonfirmasi agent utama

`backend/app/api/routes/levels.py:27` menghubungi arq sebelum menolak generate kelas
contoh. Ketika Redis tidak tersedia, permintaan yang seharusnya deterministik 400 berubah
menjadi 503. Suite awal agent utama melaporkan 175 pass/1 fail pada
`test_owned_classes.py::test_example_class_cannot_be_generated`; fakeredis pub/sub tidak
menggantikan pool arq yang terpisah. Perbaikan minimum: cek penolakan yang tidak membutuhkan
antrean lebih awal, dan mock pool arq untuk test yang tidak menguji integrasi antrean.
Ini bukan hasil eksekusi suite oleh agent audit ini.

## Deployment dan area tanpa temuan baru

- Dokploy Compose memisahkan service, menyimpan Postgres/Redis/uploads/cache model pada
  volume, menunggu migrasi melalui health backend, dan memakai frontend standalone serta
  pengguna non-root. File Compose tersebut memang membutuhkan tipe service Compose;
  satu Application hanya membangun satu Dockerfile dan tidak menjalankan seluruh stack.
- Belum dilakukan build image/running Docker produksi, pengukuran resource worker CPU,
  pengujian tunnel eksternal, TLS, DNS/domain, atau keberlanjutan volume Dokploy.
- Telusur tidak menemukan bukti baru kebocoran JWT secret lewat frontend, pemanggilan
  parsing/embedding/LLM di route, akses PDF lintas kelas, atau jawaban benar langsung pada
  snapshot soal live aktif. Ini kesimpulan terbatas pada kode yang ditinjau, bukan jaminan
  bebas bug/security.
- Pipeline sumber panjang memiliki batas bagian/putaran dan validasi Pydantic; test
  pengurutan, sumber awal–tengah–akhir, retry, serta batas PDF tersedia. Audit ini tidak
  menilai kebenaran jawaban model nyata atau menjalankan model/jaringan.

## Keluaran harness

```text
CONFIRMED student question response leaks explanation: Karena B.
CONFIRMED cross-class prerequisite accepted
CONFIRMED self prerequisite accepted
CONFIRMED approved question allows no correct option
CONFIRMED delete attempted question fails: IntegrityError
CONFIRMED delete enrolled level fails: IntegrityError
CONFIRMED generate done notification failure flips persisted status: ['generating', 'done', 'failed']
CONFIRMED overlapping quiz sessions lose best score: 100 then stale 80 persisted 80
CONFIRMED concurrent PostgreSQL quiz requests lower best_score from 100 to 80
```

Validasi skrip audit: `ruff check` dan `ruff format --check` lolos. Semua sembilan
baris konfirmasi di atas direproduksi pada database PostgreSQL terpisah. Skrip ini
bukan test suite regresi yang lulus sesudah perbaikan: assertion membuktikan bug saat
audit; perbaikan yang benar harus membuat assertion bug tersebut gagal.
