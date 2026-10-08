"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { ApiError, api } from "@/lib/api";
import ClassBadges from "@/components/ClassBadges";
import { BookIcon, PlusIcon } from "@/components/icons";
import Mascot from "@/components/Mascot";
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
      setError(err instanceof ApiError ? err.message : "Kelas belum bisa dimuat. Coba lagi ya.");
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
      setError(err instanceof ApiError ? err.message : "Kelas belum bisa dibuat. Coba lagi ya.");
    }
  }

  return (
    <PageShell title="Halo, Bapak/Ibu Guru!" icon={<BookIcon size={28} />} subtitle="Kelola kelas, materi, dan soal dari satu tempat.">
      <div className="grid gap-8 lg:grid-cols-[minmax(0,1fr)_340px] lg:items-start">
        <section aria-labelledby="my-classes">
          <h2 id="my-classes" className="mb-3 text-2xl">
            Kelas saya
          </h2>
          {loading && <p role="status" className="text-ink/75">Memuat...</p>}
          {!loading && classes.length === 0 && (
            <div className="surface flex items-center gap-4">
              <Mascot mood="thinking" size={80} className="shrink-0" />
              <div>
                <p className="font-display text-xl font-bold">Belum ada kelas</p>
                <p className="text-ink/75">Buat kelas pertamamu lewat formulir, lalu unggah materi PDF.</p>
              </div>
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
                  <span className="font-display text-xl font-bold leading-snug">{c.title}</span>
                  {c.description && <span className="line-clamp-3 text-ink/75">{c.description}</span>}
                </Link>
              </li>
            ))}
          </ul>
        </section>

        <form onSubmit={handleCreate} className="surface flex flex-col gap-4 lg:sticky lg:top-20">
          <h2 className="flex items-center gap-2 text-2xl"><PlusIcon size={24} />Buat kelas baru</h2>
          <div className="field">
            <label htmlFor="title" className="field-label">
              Nama kelas
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
            <span className="field-label">Siapa yang boleh masuk?</span>
            <div className="flex gap-2">
              {(["public", "private"] as const).map((v) => (
                <button
                  key={v}
                  type="button"
                  onClick={() => setVisibility(v)}
                  aria-pressed={visibility === v}
                  className={`min-h-[48px] flex-1 rounded-2xl border-2 px-4 py-2 font-bold transition-colors ${
                    visibility === v ? "border-sky-dark bg-sky-soft" : "border-rule bg-white hover:border-sky"
                  }`}
                >
                  {v === "public" ? "Semua murid" : "Pakai kode"}
                </button>
              ))}
            </div>
          </div>
          {error && <p role="alert" className="note border-coral bg-coral-soft text-alert">{error}</p>}
          <button type="submit" className="btn-primary">
            <PlusIcon size={22} />
            Buat kelas
          </button>
        </form>
      </div>
    </PageShell>
  );
}
