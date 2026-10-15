"""Create original elementary-school PDFs with several section/page layouts."""

import argparse
from pathlib import Path

import pymupdf

SECTIONS = {
    "Air di Sekitar Kita": (
        "Air hujan dapat dikumpulkan dalam penampungan air. Air digunakan untuk menyiram tanaman. "
        "Air bersih juga digunakan untuk mencuci tangan sebelum makan. Kita perlu memakai air "
        "secukupnya agar tidak terbuang. Keran harus ditutup setelah selesai digunakan. "
        "Air di sungai mengalir dari tempat yang tinggi ke tempat yang rendah. "
        "Sampah tidak boleh dibuang ke sungai karena dapat mengotori air. "
        "Menjaga kebersihan air membantu kita menjaga lingkungan di sekitar rumah."
    ),
    "Bagian Tumbuhan": (
        "Akar tumbuhan menyerap air dari tanah. Batang membantu tumbuhan berdiri tegak. "
        "Daun tumbuhan membantu membuat makanan dengan bantuan cahaya matahari. "
        "Bunga pada beberapa tumbuhan dapat berkembang menjadi buah. Di dalam buah terdapat biji. "
        "Biji dapat tumbuh menjadi tumbuhan baru jika mendapat kondisi yang sesuai. "
        "Kita dapat mengamati bagian tumbuhan di halaman sekolah. Tumbuhan perlu dirawat "
        "dengan menyiramnya secukupnya. Merawat tumbuhan membuat halaman lebih nyaman dan hijau."
    ),
    "Energi di Rumah": (
        "Lampu belajar menggunakan energi listrik untuk menghasilkan cahaya. Cahaya membantu "
        "kita membaca ketika ruangan gelap. Kipas angin menggunakan energi listrik untuk bergerak. "
        "Kita mematikan lampu ketika tidak diperlukan agar energi tidak terbuang. "
        "Televisi juga harus dimatikan setelah selesai ditonton. Kita tidak boleh menyentuh "
        "kabel yang rusak karena berbahaya. Mintalah bantuan orang dewasa ketika menemukan "
        "alat listrik yang rusak. Menghemat energi dapat dimulai dari kebiasaan kecil di rumah."
    ),
}
MARKERS = ["penampungan air", "Akar tumbuhan", "Lampu belajar"]


def _body(page: pymupdf.Page, text: str, top: float, bottom: float) -> None:
    remaining = page.insert_textbox((60, top, 535, bottom), text, fontsize=11, fontname="helv")
    if remaining < 0:
        raise ValueError("Fixture text did not fit inside its page rectangle")


def create_fixtures(output_dir: Path) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    titles = list(SECTIONS)
    for name in (
        "one_section_per_page",
        "one_section_per_page_toc",
        "mixed_pages",
        "mixed_pages_toc",
        "flat_headings",
    ):
        with pymupdf.open() as doc:
            if name.startswith("one_section_per_page"):
                for title, text in SECTIONS.items():
                    page = doc.new_page()
                    page.insert_text((60, 72), title, fontsize=18)
                    _body(page, text, 96, 750)
            else:
                size = 11 if name == "flat_headings" else 18
                page = doc.new_page()
                page.insert_text((60, 72), titles[0], fontsize=size)
                _body(page, SECTIONS[titles[0]], 96, 270)
                page.insert_text((60, 320), titles[1], fontsize=size)
                _body(page, SECTIONS[titles[1]], 344, 750)
                page = doc.new_page()
                _body(page, SECTIONS[titles[1]], 72, 260)
                page.insert_text((60, 300), titles[2], fontsize=size)
                _body(page, SECTIONS[titles[2]], 324, 750)
                if name == "mixed_pages_toc":
                    doc.set_toc([[1, titles[0], 1], [1, titles[1], 1], [1, titles[2], 2]])
            if name == "one_section_per_page_toc":
                doc.set_toc([[1, title, index + 1] for index, title in enumerate(titles)])
            path = output_dir / f"{name}.pdf"
            doc.save(path)
            paths.append(path)
    with pymupdf.open() as doc:
        for _ in range(5):
            page = doc.new_page()
            _body(page, (SECTIONS[titles[0]] + " ") * 3, 72, 750)
        path = output_dir / "unstructured_long.pdf"
        doc.save(path)
        paths.append(path)
    return paths


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("output_dir", type=Path)
    args = parser.parse_args()
    for fixture in create_fixtures(args.output_dir):
        print(fixture)
