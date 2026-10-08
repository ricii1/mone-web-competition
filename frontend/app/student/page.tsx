"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { ApiError, api } from "@/lib/api";
import PageShell from "@/components/PageShell";
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
    <PageShell
      title="Dashboard murid"
      subtitle="Lanjutkan peta level kelasmu, atau join class baru."
      actions={
        <Link href="/student/live" className="btn-ghost">
          Masuk live class
        </Link>
      }
    >
      {error && <p role="alert" className="mb-4 text-sm text-alert">{error}</p>}
      {loading && <p className="text-sm text-ink/60">Memuat...</p>}

      <section className="mb-10" aria-labelledby="my-classes">
        <h2 id="my-classes" className="mb-3 font-display text-xl">
          Class saya
        </h2>
        {!loading && enrolled.length === 0 && (
          <p className="surface text-sm text-ink/65">Belum join class apapun. Pilih class di bawah untuk mulai.</p>
        )}
        <ul className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {enrolled.map((c) => (
            <li key={c.id} className="card flex flex-col gap-3 p-5">
              <span className="font-display text-lg leading-snug">{c.title}</span>
              {c.description && <span className="line-clamp-2 text-sm text-ink/65">{c.description}</span>}
              <div className="mt-auto flex gap-2 pt-1">
                <Link href={`/student/classes/${c.id}/map`} className="btn-primary flex-1 text-sm">
                  Buka peta
                </Link>
                <Link href={`/student/classes/${c.id}/leaderboard`} className="btn-ghost text-sm">
                  Leaderboard
                </Link>
              </div>
            </li>
          ))}
        </ul>
      </section>

      <section aria-labelledby="available-classes">
        <h2 id="available-classes" className="mb-3 font-display text-xl">
          Class tersedia
        </h2>
        <ul className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {available.map((c) => (
            <li key={c.id} className="card flex flex-col gap-3 p-5">
              <div className="flex flex-col gap-1.5">
                <span className="badge w-fit">{c.visibility === "private" ? "Private" : "Public"}</span>
                <span className="font-display text-lg leading-snug">{c.title}</span>
                {c.description && <span className="line-clamp-2 text-sm text-ink/65">{c.description}</span>}
              </div>
              <div className="mt-auto flex gap-2">
                {c.visibility === "private" && (
                  <input
                    aria-label={`Kode undangan untuk ${c.title}`}
                    placeholder="Kode undangan"
                    value={inviteCode[c.id] ?? ""}
                    onChange={(e) => setInviteCode((s) => ({ ...s, [c.id]: e.target.value }))}
                    className="input-box min-w-0 flex-1 text-sm"
                  />
                )}
                <button onClick={() => handleJoin(c.id)} className="btn-primary text-sm">
                  Join
                </button>
              </div>
            </li>
          ))}
        </ul>
        {!loading && available.length === 0 && (
          <p className="text-sm text-ink/60">Tidak ada class tersedia saat ini.</p>
        )}
      </section>
    </PageShell>
  );
}
