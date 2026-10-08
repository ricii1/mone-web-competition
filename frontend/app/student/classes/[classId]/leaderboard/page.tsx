"use client";

import { useParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import Avatar from "@/components/Avatar";
import { CrownIcon, MedalIcon, StarIcon, TrophyIcon } from "@/components/icons";
import Mascot from "@/components/Mascot";
import PageShell from "@/components/PageShell";
import { ApiError, api } from "@/lib/api";
import { connectRealtime } from "@/lib/realtime";
import type { LeaderboardEntry } from "@/lib/types";

// Gold, silver, bronze: the rank number and medal icon also say the place, not only the color.
const PODIUM = [
  { block: "bg-highlight h-32", medal: "text-ink" },
  { block: "bg-[#C9D3DF] h-24", medal: "text-ink" },
  { block: "bg-[#E3A878] h-20", medal: "text-ink" },
];

export default function LeaderboardPage() {
  const { classId } = useParams<{ classId: string }>();
  const [entries, setEntries] = useState<LeaderboardEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [meId, setMeId] = useState<string | null>(null);

  useEffect(() => {
    api.me().then((u) => setMeId(u.id)).catch(() => {});
  }, []);

  const load = useCallback(async () => {
    setEntries(await api.getLeaderboard(classId));
  }, [classId]);

  useEffect(() => {
    load()
      .catch((err) => setError(err instanceof ApiError ? err.message : "Peringkat belum bisa dimuat. Coba lagi ya."))
      .finally(() => setLoading(false));
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

  const podium = entries.length >= 3;
  const rest = entries.slice(podium ? 3 : 0);

  return (
    <PageShell
      kid
      width="medium"
      back={{ href: `/student/classes/${classId}/map`, label: "Kembali ke peta" }}
      icon={<TrophyIcon size={28} />}
      title="Peringkat"
      subtitle="Makin banyak bintang, makin tinggi peringkatmu!"
    >
      {error && (
        <p role="alert" className="note mb-4 border-coral bg-coral-soft text-alert">
          {error}
        </p>
      )}
      {loading && <p role="status" className="surface text-center font-bold">Sebentar ya...</p>}
      {!loading && !error && entries.length === 0 && (
        <div className="surface flex items-center gap-4">
          <Mascot mood="thinking" size={90} className="shrink-0" />
          <p className="text-xl">Belum ada yang punya skor. Kamu bisa jadi yang pertama!</p>
        </div>
      )}

      {podium && (
        <ol className="surface mb-6 grid grid-cols-3 items-end gap-2 !bg-sky-soft !pt-10 sm:gap-4" aria-label="Tiga teratas">
          {[1, 0, 2].map((idx) => {
            const e = entries[idx];
            const me = e.user_id === meId;
            return (
              <li key={e.user_id} className="flex min-w-0 flex-col items-center gap-1 text-center">
                <span className={`${idx === 0 ? "bob" : ""} relative`}>
                  {idx === 0 && (
                    <span className="absolute -top-6 left-1/2 -translate-x-1/2 text-highlight-dark">
                      <CrownIcon size={30} />
                    </span>
                  )}
                  <Avatar name={e.name} size={idx === 0 ? 72 : 56} />
                </span>
                <span className="w-full truncate text-lg font-bold">{e.name}</span>
                {me && <span className="badge-highlight">Kamu</span>}
                <span className="flex items-center gap-1 font-display text-xl font-bold">
                  <StarIcon size={18} />
                  {e.score}
                </span>
                <div
                  className={`${PODIUM[idx].block} flex w-full flex-col items-center justify-start gap-1 rounded-t-2xl pt-2 font-display text-3xl font-bold text-ink`}
                >
                  <span className={PODIUM[idx].medal}>
                    <MedalIcon size={28} />
                  </span>
                  {e.rank}
                </div>
              </li>
            );
          })}
        </ol>
      )}

      <ol className="flex flex-col gap-3">
        {rest.map((e) => {
          const me = e.user_id === meId;
          return (
            <li
              key={e.user_id}
              className={`flex min-h-[64px] items-center gap-3 rounded-2xl border-2 px-4 py-2 ${
                me ? "border-highlight-dark bg-highlight/25" : "border-rule bg-white"
              }`}
              style={{ boxShadow: "0 3px 0 0 #e6dcc0" }}
            >
              <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-ink/10 font-display text-xl font-bold">
                {e.rank}
              </span>
              <Avatar name={e.name} size={44} />
              <span className="min-w-0 flex-1 truncate font-bold">
                {e.name}
                {me && <span className="badge-highlight ml-2">Kamu</span>}
              </span>
              <span className="flex items-center gap-1 font-display text-2xl font-bold">
                <span className="text-highlight-dark">
                  <StarIcon size={22} />
                </span>
                {e.score}
              </span>
            </li>
          );
        })}
      </ol>
    </PageShell>
  );
}
