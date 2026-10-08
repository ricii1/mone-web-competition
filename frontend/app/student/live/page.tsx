"use client";

import { useEffect, useRef, useState } from "react";
import AnswerTile, { type TileState } from "@/components/AnswerTile";
import Confetti from "@/components/Confetti";
import { CheckIcon, ClockIcon, CrossIcon, RocketIcon } from "@/components/icons";
import Mascot from "@/components/Mascot";
import PageShell from "@/components/PageShell";
import { ApiError, api } from "@/lib/api";
import { connectRealtime } from "@/lib/realtime";
import type { LiveSession } from "@/lib/types";

interface ActiveQuestion {
  question_id: string;
  question_text: string;
  options: string[];
  /** Server deadline in epoch seconds. */
  deadline: number;
  time_limit_seconds?: number;
}

interface ClosedQuestion {
  correct_answer: string;
  distribution: Record<string, number>;
  finished: boolean;
}

function WaitDots() {
  return (
    <span className="inline-flex gap-2" aria-hidden="true">
      {[0, 1, 2].map((i) => (
        <span key={i} className="wait-dot h-4 w-4 rounded-full bg-sky-dark" style={{ animationDelay: `${i * 160}ms` }} />
      ))}
    </span>
  );
}

export default function StudentLivePage() {
  const [joinCode, setJoinCode] = useState("");
  const [session, setSession] = useState<LiveSession | null>(null);
  const [question, setQuestion] = useState<ActiveQuestion | null>(null);
  const [closed, setClosed] = useState<ClosedQuestion | null>(null);
  const [myAnswer, setMyAnswer] = useState<string | null>(null);
  const [ended, setEnded] = useState(false);
  const [joining, setJoining] = useState(false);
  const [now, setNow] = useState(() => Date.now() / 1000);
  const [error, setError] = useState<string | null>(null);
  const answeredRef = useRef(false);

  async function handleJoin(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setJoining(true);
    try {
      const found = await api.lookupLiveSession(joinCode);
      await api.joinLiveSession(found.id, joinCode);
      setSession(found);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Belum bisa masuk. Cek kodenya ya.");
    } finally {
      setJoining(false);
    }
  }

  useEffect(() => {
    if (!session) return;
    return connectRealtime(`/ws/live/${session.id}`, (event) => {
      if (event.type !== "live_session_update") return;
      const payload = event.payload as Record<string, unknown>;
      if (payload.kind === "question_started") {
        answeredRef.current = false;
        setMyAnswer(null);
        setClosed(null);
        setError(null);
        setQuestion(payload as unknown as ActiveQuestion);
      } else if (payload.kind === "question_closed") {
        const c = payload as unknown as ClosedQuestion;
        setClosed(c);
        if (c.finished) setEnded(true);
      } else if (payload.kind === "session_ended") {
        setEnded(true);
      }
    });
  }, [session]);

  const running = !!question && !closed;
  useEffect(() => {
    if (!running) return;
    const timer = setInterval(() => setNow(Date.now() / 1000), 250);
    return () => clearInterval(timer);
  }, [running]);

  async function submitAnswer(option: string) {
    if (!session || !question || answeredRef.current) return;
    answeredRef.current = true;
    setMyAnswer(option);
    try {
      await api.answerLiveQuestion(session.id, question.question_id, option);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Jawabanmu belum terkirim.");
    }
  }

  if (!session) {
    return (
      <PageShell width="narrow" back={{ href: "/student", label: "Kembali ke kelasku" }}>
        <div className="mb-4 flex items-center gap-3">
          <Mascot mood="cheering" size={96} className="bob shrink-0" />
          <div>
            <h1 className="text-3xl">Main kuis bareng</h1>
            <p className="text-ink/75">Tulis kode dari gurumu.</p>
          </div>
        </div>
        <form onSubmit={handleJoin} className="surface flex flex-col gap-4">
          <div className="field">
            <label htmlFor="joinCode" className="field-label">
              Kode dari guru
            </label>
            <input
              id="joinCode"
              value={joinCode}
              onChange={(e) => setJoinCode(e.target.value.toUpperCase())}
              required
              autoComplete="off"
              className="input-box !py-4 text-center font-display !text-4xl font-bold uppercase tracking-[0.25em]"
            />
          </div>
          {error && (
            <p role="alert" className="note border-coral bg-coral-soft text-alert">
              {error}
            </p>
          )}
          <button type="submit" disabled={joining} className="btn-green w-full text-xl">
            <RocketIcon size={24} />
            {joining ? "Tunggu sebentar..." : "Ayo masuk!"}
          </button>
        </form>
      </PageShell>
    );
  }

  const remaining = question ? Math.max(0, Math.ceil(question.deadline - now)) : 0;
  const timeUp = running && remaining === 0;
  const myCorrect = closed && myAnswer !== null && myAnswer === closed.correct_answer;

  function tileState(opt: string): TileState {
    if (closed) {
      if (opt === closed.correct_answer) return "correct";
      if (opt === myAnswer) return "wrong";
      return "dim";
    }
    if (myAnswer === null) return "idle";
    return opt === myAnswer ? "chosen" : "dim";
  }

  return (
    <PageShell width="medium" back={{ href: "/student", label: "Keluar dari kuis" }}>
      {error && (
        <p role="alert" className="note mb-4 border-coral bg-coral-soft text-alert">
          {error}
        </p>
      )}

      {ended && (!question || closed) && (
        <div className="surface relative mb-6 overflow-hidden text-center">
          <Confetti />
          <Mascot mood="cheering" size={120} className="bob relative mx-auto" />
          <h1 className="relative mt-2 text-3xl">Kuis selesai. Hebat!</h1>
          <p className="relative text-xl text-ink/80">Terima kasih sudah ikut bermain.</p>
        </div>
      )}

      {!question && !ended && (
        <div role="status" className="surface flex flex-col items-center gap-4 py-10 text-center">
          <Mascot mood="sleepy" size={130} className="bob" />
          <h1 className="text-3xl">Kamu sudah masuk!</h1>
          <p className="text-xl text-ink/80">Tunggu gurumu memulai ya.</p>
          <WaitDots />
        </div>
      )}

      {question && (
        <section aria-live="polite">
          <div className="mb-4 flex items-center gap-4">
            <div
              className={`flex h-20 w-20 shrink-0 flex-col items-center justify-center rounded-full border-4 font-display ${
                running && remaining <= 5 ? "border-coral-dark bg-coral-soft text-coral-dark" : "border-sky-dark bg-sky-soft text-sky-dark"
              }`}
              role="timer"
              aria-label={`Sisa waktu ${remaining} detik`}
            >
              <ClockIcon size={18} />
              <span className="text-3xl font-bold leading-none">{closed ? 0 : remaining}</span>
            </div>
            <div className="min-w-0 flex-1">
              <div className="h-4 overflow-hidden rounded-full bg-white ring-2 ring-rule" aria-hidden="true">
                <div
                  className="h-full origin-left rounded-full bg-sky-dark"
                  style={{ width: "100%", transform: `scaleX(${closed ? 0 : Math.min(1, remaining / (question?.time_limit_seconds ?? 20))})`, transition: "transform 250ms linear" }}
                />
              </div>
              {timeUp && <p className="mt-1 font-bold text-coral-dark">Waktu habis!</p>}
              {myAnswer && !closed && <p className="mt-1 font-bold text-grass-dark">Jawabanmu terkirim. Tunggu ya!</p>}
            </div>
          </div>

          <h1 className="surface mb-4 !p-4 text-2xl leading-snug sm:text-3xl">{question.question_text}</h1>

          <div className="grid gap-4 sm:grid-cols-2">
            {question.options.map((opt, i) => (
              <AnswerTile
                key={opt}
                index={i}
                label={opt}
                state={tileState(opt)}
                disabled={myAnswer !== null || !!closed || timeUp}
                onClick={() => submitAnswer(opt)}
                count={closed ? closed.distribution[opt] : undefined}
              />
            ))}
          </div>

          {closed && (
            <div
              role="status"
              className={`note mt-6 items-center text-xl ${
                myCorrect ? "border-grass bg-grass-soft text-correct-dark" : "border-highlight bg-highlight/25 text-ink"
              }`}
            >
              <Mascot mood={myCorrect ? "cheering" : "thinking"} size={64} className="shrink-0" />
              <span className="flex items-center gap-2">
                {myCorrect ? <CheckIcon size={26} /> : <CrossIcon size={26} />}
                {myCorrect
                  ? "Benar! Hebat!"
                  : myAnswer
                    ? `Belum tepat. Jawaban yang benar: ${closed.correct_answer}`
                    : `Waktu habis. Jawaban yang benar: ${closed.correct_answer}`}
              </span>
            </div>
          )}
          {closed && !ended && (
            <p className="mt-4 flex items-center justify-center gap-3 text-center text-lg font-bold text-ink/75">
              Tunggu soal berikutnya <WaitDots />
            </p>
          )}
        </section>
      )}
    </PageShell>
  );
}
