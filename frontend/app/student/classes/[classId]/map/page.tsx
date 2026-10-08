"use client";

import dynamic from "next/dynamic";
import { useParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import PageShell from "@/components/PageShell";
import { ApiError, api } from "@/lib/api";
import type { Level, Progress } from "@/lib/types";

const LevelMap = dynamic(() => import("@/components/LevelMap"), { ssr: false });

export default function StudentMapPage() {
  const { classId } = useParams<{ classId: string }>();
  const [levels, setLevels] = useState<Level[]>([]);
  const [progress, setProgress] = useState<Progress[]>([]);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    const [l, p] = await Promise.all([api.listLevels(classId), api.getProgress(classId)]);
    setLevels(l);
    setProgress(p);
  }, [classId]);

  useEffect(() => {
    load().catch((err) => setError(err instanceof ApiError ? err.message : "Gagal memuat map"));
  }, [load]);

  const total = levels.length;
  const done = progress.filter((p) => p.status === "completed").length;
  const percent = total > 0 ? Math.round((done / total) * 100) : 0;
  const totalScore = progress.reduce((sum, p) => sum + p.best_score, 0);

  return (
    <PageShell
      back={{ href: "/student", label: "Class saya" }}
      crumbs={[{ label: "Class saya", href: "/student" }, { label: "Peta level" }]}
      title="Peta level"
      subtitle="Selesaikan level satu per satu untuk membuka level berikutnya."
      actions={
        <Link href={`/student/classes/${classId}/leaderboard`} className="btn-ghost">
          Leaderboard
        </Link>
      }
    >
      {error && <p className="mb-4 text-sm text-alert">{error}</p>}
      {levels.length === 0 && !error && <p className="surface text-sm text-ink/65">Belum ada level.</p>}
      {total > 0 && (
        <div className="surface mb-4 grid gap-4 sm:grid-cols-[1fr_auto_auto] sm:items-center">
          <div>
            <p className="mb-2 text-sm font-medium">
              {done} dari {total} level selesai
            </p>
            <div
              className="h-2.5 w-full overflow-hidden rounded-full bg-rule"
              role="progressbar"
              aria-valuenow={percent}
              aria-valuemin={0}
              aria-valuemax={100}
              aria-label="Progres level"
            >
              <div className="h-full rounded-full bg-correct" style={{ width: `${percent}%` }} />
            </div>
          </div>
          <div className="text-center sm:px-4">
            <p className="font-display text-2xl leading-none">{percent}%</p>
            <p className="mt-1 text-xs text-ink/65">Selesai</p>
          </div>
          <div className="text-center sm:px-4">
            <p className="font-display text-2xl leading-none">{totalScore}</p>
            <p className="mt-1 text-xs text-ink/65">Total skor</p>
          </div>
        </div>
      )}
      {levels.length > 0 && <LevelMap classId={classId} levels={levels} progress={progress} height="clamp(420px, 70vh, 760px)" />}
    </PageShell>
  );
}
