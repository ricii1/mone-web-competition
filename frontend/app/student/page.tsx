"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { ApiError, api } from "@/lib/api";
import type { SchoolClass } from "@/lib/types";

export default function StudentDashboard() {
  const [enrolled, setEnrolled] = useState<SchoolClass[]>([]);
  const [available, setAvailable] = useState<SchoolClass[]>([]);
  const [inviteCode, setInviteCode] = useState<Record<string, string>>({});
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  async function load() {
    setLoading(true);
    try {
      const [mine, all] = await Promise.all([api.listEnrolledClasses(), api.listClasses()]);
      setEnrolled(mine);
      const enrolledIds = new Set(mine.map((c) => c.id));
      setAvailable(all.filter((c) => !enrolledIds.has(c.id)));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Gagal memuat class");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function handleJoin(classId: string) {
    setError(null);
    try {
      await api.joinClass(classId, inviteCode[classId]);
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Gagal join class");
    }
  }

  return (
    <main className="mx-auto max-w-2xl px-4 py-10 sm:px-6">
      <h1 className="mb-1 font-display text-2xl">Dashboard murid</h1>
      <p className="mb-8 text-ink/60">Lanjutkan peta level kelasmu, atau join class baru.</p>
      {error && <p className="mb-4 text-sm text-alert">{error}</p>}
      {loading && <p className="text-sm text-ink/60">Memuat...</p>}

      <section className="mb-10">
        <h2 className="mb-3 font-display text-lg">Class saya</h2>
        {!loading && enrolled.length === 0 && <p className="text-sm text-ink/60">Belum join class apapun.</p>}
        <ul className="flex flex-col gap-2">
          {enrolled.map((c) => (
            <li key={c.id} className="card flex items-center justify-between">
              <span className="font-medium">{c.title}</span>
              <div className="flex gap-4 text-sm">
                <Link href={`/student/classes/${c.id}/map`} className="link-text">
                  Map
                </Link>
                <Link href={`/student/classes/${c.id}/leaderboard`} className="link-text">
                  Leaderboard
                </Link>
              </div>
            </li>
          ))}
        </ul>
      </section>

      <section>
        <h2 className="mb-3 font-display text-lg">Class tersedia</h2>
        <ul className="flex flex-col gap-2">
          {available.map((c) => (
            <li key={c.id} className="card">
              <p className="mb-3 font-medium">
                {c.title} <span className="text-xs font-normal text-ink/50">({c.visibility})</span>
              </p>
              <div className="flex gap-2">
                {c.visibility === "private" && (
                  <input
                    placeholder="Kode undangan"
                    value={inviteCode[c.id] ?? ""}
                    onChange={(e) => setInviteCode((s) => ({ ...s, [c.id]: e.target.value }))}
                    className="input-rule max-w-[10rem] text-sm"
                  />
                )}
                <button onClick={() => handleJoin(c.id)} className="btn-primary px-3 py-1.5 text-sm">
                  Join
                </button>
              </div>
            </li>
          ))}
          {available.length === 0 && <p className="text-sm text-ink/60">Tidak ada class tersedia saat ini.</p>}
        </ul>
      </section>

      <Link href="/student/live" className="link-text mt-10 inline-block text-sm">
        Masuk live class dengan kode
      </Link>
    </main>
  );
}
