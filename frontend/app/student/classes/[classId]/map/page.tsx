"use client";

import dynamic from "next/dynamic";
import { useParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
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

  return (
    <main className="mx-auto max-w-4xl px-4 py-10 sm:px-6">
      <h1 className="mb-6 font-display text-2xl">Peta level</h1>
      {error && <p className="mb-4 text-sm text-alert">{error}</p>}
      {levels.length === 0 && !error && <p className="text-sm text-ink/60">Belum ada level.</p>}
      {levels.length > 0 && <LevelMap classId={classId} levels={levels} progress={progress} />}
    </main>
  );
}
