"use client";

import { useParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import PageShell from "@/components/PageShell";
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

  const back = { href: `/teacher/classes/${classId}`, label: "Kembali ke class" };

  if (!session) {
    return (
      <PageShell width="medium" back={back} title="Mulai live class" subtitle="Pilih level yang jadi bahan kuis serentak.">
        {error && <p className="mb-4 text-sm text-alert">{error}</p>}
        <ul className="grid gap-3 sm:grid-cols-2">
          {levels.map((l) => (
            <li key={l.id}>
              <button
                onClick={() => start(l.id)}
                className="card card-link flex h-full w-full items-center justify-between gap-2 p-4 text-left"
              >
                <span>{l.title}</span>
                {l.type === "boss" && <span className="badge-alert">Boss</span>}
              </button>
            </li>
          ))}
        </ul>
        {levels.length === 0 && <p className="surface text-sm text-ink/65">Belum ada level.</p>}
      </PageShell>
    );
  }

  return (
    <PageShell width="medium" back={back} title="Live class" subtitle={`Status: ${session.status}`}>
      {error && <p className="mb-4 text-sm text-alert">{error}</p>}

      <div className="surface mb-6 text-center">
        <p className="text-sm text-ink/65">Murid masuk di halaman Live class dengan kode</p>
        <p className="mt-2 font-mono text-5xl font-semibold tracking-[0.3em] text-ink sm:text-6xl">
          {session.join_code}
        </p>
      </div>

      <div className="mb-6 flex flex-wrap gap-3 rounded-xl border border-rule bg-white/80 p-3 shadow-sm shadow-ink/5 [&>button]:min-h-[52px] [&>button]:flex-1 [&>button]:text-base">
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

      {liveState && (
        <pre className="card overflow-x-auto whitespace-pre-wrap text-xs text-ink/70">
          {JSON.stringify(liveState, null, 2)}
        </pre>
      )}
    </PageShell>
  );
}
