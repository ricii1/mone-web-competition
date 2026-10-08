"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { ApiError, api } from "@/lib/api";
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
    <main className="mx-auto max-w-2xl px-4 py-10 sm:px-6">
      <h1 className="mb-1 font-display text-2xl">Dashboard Guru</h1>
      <p className="mb-8 text-ink/60">Kelola kelas, materi, dan soal dari satu tempat.</p>

      <form onSubmit={handleCreate} className="card mb-10 flex flex-col gap-4">
        <h2 className="font-display text-lg">Buat class baru</h2>
        <div className="field">
          <label htmlFor="title" className="field-label">
            Judul class
          </label>
          <input id="title" value={title} onChange={(e) => setTitle(e.target.value)} required className="input-rule" />
        </div>
        <div className="field">
          <label htmlFor="description" className="field-label">
            Deskripsi
          </label>
          <textarea
            id="description"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            className="input-rule"
            rows={2}
          />
        </div>
        <div className="field">
          <span className="field-label">Visibilitas</span>
          <div className="flex gap-3">
            {(["public", "private"] as const).map((v) => (
              <button
                key={v}
                type="button"
                onClick={() => setVisibility(v)}
                aria-pressed={visibility === v}
                className={`rounded-sm border px-4 py-2 text-sm transition-colors ${
                  visibility === v ? "border-highlight bg-highlight/10" : "border-rule hover:border-ink/30"
                }`}
              >
                {v === "public" ? "Public" : "Private"}
              </button>
            ))}
          </div>
        </div>
        {error && <p className="text-sm text-alert">{error}</p>}
        <button type="submit" className="btn-primary self-start">
          Buat class
        </button>
      </form>

      <h2 className="mb-3 font-display text-lg">Class saya</h2>
      {loading && <p className="text-sm text-ink/60">Memuat...</p>}
      {!loading && classes.length === 0 && <p className="text-sm text-ink/60">Belum ada class.</p>}
      <ul className="flex flex-col gap-2">
        {classes.map((c) => (
          <li key={c.id}>
            <Link href={`/teacher/classes/${c.id}`} className="card block transition-colors hover:border-ink/30">
              <span className="font-medium">{c.title}</span>{" "}
              <span className="text-xs text-ink/50">
                ({c.visibility}, {c.status})
              </span>
            </Link>
          </li>
        ))}
      </ul>
    </main>
  );
}
