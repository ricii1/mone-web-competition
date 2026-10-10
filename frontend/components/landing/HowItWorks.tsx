import type { ReactNode } from "react";
import { FileIcon, MapIcon, PlayIcon, UploadIcon } from "@/components/icons";
import Reveal from "@/components/landing/Reveal";
import Stars from "@/components/Stars";

interface Step {
  n: number;
  title: string;
  text: string;
  node: string;
  icon: ReactNode;
  extra: ReactNode;
}

const STEPS: Step[] = [
  {
    n: 1,
    title: "Guru unggah materi",
    text: "Guru membuat kelas dan mengunggah materi PDF.",
    node: "bg-sky-dark shadow-[0_8px_0_0_#154f82]",
    icon: <UploadIcon size={40} />,
    extra: (
      <span className="inline-flex items-center gap-2 rounded-2xl border-2 border-sky bg-sky-soft px-3 py-1.5 text-sm font-bold text-sky-dark">
        <FileIcon size={18} /> IPA-Siklus-Air.pdf
      </span>
    ),
  },
  {
    n: 2,
    title: "AI menyusun peta",
    text: "AI membuat level dan soal sebagai draf. Guru memeriksa lalu menerbitkan.",
    node: "bg-grape-dark shadow-[0_8px_0_0_#46288f]",
    icon: <MapIcon size={40} />,
    extra: (
      <span className="flex flex-wrap gap-2 text-sm font-bold">
        <span className="rounded-full bg-grape-soft px-3 py-1 text-grape-dark">Level 1 draf</span>
        <span className="rounded-full bg-grass-soft px-3 py-1 text-grass-dark">Disetujui</span>
      </span>
    ),
  },
  {
    n: 3,
    title: "Murid bermain",
    text: "Murid membaca, menjawab kuis, mengumpulkan bintang, dan membuka level berikutnya.",
    node: "bg-highlight text-ink shadow-[0_8px_0_0_#c98f00]",
    icon: <PlayIcon size={40} />,
    extra: <Stars percent={100} size={26} />,
  },
];

/** A little game map: three stops on a dotted trail that draws itself as you scroll. */
export default function HowItWorks() {
  return (
    <div className="relative">
      {/* Trail: straight on phones, winding on wider screens. */}
      <Reveal className="pointer-events-none absolute inset-0">
        <div aria-hidden="true" className="trail absolute bottom-10 left-[44px] top-10 border-l-[6px] border-dotted border-highlight-dark md:hidden" />
        <svg aria-hidden="true" className="trail absolute inset-0 hidden h-full w-full md:block" viewBox="0 0 100 300" preserveAspectRatio="none">
          <path d="M25 50 C 25 105, 75 95, 75 150 C 75 205, 25 195, 25 250" fill="none" stroke="#E5A800" strokeWidth="6" strokeLinecap="round" strokeDasharray="0.1 14" vectorEffect="non-scaling-stroke" />
        </svg>
      </Reveal>

      <ol className="relative grid gap-10 md:grid-rows-3 md:gap-0">
        {STEPS.map((s, i) => {
          const right = i % 2 === 1;
          return (
            <li key={s.n} className="grid items-center gap-4 md:h-[300px] md:grid-cols-2 md:gap-0">
              <Reveal
                variant={right ? "right" : "left"}
                className={`flex items-center gap-5 md:justify-center ${right ? "md:order-2" : ""}`}
              >
                <div className="relative shrink-0">
                  {i === 2 && (
                    <span className="bounce-bubble absolute -top-9 left-1/2 -translate-x-1/2 rounded-2xl bg-ink px-3 py-1 font-display text-base font-bold text-chalk after:absolute after:-bottom-1.5 after:left-1/2 after:h-3 after:w-3 after:-translate-x-1/2 after:rotate-45 after:bg-ink">
                      Mulai!
                    </span>
                  )}
                  <span aria-hidden="true" className="node-ring absolute inset-0 rounded-full border-4 border-highlight" />
                  <span className={`step-node relative flex h-24 w-24 items-center justify-center rounded-full border-4 border-white text-white ${s.node}`}>
                    {s.icon}
                    <span className="absolute -left-2 -top-2 flex h-9 w-9 items-center justify-center rounded-full border-2 border-white bg-ink font-display text-lg font-bold text-chalk">
                      {s.n}
                    </span>
                  </span>
                </div>
                <div className="md:hidden">
                  <h3 className="text-xl font-extrabold">{s.title}</h3>
                </div>
              </Reveal>
              <Reveal variant={right ? "left" : "right"} delay={150} className={right ? "md:order-1 md:pr-10 md:text-right" : "md:pl-10"}>
                <div className={`surface lift ${right ? "md:ml-auto" : ""} max-w-md`}>
                  <h3 className="mb-1 hidden text-2xl font-extrabold md:block">{s.title}</h3>
                  <p className="mb-3 text-base text-ink/85">{s.text}</p>
                  {s.extra}
                </div>
              </Reveal>
            </li>
          );
        })}
      </ol>
    </div>
  );
}
