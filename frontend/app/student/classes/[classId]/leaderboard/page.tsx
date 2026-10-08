"use client";

import { useParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import PageShell from "@/components/PageShell";
import { ApiError, api } from "@/lib/api";
import { connectRealtime } from "@/lib/realtime";
import type { LeaderboardEntry } from "@/lib/types";

export default function LeaderboardPage() {
  const { classId } = useParams<{ classId: string }>();
  const [entries, setEntries] = useState<LeaderboardEntry[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [meId, setMeId] = useState<string | null>(null);

  useEffect(() => {
    api.me().then((u) => setMeId(u.id)).catch(() => {});
  }, []);

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

  const MEDAL = ["bg-highlight text-ink", "bg-chalk-dim text-ink", "bg-highlight-dark/70 text-ink"];

  return (
    <PageShell
      width="medium"
      back={{ href: `/student/classes/${classId}/map`, label: "Peta level" }}
      title="Leaderboard"
      subtitle="Skor dihitung dari nilai terbaik di setiap level."
    >
      {error && <p className="mb-4 text-sm text-alert">{error}</p>}
      {entries.length >= 3 && (
        <div className="mb-6 grid grid-cols-3 items-end gap-3" aria-label="Tiga teratas">
          {[1, 0, 2].map((idx) => {
            const e = entries[idx];
            const heights = ["h-28", "h-20", "h-16"];
            return (
              <div key={e.user_id} className="flex flex-col items-center gap-2 text-center">
                <span className="line-clamp-2 text-sm font-medium">
                  {e.name}
                  {e.user_id === meId && <span className="badge-highlight ml-1">Kamu</span>}
                </span>
                <span className="font-display text-xl">{e.score}</span>
                <div
                  className={`${heights[idx]} flex w-full items-start justify-center rounded-t-xl pt-2 font-display text-2xl ${MEDAL[idx]}`}
                >
                  {e.rank}
                </div>
              </div>
            );
          })}
        </div>
      )}
      <ol className="flex flex-col gap-2">
        {entries.slice(entries.length >= 3 ? 3 : 0).map((e) => {
          const me = e.user_id === meId;
          return (
            <li
              key={e.user_id}
              className={`flex items-center gap-4 rounded-xl border px-4 py-3 shadow-sm shadow-ink/5 ${
                me ? "border-highlight bg-highlight/15" : "border-rule bg-white/70"
              } ${e.rank <= 3 ? "py-4" : ""}`}
            >
              <span
                className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-full font-display text-base ${
                  e.rank <= 3 ? MEDAL[e.rank - 1] : "bg-ink/10 text-ink"
                }`}
              >
                {e.rank}
              </span>
              <span className="min-w-0 flex-1 truncate font-medium">
                {e.name}
                {me && <span className="badge-highlight ml-2">Kamu</span>}
              </span>
              <span className="font-display text-xl">{e.score}</span>
            </li>
          );
        })}
        {entries.length === 0 && <p className="surface text-sm text-ink/65">Belum ada skor.</p>}
      </ol>
    </PageShell>
  );
}
