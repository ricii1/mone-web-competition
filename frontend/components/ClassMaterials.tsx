"use client";

import { useState } from "react";
import MaterialPdf from "@/components/MaterialPdf";
import { ApiError, api } from "@/lib/api";
import type { Material } from "@/lib/types";

export default function ClassMaterials({ classId }: { classId: string }) {
  const [materials, setMaterials] = useState<Material[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      setMaterials(await api.listMaterials(classId));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Materi belum bisa dimuat. Coba lagi ya.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <details className="surface mt-5" onToggle={(event) => {
      if (event.currentTarget.open && materials === null && !loading) void load();
    }}>
      <summary className="min-h-[48px] cursor-pointer font-display text-xl font-bold">Materi PDF dari guru</summary>
      {loading && <p role="status">Sebentar ya, materi sedang dimuat...</p>}
      {error && <div role="alert"><p className="text-alert">{error}</p><button onClick={load} className="btn-ghost mt-2">Coba lagi</button></div>}
      {materials?.length === 0 && <p className="text-ink/75">Guru belum mengunggah PDF.</p>}
      <ul className="mt-3 flex flex-col gap-3">
        {materials?.map((material) => (
          <li key={material.id} className="rounded-2xl bg-paper p-3">
            <p className="mb-2 break-words font-bold">{material.file_name}</p>
            <MaterialPdf classId={classId} material={material} />
          </li>
        ))}
      </ul>
    </details>
  );
}
