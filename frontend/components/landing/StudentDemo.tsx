"use client";

import { useState } from "react";
import AnswerTile, { type TileState } from "@/components/AnswerTile";
import Confetti from "@/components/Confetti";
import { ArrowRightIcon, CheckIcon, LockIcon, RefreshIcon, StarIcon } from "@/components/icons";
import Markdown from "@/components/Markdown";
import Mascot from "@/components/Mascot";
import Stars from "@/components/Stars";
import { starsFor } from "@/lib/stars";
import { DEMO_ARTICLE, DEMO_LEVEL_TITLE, DEMO_QUESTIONS } from "./demoData";

type Phase = "map" | "read" | "quiz" | "result";

const NODES = [
  { x: 50, y: 110, label: "1" },
  { x: 150, y: 60, label: "2" },
  { x: 250, y: 100, label: "3" },
] as const;

function MiniMap({ done, onOpen }: { done: boolean; onOpen: () => void }) {
  return (
    <div>
      <svg viewBox="0 0 300 160" className="mx-auto w-full max-w-md" role="group" aria-label="Peta level contoh">
        <path
          d="M50 110 Q100 50 150 60 T250 100"
          fill="none"
          stroke="#E6DCC0"
          strokeWidth="6"
          strokeDasharray="2 12"
          strokeLinecap="round"
        />
        {NODES.map((n, i) => {
          const unlocked = i === 0 || (i === 1 && done);
          const completed = i === 0 && done;
          const fill = completed ? "#2A9450" : unlocked ? "#FFC83D" : "#B9C2CE";
          const body = (
            <>
              <circle cx={n.x} cy={n.y + 4} r="24" fill="#1B2A41" opacity=".18" />
              <circle cx={n.x} cy={n.y} r="24" fill={fill} stroke="#fff" strokeWidth="4" />
              {unlocked ? (
                <text x={n.x} y={n.y + 8} textAnchor="middle" fontSize="22" fontWeight="800" fill={completed ? "#fff" : "#1B2A41"} fontFamily="sans-serif">
                  {n.label}
                </text>
              ) : (
                <g fill="#fff">
                  <rect x={n.x - 8} y={n.y - 2} width="16" height="12" rx="3" />
                  <path d={`M${n.x - 5} ${n.y - 2} v-4 a5 5 0 0 1 10 0 v4`} fill="none" stroke="#fff" strokeWidth="3" strokeLinecap="round" />
                </g>
              )}
            </>
          );
          return unlocked && i === 0 ? (
            <g
              key={n.label}
              role="button"
              tabIndex={0}
              aria-label={`Buka level 1: ${DEMO_LEVEL_TITLE}`}
              className="cursor-pointer"
              onClick={onOpen}
              onKeyDown={(e) => {
                if (e.key === "Enter" || e.key === " ") {
                  e.preventDefault();
                  onOpen();
                }
              }}
            >
              <circle cx={n.x} cy={n.y} r="30" fill="transparent" />
              {body}
            </g>
          ) : (
            <g key={n.label} aria-label={`Level ${n.label} ${unlocked ? "terbuka" : "terkunci"}`} role="img">
              {body}
            </g>
          );
        })}
      </svg>
      <p className="mt-2 text-center text-base font-semibold text-ink/80">
        {done ? "Hebat! Level 2 terbuka. Di kelas sungguhan kamu bisa lanjut terus." : "Ketuk level 1 yang kuning untuk mulai."}
      </p>
      <div className="mt-4 flex justify-center">
        <button type="button" className="btn-primary" onClick={onOpen}>
          {done ? "Main level 1 lagi" : "Buka level 1"}
          <ArrowRightIcon size={22} />
        </button>
      </div>
    </div>
  );
}

export default function StudentDemo() {
  const [phase, setPhase] = useState<Phase>("map");
  const [q, setQ] = useState(0);
  const [chosen, setChosen] = useState<number | null>(null);
  const [correctCount, setCorrectCount] = useState(0);
  const [done, setDone] = useState(false);

  const question = DEMO_QUESTIONS[q];
  const percent = Math.round((correctCount / DEMO_QUESTIONS.length) * 100);

  function startQuiz() {
    setQ(0);
    setChosen(null);
    setCorrectCount(0);
    setPhase("quiz");
  }

  function choose(i: number) {
    if (chosen !== null) return;
    setChosen(i);
    if (i === question.correct) setCorrectCount((c) => c + 1);
  }

  function next() {
    if (q + 1 < DEMO_QUESTIONS.length) {
      setQ(q + 1);
      setChosen(null);
    } else {
      if (starsFor(percent) > 0) setDone(true);
      setPhase("result");
    }
  }

  function tileState(i: number): TileState {
    if (chosen === null) return "idle";
    if (i === question.correct) return "correct";
    if (i === chosen) return "wrong";
    return "dim";
  }

  return (
    <div className="kid" data-testid="student-demo" data-phase={phase}>
      {phase === "map" && <MiniMap done={done} onOpen={() => setPhase("read")} />}

      {phase === "read" && (
        <div>
          <p className="badge-sky mb-2">Level 1 &middot; Bacaan</p>
          <h4 className="mb-3 font-display text-2xl font-bold">{DEMO_LEVEL_TITLE}</h4>
          <Markdown source={DEMO_ARTICLE} />
          <div className="mt-6 flex flex-wrap gap-3">
            <button type="button" className="btn-primary" onClick={startQuiz}>
              Aku sudah paham, ayo kuis!
              <ArrowRightIcon size={22} />
            </button>
            <button type="button" className="btn-ghost" onClick={() => setPhase("map")}>
              Kembali ke peta
            </button>
          </div>
        </div>
      )}

      {phase === "quiz" && (
        <div>
          <p className="badge-grape mb-2">
            Soal {q + 1} dari {DEMO_QUESTIONS.length}
          </p>
          <h4 className="mb-4 font-display text-2xl font-bold">{question.text}</h4>
          <div className="grid gap-3 sm:grid-cols-2">
            {question.options.map((opt, i) => (
              <AnswerTile key={opt} index={i} label={opt} state={tileState(i)} disabled={chosen !== null} onClick={() => choose(i)} />
            ))}
          </div>
          <div aria-live="polite" className="mt-4">
            {chosen !== null && (
              <>
                <p
                  className={`note ${chosen === question.correct ? "border-grass bg-grass-soft text-correct-dark" : "border-coral bg-coral-soft text-alert"}`}
                >
                  {chosen === question.correct ? <CheckIcon size={24} /> : <RefreshIcon size={24} />}
                  <span>
                    {chosen === question.correct ? "Benar! Pintar sekali." : "Belum tepat, tidak apa-apa."} {question.explanation}
                  </span>
                </p>
                <div className="mt-4">
                  <button type="button" className="btn-primary" onClick={next}>
                    {q + 1 < DEMO_QUESTIONS.length ? "Soal berikutnya" : "Lihat hasil"}
                    <ArrowRightIcon size={22} />
                  </button>
                </div>
              </>
            )}
          </div>
        </div>
      )}

      {phase === "result" && (
        <div className="relative py-2 text-center" aria-live="polite">
          {starsFor(percent) > 0 && <Confetti />}
          <Mascot mood={starsFor(percent) > 0 ? "cheering" : "happy"} size={110} className="bob mx-auto" />
          <h4 className="mt-2 font-display text-3xl font-extrabold">
            {starsFor(percent) > 0 ? "Hebat sekali!" : "Ayo coba lagi!"}
          </h4>
          <p className="mb-2 text-lg font-semibold">
            Kamu benar {correctCount} dari {DEMO_QUESTIONS.length} soal ({percent}%).
          </p>
          <Stars percent={percent} size={44} animate className="justify-center" />
          <p className="mt-2 text-base text-ink/80">
            {starsFor(percent) > 0 ? "Level 2 sekarang terbuka di peta." : "Nilai 70% atau lebih untuk membuka level berikutnya."}
          </p>
          <div className="mt-5 flex flex-wrap justify-center gap-3">
            <button type="button" className="btn-primary" onClick={startQuiz}>
              <RefreshIcon size={22} />
              Main lagi
            </button>
            <button type="button" className="btn-ghost" onClick={() => setPhase("map")}>
              {done ? <StarIcon size={20} /> : <LockIcon size={20} />}
              Lihat peta
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
