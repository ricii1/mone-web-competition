import type { ReactNode } from "react";
import {
  BookIcon,
  CheckIcon,
  CrownIcon,
  FileIcon,
  LightbulbIcon,
  PlayIcon,
  RefreshIcon,
  StarIcon,
  UploadIcon,
  UsersIcon,
} from "@/components/icons";
import Reveal from "@/components/landing/Reveal";
import Mascot from "@/components/Mascot";

/** Colourful "world map" tiles; each one has a tiny looping scene instead of a plain icon. */
function Tile({
  children,
  className,
  tone,
  delay = 0,
  variant = "zoom",
}: {
  children: ReactNode;
  className: string;
  tone: string;
  delay?: number;
  variant?: "up" | "left" | "right" | "zoom" | "flip";
}) {
  return (
    <Reveal variant={variant} delay={delay} className={`tile lift overflow-hidden rounded-4xl border-4 border-white p-5 sm:p-6 ${tone} ${className}`}>
      {children}
    </Reveal>
  );
}

function TileTitle({ icon, title, text, dark = false }: { icon: ReactNode; title: string; text: string; dark?: boolean }) {
  return (
    <div className="relative z-10">
      <span className={`lift-icon mb-3 inline-flex h-12 w-12 items-center justify-center rounded-2xl ${dark ? "bg-white/15 text-highlight" : "bg-white/80 text-ink"}`}>{icon}</span>
      <h3 className="mb-1 text-2xl font-extrabold leading-tight">{title}</h3>
      <p className={`max-w-sm text-base ${dark ? "text-chalk-dim" : "text-ink/80"}`}>{text}</p>
    </div>
  );
}

function Node({ color, children, className = "" }: { color: string; children: ReactNode; className?: string }) {
  return (
    <span className={`flex h-12 w-12 items-center justify-center rounded-full border-4 border-white text-white shadow-[0_4px_0_0_rgb(0_0_0/0.18)] ${color} ${className}`}>
      {children}
    </span>
  );
}

function MapScene() {
  return (
    <div aria-hidden="true" className="relative mt-5 flex h-36 items-center justify-between rounded-3xl bg-white/60 px-4">
      <div className="float-slow flex h-16 w-14 flex-col items-center justify-center rounded-xl border-2 border-sky-dark bg-white text-sky-dark">
        <FileIcon size={26} />
        <span className="text-[10px] font-extrabold">PDF</span>
      </div>
      <div className="mx-1 flex-1 border-t-4 border-dotted border-sky-dark/60" />
      <span className="sparkle-pulse text-highlight-dark"><StarIcon size={26} /></span>
      <div className="mx-1 flex-1 border-t-4 border-dotted border-sky-dark/60" />
      <div className="relative flex items-end gap-2">
        <Node color="bg-grass-dark" className="mb-0"><CheckIcon size={22} /></Node>
        <Node color="bg-highlight text-ink" className="-mb-5 pulse-soft"><PlayIcon size={22} /></Node>
        <Node color="bg-grape-dark" className="mb-4"><CrownIcon size={22} /></Node>
      </div>
    </div>
  );
}

function QuizScene() {
  const answers = ["Panas matahari", "Angin malam", "Cahaya bulan"];
  return (
    <div aria-hidden="true" className="mt-5 grid gap-2 rounded-3xl bg-white/60 p-3">
      <div className="h-3 w-3/4 rounded-full bg-ink/15" />
      <div className="h-3 w-1/2 rounded-full bg-ink/10" />
      {answers.map((a, i) => (
        <div
          key={a}
          className={`flex items-center justify-between rounded-2xl border-2 px-3 py-2 text-sm font-bold ${i === 0 ? "answer-correct border-grass-dark bg-grass-soft text-grass-dark" : "border-rule bg-white text-ink/70"}`}
        >
          {a}
          {i === 0 && <CheckIcon size={18} />}
        </div>
      ))}
    </div>
  );
}

function PodiumScene() {
  const bars = [
    { h: "h-14", c: "bg-sky", n: 2 },
    { h: "h-20", c: "bg-highlight-dark", n: 1 },
    { h: "h-10", c: "bg-coral", n: 3 },
  ];
  return (
    <div aria-hidden="true" className="mt-5 flex h-28 items-end justify-center gap-2">
      {bars.map((b, i) => (
        <div key={b.n} className="flex flex-col items-center">
          {b.n === 1 && <span className="float-slow text-highlight-dark"><CrownIcon size={24} /></span>}
          <div className={`podium w-16 rounded-t-2xl ${b.h} ${b.c} flex items-start justify-center pt-1 font-display text-xl font-extrabold text-white`} style={{ animationDelay: `${i * 150}ms` }}>
            {b.n}
          </div>
        </div>
      ))}
    </div>
  );
}

function LiveScene() {
  const kids = ["bg-sky", "bg-grass", "bg-highlight", "bg-grape", "bg-white"];
  return (
    <div aria-hidden="true" className="mt-5 rounded-3xl bg-white/60 p-3 text-center">
      <p className="text-xs font-extrabold uppercase tracking-wider text-ink/60">Kode kelas</p>
      <p className="mb-2 font-display text-3xl font-extrabold tracking-widest text-coral-dark">4 8 2 1</p>
      <div className="flex justify-center -space-x-2">
        {kids.map((k, i) => (
          <span key={i} className="join-pop h-8 w-8 rounded-full border-2 border-white" style={{ animationDelay: `${i * 500}ms` }}>
            <span className={`block h-full w-full rounded-full ${k}`} />
          </span>
        ))}
      </div>
    </div>
  );
}

function RoleScene() {
  return (
    <div aria-hidden="true" className="mt-5 flex justify-center">
      <div className="role-toggle relative flex rounded-full bg-white/70 p-1 font-display text-lg font-extrabold">
        <span className="role-knob absolute inset-y-1 left-1 w-[calc(50%-4px)] rounded-full bg-grape-dark" />
        <span className="role-a relative z-10 px-5 py-1.5">Guru</span>
        <span className="role-b relative z-10 px-5 py-1.5">Murid</span>
      </div>
    </div>
  );
}

function TruthScene() {
  return (
    <div aria-hidden="true" className="relative mt-5 flex flex-col items-center gap-3 sm:flex-row sm:justify-end sm:gap-4">
      <div className="float-slow flex h-20 w-16 shrink-0 flex-col gap-1.5 rounded-xl bg-white p-2 shadow-lg">
        <span className="h-1.5 w-full rounded bg-ink/20" />
        <span className="h-1.5 w-3/4 rounded bg-highlight" />
        <span className="h-1.5 w-full rounded bg-ink/20" />
        <span className="h-1.5 w-2/3 rounded bg-ink/20" />
      </div>
      <div className="rounded-2xl rounded-bl-sm bg-white px-4 py-2 text-sm font-bold text-ink shadow-lg">
        Menurut materi gurumu: air menguap karena panas matahari.
      </div>
      <Mascot mood="thinking" size={70} className="bob shrink-0" />
    </div>
  );
}

export default function FeatureBento() {
  return (
    <ul className="grid gap-4 sm:grid-cols-2 lg:grid-cols-6">
      <li className="contents">
        <Tile tone="bg-sky-soft shadow-[0_8px_0_0_#9fd0f3]" className="lg:col-span-3" variant="left">
          <TileTitle icon={<UploadIcon size={28} />} title="Unggah PDF, jadi peta level" text="Guru cukup mengunggah materi. AI menyusun peta level sebagai draf. Guru yang memeriksa dan menyetujui." />
          <MapScene />
        </Tile>
      </li>
      <li className="contents">
        <Tile tone="bg-grass-soft shadow-[0_8px_0_0_#9ad9ae]" className="lg:col-span-3" variant="right" delay={120}>
          <TileTitle icon={<BookIcon size={28} />} title="Bacaan pendek dan kuis" text="Tiap level punya bacaan 2-3 menit, rangkuman, poin penting, lalu kuis pilihan ganda." />
          <QuizScene />
        </Tile>
      </li>
      <li className="contents">
        <Tile tone="bg-highlight/40 shadow-[0_8px_0_0_#e6c25c]" className="lg:col-span-2" variant="up">
          <TileTitle icon={<StarIcon size={28} />} title="Bintang dan papan juara" text="Kumpulkan bintang, lihat siapa yang paling rajin di kelas." />
          <PodiumScene />
        </Tile>
      </li>
      <li className="contents">
        <Tile tone="bg-coral-soft shadow-[0_8px_0_0_#f3a89f]" className="lg:col-span-2" variant="up" delay={120}>
          <TileTitle icon={<UsersIcon size={28} />} title="Kelas langsung ala Kahoot" text="Satu kode, semua murid menjawab bersama. Skor naik seketika." />
          <LiveScene />
        </Tile>
      </li>
      <li className="contents">
        <Tile tone="bg-grape-soft shadow-[0_8px_0_0_#c3adf3]" className="sm:col-span-2 lg:col-span-2" variant="up" delay={240}>
          <TileTitle icon={<RefreshIcon size={28} />} title="Satu akun, dua peran" text="Email yang sama bisa jadi guru untuk kelasnya dan murid di kelas orang lain." />
          <RoleScene />
        </Tile>
      </li>
      <li className="contents">
        <Tile tone="bg-ink text-chalk shadow-[0_8px_0_0_#0f1826]" className="sm:col-span-2 lg:col-span-6" variant="flip">
          <div className="grid items-center gap-2 sm:grid-cols-2">
            <TileTitle dark icon={<LightbulbIcon size={28} />} title="Hanya dari materi guru" text="AI hanya memakai materi yang diunggah guru. Kalau jawabannya tidak ada, AI bilang tidak tahu." />
            <TruthScene />
          </div>
        </Tile>
      </li>
    </ul>
  );
}
