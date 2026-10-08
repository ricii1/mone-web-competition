"use client";

import dynamic from "next/dynamic";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { MapIcon } from "@/components/icons";
import PageShell from "@/components/PageShell";
import { ApiError, api } from "@/lib/api";
import { useClassTitle } from "@/lib/useClassTitle";
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
      .catch((err) => setError(err instanceof ApiError ? err.message : "Level belum bisa dimuat. Coba lagi ya."))
      .finally(() => setLoading(false));
  }, [classId]);

  const classTitle = useClassTitle(classId);
  const editorHref = `/teacher/classes/${classId}`;

  return (
    <PageShell
      back={{ href: editorHref, label: classTitle ? `Kembali ke ${classTitle}` : "Kembali ke class" }}
      icon={<MapIcon size={28} />}
      title="Lihat seperti murid"
      subtitle="Ini peta yang dilihat murid. Semua level terbuka dan skor tidak disimpan."
    >
      {loading && <p role="status" className="text-ink/75">Memuat peta...</p>}
      {error && <p role="alert" className="note mb-4 border-coral bg-coral-soft text-alert">{error}</p>}
      {!loading && !error && levels.length === 0 && (
        <p className="surface text-ink/75">Belum ada level. Buat level dulu di halaman kelas.</p>
      )}
      {levels.length > 0 && (
        <LevelMap classId={classId} levels={levels} preview height="clamp(420px, 70vh, 760px)" />
      )}
    </PageShell>
  );
}
