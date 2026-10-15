# Status perbaikan audit — 15 Oktober 2026

Temuan pada laporan audit awal sudah diperbaiki dan diverifikasi ulang. Angka
audit awal tetap dipertahankan sebagai catatan reproduksi; dokumen ini mencatat
hasil setelah patch.

| Temuan awal | Perbaikan dan bukti |
|---|---|
| Penjelasan/jawaban kuis bocor sebelum submit | Respons murid tidak lagi memuat `explanation`; test respons HTTP/komponen memastikan jawaban benar dan penjelasan tidak bocor. Penilaian server tetap sama. |
| Prasyarat level lintas kelas, self-reference, siklus; submit bersamaan menurunkan skor | Mutasi graph diserialkan dengan lock class dan memvalidasi kelas/siklus. Progress memakai insert konflik aman dan row lock. Test Postgres multi-thread memastikan `best_score` tidak turun. |
| Delete level/soal gagal FK atau menghapus riwayat | Penghapusan yang punya progress, attempts, atau sesi aktif ditolak 409; level kosong dapat dihapus dan graph ditautkan ulang. Test meliputi referensi lama dan kegagalan FK bersamaan. |
| Pertanyaan manual tidak valid lolos; publish tidak menolak baris lama yang rusak | Opsi divalidasi saat create, update terhadap state efektif, dan publish. Test mencakup duplikasi serta jawaban yang bukan opsi. |
| Gagal pub/sub membalik generate sukses menjadi gagal | Notifikasi Redis best effort dengan log; error generate asli tetap dipertahankan. Test memaksa kegagalan notifikasi pada awal, tengah, dan akhir job. |
| Penolakan class contoh bergantung pada Redis | Endpoint memeriksa class contoh sebelum membuat pool arq; test memastikan pool tidak dipanggil. |
| Mode LLM mock membuat soal duplikat dari kalimat berulang | Kandidat dan pertanyaan dideduplikasi; sumber yang tidak cukup menghasilkan error yang jelas. Test mencakup kasus berulang dan sumber terlalu pendek. |
| Seed menggunakan materi SMA | Seed contoh baru memakai IPA SD dan tetap idempotent; contoh lama di database tidak ditulis ulang. |
| Error frontend tertelan, 422 menjadi `[object Object]`, halaman sumber mulai dari nol | Error API dinormalisasi dengan pesan aman Bahasa Indonesia; halaman sumber ditampilkan mulai 1. Halaman guru mempertahankan state gagal dan menyediakan retry. |
| Akses keyboard, tab, target sentuh, header HP, demo publish | Input upload dapat diakses keyboard, tab editor memakai panah/Home/End, kontrol minimum 48 px, header pas sampai 320 px, dan demo mensyaratkan persetujuan materi serta soal. Browser: 14 alur perbaikan dan 12 pemeriksaan branding/responsif lulus. |
| Framework/dependency runtime lama dan font eksternal | Next.js 16.4.1, React 19.3.1, Node 24; build produksi standalone lulus. Font lokal dan metadata/branding Peta Pintar terpakai. `npm audit --omit=dev`: 0 vulnerability. |
| Build dependency advisory | Full `npm audit` masih menunjukkan 7 temuan high transitif yang berasal dari `braces@3.0.3` pada jalur tooling development (Tailwind/ESLint). Upstream belum merilis patch; scanner menyarankan migrasi major Tailwind 4. Paket itu tidak disertakan pada standalone production. Lihat [laporan dependency](testing-dependencies-audit.md). |

## Verifikasi terbaru

- Backend: **207 pytest lulus**; Ruff lint/format bersih. JUnit: `/tmp/edumap-full-audit/backend-fixed-branded-results.xml`.
- Frontend: **21 test lulus**, `npm run typecheck`, `npm run lint`, dan build produksi Next.js lulus dengan Node 24.
- Integrasi: **82 pemeriksaan** melewati upload dan parsing PDF, job worker, generate/review/publish, join, quiz/progres, leaderboard, akses PDF, live, serta validasi graph dan penghapusan. Bukti sementara: `/tmp/edumap-full-audit/integration-fixed-results.json`.
- Browser: 14 skenario UX nyata dan 12 pemeriksaan nama/viewport 320–640 px; 0 page error pada alur perbaikan.
- Compose production tetap terdiri dari frontend, backend, worker, PostgreSQL, dan Redis. Deploy ke Dokploy/tunnel/domain panitia belum dijalankan.

Database pengujian terpisah dari development. Model embedding dan LLM dimock kecuali parser PDF; integrasi memakai PostgreSQL/Redis lokal khusus audit. Hasil ini tidak mengukur provider AI asli atau beban produksi.
