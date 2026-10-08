"use client";

import { useEffect, useRef, useState } from "react";
import { ApiError, api } from "@/lib/api";
import { connectRealtime } from "@/lib/realtime";
import type { LiveSession } from "@/lib/types";

interface ActiveQuestion {
  question_id: string;
  question_text: string;
  options: string[];
  deadline: number;
}

interface ClosedQuestion {
  correct_answer: string;
  distribution: Record<string, number>;
  finished: boolean;
}

export default function StudentLivePage() {
  const [joinCode, setJoinCode] = useState("");
  const [session, setSession] = useState<LiveSession | null>(null);
  const [active, setActive] = useState<ActiveQuestion | null>(null);
  const [closed, setClosed] = useState<ClosedQuestion | null>(null);
  const [answered, setAnswered] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const answeredRef = useRef(false);

  async function handleJoin(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      const found = await api.lookupLiveSession(joinCode);
      await api.joinLiveSession(found.id, joinCode);
      setSession(found);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Gagal join sesi live");
    }
  }

  useEffect(() => {
    if (!session) return;
    return connectRealtime(`/ws/live/${session.id}`, (event) => {
      if (event.type !== "live_session_update") return;
      const payload = event.payload as Record<string, unknown>;
      if (payload.kind === "question_started") {
        answeredRef.current = false;
        setAnswered(false);
        setClosed(null);
        setActive(payload as unknown as ActiveQuestion);
      } else if (payload.kind === "question_closed") {
        setActive(null);
        setClosed(payload as unknown as ClosedQuestion);
      } else if (payload.kind === "session_ended") {
        setActive(null);
      }
    });
  }, [session]);

  async function submitAnswer(option: string) {
    if (!session || !active || answeredRef.current) return;
    answeredRef.current = true;
    setAnswered(true);
    try {
      await api.answerLiveQuestion(session.id, active.question_id, option);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Gagal mengirim jawaban");
    }
  }

  if (!session) {
    return (
      <main className="mx-auto max-w-sm px-4 py-10 sm:px-6">
        <h1 className="mb-6 font-display text-2xl">Join live class</h1>
        <form onSubmit={handleJoin} className="flex flex-col gap-4">
          <div className="field">
            <label htmlFor="joinCode" className="field-label">
              Kode join
            </label>
            <input
              id="joinCode"
              value={joinCode}
              onChange={(e) => setJoinCode(e.target.value.toUpperCase())}
              required
              className="input-rule font-mono tracking-wider"
            />
          </div>
          {error && <p className="text-sm text-alert">{error}</p>}
          <button type="submit" className="btn-primary">
            Join
          </button>
        </form>
      </main>
    );
  }

  return (
    <main className="mx-auto max-w-sm px-4 py-10 sm:px-6">
      <h1 className="mb-6 font-display text-2xl">Live class</h1>
      {error && <p className="mb-4 text-sm text-alert">{error}</p>}

      {active && (
        <div>
          <p className="mb-4 font-medium">{active.question_text}</p>
          <div className="flex flex-col gap-2">
            {active.options.map((opt) => (
              <button
                key={opt}
                onClick={() => submitAnswer(opt)}
                disabled={answered}
                className="card text-left transition-colors hover:border-highlight disabled:cursor-not-allowed disabled:opacity-50"
              >
                {opt}
              </button>
            ))}
          </div>
          {answered && <p className="mt-4 text-sm text-ink/60">Jawaban terkirim, menunggu soal ditutup...</p>}
        </div>
      )}

      {closed && (
        <div className="card">
          <p className="mb-2">
            Jawaban benar: <span className="font-semibold text-correct">{closed.correct_answer}</span>
          </p>
          {closed.finished && <p className="font-medium">Sesi selesai. Terima kasih!</p>}
        </div>
      )}

      {!active && !closed && <p className="text-sm text-ink/60">Menunggu guru memulai soal...</p>}
    </main>
  );
}
