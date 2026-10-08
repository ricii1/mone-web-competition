"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { ApiError, api } from "@/lib/api";
import { BookIcon, MapIcon, PlusIcon, RocketIcon, TrophyIcon, UsersIcon } from "@/components/icons";
import Mascot from "@/components/Mascot";
import PageShell from "@/components/PageShell";
import type { SchoolClass, User } from "@/lib/types";

const CARD_COLORS = [
  { chip: "bg-sky-soft text-sky-dark", edge: "border-sky" },
  { chip: "bg-grass-soft text-grass-dark", edge: "border-grass" },
  { chip: "bg-coral-soft text-coral-dark", edge: "border-coral" },
  { chip: "bg-grape-soft text-grape-dark", edge: "border-grape" },
];

export default function StudentDashboard() {
  const [user, setUser] = useState<User | null>(null);
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
      setError(err instanceof ApiError ? err.message : "Kelas belum bisa dimuat. Coba lagi ya.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
    api.me().then(setUser).catch(() => {});
  }, []);

  async function handleJoin(classId: string) {
    setError(null);
    try {
      await api.joinClass(classId, inviteCode[classId]);
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Belum bisa masuk kelas. Cek kodenya ya.");
    }
  }

  const firstName = user?.name.split(" ")[0];

  return (
    <PageShell width="wide">
      <section className="surface mb-8 flex flex-col items-center gap-4 !bg-sky-soft sm:flex-row sm:gap-6">
        <Mascot mood="happy" size={120} className="bob shrink-0" />
        <div className="min-w-0 flex-1 text-center sm:text-left">
          <h1 className="text-3xl sm:text-4xl">{firstName ? `Halo, ${firstName}!` : "Halo!"}</h1>
          <p className="text-xl text-ink/80">Ayo belajar hari ini. Ada bintang yang menunggumu!</p>
        </div>
        <Link href="/student/live" className="btn-primary w-full sm:w-auto">
          <RocketIcon size={24} />
          Main kuis seru
        </Link>
      </section>

      {error && (
        <p role="alert" className="note mb-4 border-coral bg-coral-soft text-alert">
          {error}
        </p>
      )}
      {loading && (
        <p role="status" className="mb-4 flex items-center gap-2 font-bold text-ink/75">
          <span className="wait-dot inline-block h-3 w-3 rounded-full bg-sky" />
          Sebentar ya...
        </p>
      )}

      <section className="mb-10" aria-labelledby="my-classes">
        <h2 id="my-classes" className="mb-3 flex items-center gap-2 text-3xl">
          <BookIcon size={30} />
          Kelasku
        </h2>
        {!loading && enrolled.length === 0 && (
          <div className="surface flex items-center gap-4">
            <Mascot mood="thinking" size={80} className="shrink-0" />
            <p className="text-xl">Kamu belum punya kelas. Pilih kelas di bawah, ya!</p>
          </div>
        )}
        <ul className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {enrolled.map((c, i) => {
            const color = CARD_COLORS[i % CARD_COLORS.length];
            return (
              <li key={c.id} className={`card flex flex-col gap-3 !rounded-3xl !border-2 p-5 ${color.edge}`}>
                <span className={`flex h-14 w-14 items-center justify-center rounded-2xl ${color.chip}`}>
                  <BookIcon size={30} />
                </span>
                <span className="font-display text-2xl font-bold leading-tight">{c.title}</span>
                {c.description && <span className="line-clamp-2 text-base text-ink/75">{c.description}</span>}
                <div className="mt-auto flex flex-col gap-3 pt-2">
                  <Link href={`/student/classes/${c.id}/map`} className="btn-green">
                    <MapIcon size={22} />
                    Ayo main
                  </Link>
                  <Link href={`/student/classes/${c.id}/leaderboard`} className="btn-ghost">
                    <TrophyIcon size={22} />
                    Peringkat
                  </Link>
                </div>
              </li>
            );
          })}
        </ul>
      </section>

      <section aria-labelledby="available-classes">
        <h2 id="available-classes" className="mb-3 flex items-center gap-2 text-3xl">
          <PlusIcon size={30} />
          Cari kelas baru
        </h2>
        <ul className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {available.map((c) => (
            <li key={c.id} className="card flex flex-col gap-3 !rounded-3xl p-5">
              <span className="badge w-fit">
                <UsersIcon size={16} />
                {c.visibility === "private" ? "Pakai kode" : "Terbuka"}
              </span>
              <span className="font-display text-2xl font-bold leading-tight">{c.title}</span>
              {c.description && <span className="line-clamp-2 text-base text-ink/75">{c.description}</span>}
              <div className="mt-auto flex flex-col gap-3 pt-2">
                {c.visibility === "private" && (
                  <input
                    aria-label={`Kode kelas ${c.title}`}
                    placeholder="Tulis kode kelas"
                    value={inviteCode[c.id] ?? ""}
                    onChange={(e) => setInviteCode((s) => ({ ...s, [c.id]: e.target.value }))}
                    className="input-box"
                  />
                )}
                <button onClick={() => handleJoin(c.id)} className="btn-primary">
                  <PlusIcon size={22} />
                  Gabung
                </button>
              </div>
            </li>
          ))}
        </ul>
        {!loading && available.length === 0 && (
          <p className="surface text-center text-xl">Belum ada kelas lain. Nanti cek lagi ya!</p>
        )}
      </section>
    </PageShell>
  );
}
