"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import Confetti from "@/components/Confetti";
import {
  ArrowRightIcon,
  BookIcon,
  CheckIcon,
  CircleIcon,
  ClockIcon,
  CrossIcon,
  DiamondIcon,
  LightbulbIcon,
  MapIcon,
  PlayIcon,
  RefreshIcon,
  ScrollIcon,
  SparklesIcon,
  SquareIcon,
  StarIcon,
  TriangleIcon,
} from "@/components/icons";
import Markdown from "@/components/Markdown";
import Mascot from "@/components/Mascot";
import PageShell from "@/components/PageShell";
import Stars from "@/components/Stars";
import { ApiError, api } from "@/lib/api";
import { countWords, formatSource, readMinutes } from "@/lib/levels";
import type { Level, Question, QuizSubmitResult } from "@/lib/types";

// Mirrors backend PASSING_SCORE (services/progress_service.py); only used for teacher preview.
const PASSING_SCORE = 70;

type Stage = "lesson" | "quiz" | "result";

export type PlayerMode = "student" | "preview";

// Each answer tile has its own color AND shape, so color is never the only cue.
const TILES = [
  { Shape: TriangleIcon, idle: "border-sky bg-sky-soft", badge: "bg-sky-dark text-white", on: "border-sky-dark bg-sky-dark text-white" },
  { Shape: DiamondIcon, idle: "border-grass bg-grass-soft", badge: "bg-grass-dark text-white", on: "border-grass-dark bg-grass-dark text-white" },
  { Shape: CircleIcon, idle: "border-coral bg-coral-soft", badge: "bg-coral-dark text-white", on: "border-coral-dark bg-coral-dark text-white" },
  { Shape: SquareIcon, idle: "border-grape bg-grape-soft", badge: "bg-grape-dark text-white", on: "border-grape-dark bg-grape-dark text-white" },
] as const;

function PreviewBanner({ editorHref }: { editorHref: string }) {
  return (
    <div role="status" className="note mb-4 border-highlight bg-highlight/25 text-base">
      <span>
        <strong>Pratinjau guru.</strong> Tampilannya sama seperti murid. Jawaban dan skor tidak disimpan.{" "}
        <Link href={editorHref} className="link-text">
          Kembali ke editor
        </Link>
      </span>
    </div>
  );
}

/** Thin bar at the top that fills while the article scrolls. */
function ReadingProgress() {
  const barRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    let frame = 0;
    const update = () => {
      frame = 0;
      const doc = document.documentElement;
      const max = doc.scrollHeight - window.innerHeight;
      const ratio = max > 0 ? Math.min(1, Math.max(0, window.scrollY / max)) : 0;
      if (barRef.current) {
        barRef.current.style.transform = `scaleX(${ratio})`;
        barRef.current.parentElement?.setAttribute("aria-valuenow", String(Math.round(ratio * 100)));
      }
    };
    const onScroll = () => {
      if (!frame) frame = requestAnimationFrame(update);
    };
    update();
    window.addEventListener("scroll", onScroll, { passive: true });
    window.addEventListener("resize", onScroll);
    return () => {
      window.removeEventListener("scroll", onScroll);
      window.removeEventListener("resize", onScroll);
      if (frame) cancelAnimationFrame(frame);
    };
  }, []);
  return (
    <div
      role="progressbar"
      aria-label="Progres membaca"
      aria-valuenow={0}
      aria-valuemin={0}
      aria-valuemax={100}
      className="fixed inset-x-0 top-0 z-40 h-1.5 bg-transparent"
    >
      <div ref={barRef} className="h-full origin-left scale-x-0 bg-sky-dark" />
    </div>
  );
}

function SectionTitle({ icon, color, children }: { icon: React.ReactNode; color: string; children: React.ReactNode }) {
  return (
    <h2 className="mb-3 flex items-center gap-3 text-2xl">
      <span className={`flex h-10 w-10 items-center justify-center rounded-xl ${color}`}>{icon}</span>
      {children}
    </h2>
  );
}

export default function LevelPlayer({
  classId,
  levelId,
  mode,
}: {
  classId: string;
  levelId: string;
  mode: PlayerMode;
}) {
  const preview = mode === "preview";
  const [level, setLevel] = useState<Level | null>(null);
  const [allQuestions, setQuestions] = useState<Question[]>([]);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [result, setResult] = useState<QuizSubmitResult | null>(null);
  const [stage, setStage] = useState<Stage>("lesson");
  const [step, setStep] = useState(0);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [includeDrafts, setIncludeDrafts] = useState(false);

  useEffect(() => {
    Promise.all([api.listLevels(classId), api.listQuestions(levelId)])
      .then(([levels, qs]) => {
        setLevel(levels.find((l) => l.id === levelId) ?? null);
        setQuestions(qs);
      })
      .catch((err) => setError(err instanceof ApiError ? err.message : "Level belum bisa dibuka. Coba lagi ya."))
      .finally(() => setLoading(false));
  }, [classId, levelId]);

  // Preview shows what students will see (approved only) unless the teacher includes drafts.
  const quizQuestions = preview && !includeDrafts ? allQuestions.filter((q) => q.status === "approved") : allQuestions;

  function gradeLocally(): QuizSubmitResult {
    const graded = quizQuestions.map((q) => ({
      question_id: q.id,
      your_answer: answers[q.id] ?? null,
      is_correct: answers[q.id] === q.correct_answer,
      correct_answer: q.correct_answer ?? "",
      explanation: q.explanation,
    }));
    const correct = graded.filter((r) => r.is_correct).length;
    const percent = graded.length ? Math.round((correct / graded.length) * 100) : 0;
    return {
      score_percent: percent,
      passed: percent >= PASSING_SCORE,
      correct_count: correct,
      total_count: graded.length,
      results: graded,
    };
  }

  async function handleSubmit() {
    setError(null);
    setSubmitting(true);
    try {
      setResult(preview ? gradeLocally() : await api.submitQuiz(levelId, answers));
      setStage("result");
      window.scrollTo(0, 0);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Jawabanmu belum terkirim. Coba lagi ya.");
    } finally {
      setSubmitting(false);
    }
  }

  function startQuiz() {
    setStep(0);
    setStage("quiz");
    window.scrollTo(0, 0);
  }

  const mapHref = preview ? `/teacher/classes/${classId}/preview` : `/student/classes/${classId}/map`;
  const editorHref = `/teacher/classes/${classId}/levels/${levelId}`;
  const backTarget = { href: mapHref, label: "Kembali ke peta" };
  const banner = preview ? <PreviewBanner editorHref={editorHref} /> : null;

  if (loading) {
    return (
      <PageShell kid width="medium" back={backTarget}>
        <div role="status" className="surface flex flex-col items-center gap-3 py-10 text-center">
          <Mascot mood="sleepy" size={110} className="bob" />
          <p className="font-display text-xl font-bold">Sebentar ya, levelnya disiapkan...</p>
        </div>
      </PageShell>
    );
  }

  if (!level) {
    return (
      <PageShell kid width="medium" back={backTarget}>
        <div role="alert" className="surface flex flex-col items-center gap-3 py-10 text-center">
          <Mascot mood="oops" size={110} />
          <p className="font-display text-xl font-bold">{error ?? "Level tidak ditemukan"}</p>
          <Link href={mapHref} className="btn-primary">
            <MapIcon size={22} />
            Kembali ke peta
          </Link>
        </div>
      </PageShell>
    );
  }

  const boss = level.type === "boss";

  if (stage === "lesson") {
    const words = countWords(level.content);
    const minutes = readMinutes(words || countWords(level.summary));
    const hasQuiz = quizQuestions.length > 0;
    return (
      <PageShell kid width="medium" back={backTarget}>
        <ReadingProgress />
        {banner}

        <header className="surface mb-6 flex items-center gap-4 !bg-sky-soft">
          <Mascot mood="happy" size={88} className="shrink-0" />
          <div className="min-w-0">
            <div className="mb-2 flex flex-wrap gap-2">
              <span className={boss ? "badge-grape" : "badge-sky"}>{boss ? "Level bos" : "Ayo belajar"}</span>
              <span className="badge">
                <ClockIcon size={16} />
                Waktu baca: ± {minutes} menit
              </span>
            </div>
            <h1 className="text-3xl sm:text-4xl">{level.title}</h1>
          </div>
        </header>

        {level.content && (
          <section className="surface mb-6" aria-labelledby="materi">
            <SectionTitle icon={<BookIcon size={24} />} color="bg-sky-soft text-sky-dark">
              <span id="materi">Materi</span>
            </SectionTitle>
            <Markdown source={level.content} />
            {hasQuiz && (
              <div className="mt-8 flex flex-col items-center gap-3 rounded-2xl bg-grass-soft p-5 text-center sm:flex-row sm:text-left">
                <Mascot mood="cheering" size={72} className="shrink-0" />
                <p className="flex-1 font-display text-xl font-bold">Sudah selesai membaca?</p>
                <button onClick={startQuiz} className="btn-green w-full sm:w-auto">
                  Selesai membaca, ayo kuis!
                </button>
              </div>
            )}
          </section>
        )}

        <section className="surface mb-6" aria-labelledby="rangkuman">
          <SectionTitle icon={<ScrollIcon size={24} />} color="bg-highlight/40 text-ink">
            <span id="rangkuman">Rangkuman</span>
          </SectionTitle>
          {level.summary ? (
            <p className="max-w-[65ch] whitespace-pre-wrap leading-8 text-ink/90">{level.summary}</p>
          ) : (
            <p className="text-ink/75">Rangkuman belum ada.</p>
          )}
        </section>

        {level.key_points.length > 0 && (
          <section className="mb-6 rounded-3xl border-2 border-highlight bg-highlight/20 p-5 sm:p-6" aria-labelledby="poin">
            <SectionTitle icon={<LightbulbIcon size={24} />} color="bg-highlight text-ink">
              <span id="poin">Poin penting</span>
            </SectionTitle>
            <ul className="flex flex-col gap-3">
              {level.key_points.map((p, i) => (
                <li key={i} className="flex items-start gap-3">
                  <span className="mt-1 flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-grass-dark text-white">
                    <CheckIcon size={16} />
                  </span>
                  <span className="min-w-0 leading-snug">{p}</span>
                </li>
              ))}
            </ul>
          </section>
        )}

        {level.sources.length > 0 && (
          <section className="mb-6" aria-labelledby="sumber">
            <h2 id="sumber" className="mb-2 flex items-center gap-2 text-xl">
              <ScrollIcon size={22} />
              Sumber
            </h2>
            <ul className="flex flex-wrap gap-2">
              {level.sources.map((s, i) => (
                <li key={i} className="badge text-base">
                  {formatSource(s)}
                </li>
              ))}
            </ul>
          </section>
        )}

        <section className="surface text-center" aria-labelledby="siap">
          <h2 id="siap" className="mb-1 text-2xl">
            Siap main kuis?
          </h2>
          <p className="mb-4 text-ink/75">
            {hasQuiz
              ? `Ada ${quizQuestions.length} soal. Dapat ${PASSING_SCORE}% atau lebih, level berikutnya terbuka!`
              : "Soal untuk level ini belum ada."}
          </p>
          {error && (
            <p role="alert" className="note mb-4 border-coral bg-coral-soft text-alert">
              {error}
            </p>
          )}
          {preview && (
            <label className="mb-4 flex min-h-[48px] items-center justify-center gap-3 text-base">
              <input
                type="checkbox"
                checked={includeDrafts}
                onChange={(e) => setIncludeDrafts(e.target.checked)}
                className="h-6 w-6 accent-sky-dark"
              />
              Sertakan soal draft ({allQuestions.filter((q) => q.status !== "approved").length})
            </label>
          )}
          {hasQuiz && (
            <button onClick={startQuiz} className="btn-green w-full text-xl sm:w-auto sm:min-w-[260px]">
              <PlayIcon size={24} />
              Mulai kuis
            </button>
          )}
        </section>
      </PageShell>
    );
  }

  if (stage === "result" && result) {
    const byId = new Map(quizQuestions.map((q, i) => [q.id, { q, n: i + 1 }]));
    return (
      <PageShell kid width="medium" back={backTarget}>
        {banner}
        <div className="surface relative mb-6 overflow-hidden text-center">
          {result.passed && <Confetti />}
          <div className="relative">
            <Mascot mood={result.passed ? "cheering" : "oops"} size={130} className="bob mx-auto" />
            <h1 className="mt-2 text-4xl">{result.passed ? "Hebat! Kamu lulus!" : "Hampir berhasil!"}</h1>
            <p className="mt-1 text-xl text-ink/80">
              {result.passed ? "Kerja bagus, terus semangat!" : "Ayo coba lagi, kamu pasti bisa!"}
            </p>
            <div className="my-4 flex justify-center">
              <Stars percent={result.score_percent} size={48} animate />
            </div>
            <p className="mx-auto mb-2 inline-flex flex-wrap items-center justify-center gap-2">
              <span className={`${result.passed ? "badge-success" : "badge-alert"} !px-4 !py-1.5 !text-xl`}>
                Skor {result.score_percent}%
              </span>
              <span className="badge !px-4 !py-1.5 !text-xl">
                {result.correct_count} dari {result.total_count} benar
              </span>
            </p>
            {result.passed && !preview && (
              <p className="mt-2 flex items-center justify-center gap-2 font-display text-xl font-bold text-grass-dark">
                <SparklesIcon size={24} />
                Level baru terbuka!
              </p>
            )}
            <div className="mt-6 flex flex-col justify-center gap-4 sm:flex-row">
              {!result.passed && (
                <button
                  onClick={() => {
                    setResult(null);
                    setAnswers({});
                    startQuiz();
                  }}
                  className="btn-primary"
                >
                  <RefreshIcon size={22} />
                  Coba lagi
                </button>
              )}
              <Link href={mapHref} className={result.passed ? "btn-green" : "btn-ghost"}>
                <MapIcon size={22} />
                {result.passed ? "Lanjut ke peta" : "Kembali ke peta"}
              </Link>
            </div>
          </div>
        </div>

        <section aria-labelledby="bahas">
          <h2 id="bahas" className="mb-3 flex items-center gap-2 text-2xl">
            <LightbulbIcon size={26} />
            Yuk lihat jawabannya
          </h2>
          <ul className="flex flex-col gap-4">
            {result.results.map((r) => {
              const info = byId.get(r.question_id);
              return (
                <li key={r.question_id} className={`card !border-2 ${r.is_correct ? "!border-grass" : "!border-coral"}`}>
                  <p className="mb-2 font-bold">{info ? `${info.n}. ${info.q.question_text}` : "Soal"}</p>
                  <p
                    className={`mb-1 flex items-center gap-2 font-bold ${r.is_correct ? "text-correct-dark" : "text-alert"}`}
                  >
                    {r.is_correct ? <CheckIcon size={20} /> : <CrossIcon size={20} />}
                    {r.is_correct ? "Benar!" : "Belum tepat"}
                  </p>
                  <p className="text-ink/85">Jawabanmu: {r.your_answer ?? "Tidak dijawab"}</p>
                  {!r.is_correct && <p className="font-semibold text-correct-dark">Jawaban yang benar: {r.correct_answer}</p>}
                  {r.explanation && (
                    <p className="mt-2 flex items-start gap-2 rounded-xl bg-highlight/20 p-3 text-base">
                      <span className="mt-0.5 shrink-0">
                        <LightbulbIcon size={20} />
                      </span>
                      {r.explanation}
                    </p>
                  )}
                </li>
              );
            })}
          </ul>
        </section>
      </PageShell>
    );
  }

  // Quiz: one question per screen.
  const total = quizQuestions.length;
  const q = quizQuestions[Math.min(step, total - 1)];
  const isLast = step >= total - 1;
  const answeredCount = Object.keys(answers).length;
  const current = q ? answers[q.id] : undefined;
  const percentDone = total ? Math.round(((step + (current ? 1 : 0)) / total) * 100) : 0;

  return (
    <PageShell kid width="medium" back={{ href: mapHref, label: "Kembali ke peta" }}>
      {banner}
      <div className="mb-4 flex items-center justify-between gap-3">
        <p className="font-display text-xl font-bold">
          Soal {Math.min(step + 1, total)} dari {total}
        </p>
        <button onClick={() => setStage("lesson")} className="btn-ghost">
          <BookIcon size={20} />
          Baca lagi
        </button>
      </div>
      <div
        className="mb-6 h-4 w-full overflow-hidden rounded-full bg-white ring-2 ring-rule"
        role="progressbar"
        aria-valuenow={percentDone}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label="Progres kuis"
      >
        <div className="h-full rounded-full bg-grass transition-[width] duration-300" style={{ width: `${percentDone}%` }} />
      </div>

      {q && (
        <fieldset className="surface mb-6">
          <legend className="sr-only">Soal {step + 1}</legend>
          <p className="mb-5 flex items-start gap-3 font-display text-2xl font-bold leading-snug">
            <span className="mt-1 shrink-0 text-highlight-dark">
              <StarIcon size={26} />
            </span>
            {q.question_text}
          </p>
          <div className="flex flex-col gap-3">
            {q.options.map((opt, oi) => {
              const tile = TILES[oi % TILES.length];
              const selected = answers[q.id] === opt;
              return (
                <label
                  key={opt}
                  className={`flex min-h-[64px] cursor-pointer items-center gap-3 rounded-2xl border-[3px] px-4 py-3 font-bold leading-snug transition-transform duration-100 focus-within:ring-4 focus-within:ring-sky-dark/40 active:scale-[0.99] ${
                    selected ? `${tile.on} shadow-[0_4px_0_0_rgb(27_42_65/0.35)]` : tile.idle
                  }`}
                >
                  <input
                    type="radio"
                    name={q.id}
                    checked={selected}
                    onChange={() => setAnswers((a) => ({ ...a, [q.id]: opt }))}
                    className="sr-only"
                  />
                  <span
                    aria-hidden="true"
                    className={`flex h-11 w-11 shrink-0 items-center justify-center gap-0.5 rounded-xl ${
                      selected ? "bg-white text-ink" : tile.badge
                    }`}
                  >
                    <tile.Shape size={16} />
                    <span className="font-display text-lg">{String.fromCharCode(65 + oi)}</span>
                  </span>
                  <span className="min-w-0 flex-1">{opt}</span>
                  {selected && <CheckIcon size={26} className="shrink-0" />}
                </label>
              );
            })}
          </div>
        </fieldset>
      )}

      {error && (
        <p role="alert" className="note mb-4 border-coral bg-coral-soft text-alert">
          {error}
        </p>
      )}
      {total === 0 && <p className="surface text-center">Soal belum ada.</p>}

      <div className="flex gap-3">
        {step > 0 && (
          <button onClick={() => setStep((s) => s - 1)} className="btn-ghost">
            Sebelumnya
          </button>
        )}
        {isLast ? (
          <button
            onClick={handleSubmit}
            disabled={submitting || answeredCount < total}
            className="btn-green flex-1 text-xl"
          >
            {submitting ? "Mengirim..." : "Kirim jawaban"}
          </button>
        ) : (
          <button onClick={() => setStep((s) => s + 1)} disabled={!current} className="btn-primary flex-1 text-xl">
            Lanjut
            <ArrowRightIcon size={22} />
          </button>
        )}
      </div>
      {isLast && answeredCount < total && (
        <p className="mt-3 text-center text-base text-ink/75">Jawab semua soal dulu ya, lalu kirim.</p>
      )}
    </PageShell>
  );
}
