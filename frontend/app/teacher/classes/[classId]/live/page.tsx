"use client";

import { useParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { ApiError, api } from "@/lib/api";
import { connectRealtime } from "@/lib/realtime";
import type { Level, LiveSession } from "@/lib/types";

export default function TeacherLivePage() {
  const { classId } = useParams<{ classId: string }>();
  const [levels, setLevels] = useState<Level[]>([]);
  const [session, setSession] = useState<LiveSession | null>(null);
  const [liveState, setLiveState] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.listLevels(classId).then(setLevels).catch(() => {});
  }, [classId]);

  useEffect(() => {
    if (!session) return;
    return connectRealtime(`/ws/live/${session.id}`, (event) => {
      if (event.type === "live_session_update") setLiveState(event.payload);
    });
  }, [session]);

  async function start(levelId: string) {
    setError(null);
    try {
      const s = await api.createLiveSession(classId, levelId);
      setSession(s);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Gagal membuat sesi live");
    }
  }

  const begin = useCallback(async () => {
    if (!session) return;
    try {
      await api.startLiveSession(session.id);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Gagal memulai sesi");
    }
  }, [session]);

  async function next() {
    if (!session) return;
    try {
      await api.nextLiveQuestion(session.id);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Gagal lanjut ke soal berikutnya");
    }
  }

  async function end() {
    if (!session) return;
    try {
      await api.endLiveSession(session.id);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Gagal mengakhiri sesi");
    }
  }

  if (!session) {
    return (
      <main className="mx-auto max-w-2xl px-4 py-10 sm:px-6">
        <h1 className="mb-6 font-display text-2xl">Mulai live class</h1>
        {error && <p className="mb-4 text-sm text-alert">{error}</p>}
        <ul className="flex flex-col gap-2">
          {levels.map((l) => (
            <li key={l.id}>
              <button onClick={() => start(l.id)} className="card block w-full text-left transition-colors hover:border-ink/30">
                {l.title} ({l.type})
              </button>
            </li>
          ))}
          {levels.length === 0 && <p className="text-sm text-ink/60">Belum ada level.</p>}
        </ul>
      </main>
    );
  }

  return (
    <main className="mx-auto max-w-2xl px-4 py-10 sm:px-6">
      <h1 className="mb-1 font-display text-2xl">Live class</h1>
      <p className="mb-6 text-sm text-ink/60">
        Kode join: <span className="font-mono font-semibold text-ink">{session.join_code}</span> · status:{" "}
        {session.status}
      </p>
      {error && <p className="mb-4 text-sm text-alert">{error}</p>}

      {liveState && (
        <pre className="card mb-6 overflow-x-auto whitespace-pre-wrap text-xs text-ink/70">
          {JSON.stringify(liveState, null, 2)}
        </pre>
      )}

      <div className="flex gap-3">
        <button onClick={begin} className="btn-primary">
          Mulai
        </button>
        <button onClick={next} className="btn-ghost">
          Soal berikutnya
        </button>
        <button onClick={end} className="btn-danger">
          Akhiri
        </button>
      </div>
    </main>
  );
}
