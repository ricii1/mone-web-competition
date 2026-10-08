"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { ApiError, api } from "@/lib/api";
import { connectRealtime } from "@/lib/realtime";
import type { Level, Material, SchoolClass, VectorStatus } from "@/lib/types";

const VECTOR_STATUS_COLOR: Record<VectorStatus, string> = {
  pending: "text-ink/50",
  processing: "text-highlight-dark",
  ready: "text-correct",
  failed: "text-alert",
};

export default function TeacherClassPage() {
  const { classId } = useParams<{ classId: string }>();
  const [cls, setCls] = useState<SchoolClass | null>(null);
  const [materials, setMaterials] = useState<Material[]>([]);
  const [levels, setLevels] = useState<Level[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);

  const loadClass = useCallback(async () => {
    setCls(await api.getClass(classId));
  }, [classId]);

  const loadMaterials = useCallback(async () => {
    setMaterials(await api.listMaterials(classId));
  }, [classId]);

  const loadLevels = useCallback(async () => {
    setLevels(await api.listLevels(classId));
  }, [classId]);

  useEffect(() => {
    loadClass().catch(() => {});
    loadMaterials().catch(() => {});
    loadLevels().catch(() => {});
  }, [loadClass, loadMaterials, loadLevels]);

  useEffect(() => {
    const stop = connectRealtime(
      `/ws/classes/${classId}`,
      (event) => {
        if (event.type === "material_progress" || event.type === "level_created") {
          loadMaterials().catch(() => {});
          loadLevels().catch(() => {});
        }
      },
      () => {
        loadMaterials().catch(() => {});
        loadLevels().catch(() => {});
      }
    );
    return stop;
  }, [classId, loadMaterials, loadLevels]);

  async function handleUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    setError(null);
    try {
      await api.uploadMaterial(classId, file);
      await loadMaterials();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Gagal mengunggah materi");
    } finally {
      setUploading(false);
      e.target.value = "";
    }
  }

  async function handleGenerate() {
    setError(null);
    try {
      await api.generateLevels(classId);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Gagal memulai generate level");
    }
  }

  async function handlePublish() {
    setError(null);
    try {
      await api.publishClass(classId);
      await loadClass();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Gagal publish class");
    }
  }

  const readyMaterials = materials.some((m) => m.vector_status === "ready");

  return (
    <main className="mx-auto max-w-2xl px-4 py-10 sm:px-6">
      <h1 className="mb-1 font-display text-2xl">{cls?.title ?? "Memuat..."}</h1>
      {cls && (
        <p className="mb-6 text-sm text-ink/60">
          {cls.is_example && (
            <span className="mr-2 rounded-sm bg-highlight/20 px-2 py-0.5 text-xs font-medium text-ink">
              Contoh
            </span>
          )}
          {cls.visibility} · {cls.status}
          {cls.invite_code && <> · kode undangan: {cls.invite_code}</>}
        </p>
      )}
      {cls?.is_example && (
        <p className="mb-4 rounded-sm border border-highlight/40 bg-highlight/10 p-3 text-sm">
          {cls.description}
        </p>
      )}
      {error && <p className="mb-4 text-sm text-alert">{error}</p>}

      <section className="card mb-6">
        <h2 className="mb-3 font-display text-lg">Materi PDF</h2>
        <label className="btn-ghost w-fit cursor-pointer text-sm">
          {uploading ? "Mengunggah..." : "Unggah PDF"}
          <input
            type="file"
            accept="application/pdf"
            onChange={handleUpload}
            disabled={uploading}
            className="hidden"
          />
        </label>
        <ul className="mt-4 flex flex-col gap-1 text-sm">
          {materials.map((m) => (
            <li key={m.id}>
              {m.file_name} —{" "}
              <span className={`font-medium ${VECTOR_STATUS_COLOR[m.vector_status]}`}>{m.vector_status}</span>
              {m.error_message && <span className="text-alert"> ({m.error_message})</span>}
            </li>
          ))}
          {materials.length === 0 && <li className="text-ink/50">Belum ada materi.</li>}
        </ul>
      </section>

      <section className="card mb-6">
        <div className="mb-3 flex items-center justify-between">
          <h2 className="font-display text-lg">Level & soal</h2>
          <button
            onClick={handleGenerate}
            disabled={!readyMaterials}
            className="btn-primary px-3 py-1.5 text-sm"
          >
            Generate level
          </button>
        </div>
        <ul className="flex flex-col gap-1 text-sm">
          {levels.map((l) => (
            <li key={l.id}>
              <Link href={`/teacher/classes/${classId}/levels/${l.id}`} className="link-text">
                {l.order_index + 1}. {l.title} ({l.type}, {l.status})
              </Link>
            </li>
          ))}
          {levels.length === 0 && <li className="text-ink/50">Belum ada level.</li>}
        </ul>
      </section>

      <div className="flex gap-3">
        {!cls?.is_example && (
          <button onClick={handlePublish} className="btn-primary">
            Publish class
          </button>
        )}
        <Link href={`/teacher/classes/${classId}/live`} className="btn-ghost">
          Live class
        </Link>
      </div>
    </main>
  );
}
