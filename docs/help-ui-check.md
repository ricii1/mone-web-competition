# Perbaikan bantuan terpotong dan panduan interaktif

Uji dilakukan pada 12 Oktober 2026 dengan Chrome headless yang sudah tersedia di
mesin. Tidak memasang dependency baru, tidak membuat akun dan tidak mengubah data
kelas. Halaman guru/murid dibuka tanpa token; panel bantuan tetap dapat diuji.

## Akar masalah

`HelpButton` sebelumnya merender overlay `fixed inset-0` di dalam `AppHeader` yang
memakai `backdrop-blur`. Filter header membentuk containing block untuk posisi
fixed. Hasil pengukuran di lebar 360px: overlay hanya setinggi 64px, panel mulai di
`y=-524.8` dan berakhir di `y=64`. Jadi sebagian besar bantuan berada di atas layar;
menambah tinggi panel atau z-index saja tidak menyelesaikannya.

Solusi memakai dialog modal native (`showModal`) di lapisan atas browser. Panel
mengikuti tinggi dinamis layar, memiliki safe-area, isi yang bisa digulir, header
lengket dengan tombol tutup, dan navigasi langkah lengket di bawah. Saat dibuka
ulang/ganti mode, guliran kembali ke awal sehingga langkah pertama tidak tersembunyi.

## Interaksi

- Guru/murid dapat mengganti panduan dan memilih satu dari enam langkah.
  HP memakai pilihan dropdown agar artikel mendapat ruang lebih luas; layar lebar
  memakai tombol nomor. Keduanya berukuran minimal 48px.
- Tombol Sebelumnya/Berikutnya berpindah langkah; langkah terakhir memiliki Selesai.
- Penanda Sudah paham dapat ditoggle; hitungan tiap mode tetap ada selama komponen
  masih aktif. Penanda tidak disimpan ke server dan tidak mengubah nilai kuis.
- Tautan memakai kelas/level dari halaman yang sedang dibuka. Jika belum ada kelas,
  pengguna diarahkan memilih kelas dahulu. Mode lain tidak memakai ID kelas asal.
- FAQ memakai `details/summary`. Panduan mencakup PDF asli/pratinjau, retry PDF,
  review materi dan soal, publish, kuis bersama, serta penghapusan kelas.
- Dialog dapat ditutup lewat tombol, Escape atau klik latar. Fokus kembali ke
  tombol Bantuan dan overflow body dipulihkan. Tab mode memakai panah/Home/End.
  Dialog native menjaga halaman belakang inert; fokus browser/address bar tetap
  merupakan perilaku browser, bukan kontrol aplikasi di belakang modal.

## Hasil uji browser

Delapan kombinasi guru/murid pada 320×568, 360×640, 800×360 dan 1280×800 lolos:

- panel dan judul berada di dalam layar, tanpa overflow horizontal pada panel;
- guliran awal nol setiap dibuka dan kontrol tutup tetap terlihat setelah isi digulir;
- pilih langkah langsung, lanjut, penanda pemahaman dan FAQ berfungsi;
- ganti tab dengan keyboard mereset langkah ke satu;
- Escape/klik latar menutup, fokus kembali ke Bantuan dan scroll halaman dipulihkan.

Pengukuran dan screenshot sesi tersedia di `/tmp/edumap-help-ui/`: `before.json`,
`before-360.png`, `after.json` dan screenshot tiap mode/ukuran. Script uji sementara
menggunakan Chrome DevTools Protocol melalui paket `websockets` yang sudah tersedia.
Fixture browser sempat mengharapkan label Inggris dan mengasumsikan penanda selalu
kosong setiap dibuka; diperbaiki untuk label Guru/Murid dan toggle state yang memang
bertahan selama komponen aktif. Assertion geometri dan interaksi tetap dipertahankan.

Uji manual berikutnya dapat dilakukan dengan membuka Bantuan dari halaman peta,
kelas guru, editor level dan kuis; pilih langkah, buka FAQ, lanjut, tutup, lalu buka
kembali. Layar sangat pendek tetap menyediakan guliran dan tombol navigasi.
