# Audit dependency — 15 Oktober 2026

Pemeriksaan bersifat read-only; tidak menjalankan `npm audit fix`, mengubah lockfile,
atau menaikkan versi dependency. Temuan scanner dibedakan dari eksploitasi yang
terbukti pada aplikasi.

## Frontend

`npm audit --omit=dev --json` keluar dengan status 1 dan melaporkan **3 package**:
1 critical (`next`) dan 2 high (`postcss` transitif serta `source-map-js`). Angka ini
jumlah package menurut scanner, bukan jumlah kerentanan yang berhasil dieksploitasi.
JSON mentah tersimpan di `/tmp/edumap-full-audit/npm-audit.json`.

| Package terpasang | Lokasi/keterangan | Hasil scanner |
|---|---|---|
| `next@14.2.35` | Dependency langsung; App Router | Critical, dengan beberapa advisory high/moderate lain |
| `postcss@8.4.31` | `node_modules/next/node_modules/postcss`; PostCSS langsung repo sudah `8.5.28` | High |
| `source-map-js@1.2.1` | Dependency transitif | High |

Contoh sumber primer yang diperiksa:

- [Advisory Next.js GHSA-h25m-26qc-wcjf](https://github.com/vercel/next.js/security/advisories/GHSA-h25m-26qc-wcjf)
  mencantumkan Next.js 14 pada rentang terdampak denial of service di Server Components.
- [Advisory Next.js GHSA-2xp9-vwfh-vxw4](https://github.com/vercel/next.js/security/advisories/GHSA-2xp9-vwfh-vxw4)
  menyangkut Image Optimization API dengan AVIF dan rentang versi yang mencakup versi
  terpasang. Scanner juga menyertakan advisory khusus Windows; target Docker Linux
  tidak otomatis terdampak jalur khusus Windows tersebut.
- [Advisory source-map-js GHSA-68fv-2mgg-jv7q](https://github.com/advisories/GHSA-68fv-2mgg-jv7q)
  dan [PostCSS GHSA-6g55-p6wh-862q](https://github.com/advisories/GHSA-6g55-p6wh-862q)
  tercantum di hasil registry.

Penelusuran sumber tidak menemukan penggunaan `next/image`, `next/script`,
`remotePatterns`, atau deklarasi `use server` pada aplikasi. Ini membantu menilai
prasyarat beberapa advisory, **bukan bukti bahwa seluruh endpoint framework aman**.
Tidak ada payload eksploitasi/DoS yang dikirim ke aplikasi atau server panitia.

Prioritas sebelum deployment publik: lakukan penilaian advisory yang relevan,
pilih rilis Next.js yang masih didukung dan sudah ditambal, lalu uji kompatibilitas
React/Node/build/runtime. Saran otomatis registry adalah perubahan major; pekerjaan
upgrade dan keputusan versi perlu menjadi perubahan terpisah yang diuji, bukan
diterapkan otomatis saat audit.

## Backend

`python -m pip check` awalnya melihat package ROS global
`generate-parameter-library-py` yang kekurangan `typeguard`, karena `PYTHONPATH`
shell memasukkan toolchain lain. Dengan environment diisolasi:

```bash
PYTHONPATH= /home/ricii/miniconda3/envs/edumap/bin/python -m pip check
```

Hasil: **No broken requirements found.** Tidak menambah `typeguard` atau dependency
yang bukan kebutuhan aplikasi. `pip check` hanya memeriksa konsistensi requirement;
ini **bukan pemindaian kerentanan Python**, dan tidak dinyatakan sebagai hasil audit
CVE bersih. Audit kerentanan Python/container image belum dilakukan.
