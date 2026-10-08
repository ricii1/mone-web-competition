"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { ApiError, api } from "@/lib/api";
import ClassBadges from "@/components/ClassBadges";
import PageShell from "@/components/PageShell";
import type { SchoolClass } from "@/lib/types";

export default function TeacherDashboard() {
  const [classes, setClasses] = useState<SchoolClass[]>([]);
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [visibility, setVisibility] = useState<"public" | "private">("public");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  async function load() {
    setLoading(true);
    try {
      setClasses(await api.listOwnedClasses());
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Gagal memuat class");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      await api.createClass(title, description, visibility);
      setTitle("");
      setDescription("");
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Gagal membuat class");
    }
  }

  return (
    <PageShell title="Dashboard guru" subtitle="Kelola kelas, materi, dan soal dari satu tempat.">
      <div className="grid gap-8 lg:grid-cols-[minmax(0,1fr)_340px] lg:items-start">
        <section aria-labelledby="my-classes">
          <h2 id="my-classes" className="mb-3 font-display text-xl">
            Class saya
          </h2>
          {loading && <p className="text-sm text-ink/60">Memuat...</p>}
          {!loading && classes.length === 0 && (
            <div className="surface text-center">
              <p className="font-display text-lg">Belum ada class</p>
              <p className="mt-1 text-sm text-ink/65">Buat class pertamamu lewat formulir, lalu unggah materi PDF.</p>
            </div>
          )}
          <ul className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
            {classes.map((c) => (
              <li key={c.id}>
                <Link
                  href={`/teacher/classes/${c.id}`}
                  className="card card-link flex h-full flex-col gap-2 p-5"
                >
                  <ClassBadges cls={c} />
                  <span className="font-display text-lg leading-snug">{c.title}</span>
                  {c.description && <span className="line-clamp-3 text-sm text-ink/65">{c.description}</span>}
                </Link>
              </li>
            ))}
          </ul>
        </section>

        <form onSubmit={handleCreate} className="surface flex flex-col gap-4 lg:sticky lg:top-20">
          <h2 className="font-display text-xl">Buat class baru</h2>
          <div className="field">
            <label htmlFor="title" className="field-label">
              Judul class
            </label>
            <input id="title" value={title} onChange={(e) => setTitle(e.target.value)} required className="input-box" />
          </div>
          <div className="field">
            <label htmlFor="description" className="field-label">
              Deskripsi
            </label>
            <textarea
              id="description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="input-box"
              rows={3}
            />
          </div>
          <div className="field">
            <span className="field-label">Visibilitas</span>
            <div className="flex gap-2">
              {(["public", "private"] as const).map((v) => (
                <button
                  key={v}
                  type="button"
                  onClick={() => setVisibility(v)}
                  aria-pressed={visibility === v}
                  className={`min-h-[44px] flex-1 rounded-lg border px-4 py-2 text-sm transition-colors ${
                    visibility === v ? "border-highlight bg-highlight/15 font-medium" : "border-rule hover:border-ink/30"
                  }`}
                >
                  {v === "public" ? "Public" : "Private"}
                </button>
              ))}
            </div>
          </div>
          {error && <p className="text-sm text-alert">{error}</p>}
          <button type="submit" className="btn-primary">
            Buat class
          </button>
        </form>
      </div>
    </PageShell>
  );
}
