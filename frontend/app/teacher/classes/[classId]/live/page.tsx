"use client";

import { useParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { ArrowRightIcon, CheckIcon, CrownIcon, PlayIcon, RocketIcon, UsersIcon } from "@/components/icons";
import Mascot from "@/components/Mascot";
import PageShell from "@/components/PageShell";
import { ApiError, api } from "@/lib/api";
import { connectRealtime } from "@/lib/realtime";
import { useClassTitle } from "@/lib/useClassTitle";
import type { Level, LiveSession } from "@/lib/types";

interface LiveState {
  kind?: string;
  question_text?: string;
  options?: string[];
  index?: number;
  total?: number;
  correct_answer?: string;
  distribution?: Record<string, number>;
  finished?: boolean;
}

export default function TeacherLivePage() {
  const { classId } = useParams<{ classId: string }>();
  const classTitle = useClassTitle(classId);
  const [levels, setLevels] = useState<Level[]>([]);
  const [loading, setLoading] = useState(true);
  const [session, setSession] = useState<LiveSession | null>(null);
  const [liveState, setLiveState] = useState<LiveState | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .listLevels(classId)
      .then(setLevels)
      .catch(() => setError("Daftar level belum bisa dimuat."))
      .finally(() => setLoading(false));
  }, [classId]);

  useEffect(() => {
    if (!session) return;
    return connectRealtime(`/ws/live/${session.id}`, (event) => {
      if (event.type === "live_session_update") setLiveState(event.payload as LiveState);
    });
  }, [session]);

  async function start(levelId: string) {
    setError(null);
    try {
      setSession(await api.createLiveSession(classId, levelId));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Kuis bersama belum bisa dibuat. Coba lagi ya.");
    }
  }

  const begin = useCallback(async () => {
    if (!session) return;
    try {
      await api.startLiveSession(session.id);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Kuis belum bisa dimulai.");
    }
  }, [session]);

  async function next() {
    if (!session) return;
    try {
      await api.nextLiveQuestion(session.id);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Belum bisa lanjut ke soal berikutnya.");
    }
  }

  async function end() {
    if (!session) return;
    try {
      await api.endLiveSession(session.id);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Kuis belum bisa diakhiri.");
    }
  }

  const back = { href: `/teacher/classes/${classId}`, label: classTitle ? `Kembali ke ${classTitle}` : "Kembali ke kelas" };

  if (!session) {
    return (
      <PageShell
        width="medium"
        back={back}
        icon={<RocketIcon size={28} />}
        title="Mulai kuis bersama"
        subtitle="Pilih level. Murid menjawab soalnya bersamaan di HP masing-masing."
      >
        {error && (
          <p role="alert" className="note mb-4 border-coral bg-coral-soft text-alert">
            {error}
          </p>
        )}
        {loading && <p role="status" className="text-ink/75">Memuat level...</p>}
        <ul className="grid gap-3 sm:grid-cols-2">
          {levels.map((l, i) => (
            <li key={l.id}>
              <button onClick={() => start(l.id)} className="card card-link flex min-h-[64px] w-full items-center gap-3 p-4 text-left">
                <span
                  className={`flex h-11 w-11 shrink-0 items-center justify-center rounded-xl font-display text-xl font-bold ${
                    l.type === "boss" ? "bg-grape-dark text-white" : "bg-sky-soft text-sky-dark"
                  }`}
                >
                  {l.type === "boss" ? <CrownIcon size={24} /> : i + 1}
                </span>
                <span className="min-w-0 flex-1 font-bold">{l.title}</span>
                {l.type === "boss" && <span className="badge-grape">Bos</span>}
              </button>
            </li>
          ))}
        </ul>
        {!loading && levels.length === 0 && (
          <div className="surface flex items-center gap-4">
            <Mascot mood="thinking" size={80} className="shrink-0" />
            <p>Belum ada level. Buat level dulu di halaman kelas.</p>
          </div>
        )}
      </PageShell>
    );
  }

  const state = liveState?.kind;
  const statusText =
    state === "question_started"
      ? `Soal ${(liveState?.index ?? 0) + 1} dari ${liveState?.total ?? "?"} sedang berjalan`
      : state === "question_closed"
        ? "Soal sudah ditutup"
        : state === "session_ended"
          ? "Kuis selesai"
          : "Menunggu murid masuk";

  return (
    <PageShell width="medium" back={back} icon={<RocketIcon size={28} />} title="Kuis bersama" subtitle={statusText}>
      {error && (
        <p role="alert" className="note mb-4 border-coral bg-coral-soft text-alert">
          {error}
        </p>
      )}

      <div className="surface mb-6 text-center !bg-sky-soft">
        <p className="flex items-center justify-center gap-2 text-lg font-bold">
          <UsersIcon size={22} />
          Murid masuk lewat menu &quot;Main kuis seru&quot; dengan kode ini
        </p>
        <p className="mt-2 font-display text-6xl font-extrabold tracking-[0.25em] text-ink sm:text-7xl">{session.join_code}</p>
      </div>

      <div className="mb-6 grid gap-3 sm:grid-cols-3">
        <button onClick={begin} className="btn-green min-h-[56px]">
          <PlayIcon size={22} />
          Mulai
        </button>
        <button onClick={next} className="btn-primary min-h-[56px]">
          Soal berikutnya
          <ArrowRightIcon size={22} />
        </button>
        <button onClick={end} className="btn-danger min-h-[56px]">
          Akhiri
        </button>
      </div>

      {liveState?.kind === "question_started" && (
        <section className="surface" aria-live="polite">
          <p className="mb-3 font-display text-2xl font-bold">{liveState.question_text}</p>
          <ul className="grid gap-2 sm:grid-cols-2">
            {liveState.options?.map((o, i) => (
              <li key={o} className="rounded-2xl bg-paper px-4 py-3 font-semibold">
                {String.fromCharCode(65 + i)}. {o}
              </li>
            ))}
          </ul>
        </section>
      )}

      {liveState?.kind === "question_closed" && (
        <section className="surface" aria-live="polite">
          <p className="mb-3 flex items-center gap-2 font-display text-xl font-bold text-correct-dark">
            <CheckIcon size={24} />
            Jawaban benar: {liveState.correct_answer}
          </p>
          <ul className="flex flex-col gap-2">
            {Object.entries(liveState.distribution ?? {}).map(([opt, n]) => (
              <li key={opt} className="flex items-center gap-3">
                <span className="min-w-0 flex-1 truncate font-semibold">{opt}</span>
                <span className="font-display text-xl font-bold">{n}</span>
              </li>
            ))}
          </ul>
        </section>
      )}

      {liveState?.kind === "session_ended" && (
        <div className="surface flex items-center gap-4">
          <Mascot mood="cheering" size={80} className="shrink-0" />
          <p className="font-display text-xl font-bold">Kuis selesai. Kerja bagus!</p>
        </div>
      )}
    </PageShell>
  );
}
