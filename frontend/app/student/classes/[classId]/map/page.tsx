"use client";

import dynamic from "next/dynamic";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { FlagIcon, MapIcon, StarIcon, TrophyIcon } from "@/components/icons";
import Mascot from "@/components/Mascot";
import PageShell from "@/components/PageShell";
import { ApiError, api } from "@/lib/api";
import { useClassTitle } from "@/lib/useClassTitle";
import type { Level, Progress } from "@/lib/types";

const LevelMap = dynamic(() => import("@/components/LevelMap"), {
  ssr: false,
  loading: () => (
    <p role="status" className="surface text-center font-bold">
      Peta sedang disiapkan...
    </p>
  ),
});

export default function StudentMapPage() {
  const { classId } = useParams<{ classId: string }>();
  const classTitle = useClassTitle(classId);
  const [levels, setLevels] = useState<Level[]>([]);
  const [progress, setProgress] = useState<Progress[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    const [l, p] = await Promise.all([api.listLevels(classId), api.getProgress(classId)]);
    setLevels(l);
    setProgress(p);
  }, [classId]);

  useEffect(() => {
    load()
      .catch((err) => setError(err instanceof ApiError ? err.message : "Peta belum bisa dibuka. Coba lagi ya."))
      .finally(() => setLoading(false));
  }, [load]);

  const total = levels.length;
  const done = progress.filter((p) => p.status === "completed").length;
  const percent = total > 0 ? Math.round((done / total) * 100) : 0;
  const totalScore = progress.reduce((sum, p) => sum + p.best_score, 0);

  return (
    <PageShell
      back={{ href: "/student", label: "Kembali ke kelasku" }}
      icon={<MapIcon size={28} />}
      title={classTitle ?? "Peta petualangan"}
      subtitle="Selesaikan level satu per satu. Kumpulkan bintang!"
      actions={
        <Link href={`/student/classes/${classId}/leaderboard`} className="btn-primary">
          <TrophyIcon size={22} />
          Peringkat
        </Link>
      }
    >
      {error && (
        <div role="alert" className="surface mb-4 flex items-center gap-4">
          <Mascot mood="oops" size={80} className="shrink-0" />
          <p className="text-xl font-bold">{error}</p>
        </div>
      )}
      {loading && (
        <p role="status" className="surface text-center font-bold">
          Sebentar ya...
        </p>
      )}
      {!loading && !error && total === 0 && (
        <div className="surface flex items-center gap-4">
          <Mascot mood="sleepy" size={90} className="shrink-0" />
          <p className="text-xl">Level belum ada. Tunggu gurumu menyiapkannya ya!</p>
        </div>
      )}
      {total > 0 && (
        <div className="mb-5 grid grid-cols-2 gap-3 sm:grid-cols-[1fr_auto_auto] sm:items-center">
          <div className="surface col-span-2 !p-4 sm:col-span-1">
            <p className="mb-2 flex items-center gap-2 font-display text-xl font-bold">
              <FlagIcon size={22} />
              {done} dari {total} level selesai
            </p>
            <div
              className="h-5 w-full overflow-hidden rounded-full bg-rule/60"
              role="progressbar"
              aria-valuenow={percent}
              aria-valuemin={0}
              aria-valuemax={100}
              aria-label="Progres level"
            >
              <div className="h-full rounded-full bg-grass transition-[width] duration-300" style={{ width: `${percent}%` }} />
            </div>
          </div>
          <div className="surface flex items-center justify-center gap-2 !p-4">
            <span className="text-highlight-dark">
              <StarIcon size={30} />
            </span>
            <span>
              <span className="block font-display text-2xl font-bold leading-none">{totalScore}</span>
              <span className="text-base text-ink/75">Skor</span>
            </span>
          </div>
          <div className="surface flex items-center justify-center gap-2 !p-4">
            <span className="text-grass-dark">
              <FlagIcon size={30} />
            </span>
            <span>
              <span className="block font-display text-2xl font-bold leading-none">{percent}%</span>
              <span className="text-base text-ink/75">Selesai</span>
            </span>
          </div>
        </div>
      )}
      {total > 0 && <LevelMap classId={classId} levels={levels} progress={progress} height="clamp(440px, 68vh, 760px)" />}
    </PageShell>
  );
}
