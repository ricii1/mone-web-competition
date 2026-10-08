"use client";

import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { ApiError, api } from "@/lib/api";
import type { Level, QuizSubmitResult, Question } from "@/lib/types";

export default function StudentLevelPage() {
  const { classId, levelId } = useParams<{ classId: string; levelId: string }>();
  const router = useRouter();
  const [level, setLevel] = useState<Level | null>(null);
  const [questions, setQuestions] = useState<Question[]>([]);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [result, setResult] = useState<QuizSubmitResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showQuiz, setShowQuiz] = useState(false);

  useEffect(() => {
    api
      .listLevels(classId)
      .then((levels) => setLevel(levels.find((l) => l.id === levelId) ?? null))
      .catch(() => {});
    api
      .listQuestions(levelId)
      .then(setQuestions)
      .catch((err) => setError(err instanceof ApiError ? err.message : "Gagal memuat soal"));
  }, [classId, levelId]);

  async function handleSubmit() {
    setError(null);
    try {
      const res = await api.submitQuiz(levelId, answers);
      setResult(res);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Gagal submit kuis");
    }
  }

  if (!showQuiz) {
    return (
      <main className="mx-auto max-w-2xl px-4 py-10 sm:px-6">
        <h1 className="mb-3 font-display text-2xl">{level?.title ?? "Memuat..."}</h1>
        <p className="mb-8 whitespace-pre-wrap leading-relaxed text-ink/70">{level?.summary}</p>
        {error && <p className="mb-4 text-sm text-alert">{error}</p>}
        <button onClick={() => setShowQuiz(true)} className="btn-primary">
          Mulai kuis
        </button>
      </main>
    );
  }

  if (result) {
    return (
      <main className="mx-auto max-w-2xl px-4 py-10 text-center sm:px-6">
        <h1 className="mb-3 font-display text-2xl">{result.passed ? "Selamat, lulus!" : "Belum lulus"}</h1>
        <p className="mb-8 text-lg text-ink/70">
          Skor: <span className={result.passed ? "font-semibold text-correct" : "font-semibold text-alert"}>
            {result.score_percent}%
          </span>{" "}
          ({result.correct_count}/{result.total_count} benar)
        </p>
        <div className="flex justify-center gap-3">
          <button onClick={() => router.push(`/student/classes/${classId}/map`)} className="btn-ghost">
            Kembali ke map
          </button>
          {!result.passed && (
            <button
              onClick={() => {
                setResult(null);
                setAnswers({});
              }}
              className="btn-primary"
            >
              Ulangi
            </button>
          )}
        </div>
      </main>
    );
  }

  return (
    <main className="mx-auto max-w-2xl px-4 py-10 sm:px-6">
      <h1 className="mb-6 font-display text-2xl">Kuis: {level?.title}</h1>
      {error && <p className="mb-4 text-sm text-alert">{error}</p>}
      <ul className="flex flex-col gap-4">
        {questions.map((q, i) => (
          <li key={q.id} className="card">
            <p className="mb-3 font-medium">
              {i + 1}. {q.question_text}
            </p>
            <div className="flex flex-col gap-2">
              {q.options.map((opt) => (
                <label key={opt} className="flex items-center gap-2 text-sm">
                  <input
                    type="radio"
                    name={q.id}
                    checked={answers[q.id] === opt}
                    onChange={() => setAnswers((a) => ({ ...a, [q.id]: opt }))}
                    className="accent-highlight"
                  />
                  {opt}
                </label>
              ))}
            </div>
          </li>
        ))}
      </ul>
      <button
        onClick={handleSubmit}
        disabled={Object.keys(answers).length < questions.length}
        className="btn-primary mt-8"
      >
        Submit
      </button>
    </main>
  );
}
