# Audit frontend dan komponen — 15 Oktober 2026

Audit ini memeriksa frontend tanpa mengubah kode aplikasi. Pengujian backend dan browser interaktif dicatat oleh audit terpisah.

## Hasil pemeriksaan

| Pemeriksaan | Hasil |
|---|---|
| `node --test frontend/tests/*.test.cjs` | 16 lulus, 0 gagal; sebelumnya hanya 4 test |
| `cd frontend && npm run lint` | Lulus, tanpa warning |
| `cd frontend && ./node_modules/.bin/tsc --noEmit --incremental false` | Lulus |
| `npm run build` pada salinan frontend di `/tmp` | Terblokir pengambilan font Google: `fonts.gstatic.com` mengalami `ETIMEDOUT` |
| Build diagnostik dengan mock font bawaan Next | Lulus kompilasi, pemeriksaan tipe, prerender 10 halaman dan build trace |

Build diagnostik memakai `NEXT_FONT_GOOGLE_MOCKED_RESPONSES` hanya pada salinan `/tmp`; berkas aplikasi/repo tidak diubah. Hasil tersebut membuktikan proses build selain pengambilan font dapat berjalan, tetapi **tidak membuktikan build produksi dengan font asli berhasil**. Percobaan `curl -4` ke font juga timeout. Root layout meminta Baloo 2 dan Nunito melalui `next/font/google` (`frontend/app/layout.tsx:2`). Build deployment tetap memerlukan akses Google Fonts atau font lokal.

Build dan pengecekan TypeScript tidak berbagi direktori `.next` dengan server development yang dipakai audit UX.

## Temuan terkonfirmasi

### P2 — Pesan validasi API berubah menjadi `[object Object]`

Lokasi: `frontend/lib/api.ts:38`, juga jalur upload pada baris 54.

FastAPI/Pydantic mengembalikan `detail` berupa array untuk kesalahan validasi. Client meneruskannya langsung ke `new ApiError(...)`; konstruktor `Error` mengubah array objek menjadi string `[object Object]`.

Reproduksi runtime terhadap modul asli yang ditranspilasi:

```text
Respons: HTTP 422
{"detail":[{"type":"string_too_long","loc":["body","name"],"msg":"String should have at most 100 characters"}]}
ApiError.status: 422
ApiError.message: "[object Object]"
```

Alur UI yang dapat memicu: form daftar mengizinkan nama lebih dari 100 karakter karena input tidak memiliki `maxLength` (`frontend/app/(auth)/register/page.tsx:61`), sedangkan backend menolaknya. Kesalahan kata sandi lebih dari 72 byte juga berasal dari validasi backend. Pengguna tidak mendapat instruksi perbaikan yang dapat dipahami.

Usulan: normalkan `detail` di satu helper client untuk request JSON dan upload; untuk array validasi tampilkan pesan Bahasa Indonesia yang aman dan jelas. Tambahkan pengujian respons array/objek selain string. Temuan ini belum diperbaiki dalam pekerjaan pengujian.

### P2 — Nomor halaman sumber level dimulai dari nol

Lokasi: `frontend/lib/levels.ts:6`–7; dipakai oleh `frontend/components/LevelPlayer.tsx`.

Reproduksi runtime:

```text
formatSource({page_start: 0, page_end: 1, section_title: "Air"})
Hasil: "Hal. 0-1 - Air"
Seharusnya: "Hal. 1-2 - Air"
```

Chunking menyimpan indeks halaman dari nol (`backend/app/rag/chunking.py:84`), dan `backend/app/services/level_service.py:45`–46 meneruskannya tanpa konversi. Komponen pembagian materi sudah menambahkan 1 (`frontend/components/MaterialSections.tsx:27`–29), sehingga referensi PDF berbeda antara dua tampilan.

Usulan: tambahkan 1 hanya pada format tampilan sumber, pertahankan indeks internal, dan uji halaman tunggal serta rentang. Temuan ini belum diperbaiki dalam pekerjaan pengujian.

## Pengujian regresi yang ditambahkan

Semua memakai dependency yang sudah ada, tanpa package tambahan.

- `frontend/tests/components.test.cjs`: lima pengujian rendering React yang sebenarnya memakai `react-dom/server` terhadap TSX asli: Markdown heading/list/emphasis/CRLF, escaping HTML berbahaya, batas skor bintang 69/70/84/85/99/100, state pressed/disabled/count pada AnswerTile, serta satu pilihan aktif pada RoleChooser.
- `frontend/tests/api.test.cjs`: lima pengujian tambahan untuk origin API konfigurasi, login tanpa Bearer saat belum masuk, status/detail error biasa dan error non-JSON, upload multipart tanpa Content-Type buatan, serta pagination dan AbortSignal preview sumber.
- `frontend/tests/realtime.test.cjs`: dua pengujian tambahan untuk encoding token WebSocket, pesan JSON rusak, polling saat koneksi terbuka, dan callback reconnect yang tidak menghidupkan socket setelah cleanup.

Total: 7 test client API + 5 test rendering komponen + 4 test realtime = 16.

## Pemeriksaan kode dan batas bukti

- Viewer PDF mengambil blob dengan Bearer, membatalkan request, mengabaikan hasil request setelah abort, dan melepas object URL di cleanup; terdapat loading/error/download/iframe title. Tes API membuktikan autentikasi dan penerusan sinyal; lifecycle object URL belum diuji dengan DOM.
- Preview pembagian sumber menyediakan pagination, loading/error/empty, retry, dan abort. Pengujian client membuktikan offset/limit/sinyal; interaksi expand/pagination memerlukan browser.
- Halaman live menggunakan snapshot REST dan polling melalui `connectRealtime`; helper reconnect/cleanup diuji runtime dengan timer/socket palsu. Tes ini tidak membuktikan seluruh perjalanan sesi live terhadap server.
- React Flow dimuat dinamis pada halaman peta; pemulihan viewport memakai hook `useDefaultView`. Ukuran layar dan interaksi peta menjadi tanggung jawab audit browser.
- Panel bantuan menggunakan dialog modal native, navigasi keyboard, safe area dan ukuran kontrol pada kode. Tidak ada klaim bahwa semua aspek aksesibilitas lulus hanya berdasarkan pembacaan sumber.
- Rendering server menguji markup dan escaping komponen, **bukan** klik, fokus, hydration, ukuran sentuh, kontras, screen reader, atau perilaku perangkat low-end.
- Ditemukan potensi banner error leaderboard tidak dibersihkan setelah polling pulih (`frontend/app/student/classes/[classId]/leaderboard/page.tsx:31`–38); ini hasil pembacaan kode dan belum direproduksi di browser, sehingga tidak dihitung sebagai temuan terkonfirmasi pada daftar di atas.
- Kemajuan membaca hanya memperbarui visual `transform` tanpa `aria-valuenow` (`frontend/components/LevelPlayer.tsx:85`–90); evaluasi pembaca layar belum dijalankan.

Tidak ada uji jaringan LLM/embedding, perubahan dependency, perubahan kode aplikasi, atau penggunaan data produksi.
