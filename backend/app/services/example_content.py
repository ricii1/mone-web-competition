"""Hand-written reference lessons for the example class (IPA Kelas 4 - Siklus Air).

This is the quality bar for AI-generated levels, written for 9-10 year olds: a detailed lesson
(`content`, about 450-600 words = a 2-3 minute read, Markdown subset: `###` headings,
paragraphs, `-` lists, `**bold**`), then a real recap (`summary`), `key_points` and five
questions whose answers can all be found in the lesson. `pages` is the page range of the
fictional source material shown as "Sumber".
"""

MATERIAL_FILE_NAME = "Contoh - IPA Siklus Air.pdf"

# Each question: (text, options, index of the correct option, short friendly explanation).
LESSONS: list[dict] = [
    {
        "title": "Air di Sekitar Kita",
        "pages": (1, 4),
        "content": """### Air ada di mana-mana

Coba lihat di sekitarmu. Air ada di sungai, di danau, di laut, dan di dalam tanah. Air juga ada di dalam tubuhmu. Kita minum air, mandi dengan air, dan mencuci baju dengan air. Tanpa air, manusia, hewan, dan tumbuhan tidak bisa hidup.

Air di bumi tidak pernah habis begitu saja. Air itu terus berputar dari tempat yang satu ke tempat yang lain. Perjalanan air yang berputar ini disebut **siklus air**. Pelajaran ini membahas bagian pertamanya, yaitu bagaimana air naik ke udara.

### Tiga wujud air

Air dapat berubah bentuk. Bentuk air disebut **wujud**. Air punya tiga wujud:

- **Cair**: air minum, air hujan, dan air sungai. Air cair bisa mengalir.
- **Padat**: es batu. Air menjadi padat saat sangat dingin.
- **Gas**: uap air. Uap air tidak bisa kita lihat, tetapi ada di udara.

Air yang berubah wujud tetaplah air. Es batu yang meleleh menjadi air cair. Air cair yang dipanaskan menjadi uap air.

### Penguapan: air naik ke udara

Pernahkah kamu melihat jemuran basah yang menjadi kering? Ke mana air di baju itu pergi? Air itu berubah menjadi uap air dan naik ke udara. Peristiwa air cair berubah menjadi uap air disebut **penguapan**.

Penguapan terjadi karena panas. Panas matahari membuat air di permukaan bumi menguap. Air dari laut, sungai, danau, dan genangan ikut menguap. Air di tanah yang basah juga menguap. Tumbuhan pun melepaskan sedikit uap air dari daunnya.

Saat air mendidih, kamu bisa melihat asap putih yang naik dari panci. Itu bukan uap air yang sebenarnya. Uap air yang sebenarnya tidak terlihat. Asap putih itu adalah titik air kecil yang sudah mulai dingin lagi.

### Mengapa baju cepat kering?

Penguapan bisa cepat atau lambat. Ada tiga hal yang membuatnya lebih cepat:

- Cuaca panas. Baju yang dijemur saat matahari terik lebih cepat kering.
- Angin. Angin membawa uap air pergi, sehingga air yang lain bisa ikut menguap.
- Permukaan yang luas. Baju yang dibentangkan lebih cepat kering daripada baju yang digulung.

Karena itu, ibu menjemur baju di tempat yang terkena matahari dan angin. Saat hujan atau mendung, baju lebih lama kering karena panasnya kurang.

### Percobaan sederhana

Kamu bisa mencoba sendiri. Tuang air ke dua piring yang sama. Taruh satu piring di bawah sinar matahari. Taruh piring yang lain di tempat teduh. Setelah beberapa jam, air di piring yang kena matahari lebih cepat berkurang. Air itu tidak hilang. Air itu sudah menjadi uap air di udara.

### Uap air pergi ke mana?

Uap air sangat ringan, sehingga naik ke langit. Makin tinggi, udara makin dingin. Uap air yang naik akan menjadi dingin. Apa yang terjadi setelah itu? Kita akan mempelajarinya di pelajaran berikutnya.

### Ayo ingat lagi

Air ada di sungai, laut, danau, dan tanah. Air punya tiga wujud, yaitu cair, padat, dan gas. Panas matahari membuat air cair menguap menjadi uap air. Penguapan lebih cepat saat cuaca panas, berangin, dan permukaannya luas.""",
        "summary": (
            "Air ada di sungai, danau, laut, dan tanah, dan air terus berputar dalam siklus air. "
            "Air punya tiga wujud, yaitu cair, padat, dan gas. Panas matahari membuat air cair "
            "berubah menjadi uap air yang naik ke udara, dan peristiwa ini disebut penguapan. "
            "Penguapan lebih cepat saat cuaca panas, berangin, dan permukaannya luas, seperti "
            "baju yang dijemur."
        ),
        "key_points": [
            "Siklus air adalah perjalanan air yang berputar terus-menerus.",
            "Air punya tiga wujud: cair, padat (es), dan gas (uap air).",
            "Penguapan adalah peristiwa air cair berubah menjadi uap air.",
            "Panas matahari membuat air menguap.",
            "Penguapan lebih cepat saat panas, berangin, dan permukaannya luas.",
        ],
        "questions": [
            (
                "Apa nama perjalanan air yang berputar terus-menerus?",
                ["Siklus air", "Banjir", "Gerhana", "Pelangi"],
                0,
                "Perjalanan air yang berputar disebut siklus air.",
            ),
            (
                "Wujud air yang berupa es batu adalah wujud...",
                ["Cair", "Padat", "Gas", "Awan"],
                1,
                "Es batu adalah air yang berwujud padat.",
            ),
            (
                "Air cair berubah menjadi uap air. Peristiwa ini disebut...",
                ["Pembekuan", "Hujan", "Penguapan", "Resapan"],
                2,
                "Air cair yang berubah menjadi uap air disebut penguapan.",
            ),
            (
                "Apa yang membuat air di genangan menguap?",
                ["Panas matahari", "Cahaya bulan", "Suara petir", "Bayangan pohon"],
                0,
                "Panas matahari membuat air menguap ke udara.",
            ),
            (
                "Baju paling cepat kering jika dijemur saat...",
                [
                    "Hujan deras",
                    "Mendung dan tanpa angin",
                    "Panas, berangin, dan dibentangkan",
                    "Malam hari dalam keadaan digulung",
                ],
                2,
                "Cuaca panas, angin, dan permukaan yang luas membuat penguapan lebih cepat.",
            ),
        ],
    },
    {
        "title": "Awan dan Hujan",
        "pages": (5, 8),
        "content": """### Dari uap air menjadi awan

Di pelajaran sebelumnya, kita tahu bahwa panas matahari membuat air menguap. Uap air naik tinggi ke langit. Makin tinggi, udara makin dingin. Uap air yang kedinginan berubah menjadi titik-titik air yang sangat kecil. Peristiwa uap air berubah menjadi titik air disebut **pengembunan**.

Kamu bisa melihat pengembunan di sekitarmu. Coba isi gelas dengan es batu, lalu tunggu beberapa menit. Bagian luar gelas akan basah. Air itu tidak bocor dari dalam gelas. Uap air di udara menyentuh kaca gelas yang dingin, lalu berubah menjadi titik air. Embun di daun pada pagi hari juga terjadi karena pengembunan.

### Apa itu awan?

Di langit, titik-titik air yang sangat kecil itu berkumpul. Jumlahnya sangat banyak sampai kita bisa melihatnya dari bawah. Kumpulan titik air itulah yang kita sebut **awan**. Awan tidak terbuat dari kapas. Awan juga bukan asap. Awan adalah kumpulan titik air kecil yang melayang di langit.

Awan punya bentuk dan warna yang berbeda:

- Awan putih tipis biasanya muncul saat cuaca cerah.
- Awan tebal berwarna abu-abu gelap sering muncul sebelum hujan. Awan ini disebut awan mendung.

Awan mendung berwarna gelap karena isinya sangat banyak titik air. Cahaya matahari sulit menembusnya.

### Bagaimana hujan terjadi?

Titik-titik air di awan terus bertambah. Titik-titik itu saling menempel dan membesar. Akhirnya titik air menjadi berat. Awan tidak kuat lagi menahannya. Titik air itu jatuh ke bumi. Air yang jatuh dari awan ke bumi disebut **hujan**. Peristiwa jatuhnya air dari awan disebut **presipitasi**.

Tidak semua hujan berbentuk air. Di tempat yang sangat dingin, air dari awan bisa jatuh sebagai butiran es atau salju. Di negara kita, hujan biasanya berupa air.

### Urutan terjadinya hujan

Agar mudah diingat, ikuti urutan ini:

- Matahari memanaskan air di laut, sungai, dan danau.
- Air menguap menjadi uap air dan naik ke langit.
- Uap air menjadi dingin dan mengembun menjadi titik air.
- Titik air berkumpul membentuk awan.
- Titik air membesar dan berat, lalu jatuh sebagai hujan.

### Hujan itu bermanfaat

Hujan membawa air bersih untuk bumi. Tanaman menjadi subur. Sungai dan sumur terisi air. Petani bisa mengairi sawah mereka. Hujan juga membersihkan debu di udara.

Namun hujan yang terlalu deras dan terlalu lama bisa membuat sungai meluap. Air yang meluap menyebabkan banjir. Karena itu, kita tidak boleh membuang sampah ke sungai. Sampah yang menumpuk membuat air sulit mengalir.

### Cobalah di rumah

Minta bantuan orang dewasa untuk memanaskan air sampai mengeluarkan uap. Pegang sendok dingin di atas uap itu dengan hati-hati. Sendok akan basah oleh titik air. Itulah gambaran kecil bagaimana awan terbentuk.

### Ayo ingat lagi

Uap air yang naik menjadi dingin dan mengembun menjadi titik air. Kumpulan titik air itu membentuk awan. Saat titik air terlalu berat, air jatuh ke bumi sebagai hujan. Hujan bermanfaat bagi makhluk hidup, tetapi hujan yang berlebihan bisa menyebabkan banjir.""",
        "summary": (
            "Uap air yang naik ke langit menjadi dingin dan berubah menjadi titik air kecil. "
            "Peristiwa ini disebut pengembunan. Kumpulan titik air itu membentuk awan, dan saat "
            "titik air makin besar dan berat, air jatuh ke bumi sebagai hujan atau presipitasi. "
            "Hujan sangat bermanfaat, tetapi hujan yang terlalu deras dapat menyebabkan banjir."
        ),
        "key_points": [
            "Pengembunan adalah peristiwa uap air berubah menjadi titik air.",
            "Awan adalah kumpulan titik air kecil yang melayang di langit.",
            "Presipitasi adalah jatuhnya air dari awan ke bumi, misalnya hujan.",
            "Urutan hujan: menguap, mengembun, membentuk awan, lalu jatuh sebagai hujan.",
            "Hujan bermanfaat, tetapi hujan berlebihan dapat menyebabkan banjir.",
        ],
        "questions": [
            (
                "Uap air berubah menjadi titik air saat kedinginan. Peristiwa ini disebut...",
                ["Penguapan", "Pengembunan", "Pembekuan", "Pelelehan"],
                1,
                "Uap air yang berubah menjadi titik air disebut pengembunan.",
            ),
            (
                "Mengapa bagian luar gelas es menjadi basah?",
                [
                    "Gelasnya bocor",
                    "Uap air di udara mengembun di kaca yang dingin",
                    "Es batu menembus kaca",
                    "Kaca mengeluarkan air sendiri",
                ],
                1,
                "Uap air menyentuh kaca dingin lalu mengembun menjadi titik air.",
            ),
            (
                "Awan adalah...",
                [
                    "Kapas di langit",
                    "Asap dari gunung",
                    "Kumpulan titik air kecil di langit",
                    "Bintang yang redup",
                ],
                2,
                "Awan terdiri dari kumpulan titik air kecil yang melayang.",
            ),
            (
                "Jatuhnya air dari awan ke bumi disebut...",
                ["Presipitasi", "Penguapan", "Resapan", "Pengembunan"],
                0,
                "Presipitasi adalah jatuhnya air dari awan, misalnya hujan.",
            ),
            (
                "Urutan yang benar terjadinya hujan adalah...",
                [
                    "Hujan, awan, mengembun, menguap",
                    "Awan, menguap, hujan, mengembun",
                    "Menguap, mengembun, awan, hujan",
                    "Mengembun, hujan, menguap, awan",
                ],
                2,
                "Air menguap, lalu mengembun, membentuk awan, dan jatuh sebagai hujan.",
            ),
        ],
    },
    {
        "title": "Perjalanan Air Kembali",
        "pages": (9, 12),
        "content": """### Ke mana air hujan pergi?

Setelah hujan turun, air jatuh ke bumi. Ke mana air itu pergi? Sebagian air hujan mengalir di atas tanah. Sebagian lagi masuk ke dalam tanah. Air hujan juga mengisi genangan di jalan. Saat matahari bersinar lagi, genangan itu akan menguap.

### Air masuk ke dalam tanah

Air hujan yang meresap ke dalam tanah disebut **resapan**. Air yang meresap itu disimpan di dalam tanah. Simpanan air di dalam tanah disebut **air tanah**. Kita memakai air tanah saat mengambil air dari sumur.

Tanah yang berumput dan banyak pohon lebih mudah menyerap air. Akar pohon membuat tanah gembur, sehingga air mudah masuk. Tanah yang tertutup semen atau aspal sulit menyerap air. Air pun mengalir di permukaan dan bisa menimbulkan banjir. Karena itu, menanam pohon sangat baik untuk bumi.

### Air mengalir ke sungai dan laut

Air hujan yang tidak meresap mengalir ke tempat yang lebih rendah. Air mengalir ke selokan, lalu ke sungai. Sungai mengalir terus menuju laut. Air tanah pun pelan-pelan keluar sebagai mata air dan juga mengalir ke sungai.

Di laut, air berkumpul sangat banyak. Panas matahari kembali memanaskan air laut. Air laut menguap menjadi uap air. Setelah itu, uap air naik ke langit, mengembun, dan membentuk awan lagi.

### Siklus air: berputar tanpa henti

Sekarang kita bisa menyusun perjalanan air secara lengkap. Urutannya seperti ini:

- **Penguapan**: air di laut, sungai, dan genangan berubah menjadi uap air.
- **Pengembunan**: uap air mendingin dan menjadi titik air, lalu membentuk awan.
- **Presipitasi**: air jatuh dari awan sebagai hujan.
- **Resapan dan aliran**: air meresap ke tanah atau mengalir ke sungai dan laut.

Setelah sampai di laut, air menguap lagi. Perjalanan ini berulang terus. Karena itu, kita menyebutnya **siklus**. Jumlah air di bumi tetap sama. Namun air bersih yang bisa kita minum jumlahnya tidak banyak. Air laut asin, sehingga tidak bisa langsung diminum.

### Kisah setetes air

Bayangkan ada setetes air di laut. Panas matahari memanaskannya sampai menjadi uap air. Uap air itu naik ke langit dan menjadi dingin. Ia bergabung dengan banyak titik air lain menjadi awan. Angin membawa awan itu ke daratan. Lalu setetes air itu jatuh sebagai hujan di sebuah desa. Sebagian hujan meresap ke tanah dan mengisi sumur. Sebagian lagi mengalir ke sungai dan kembali ke laut. Begitulah setetes air melakukan perjalanan yang sama berulang-ulang.

### Ayo hemat air!

Air bersih sangat berharga. Kita bisa menjaganya dengan cara sederhana:

- Matikan keran saat menyikat gigi.
- Mandi dengan secukupnya, jangan terlalu lama.
- Segera perbaiki keran yang bocor.
- Gunakan air bekas mencuci sayur untuk menyiram tanaman.
- Jangan membuang sampah ke sungai.

Satu keran yang menetes terus bisa membuang banyak air dalam sehari. Jika semua orang berhemat, air bersih akan cukup untuk semua.

### Ayo ingat lagi

Air hujan meresap ke dalam tanah menjadi air tanah atau mengalir ke sungai, lalu sampai ke laut. Panas matahari membuat air laut menguap lagi, sehingga siklus air berputar terus. Pohon membantu tanah menyerap air. Kita harus menghemat air dan menjaga sungai tetap bersih.""",
        "summary": (
            "Air hujan sebagian meresap ke dalam tanah menjadi air tanah, dan sebagian mengalir "
            "ke sungai lalu ke laut. Di laut, panas matahari membuat air menguap lagi sehingga "
            "siklus air berulang terus: menguap, mengembun, hujan, lalu meresap atau mengalir. "
            "Pohon membantu tanah menyerap air, dan kita perlu menghemat air karena air bersih "
            "jumlahnya tidak banyak."
        ),
        "key_points": [
            "Resapan adalah air hujan yang masuk ke dalam tanah menjadi air tanah.",
            "Air yang tidak meresap mengalir ke sungai lalu ke laut.",
            "Air laut menguap lagi, sehingga siklus air berulang terus.",
            "Pohon membuat tanah mudah menyerap air.",
            "Kita harus menghemat air dan tidak membuang sampah ke sungai.",
        ],
        "questions": [
            (
                "Air hujan yang masuk ke dalam tanah disebut...",
                ["Resapan", "Penguapan", "Awan", "Banjir"],
                0,
                "Air hujan yang meresap ke dalam tanah disebut resapan.",
            ),
            (
                "Air hujan yang tidak meresap akan mengalir ke selokan, lalu ke sungai, dan akhirnya ke...",
                ["Awan", "Gunung", "Laut", "Atap rumah"],
                2,
                "Sungai mengalir terus menuju laut.",
            ),
            (
                "Mengapa perjalanan air disebut siklus?",
                [
                    "Karena airnya hanya sekali jalan",
                    "Karena perjalanannya berulang terus",
                    "Karena airnya berhenti di laut",
                    "Karena airnya berubah menjadi tanah",
                ],
                1,
                "Setelah sampai di laut, air menguap lagi sehingga perjalanan berulang.",
            ),
            (
                "Tanah yang mudah menyerap air adalah tanah yang...",
                [
                    "Tertutup semen",
                    "Tertutup aspal",
                    "Berumput dan banyak pohon",
                    "Keras dan gundul",
                ],
                2,
                "Akar pohon membuat tanah gembur sehingga air mudah masuk.",
            ),
            (
                "Cara menghemat air yang benar adalah...",
                [
                    "Membiarkan keran menetes",
                    "Mandi lama sekali",
                    "Mematikan keran saat menyikat gigi",
                    "Membuang sampah ke sungai",
                ],
                2,
                "Mematikan keran saat menyikat gigi menghemat air.",
            ),
        ],
    },
]

BOSS_LEVEL = {
    "title": "Boss: Petualangan Siklus Air",
    "summary": (
        "Level ini menggabungkan tiga pelajaran sebelumnya. Panas matahari membuat air "
        "menguap menjadi uap air. Uap air mengembun menjadi awan, lalu jatuh sebagai hujan. "
        "Air hujan meresap atau mengalir ke sungai dan laut, kemudian menguap lagi sehingga "
        "siklus air berulang terus."
    ),
    "key_points": [
        "Air punya tiga wujud: cair, padat, dan gas.",
        "Penguapan terjadi karena panas matahari.",
        "Pengembunan mengubah uap air menjadi titik air dan membentuk awan.",
        "Presipitasi adalah jatuhnya air dari awan, misalnya hujan.",
        "Air hujan meresap ke tanah atau mengalir ke sungai dan laut.",
    ],
    "questions": [
        (
            "Wujud air yang tidak bisa kita lihat, yaitu uap air, adalah wujud...",
            ["Cair", "Padat", "Gas", "Salju"],
            2,
            "Uap air adalah air yang berwujud gas.",
        ),
        (
            "Peristiwa air cair berubah menjadi uap air disebut...",
            ["Penguapan", "Pengembunan", "Resapan", "Presipitasi"],
            0,
            "Air cair yang menjadi uap air disebut penguapan.",
        ),
        (
            "Kumpulan titik air kecil yang melayang di langit disebut...",
            ["Embun", "Awan", "Sungai", "Sumur"],
            1,
            "Awan adalah kumpulan titik air kecil.",
        ),
        (
            "Air hujan yang masuk ke dalam tanah disebut...",
            ["Penguapan", "Banjir", "Resapan", "Pengembunan"],
            2,
            "Air yang masuk ke dalam tanah disebut resapan.",
        ),
        (
            "Setelah air sampai di laut, apa yang terjadi selanjutnya?",
            [
                "Air hilang selamanya",
                "Air menguap lagi karena panas matahari",
                "Air berubah menjadi batu",
                "Air berhenti bergerak",
            ],
            1,
            "Air laut menguap lagi sehingga siklus air berulang.",
        ),
    ],
}
