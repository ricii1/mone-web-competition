# Hasil pengujian menyeluruh — 15 Oktober 2026

> **Status setelah perbaikan:** isu aplikasi yang tercantum di audit awal telah
> ditangani dan diuji ulang. Lihat [status perbaikan](testing-fixes.md) untuk
> rincian bukti terbaru. Dependency development masih memiliki advisory upstream
> yang belum ditambal; dependency runtime tidak melaporkan temuan.

Tiga agent memeriksa UX browser, kode backend, serta frontend/komponen secara
paralel. Agent utama menjalankan suite backend, integrasi HTTP/job, transport
WebSocket, validasi Compose, dan pemeriksaan dependency. Kode aplikasi tidak
diubah; hasil audit, harness reproduksi, dan 12 test frontend baru ditambahkan.

## Hasil terukur

| Area | Hasil | Laporan |
|---|---|---|
| Backend | 176 pytest lulus dengan Redis test khusus; Ruff lint/format lulus | [Backend/integrasi](testing-backend-audit.md) |
| Frontend/komponen | 16 test lulus: 7 API, 5 render React asli, 4 realtime; ESLint dan TypeScript lulus | [Frontend](testing-frontend-audit.md) |
| Browser | 26 skenario selesai: landing/auth 16, akun/kelas/kuis 7, live polling 3; 13 observasi tambahan; 0 JS pageerror | [UX](testing-ux-audit.md) |
| Integrasi | PDF 5 section → 6 level/30 soal draft → approve/publish → join/kuis/unlock/leaderboard → PDF → live; 75 pemeriksaan tercatat | [Backend/integrasi](testing-backend-audit.md) |
| WebSocket nyata | Ketiga channel class/material/live menerima event dari Redis; tanpa token dan tanpa enrollment ditolak | [Backend/integrasi](testing-backend-audit.md) |
| Migrasi | Database audit kosong berhasil `0001 → 0010` | [Backend/integrasi](testing-backend-audit.md) |
| Deployment | Compose valid: 5 service, volume persisten, tanpa port host/bind mount/env backend di frontend; lima env wajib dijaga | [Audit kode](testing-code-audit.md) |
| Build produksi | Terhalang unduh Google Fonts; build diagnostik font mock lolos, bukan bukti build asli | [Frontend](testing-frontend-audit.md) |
| Dependency | npm menandai 3 package: 1 critical + 2 high; dampak aplikasi perlu dinilai. Requirement Python konsisten setelah mengisolasi environment | [Dependency](testing-dependencies-audit.md) |

## Prioritas perbaikan

Tiga **P1 terkonfirmasi**, dengan reproduksi PostgreSQL terpisah dan bukti di
[audit kode](testing-code-audit.md):

1. Penjelasan soal murid dikirim sebelum submit dan dapat memuat jawaban benar.
   HTTP audit nyata menemukan teks jawaban pada 4 dari 5 penjelasan fixture.
2. Edit prasyarat menerima hubungan lintas kelas dan self-reference/siklus, sehingga
   dapat merusak jalur unlock dan menghambat penghapusan kelas lain.
3. Dua submit bersamaan dapat menurunkan `best_score` dari 100 menjadi 80.

Temuan fungsional berikutnya: hapus soal/level yang sudah direferensikan gagal FK,
soal manual approved dapat memiliki jawaban di luar opsi, notifikasi gagal dapat
mengubah generate sukses menjadi failed, penolakan kelas contoh bergantung pada
Redis, serta mode mock gagal pada kalimat sumber berulang.
Seed development lama juga masih membuat kelas Biologi Sel Kelas XI meskipun
konten contoh proyek diwajibkan tingkat SD; fixture audit memakai IPA SD.

Temuan frontend/UX: halaman guru menelan error API, upload tidak dapat dijangkau
keyboard, header overflow pada 360 px, error 422 menjadi `[object Object]`, halaman
sumber dimulai dari nol, tab editor belum mendukung tombol panah, demo guru masih
mengajarkan aturan publish lama, dan sebagian target tombol hanya 44 px.

Dependency Next.js yang ditandai scanner memerlukan penanganan sebelum deployment
publik. Ini temuan versi/dependency; audit tidak mengklaim eksploitasi berhasil.

## Isolasi, bukti, dan batas

Suite memakai `edumap_test`. Akun/PDF/API browser berada di
`edumap_audit_20261015`; reproduksi bug memakai
`edumap_audit_review_20261015`. Redis audit terpisah pada loopback port 16379,
dengan DB berbeda untuk suite dan browser. Data development tidak dihapus atau
dimigrasi. LLM mock dan embedding palsu dipakai untuk seluruh pengujian otomatis.
Setelah audit, Next/Chrome/API audit dan Redis audit dihentikan. PostgreSQL repo
dikembalikan ke keadaan berhenti seperti sebelum tugas. Database/volume dan
artefak bukti dipertahankan; tidak ada service audit yang masih membuka port.

Harness yang dipertahankan di repo:

- `backend/scripts/audit_regressions.py`: reproduksi bug saat ini dengan guard
  nama database; assertion-nya mengonfirmasi bug, bukan suite regresi yang seharusnya
  dipertahankan setelah bug diperbaiki.
- `frontend/tests/components.test.cjs`, `api.test.cjs`, dan `realtime.test.cjs`:
  test perilaku yang dapat dijalankan ulang lewat `node --test tests/*.test.cjs`.

Screenshot/harness browser dan hasil JSON di `/tmp/edumap-audit-ux`; hasil integrasi,
JUnit suite, dan scanner di `/tmp/edumap-full-audit`. Artefak `/tmp` bersifat sementara;
laporan di repo menyimpan hasil, cara reproduksi, dan batas bukti. Token/secret tidak
disalin ke repo.

Belum diuji: kualitas provider AI/embedding asli, beban skala sekolah, perangkat
fisik/screen reader lengkap, build image production, restart worker nyata saat job
aktif, backup/restore deployment, tunnel eksternal, DNS/TLS, dan server panitia.
Koneksi WebSocket berhasil diuji dari client Python lokal; browser live sengaja
memblokir WebSocket untuk membuktikan fallback polling.

Test yang lulus tidak meniadakan temuan audit. Perbaikan aplikasi belum diterapkan,
dan hasil ini belum menjadi pernyataan bahwa aplikasi siap deployment publik.
