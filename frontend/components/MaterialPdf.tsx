"use client";

import { useEffect, useState } from "react";
import { ApiError, api } from "@/lib/api";
import type { Material } from "@/lib/types";

export default function MaterialPdf({ classId, material }: { classId: string; material: Material }) {
  const [open, setOpen] = useState(false);
  const [url, setUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!open) return;
    const controller = new AbortController();
    let objectUrl: string | null = null;
    setError(null);
    setUrl(null);
    api.getMaterialPdf(classId, material.id, controller.signal).then((blob) => {
      if (controller.signal.aborted) return;
      objectUrl = URL.createObjectURL(blob);
      setUrl(objectUrl);
    }).catch((err) => {
      if (!controller.signal.aborted) {
        setError(err instanceof ApiError ? err.message : "PDF belum bisa dibuka. Coba lagi ya.");
      }
    });
    return () => {
      controller.abort();
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [open, classId, material.id]);

  function toggle() {
    setUrl(null);
    setError(null);
    setOpen((value) => !value);
  }

  return (
    <div className="w-full">
      <button type="button" onClick={toggle} aria-expanded={open} className="btn-ghost min-h-[48px]">
        {open ? "Tutup PDF" : "Lihat PDF"}
      </button>
      {open && (
        <div className="mt-3">
          {error ? <p role="alert" className="text-alert">{error}</p> : !url ? (
            <p role="status" className="text-ink/75">PDF sedang dibuka...</p>
          ) : (
            <>
              <p className="mb-2 text-ink/75">
                Jika PDF tidak terlihat, unduh lalu buka di perangkatmu.
              </p>
              <a href={url} download={material.file_name} className="btn-ghost mb-3 min-h-[48px]">Unduh PDF</a>
              <iframe src={url} title={`Materi PDF: ${material.file_name}`} className="h-[65vh] min-h-[320px] w-full rounded-2xl border-2 border-rule bg-white" />
            </>
          )}
        </div>
      )}
    </div>
  );
}
