"use client";

import { useParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { ApiError, api } from "@/lib/api";
import type { Question } from "@/lib/types";

export default function TeacherLevelReviewPage() {
  const { levelId } = useParams<{ classId: string; levelId: string }>();
  const [questions, setQuestions] = useState<Question[]>([]);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setQuestions(await api.listQuestions(levelId));
  }, [levelId]);

  useEffect(() => {
    load().catch((err) => setError(err instanceof ApiError ? err.message : "Gagal memuat soal"));
  }, [load]);

  async function approve(q: Question) {
    try {
      await api.updateQuestion(q.id, { status: q.status === "approved" ? "draft" : "approved" });
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Gagal mengubah status soal");
    }
  }

  async function remove(q: Question) {
    try {
      await api.deleteQuestion(q.id);
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Gagal menghapus soal");
    }
  }

  return (
    <main className="mx-auto max-w-2xl px-4 py-10 sm:px-6">
      <h1 className="mb-6 font-display text-2xl">Review soal</h1>
      {error && <p className="mb-4 text-sm text-alert">{error}</p>}
      <ul className="flex flex-col gap-4">
        {questions.map((q) => (
          <li key={q.id} className="card">
            <p className="mb-3 font-medium">{q.question_text}</p>
            <ul className="mb-3 flex flex-col gap-1 text-sm">
              {q.options.map((opt) => (
                <li key={opt} className={opt === q.correct_answer ? "font-semibold text-correct" : "text-ink/80"}>
                  {opt}
                </li>
              ))}
            </ul>
            {q.explanation && <p className="mb-3 text-sm text-ink/60">{q.explanation}</p>}
            <div className="flex items-center gap-3">
              <span className={`text-xs ${q.status === "approved" ? "text-correct" : "text-ink/50"}`}>
                {q.status === "approved" ? "Approved" : "Draft"}
              </span>
              <button onClick={() => approve(q)} className="btn-primary px-3 py-1 text-xs">
                {q.status === "approved" ? "Batalkan approve" : "Approve"}
              </button>
              <button onClick={() => remove(q)} className="btn-danger px-3 py-1 text-xs">
                Hapus
              </button>
            </div>
          </li>
        ))}
        {questions.length === 0 && <p className="text-sm text-ink/60">Belum ada soal.</p>}
      </ul>
    </main>
  );
}
