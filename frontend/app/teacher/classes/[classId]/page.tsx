"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import dynamic from "next/dynamic";
import { useCallback, useEffect, useState } from "react";
import { ApiError, api } from "@/lib/api";
import { connectRealtime, type GenerationProgressEvent } from "@/lib/realtime";
import ClassBadges from "@/components/ClassBadges";
import PageShell from "@/components/PageShell";
import type { Level, Material, SchoolClass, VectorStatus } from "@/lib/types";

const LevelMap = dynamic(() => import("@/components/LevelMap"), {
  ssr: false,
  loading: () => <p className="p-4 text-sm text-ink/50">Memuat peta level...</p>,
});

const STAGE_LABEL: Record<GenerationProgressEvent["payload"]["stage"], string> = {
  generating_levels: "Membuat level",
  generating_questions: "Membuat soal",
  done: "Selesai",
  failed: "Gagal",
};

const VECTOR_STATUS_COLOR: Record<VectorStatus, string> = {
  pending: "badge",
  processing: "badge-highlight",
  ready: "badge-success",
  failed: "badge-alert",
};

export default function TeacherClassPage() {
  const { classId } = useParams<{ classId: string }>();
  const [cls, setCls] = useState<SchoolClass | null>(null);
  const [materials, setMaterials] = useState<Material[]>([]);
  const [levels, setLevels] = useState<Level[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState<GenerationProgressEvent["payload"] | null>(null);
  const [confirming, setConfirming] = useState(false);
  const [starting, setStarting] = useState(false);
  const [loaded, setLoaded] = useState(false);

  const loadClass = useCallback(async () => {
    setCls(await api.getClass(classId));
  }, [classId]);

  const loadMaterials = useCallback(async () => {
    setMaterials(await api.listMaterials(classId));
  }, [classId]);

  const loadLevels = useCallback(async () => {
    setLevels(await api.listLevels(classId));
  }, [classId]);

  const refreshAll = useCallback(() => {
    loadClass().catch(() => {});
    loadMaterials().catch(() => {});
    loadLevels().catch(() => {});
  }, [loadClass, loadMaterials, loadLevels]);

  useEffect(() => {
    Promise.allSettled([loadClass(), loadMaterials(), loadLevels()]).then(() => setLoaded(true));
  }, [loadClass, loadMaterials, loadLevels]);

  const generating = cls?.generation_status === "generating";

  // Safety net while generating: events are only notifications, REST is the truth.
  useEffect(() => {
    if (!generating) return;
    const timer = setInterval(refreshAll, 5000);
    return () => clearInterval(timer);
  }, [generating, refreshAll]);

  useEffect(() => {
    const stop = connectRealtime(
      `/ws/classes/${classId}`,
      (event) => {
        if (event.type === "generation_progress") {
          setProgress(event.payload);
          refreshAll();
        } else if (event.type === "material_progress" || event.type === "level_created") {
          loadMaterials().catch(() => {});
          loadLevels().catch(() => {});
        }
      },
      refreshAll
    );
    return stop;
  }, [classId, loadMaterials, loadLevels, refreshAll]);

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
    setConfirming(false);
    setStarting(true);
    setProgress(null);
    try {
      await api.generateLevels(classId);
      await loadClass();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Gagal memulai generate level");
    } finally {
      setStarting(false);
    }
  }

  function handleGenerateClick() {
    if (levels.length > 0 && !confirming) {
      setConfirming(true);
      return;
    }
    handleGenerate().catch(() => {});
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
  const busy = generating || starting;
  const failedMessage =
    cls?.generation_status === "failed"
      ? (cls.generation_error ?? progress?.error_message ?? "Generate level gagal.")
      : null;
  const liveProgress = progress && progress.stage !== "done" && progress.stage !== "failed" ? progress : null;
  const percent =
    liveProgress && liveProgress.total > 0
      ? Math.min(100, Math.round((liveProgress.current / liveProgress.total) * 100))
      : 0;

  return (
    <PageShell
      back={{ href: "/teacher", label: "Class saya" }}
      crumbs={[{ label: "Class saya", href: "/teacher" }, { label: cls?.title ?? "..." }]}
      title={cls?.title ?? "Memuat..."}
      subtitle={
        cls && (
          <span className="flex flex-wrap items-center gap-2">
            <ClassBadges cls={cls} />
            {cls.invite_code && (
              <span className="text-sm">
                Kode undangan: <span className="font-mono font-semibold text-ink">{cls.invite_code}</span>
              </span>
            )}
          </span>
        )
      }
      actions={
        <>
          <Link href={`/teacher/classes/${classId}/preview`} className="btn-ghost">
            Pratinjau
          </Link>
          <Link href={`/teacher/classes/${classId}/live`} className="btn-ghost">
            Live class
          </Link>
          {!cls?.is_example && (
            <button onClick={handlePublish} className="btn-primary">
              Publish class
            </button>
          )}
        </>
      }
    >
      {cls?.is_example && (
        <p className="mb-4 rounded-xl border border-highlight/40 bg-highlight/10 p-3 text-sm">{cls.description}</p>
      )}
      {error && (
        <p role="alert" className="mb-4 rounded-lg border border-alert/30 bg-alert/10 p-3 text-sm text-alert">
          {error}
        </p>
      )}

      <div className="grid gap-6 lg:grid-cols-[minmax(0,2fr)_minmax(0,3fr)] lg:items-start">
        <div className="flex flex-col gap-6">
          <section className="surface">
            <h2 className="mb-3 font-display text-xl">Materi PDF</h2>
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
            <ul className="mt-4 flex flex-col gap-2 text-sm">
              {materials.map((m) => (
                <li key={m.id} className="flex flex-wrap items-center justify-between gap-2 rounded-lg bg-paper/70 px-3 py-2">
                  <span className="min-w-0 break-words">{m.file_name}</span>
                  <span className={VECTOR_STATUS_COLOR[m.vector_status]}>{m.vector_status}</span>
                  {m.error_message && <span className="w-full text-alert">{m.error_message}</span>}
                </li>
              ))}
              {materials.length === 0 && <li className="text-ink/60">Belum ada materi.</li>}
            </ul>
          </section>

          <section className="surface">
            <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
              <h2 className="font-display text-xl">Level & soal</h2>
              <button
                onClick={handleGenerateClick}
                disabled={busy || !readyMaterials}
                className="btn-primary px-3 py-1.5 text-sm"
              >
                {busy ? "Memproses..." : levels.length > 0 ? "Generate ulang" : "Generate level"}
              </button>
            </div>
            {!readyMaterials && !busy && (
              <p className="mb-3 text-sm text-ink/60">Unggah dan tunggu materi PDF siap sebelum membuat level.</p>
            )}
            {confirming && (
              <div className="mb-3 rounded-lg border border-highlight/40 bg-highlight/10 p-3 text-sm" role="alert">
                <p className="mb-2">Level draft akan diganti. Lanjutkan?</p>
                <div className="flex gap-2">
                  <button onClick={() => handleGenerate()} className="btn-primary px-3 py-1.5 text-sm">
                    Ya, generate ulang
                  </button>
                  <button onClick={() => setConfirming(false)} className="btn-ghost px-3 py-1.5 text-sm">
                    Batal
                  </button>
                </div>
              </div>
            )}
            {busy && (
              <div className="mb-3 rounded-lg border border-rule bg-paper/70 p-3 text-sm" role="status" aria-live="polite">
                <p className="mb-2 font-medium">
                  {liveProgress ? STAGE_LABEL[liveProgress.stage] : "Menyiapkan generate"}
                  {liveProgress && liveProgress.total > 0 && (
                    <span className="font-normal text-ink/60">
                      {" "}
                      — level {liveProgress.current} dari {liveProgress.total}
                    </span>
                  )}
                </p>
                <div className="h-2 w-full overflow-hidden rounded-full bg-rule">
                  <div
                    className="h-full rounded-full bg-highlight transition-[width] duration-300"
                    style={{ width: `${liveProgress ? Math.max(percent, 4) : 4}%` }}
                  />
                </div>
              </div>
            )}
            {!busy && failedMessage && (
              <div className="mb-3 rounded-lg border border-alert/40 bg-alert/10 p-3 text-sm" role="alert">
                <p className="mb-2 text-alert">{failedMessage}</p>
                <button
                  onClick={() => handleGenerate()}
                  disabled={!readyMaterials}
                  className="btn-ghost px-3 py-1.5 text-sm"
                >
                  Coba lagi
                </button>
              </div>
            )}
            {levels.length > 0 && (
              <ul className="flex flex-col gap-1 text-sm">
                {levels.map((l) => (
                  <li key={l.id}>
                    <Link
                      href={`/teacher/classes/${classId}/levels/${l.id}`}
                      className="flex min-h-[44px] items-center justify-between gap-2 rounded-lg px-3 py-2 hover:bg-paper"
                    >
                      <span>
                        {l.order_index + 1}. {l.title}
                      </span>
                      <span className="flex gap-1.5">
                        {l.type === "boss" && <span className="badge-alert">Boss</span>}
                        <span className={l.status === "approved" ? "badge-success" : "badge"}>
                          {l.status === "approved" ? "Approved" : "Draft"}
                        </span>
                      </span>
                    </Link>
                  </li>
                ))}
              </ul>
            )}
          </section>
        </div>

        <section className="surface lg:sticky lg:top-20">
          <h2 className="mb-3 font-display text-xl">Peta level</h2>
          {!loaded ? (
            <p className="text-sm text-ink/50">Memuat level...</p>
          ) : levels.length === 0 ? (
            <p className="rounded-lg border border-dashed border-rule p-10 text-center text-sm text-ink/60">
              {busy ? "Level akan muncul satu per satu di sini." : "Belum ada level."}
            </p>
          ) : (
            <>
              <LevelMap classId={classId} levels={levels} teacher height="clamp(420px, 62vh, 640px)" />
              <p className="mt-2 text-xs text-ink/65">
                Abu-abu: draft · Hijau: disetujui · Garis merah: level boss. Ketuk level untuk meninjau.
              </p>
            </>
          )}
        </section>
      </div>
    </PageShell>
  );
}
