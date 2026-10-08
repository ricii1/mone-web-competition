"use client";

import { useParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { ApiError, api } from "@/lib/api";
import { connectRealtime } from "@/lib/realtime";
import type { LeaderboardEntry } from "@/lib/types";

export default function LeaderboardPage() {
  const { classId } = useParams<{ classId: string }>();
  const [entries, setEntries] = useState<LeaderboardEntry[]>([]);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setEntries(await api.getLeaderboard(classId));
  }, [classId]);

  useEffect(() => {
    load().catch((err) => setError(err instanceof ApiError ? err.message : "Gagal memuat leaderboard"));
  }, [load]);

  useEffect(() => {
    return connectRealtime(
      `/ws/classes/${classId}`,
      (event) => {
        if (event.type === "leaderboard_updated") load().catch(() => {});
      },
      () => load().catch(() => {})
    );
  }, [classId, load]);

  return (
    <main className="mx-auto max-w-md px-4 py-10 sm:px-6">
      <h1 className="mb-6 font-display text-2xl">Leaderboard</h1>
      {error && <p className="mb-4 text-sm text-alert">{error}</p>}
      <ol className="flex flex-col gap-2">
        {entries.map((e) => (
          <li key={e.user_id} className="card flex items-center justify-between py-3">
            <span className="text-sm">
              <span className="mr-2 text-ink/40">#{e.rank}</span>
              {e.name}
            </span>
            <span className="font-display text-lg text-highlight-dark">{e.score}</span>
          </li>
        ))}
        {entries.length === 0 && <p className="text-sm text-ink/60">Belum ada skor.</p>}
      </ol>
    </main>
  );
}
