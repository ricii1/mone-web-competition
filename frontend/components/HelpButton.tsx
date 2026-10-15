"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useRef, useState, type KeyboardEvent } from "react";
import Mascot from "@/components/Mascot";
import { ArrowRightIcon, CrossIcon, QuestionIcon } from "@/components/icons";

type Mode = "student" | "teacher";
type Destination = "dashboard" | "class" | "lesson" | "leaderboard" | "live";
interface Step {
  title: string;
  text: string;
  tip: string;
  action: string;
  destination: Destination;
}
interface Guide {
  label: string;
  intro: string;
  steps: Step[];
  questions: { question: string; answer: string }[];
}

const GUIDES: Record<Mode, Guide> = {
  student: {
    label: "Murid",
    intro: "Yuk, belajar bersama!",
    steps: [
      {
        title: "Masuk ke kelas",
        text: "Pilih kelas yang terbuka. Untuk kelas rahasia, tulis kode dari gurumu lalu ketuk Gabung.",
        tip: "Kelas yang sudah kamu ikuti ada di bagian Kelas saya.",
        action: "Cari kelas",
        destination: "dashboard",
      },
      {
        title: "Buka peta level",
        text: "Ketuk kelasmu untuk melihat peta. Mulai dari level pertama yang terbuka.",
        tip: "Peta bergeser? Ketuk Tampilan awal untuk mengembalikannya.",
        action: "Buka peta kelas",
        destination: "class",
      },
      {
        title: "Baca, lalu jawab kuis",
        text: "Baca materinya dan rangkumannya. Setelah itu jawab kuis. Tidak perlu terburu-buru ya.",
        tip: "Ingin membaca sumber aslinya? Buka Materi PDF dari guru di halaman peta.",
        action: "Mulai belajar",
        destination: "lesson",
      },
      {
        title: "Buka level berikutnya",
        text: "Nilai 70% atau lebih membuka level berikutnya. Kalau belum berhasil, baca lagi dan coba kuisnya sekali lagi!",
        tip: "Nilai terbaikmu tetap disimpan. Mengulang kuis tidak menurunkannya.",
        action: "Lihat levelku",
        destination: "class",
      },
      {
        title: "Lihat peringkat",
        text: "Buka papan peringkat untuk melihat hasil belajarmu bersama teman-teman.",
        tip: "Peringkat memakai jumlah nilai terbaik dari semua level.",
        action: "Lihat peringkat",
        destination: "leaderboard",
      },
      {
        title: "Ikut kuis bersama",
        text: "Kalau gurumu mengajak main kuis bersama, buka Kuis bersama lalu tulis kode sesi dari guru.",
        tip: "Ikuti kelasnya terlebih dahulu. Kuis bersama tidak mengubah level belajarmu.",
        action: "Buka kuis bersama",
        destination: "live",
      },
    ],
    questions: [
      {
        question: "Kenapa levelku masih terkunci?",
        answer: "Selesaikan level sebelumnya dengan nilai minimal 70%. Setelah lulus, level berikutnya akan terbuka.",
      },
      {
        question: "PDF tidak muncul di HP?",
        answer: "Ketuk Unduh PDF, lalu buka file itu dengan pembaca PDF di HP. Kamu tetap bisa membaca artikel levelnya.",
      },
      {
        question: "Kode kuis tidak bisa dipakai?",
        answer: "Pastikan kamu sudah mengikuti kelasnya. Tulis kode sesi kuis dari guru, bukan kode untuk masuk kelas.",
      },
    ],
  },
  teacher: {
    label: "Guru",
    intro: "Pilih langkah yang ingin dicoba.",
    steps: [
      {
        title: "Buat kelas baru",
        text: "Isi nama kelas dan pilih siapa yang boleh masuk: semua murid atau hanya murid dengan kode.",
        tip: "Akun yang sama bisa dipakai sebagai guru dan murid. Ganti mode lewat tombol di atas.",
        action: "Buka daftar kelas",
        destination: "dashboard",
      },
      {
        title: "Unggah dan periksa PDF",
        text: "Unggah PDF di halaman kelas. Tunggu status Siap, lalu buka Lihat pembagian materi untuk memeriksa judul, urutan, dan halaman sumber.",
        tip: "Lihat PDF membuka file asli. PDF yang gagal bisa dicoba proses lagi.",
        action: "Buka materi kelas",
        destination: "class",
      },
      {
        title: "Buat level dan soal",
        text: "Setelah sumber siap, ketuk Buat level. Progres dan level yang selesai akan muncul di halaman kelas.",
        tip: "Hasilnya masih draf. Tunggu proses selesai sebelum meninjau semuanya.",
        action: "Buka pembuatan level",
        destination: "class",
      },
      {
        title: "Tinjau dan setujui",
        text: "Buka setiap level. Periksa artikel, rangkuman, sumber, dan soal. Perbaiki jika perlu, lalu setujui soal dan materi level.",
        tip: "Pertanyaan yang sama tidak boleh diulang dalam satu level, termasuk jika hanya spasi atau huruf besarnya berbeda.",
        action: "Buka tinjauan level",
        destination: "lesson",
      },
      {
        title: "Terbitkan kelas",
        text: "Setiap materi level harus disetujui dan punya minimal satu soal yang disetujui. Setelah itu ketuk Terbitkan kelas dan bagikan kelasnya.",
        tip: "Untuk kelas dengan kode, bagikan kode masuknya kepada murid. Kelas contoh tidak bisa diterbitkan.",
        action: "Buka halaman kelas",
        destination: "class",
      },
      {
        title: "Pimpin kuis bersama",
        text: "Buka Kuis bersama di halaman kelas. Pilih level, bagikan kode sesi, lalu mulai kuis ketika murid sudah siap.",
        tip: "Bapak/Ibu mengatur soal berikutnya dan mengakhiri sesi. Kode sesi berbeda dari kode masuk kelas.",
        action: "Buka kuis bersama",
        destination: "live",
      },
    ],
    questions: [
      {
        question: "PDF gagal diproses?",
        answer: "Klik Coba proses lagi pada PDF gagal. Pastikan PDF berisi tulisan yang bisa disalin, bukan hanya foto. Jika file sudah tidak diperlukan dan belum dipakai sebagai sumber, pilih Hapus PDF gagal.",
      },
      {
        question: "Kelas belum bisa diterbitkan?",
        answer: "Tunggu pembuatan level selesai. Periksa bahwa setiap materi level disetujui dan memiliki setidaknya satu soal yang disetujui.",
      },
      {
        question: "Bagaimana menghapus kelas?",
        answer: "Buka bagian Hapus kelas di bawah peta, lalu ketik nama kelas sebagai konfirmasi. Akhiri kuis bersama dan tunggu pemrosesan PDF atau level selesai dahulu. Semua materi dan progres kelas akan dihapus permanen.",
      },
    ],
  },
};
const MODES: Mode[] = ["student", "teacher"];

export default function HelpButton({ initialMode }: { initialMode: Mode }) {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);
  const [mode, setMode] = useState<Mode>(initialMode);
  const [step, setStep] = useState(0);
  const [understood, setUnderstood] = useState<Record<Mode, number[]>>({ student: [], teacher: [] });
  const dialogRef = useRef<HTMLDialogElement>(null);
  const panelRef = useRef<HTMLDivElement>(null);
  const closeRef = useRef<HTMLButtonElement>(null);
  const contentRef = useRef<HTMLDivElement>(null);
  const tabRefs = useRef<Record<Mode, HTMLButtonElement | null>>({ student: null, teacher: null });

  useEffect(() => {
    if (!open) return;
    const dialog = dialogRef.current;
    if (!dialog) return;
    // A native modal escapes the header's backdrop-filter containing block.
    dialog.showModal();
    if (panelRef.current) panelRef.current.scrollTop = 0;
    closeRef.current?.focus({ preventScroll: true });
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      dialog.close();
      document.body.style.overflow = previousOverflow;
    };
  }, [open]);

  function openGuide() {
    setMode(initialMode);
    setStep(0);
    setOpen(true);
  }
  function selectMode(next: Mode) {
    setMode(next);
    setStep(0);
    if (panelRef.current) panelRef.current.scrollTop = 0;
  }
  function onTabKey(event: KeyboardEvent<HTMLButtonElement>) {
    let next: Mode;
    if (event.key === "ArrowLeft" || event.key === "ArrowRight") next = mode === "student" ? "teacher" : "student";
    else if (event.key === "Home") next = MODES[0];
    else if (event.key === "End") next = MODES[MODES.length - 1];
    else return;
    event.preventDefault();
    selectMode(next);
    tabRefs.current[next]?.focus();
  }
  function goToStep(next: number) {
    setStep(next);
    contentRef.current?.scrollIntoView({ block: "nearest" });
  }
  function toggleUnderstood() {
    setUnderstood((current) => ({
      ...current,
      [mode]: current[mode].includes(step)
        ? current[mode].filter((index) => index !== step)
        : [...current[mode], step],
    }));
  }

  const guide = GUIDES[mode];
  const current = guide.steps[step];
  const isUnderstood = understood[mode].includes(step);
  const match = pathname.match(/^\/(teacher|student)\/classes\/([^/]+)(?:\/levels\/([^/]+))?/);
  const classId = mode === initialMode ? match?.[2] : undefined;
  const levelId = mode === initialMode ? match?.[3] : undefined;
  let href = `/${mode}`;
  if (classId && current.destination !== "dashboard") {
    href = mode === "teacher" ? `/teacher/classes/${classId}` : `/student/classes/${classId}/map`;
    if (current.destination === "lesson" && levelId) href = `/${mode}/classes/${classId}/levels/${levelId}`;
    if (current.destination === "leaderboard") href = `/student/classes/${classId}/leaderboard`;
    if (current.destination === "live" && mode === "teacher") href = `/teacher/classes/${classId}/live`;
  }
  if (current.destination === "live" && mode === "student") href = "/student/live";
  const actionLabel = !classId && current.destination !== "dashboard" && !(current.destination === "live" && mode === "student") ? "Pilih kelas dulu" : current.action;

  return <>
    <button onClick={openGuide} className="btn-ghost" aria-label="Bantuan" aria-haspopup="dialog">
      <QuestionIcon size={20} /><span className="hidden sm:inline">Bantuan</span>
    </button>
    <dialog ref={dialogRef} aria-labelledby="help-title" onCancel={() => setOpen(false)} onClose={() => setOpen(false)}
      onClick={(event) => { if (event.target === event.currentTarget) setOpen(false); }}
      className="fixed inset-0 m-0 h-[100dvh] max-h-none w-full max-w-none border-0 bg-transparent p-3 text-ink backdrop:bg-ink/50 sm:p-6"
      style={{ paddingTop: "max(12px, env(safe-area-inset-top))", paddingBottom: "max(12px, env(safe-area-inset-bottom))" }}>
      <div className="flex h-full items-end justify-center sm:items-center" onClick={(event) => { if (event.target === event.currentTarget) setOpen(false); }}>
        <div ref={panelRef} className="flex max-h-full w-full max-w-xl flex-col overflow-y-auto overscroll-contain rounded-3xl border-2 border-rule bg-paper shadow-xl">
          <div className="sticky top-0 z-10 flex shrink-0 items-start gap-3 border-b-2 border-rule bg-paper p-4">
            <Mascot mood="happy" size={48} className="hidden shrink-0 min-[400px]:block" />
            <div className="min-w-0 flex-1"><h2 id="help-title" className="text-xl sm:text-2xl">Bantuan Bu Hoo</h2><p className="mt-1 text-base">{guide.intro}</p></div>
            <button ref={closeRef} type="button" onClick={() => setOpen(false)} className="btn-ghost min-h-[48px] min-w-[48px] shrink-0" aria-label="Tutup bantuan"><CrossIcon size={20} /></button>
          </div>
          <div className="grid shrink-0 grid-cols-2 gap-2 px-4 pt-3" role="tablist" aria-label="Pilih panduan">
            {MODES.map((item) => <button key={item} ref={(element) => { tabRefs.current[item] = element; }} type="button" role="tab"
              id={`help-tab-${item}`} aria-selected={mode === item} aria-controls={`help-panel-${item}`} tabIndex={mode === item ? 0 : -1}
              onClick={() => selectMode(item)} onKeyDown={onTabKey} className={`${mode === item ? "btn-sky" : "btn-ghost"} min-h-[48px] px-2`}>{GUIDES[item].label}</button>)}
          </div>
          <div role="tabpanel" id={`help-panel-${mode}`} aria-labelledby={`help-tab-${mode}`} className="shrink-0 p-4">
            <p className="mb-2 text-sm font-semibold text-ink/75">Langkah {step + 1}/{guide.steps.length} · {understood[mode].length} sudah dipahami</p>
            <select aria-label="Pilih langkah" value={step} onChange={(event) => goToStep(Number(event.target.value))} className="input-box mb-4 min-h-[48px] sm:hidden">
              {guide.steps.map((item, index) => <option key={item.title} value={index}>{index + 1}. {item.title}</option>)}
            </select>
            <ol className="mb-4 hidden grid-cols-6 gap-2 sm:grid" aria-label="Langkah panduan">
              {guide.steps.map((item, index) => <li key={item.title}><button type="button" onClick={() => goToStep(index)} aria-current={step === index ? "step" : undefined}
                aria-label={`Langkah ${index + 1}: ${item.title}${understood[mode].includes(index) ? ", sudah dipahami" : ""}`}
                className={`flex h-12 w-full items-center justify-center rounded-2xl border-2 font-display text-xl font-bold ${step === index ? "border-sky-dark bg-sky-soft" : understood[mode].includes(index) ? "border-grass bg-grass-soft" : "border-rule bg-white"}`}>{index + 1}</button></li>)}
            </ol>
            <div ref={contentRef} className="rounded-2xl border-2 border-rule bg-white p-4" aria-live="polite" aria-atomic="true">
              <p className="mb-1 text-sm font-semibold text-sky-dark">Langkah {step + 1} dari {guide.steps.length}</p>
              <h3 className="text-xl">{current.title}</h3><p className="mt-2 text-base leading-relaxed">{current.text}</p><p className="mt-3 rounded-xl bg-highlight/20 p-3 text-base">{current.tip}</p>
            </div>
            <div className="mt-3 flex flex-wrap gap-2">
              <button type="button" onClick={toggleUnderstood} aria-pressed={isUnderstood} className={`${isUnderstood ? "btn-primary" : "btn-ghost"} min-h-[48px]`}>{isUnderstood ? "Sudah paham ✓" : "Aku sudah paham"}</button>
              <Link href={href} onClick={() => setOpen(false)} className="btn-sky min-h-[48px]">{actionLabel}<ArrowRightIcon size={20} /></Link>
            </div>
            <div className="mt-5 border-t-2 border-rule pt-4"><h3 className="mb-2 text-lg">Butuh bantuan lain?</h3>
              {guide.questions.map((item) => <details key={item.question} className="mb-2 rounded-xl border border-rule bg-white"><summary className="min-h-[48px] cursor-pointer px-3 py-3 font-semibold">{item.question}</summary><p className="px-3 pb-3 text-base leading-relaxed">{item.answer}</p></details>)}
            </div>
          </div>
          <div className="sticky bottom-0 flex shrink-0 gap-2 border-t-2 border-rule bg-paper p-3">
            <button type="button" className="btn-ghost min-h-[48px] flex-1 px-2" disabled={step === 0} onClick={() => goToStep(step - 1)}>Sebelumnya</button>
            {step < guide.steps.length - 1
              ? <button type="button" className="btn-primary min-h-[48px] flex-1 px-2" onClick={() => goToStep(step + 1)}>Berikutnya</button>
              : <button type="button" className="btn-primary min-h-[48px] flex-1 px-2" onClick={() => setOpen(false)}>Selesai</button>}
          </div>
        </div>
      </div>
    </dialog>
  </>;
}
