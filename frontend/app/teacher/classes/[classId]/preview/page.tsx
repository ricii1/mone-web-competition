"use client";

import dynamic from "next/dynamic";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import PageShell from "@/components/PageShell";
import { ApiError, api } from "@/lib/api";
import type { Level } from "@/lib/types";

const LevelMap = dynamic(() => import("@/components/LevelMap"), { ssr: false });

export default function TeacherClassPreviewPage() {
  const { classId } = useParams<{ classId: string }>();
  const [levels, setLevels] = useState<Level[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .listLevels(classId)
      .then(setLevels)
      .catch((err) => setError(err instanceof ApiError ? err.message : "Gagal memuat level"))
      .finally(() => setLoading(false));
  }, [classId]);

  const editorHref = `/teacher/classes/${classId}`;

  return (
    <PageShell
      back={{ href: editorHref, label: "Kembali ke class" }}
      crumbs={[{ label: "Class saya", href: "/teacher" }, { label: "Class", href: editorHref }, { label: "Pratinjau" }]}
      title="Pratinjau sebagai murid"
      subtitle="Peta level seperti yang dilihat murid. Semua level terbuka dan tidak ada progres yang disimpan."
    >
      {loading && <p className="text-sm text-ink/60">Memuat peta...</p>}
      {error && <p className="mb-4 text-sm text-alert">{error}</p>}
      {!loading && !error && levels.length === 0 && (
        <p className="surface text-sm text-ink/65">Belum ada level untuk dipratinjau. Generate level terlebih dahulu.</p>
      )}
      {levels.length > 0 && (
        <LevelMap classId={classId} levels={levels} preview height="clamp(420px, 70vh, 760px)" />
      )}
    </PageShell>
  );
}
