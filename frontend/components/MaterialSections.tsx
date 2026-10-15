"use client";

import { useEffect, useState } from "react";
import { ApiError, api } from "@/lib/api";
import type { MaterialSection, MaterialSectionsResponse } from "@/lib/types";

function SourceSection({ classId, materialId, section }: { classId: string; materialId: string; section: MaterialSection }) {
  const [open, setOpen] = useState(false);
  const [content, setContent] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [retry, setRetry] = useState(0);
  useEffect(() => {
    if (!open || content !== null) return;
    const controller = new AbortController();
    setError(null);
    api.getMaterialSection(classId, materialId, section.id, controller.signal)
      .then((result) => { if (!controller.signal.aborted) setContent(result.content); })
      .catch((err: unknown) => {
        if (!controller.signal.aborted) setError(err instanceof ApiError ? err.message : "Bagian ini belum bisa dimuat. Coba lagi ya.");
      });
    return () => controller.abort();
  }, [classId, materialId, section.id, open, content, retry]);
  const page = section.page_start === section.page_end
    ? `Halaman ${section.page_start + 1}`
    : `Halaman ${section.page_start + 1}–${section.page_end + 1}`;
  return (
    <li className="rounded-xl border border-rule bg-white p-3">
      <p className="break-words font-semibold">{section.order_index + 1}. {section.section_title || "Bagian materi"}</p>
      <p className="text-sm text-ink/75">{page} · {section.character_count.toLocaleString("id-ID")} huruf</p>
      <p className="mt-2 whitespace-pre-wrap break-words text-sm">{section.excerpt}{section.character_count > section.excerpt.length ? "…" : ""}</p>
      <button type="button" className="btn-ghost mt-2 min-h-[48px]" aria-expanded={open} onClick={() => setOpen(!open)}>
        {open ? "Tutup teks lengkap" : "Baca teks lengkap"}
      </button>
      {open && (
        <div className="mt-2 max-h-80 overflow-y-auto whitespace-pre-wrap break-words rounded-xl bg-paper p-3">
          {error ? <div role="alert"><p>{error}</p><button type="button" className="btn-ghost min-h-[48px]" onClick={() => setRetry(retry + 1)}>Coba lagi</button></div>
            : content === null ? <p role="status">Memuat teks...</p> : content}
        </div>
      )}
    </li>
  );
}

export default function MaterialSections({ classId, materialId }: { classId: string; materialId: string }) {
  const [open, setOpen] = useState(false);
  const [offset, setOffset] = useState(0);
  const [data, setData] = useState<MaterialSectionsResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [retry, setRetry] = useState(0);
  useEffect(() => {
    if (!open) return;
    const controller = new AbortController();
    setData(null);
    setError(null);
    api.listMaterialSections(classId, materialId, offset, controller.signal)
      .then((result) => { if (!controller.signal.aborted) setData(result); })
      .catch((err: unknown) => {
        if (!controller.signal.aborted) setError(err instanceof ApiError ? err.message : "Pembagian materi belum bisa dimuat.");
      });
    return () => controller.abort();
  }, [classId, materialId, open, offset, retry]);
  return (
    <div className="w-full min-w-0">
      <button type="button" className="btn-ghost min-h-[48px]" aria-expanded={open} onClick={() => setOpen(!open)}>
        {open ? "Tutup pembagian materi" : "Lihat pembagian materi"}
      </button>
      {open && <div className="mt-3">
        <p className="mb-3 text-sm text-ink/75">Periksa urutan, judul, dan halaman sebelum membuat level. Satu subbab yang panjang bisa terbagi menjadi beberapa bagian.</p>
        {error ? <div role="alert"><p className="text-alert">{error}</p><button type="button" className="btn-ghost min-h-[48px]" onClick={() => setRetry(retry + 1)}>Coba lagi</button></div>
          : !data ? <p role="status">Memuat pembagian materi...</p>
          : data.total === 0 ? <p>Belum ada bagian materi yang ditemukan.</p>
          : <>
            <p className="mb-2 text-sm">{data.offset + 1}–{data.offset + data.sections.length} dari {data.total} bagian</p>
            <ol className="flex flex-col gap-2">{data.sections.map((section) => <SourceSection key={section.id} classId={classId} materialId={materialId} section={section} />)}</ol>
            <div className="mt-3 flex flex-wrap gap-2">
              <button type="button" className="btn-ghost min-h-[48px]" disabled={offset === 0} onClick={() => setOffset(Math.max(0, offset - data.limit))}>Sebelumnya</button>
              <button type="button" className="btn-ghost min-h-[48px]" disabled={offset + data.limit >= data.total} onClick={() => setOffset(offset + data.limit)}>Berikutnya</button>
            </div>
          </>}
      </div>}
    </div>
  );
}
