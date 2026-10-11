"use client";

import { useEffect, useRef, useState } from "react";
import Mascot from "@/components/Mascot";
import { CrossIcon, QuestionIcon } from "@/components/icons";

type Mode = "student" | "teacher";

interface Step {
  title: string;
  text: string;
}

const GUIDES: Record<Mode, { label: string; intro: string; steps: Step[] }> = {
  student: {
    label: "Murid",
    intro: "Belajar di EduMap seperti main game. Ayo ikuti langkahnya!",
    steps: [
      {
        title: "Masuk ke kelas",
        text: "Pilih kelas yang terbuka, atau tulis kode dari gurumu untuk kelas rahasia.",
      },
      {
        title: "Buka peta level",
        text: "Ketuk kelasmu. Kamu akan melihat peta. Mulai dari level pertama ya.",
      },
      {
        title: "Baca, lalu jawab kuis",
        text: "Baca cerita pendeknya dan rangkumannya. Setelah itu jawab soal-soalnya.",
      },
      {
        title: "Kumpulkan bintang",
        text: "Nilai 70% atau lebih membuka level berikutnya. Kalau belum, boleh coba lagi!",
      },
      {
        title: "Lihat peringkat",
        text: "Cek papan peringkat untuk melihat teman-temanmu. Kalau gurumu mengajak main kuis bareng, tulis kode dari guru.",
      },
    ],
  },
  teacher: {
    label: "Guru",
    intro: "EduMap mengubah PDF materimu menjadi peta level. Kamu yang menentukan hasil akhirnya.",
    steps: [
      {
        title: "Buat kelas baru",
        text: "Isi judul dan pilih siapa yang boleh masuk: semua orang atau hanya yang punya kode.",
      },
      {
        title: "Unggah materi PDF",
        text: "Sistem membaca PDF dan menyusun level. Kamu bisa melihat progresnya langsung.",
      },
      {
        title: "Periksa level dan soal",
        text: "Hasil AI masih berupa draf. Ubah artikel, rangkuman, dan soal, lalu setujui soal yang sudah benar.",
      },
      {
        title: "Terbitkan kelas",
        text: "Kelas bisa diterbitkan kalau setiap level punya soal yang disetujui. Bagikan kodenya ke murid.",
      },
      {
        title: "Main kuis bareng",
        text: "Mulai sesi kuis serentak dari sebuah level. Murid masuk dengan kode, lalu kamu yang mengatur soal berikutnya.",
      },
    ],
  },
};

const MODES: Mode[] = ["student", "teacher"];

export default function HelpButton({ initialMode }: { initialMode: Mode }) {
  const [open, setOpen] = useState(false);
  const [mode, setMode] = useState<Mode>(initialMode);
  const closeRef = useRef<HTMLButtonElement>(null);
  const triggerRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (!open) return;
    closeRef.current?.focus();
    const trigger = triggerRef.current;
    const prevOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") setOpen(false);
    }
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("keydown", onKey);
      document.body.style.overflow = prevOverflow;
      trigger?.focus();
    };
  }, [open]);

  function openGuide() {
    setMode(initialMode);
    setOpen(true);
  }

  const guide = GUIDES[mode];

  return (
    <>
      <button
        ref={triggerRef}
        onClick={openGuide}
        className="btn-ghost"
        aria-label="Bantuan"
        aria-haspopup="dialog"
      >
        <QuestionIcon size={20} />
        <span className="hidden sm:inline">Bantuan</span>
      </button>
      {open && (
        <div
          className="fixed inset-0 z-50 flex items-end justify-center bg-ink/50 p-0 sm:items-center sm:p-4"
          onClick={() => setOpen(false)}
        >
          <div
            role="dialog"
            aria-modal="true"
            aria-labelledby="help-title"
            className="pop-in flex max-h-[92vh] w-full max-w-lg flex-col overflow-hidden rounded-t-3xl border-2 border-rule bg-paper sm:rounded-3xl"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-start gap-3 border-b-2 border-rule p-4">
              <Mascot mood="happy" size={56} className="shrink-0" />
              <div className="min-w-0 flex-1">
                <h2 id="help-title" className="font-display text-2xl font-extrabold">
                  Cara memakai EduMap
                </h2>
                <p className="text-base">{guide.intro}</p>
              </div>
              <button
                ref={closeRef}
                onClick={() => setOpen(false)}
                className="btn-ghost btn-sm shrink-0"
                aria-label="Tutup bantuan"
              >
                <CrossIcon size={20} />
              </button>
            </div>
            <div className="flex gap-2 px-4 pt-3" role="tablist" aria-label="Pilih panduan">
              {MODES.map((m) => (
                <button
                  key={m}
                  role="tab"
                  aria-selected={mode === m}
                  onClick={() => setMode(m)}
                  className={`${mode === m ? "btn-sky" : "btn-ghost"} btn-sm flex-1`}
                >
                  Sebagai {GUIDES[m].label}
                </button>
              ))}
            </div>
            <ol className="flex flex-col gap-3 overflow-y-auto p-4">
              {guide.steps.map((s, i) => (
                <li key={s.title} className="card flex gap-3">
                  <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-highlight font-display text-xl font-extrabold text-ink">
                    {i + 1}
                  </span>
                  <div className="min-w-0">
                    <h3 className="font-display text-lg font-bold">{s.title}</h3>
                    <p className="text-base">{s.text}</p>
                  </div>
                </li>
              ))}
            </ol>
            <div className="border-t-2 border-rule p-4">
              <button onClick={() => setOpen(false)} className="btn-primary w-full">
                Mengerti!
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
