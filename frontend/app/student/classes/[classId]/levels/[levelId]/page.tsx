"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import PageShell from "@/components/PageShell";
import { ApiError, api } from "@/lib/api";
import { formatSource } from "@/lib/levels";
import type { Level, Question, QuizSubmitResult } from "@/lib/types";

type Stage = "lesson" | "quiz" | "result";

export default function StudentLevelPage() {
  const { classId, levelId } = useParams<{ classId: string; levelId: string }>();
  const [level, setLevel] = useState<Level | null>(null);
  const [questions, setQuestions] = useState<Question[]>([]);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [result, setResult] = useState<QuizSubmitResult | null>(null);
  const [stage, setStage] = useState<Stage>("lesson");
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([api.listLevels(classId), api.listQuestions(levelId)])
      .then(([levels, qs]) => {
        setLevel(levels.find((l) => l.id === levelId) ?? null);
        setQuestions(qs);
      })
      .catch((err) => setError(err instanceof ApiError ? err.message : "Gagal memuat level"))
      .finally(() => setLoading(false));
  }, [classId, levelId]);

  async function handleSubmit() {
    setError(null);
    setSubmitting(true);
    try {
      setResult(await api.submitQuiz(levelId, answers));
      setStage("result");
      window.scrollTo(0, 0);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Gagal mengirim kuis");
    } finally {
      setSubmitting(false);
    }
  }

  const mapHref = `/student/classes/${classId}/map`;

  if (loading) {
    return (
      <PageShell width="medium" back={{ href: mapHref, label: "Peta level" }}>
        <p className="text-sm text-ink/60">Memuat level...</p>
      </PageShell>
    );
  }

  if (!level) {
    return (
      <PageShell width="medium" back={{ href: mapHref, label: "Peta level" }}>
        <p className="mb-4 text-sm text-alert">{error ?? "Level tidak ditemukan"}</p>
        <Link href={mapHref} className="btn-ghost">
          Kembali ke peta
        </Link>
      </PageShell>
    );
  }

  if (stage === "lesson") {
    return (
      <PageShell width="medium" back={{ href: mapHref, label: "Peta level" }}>
        <article className="surface mb-6">
        <h1 className="mb-4 font-display text-2xl sm:text-3xl">{level.title}</h1>
        {level.summary ? (
          <p className="whitespace-pre-wrap text-base leading-relaxed text-ink/85 sm:text-lg sm:leading-8">{level.summary}</p>
        ) : (
          <p className="text-sm text-ink/60">Rangkuman belum tersedia.</p>
        )}
        </article>
        {level.key_points.length > 0 && (
          <section className="mb-6 rounded-xl border border-highlight/40 bg-highlight/10 p-5">
            <h2 className="mb-2 font-display text-lg">Poin penting</h2>
            <ul className="list-disc space-y-1 pl-5 text-ink/80">
              {level.key_points.map((p, i) => (
                <li key={i}>{p}</li>
              ))}
            </ul>
          </section>
        )}
        {level.sources.length > 0 && (
          <p className="mb-8 text-sm text-ink/60">Sumber: {level.sources.map(formatSource).join("; ")}</p>
        )}
        {error && (
          <p role="alert" className="mb-4 text-sm text-alert">
            {error}
          </p>
        )}
        {questions.length === 0 ? (
          <p className="text-sm text-ink/60">Belum ada soal untuk level ini.</p>
        ) : (
          <button onClick={() => setStage("quiz")} className="btn-primary">
            Mulai kuis
          </button>
        )}
      </PageShell>
    );
  }

  if (stage === "result" && result) {
    const byId = new Map(questions.map((q, i) => [q.id, { q, n: i + 1 }]));
    return (
      <PageShell width="medium" back={{ href: mapHref, label: "Peta level" }}>
        <div className="surface mb-6 text-center">
          <div
            className={`mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full ${
              result.passed ? "bg-correct text-chalk ring-8 ring-correct/15" : "bg-highlight/25 text-ink"
            }`}
          >
            {result.passed ? (
              <svg width="30" height="30" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                <path d="m3 8.5 3.2 3L13 4.5" />
              </svg>
            ) : (
              <span className="font-display text-2xl" aria-hidden="true">
                !
              </span>
            )}
          </div>
          {result.passed && (
            <div className="mb-2 flex justify-center gap-2" aria-hidden="true">
              {["bg-highlight", "bg-correct", "bg-alert", "bg-ink", "bg-highlight"].map((c, i) => (
                <span
                  key={i}
                  className={`confetti-dot h-2 w-2 rounded-full ${c}`}
                  style={{ animationDelay: `${i * 90}ms` }}
                />
              ))}
            </div>
          )}
          <h1 className="mb-3 font-display text-2xl sm:text-3xl">
            {result.passed ? "Selamat, kamu lulus!" : "Belum lulus, coba lagi ya"}
          </h1>
          <p className="text-lg text-ink/70">
            Skor:{" "}
            <span className={result.passed ? "font-semibold text-correct" : "font-semibold text-alert"}>
              {result.score_percent}%
            </span>{" "}
            ({result.correct_count}/{result.total_count} benar)
          </p>
          {result.passed && <p className="mt-1 text-sm text-ink/60">Level berikutnya sudah terbuka.</p>}
        </div>

        <h2 className="mb-3 font-display text-lg">Pembahasan</h2>
        <ul className="mb-8 flex flex-col gap-4">
          {result.results.map((r) => {
            const info = byId.get(r.question_id);
            return (
              <li key={r.question_id} className="card">
                <p className="mb-2 font-medium">
                  {info ? `${info.n}. ${info.q.question_text}` : "Soal"}
                </p>
                <p className={`mb-1 flex items-center gap-1.5 text-sm font-semibold ${r.is_correct ? "text-correct" : "text-alert"}`}>
                  <svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                    {r.is_correct ? <path d="m3 8.5 3.2 3L13 4.5" /> : <path d="m4 4 8 8M12 4l-8 8" />}
                  </svg>
                  {r.is_correct ? "Benar" : "Salah"}
                </p>
                <p className="text-sm text-ink/80">Jawabanmu: {r.your_answer ?? "Tidak dijawab"}</p>
                {!r.is_correct && <p className="text-sm text-correct">Jawaban benar: {r.correct_answer}</p>}
                {r.explanation && <p className="mt-2 text-sm text-ink/60">{r.explanation}</p>}
              </li>
            );
          })}
        </ul>

        <div className="flex flex-wrap justify-center gap-3">
          <Link href={mapHref} className={result.passed ? "btn-primary" : "btn-ghost"}>
            {result.passed ? "Lanjut ke level berikutnya" : "Kembali ke peta"}
          </Link>
          {!result.passed && (
            <button
              onClick={() => {
                setResult(null);
                setAnswers({});
                setStage("quiz");
              }}
              className="btn-primary"
            >
              Ulangi
            </button>
          )}
        </div>
      </PageShell>
    );
  }

  return (
    <PageShell width="medium" back={{ href: mapHref, label: "Peta level" }}>
      <h1 className="mb-4 font-display text-2xl sm:text-3xl">Kuis: {level.title}</h1>
      <div className="mb-6">
        <p className="mb-2 text-sm font-medium">
          {Object.keys(answers).length} dari {questions.length} soal terjawab
        </p>
        <div
          className="h-2.5 w-full overflow-hidden rounded-full bg-rule"
          role="progressbar"
          aria-valuenow={Object.keys(answers).length}
          aria-valuemin={0}
          aria-valuemax={questions.length}
          aria-label="Progres kuis"
        >
          <div
            className="h-full rounded-full bg-highlight transition-[width] duration-300"
            style={{ width: `${questions.length ? (Object.keys(answers).length / questions.length) * 100 : 0}%` }}
          />
        </div>
      </div>
      {error && (
        <p role="alert" className="mb-4 text-sm text-alert">
          {error}
        </p>
      )}
      <ul className="flex flex-col gap-4">
        {questions.map((q, i) => (
          <li key={q.id} className="card">
            <fieldset>
              <legend className="mb-3 font-medium">
                {i + 1}. {q.question_text}
              </legend>
              <div className="flex flex-col gap-2">
                {q.options.map((opt, oi) => (
                  <label key={opt} className={`flex min-h-[48px] cursor-pointer items-center gap-3 rounded-lg border px-3 py-2 text-sm transition-colors ${answers[q.id] === opt ? "border-highlight bg-highlight/10" : "border-rule hover:border-ink/30"}`}>
                    <input
                      type="radio"
                      name={q.id}
                      checked={answers[q.id] === opt}
                      onChange={() => setAnswers((a) => ({ ...a, [q.id]: opt }))}
                      className="sr-only"
                    />
                    <span
                      aria-hidden="true"
                      className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-md text-xs font-semibold ${
                        answers[q.id] === opt ? "bg-highlight text-ink" : "bg-ink/10 text-ink"
                      }`}
                    >
                      {String.fromCharCode(65 + oi)}
                    </span>
                    {opt}
                  </label>
                ))}
              </div>
            </fieldset>
          </li>
        ))}
      </ul>
      <div className="mt-8 flex gap-3">
        <button onClick={() => setStage("lesson")} className="btn-ghost">
          Baca ulang materi
        </button>
        <button
          onClick={handleSubmit}
          disabled={submitting || Object.keys(answers).length < questions.length}
          className="btn-primary"
        >
          {submitting ? "Mengirim..." : "Kirim jawaban"}
        </button>
      </div>
    </PageShell>
  );
}
