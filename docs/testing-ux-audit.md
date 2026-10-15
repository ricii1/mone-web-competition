# Audit UX dan browser Peta Pintar — 15 Oktober 2026

Audit dilakukan dengan Google Chrome headless dan Playwright yang sudah tersedia global, tanpa dependency baru dan tanpa mengubah kode aplikasi. Ukuran utama 360×800 (HP) dan 1280×800 (desktop), termasuk preferensi gerak berkurang. Pengujian ini bukan pengganti uji langsung bersama anak/guru atau perangkat fisik.

## Lingkungan dan isolasi

- Frontend Next development: `127.0.0.1:3000`.
- API audit: `127.0.0.1:18000`, database `edumap_audit_20261015`, Redis khusus audit `16379`.
- Browser meneruskan request API frontend ke API audit melalui interception; tidak memakai akun/data development. Token dan password tidak dimasukkan ke laporan.
- Fixture SD: kelas Siklus Air published, kelas draft untuk guru, empat level per kelas, PDF asli fixture, akun guru/murid audit.
- Landing/auth error memakai respons API terkontrol. Pengujian kelas/kuis/live memakai backend sungguhan dan fixture audit.
- Semua WebSocket diblok pada pengujian authenticated/live. Hasil live dengan demikian menguji fallback REST polling, bukan koneksi WebSocket yang berhasil.

## Hasil pengujian

Tiga harness alur utama menyelesaikan **26 skenario tanpa exception akhir**: 16 landing/auth (8 pada tiap ukuran), 7 alur authenticated, dan 3 live class. Skenario yang berhasil belum berarti seluruh UX bebas masalah; temuan geometri dan aksesibilitas di bawah tetap berlaku. Ada 13 observasi tambahan dari harness error, bantuan, dan aksesibilitas.

| Area | Bukti perilaku |
|---|---|
| Landing murid, kedua ukuran | Buka level → baca → jawab 3/3 benar → hasil 100% → pesan level 2 terbuka. |
| Landing guru, kedua ukuran | Progres simulasi → review → tombol publish terkunci sebelum approval soal → publish → hasil terbit. |
| Tab demo | ArrowRight memindah fokus dan `aria-selected` dari Murid ke Guru. |
| Login/register, kedua ukuran | Tampilkan/sembunyikan kata sandi berfungsi; kegagalan API tampil sebagai alert; tidak ada overflow horizontal. |
| Dashboard murid dan map | Kelas ter-enroll terlihat; empat node; tombol Tampilan awal berfungsi. |
| PDF murid | Viewer membuat URL blob, menyediakan Unduh PDF, dan iframe hilang setelah Tutup PDF. Tidak membuktikan perilaku viewer PDF pada semua browser HP. |
| Kuis murid | Lanjut awalnya disabled; 5 jawaban dikirim ke backend, hasil 100%, level kedua terbuka, leaderboard menampilkan skor. |
| Guru | Publish draft terkunci saat materi belum disetujui; peta, pratinjau pembagian PDF, teks lengkap sumber, editor materi dan tab soal dapat dibuka. |
| Live dengan WS diblok | Guru buat sesi → murid gabung kode 6 karakter → peserta muncul → mulai → jawaban murid terkirim → akhiri → hasil diterima kedua browser. Snapshot final mencatat 3 GET polling per browser; skor peserta tersimpan dan tampil. |
| Bantuan, kedua ukuran | Dialog mengikuti viewport tanpa overflow internal horizontal; fokus awal pada Tutup bantuan; Escape menutup dan mengembalikan fokus ke Bantuan. |
| Tanpa JS/gerak berkurang | Heading landing tidak tersembunyi; saat reduced-motion tidak ada animasi berjalan yang terdeteksi pada landing. |

Tidak ada JavaScript `pageerror` pada harness landing/auth, authenticated, bantuan/error, dan live. Beberapa percobaan awal harness memakai selector yang terlalu luas atau mengeklik input radio `sr-only`; selector diperbaiki ke elemen yang dilihat pengguna dan skenario dijalankan ulang. Kegagalan selector tersebut bukan bug aplikasi.

## Temuan yang dapat direproduksi

### P2 — Halaman kelola kelas menelan kegagalan muat

**Lokasi:** `frontend/app/teacher/classes/[classId]/page.tsx:76` dan `:194`.

Repro: buka halaman kelola kelas dengan API mengembalikan 503 untuk kelas, materi, dan level. Setelah request selesai, heading tetap **Memuat...**, tidak ada alert, daftar mengklaim belum ada materi/level, bahkan tombol Terbitkan kelas aktif. Terjadi pada 360 dan 1280 px. `Promise.allSettled` hanya menetapkan `loaded=true` tanpa membaca rejection; state kosong diperlakukan sebagai hasil sah. Endpoint backend masih melindungi aksi yang tidak sah, tetapi guru tidak dapat memahami penyebab halaman kosong.

Perbaikan yang disarankan: tangani hasil gagal, tampilkan pesan dan Coba lagi, dan hanya izinkan publish setelah kelas serta daftar level berhasil dimuat.

### P2 — Unggah PDF tidak dapat dijangkau melalui keyboard

**Lokasi:** `frontend/app/teacher/classes/[classId]/page.tsx:223`.

Repro: navigasikan halaman guru hanya dengan Tab. Label Unggah PDF tidak fokusable dan input memiliki `display:none` dari kelas `hidden`. Pemanggilan fokus DOM ke input pun meninggalkan fokus pada BODY. Klik mouse masih berfungsi. Guru yang memakai keyboard tidak dapat membuka pemilih file.

Perbaikan yang disarankan: gunakan input `sr-only` yang tetap fokusable dengan label/focus-within, atau tombol native yang memicu input melalui ref.

### P2 — Header melewati lebar HP dan avatar tertimpa

**Lokasi:** `frontend/components/AppHeader.tsx:35` dan `:48`.

Repro: masuk, buka `/student` pada viewport 360 px. `documentElement.scrollWidth=364`; sisi kanan tombol Keluar mencapai **363,89 px**. Avatar menyempit dan tertimpa tombol pergantian mode. Pada editor guru 360 px tercatat scrollWidth **366**. Desktop 1280 px tidak mengalami overflow.

Perbaikan yang disarankan: kurangi ruang horizontal/gap/padding khusus HP, sembunyikan avatar pada HP, atau kelompokkan aksi. Pertahankan target tombol minimal 48 px.

### P3 — Tab editor guru tidak mendukung pola keyboard tab

**Lokasi:** `frontend/app/teacher/classes/[classId]/levels/[levelId]/page.tsx:177`.

Repro: fokus tab Materi lalu tekan ArrowRight. Fokus dan tab terpilih tetap Materi; kedua tab mempunyai `tabIndex=0`. Klik tab Soal bekerja. Komponen memakai `role=tablist/tab`, tetapi tidak menerapkan arrow keys dan roving tabindex seperti tab demo/bantuan.

Perbaikan yang disarankan: tambahkan ArrowLeft/Right, Home/End, serta tabindex 0 hanya pada tab aktif.

### P3 — Demo guru mengajarkan aturan publish yang tidak lengkap

**Lokasi:** `frontend/components/landing/TeacherDemo.tsx:194`.

Repro: jalankan demo guru, biarkan tiga level tetap berlabel Draft, setujui satu soal, lalu Publish kelas berhasil. Teks mengajarkan hanya approval soal. Produk riil membutuhkan semua materi level disetujui serta minimal satu soal approved di tiap level. Demo boleh disederhanakan, tetapi persyaratan utama perlu dijelaskan dan direpresentasikan agar guru tidak bingung saat memakai aplikasi.

### P3 — Beberapa target tombol lebih kecil dari ketentuan proyek

**Lokasi:** `frontend/app/globals.css:113`, dipakai oleh `frontend/app/page.tsx:98` dan kontrol editor guru.

Pengukuran browser pada landing: tombol Masuk 82,73×44 px dan Daftar 79,06×44 px. Ketentuan proyek meminta target minimal 48 px; `.btn-sm` menetapkan minimal 44 px. Target lain pada form login/register yang diperiksa memenuhi ukuran minimum.

## Artefak dan batas cakupan

Harness, keluaran JSON, dan screenshot berada di `/tmp/edumap-audit-ux/`: `public.cjs`, `authenticated.cjs`, `live.cjs`, `failures.cjs`, `accessibility.cjs`, serta `*-results.json`. Screenshot utama: `student-header-360.png`, `teacher-error-360.png`, `student-auth-360.png`, `teacher-editor-1280.png`, `live-student-360.png`, login/register dan landing kedua ukuran. Artefak `/tmp` bersifat sementara; laporan ini menyimpan hasil yang perlu dipertahankan.

Belum diuji: Safari/iOS/perangkat Android fisik, pembaca layar penuh, kontras warna secara instrumentasi, performa HP low-end/jaringan tersendat, produksi HTTPS/tunnel, WebSocket sukses, seluruh variasi error/upload besar, semua aksi edit/hapus/publish destruktif, atau pipeline AI nyata. Pengujian backend/komponen terpisah melengkapi laporan ini. Tidak ada perbaikan aplikasi yang diterapkan pada audit ini.
