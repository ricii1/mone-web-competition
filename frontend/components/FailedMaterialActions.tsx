"use client";

import { useState } from "react";
import { ApiError, api } from "@/lib/api";
import type { Material } from "@/lib/types";

export default function FailedMaterialActions({ classId, material, disabled, onChanged }: { classId: string; material: Material; disabled: boolean; onChanged: () => void }) {
  const [confirming, setConfirming] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  async function act(remove: boolean) {
    setBusy(true);
    setError(null);
    try {
      if (remove) await api.deleteMaterial(classId, material.id);
      else await api.retryMaterial(classId, material.id);
      setConfirming(false);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Tindakan belum berhasil. Coba lagi ya.");
    } finally {
      setBusy(false);
      onChanged();
    }
  }
  return <div className="w-full">
    <div className="flex flex-wrap gap-2">
      <button type="button" className="btn-ghost min-h-[48px]" disabled={disabled || busy} onClick={() => act(false)}>{busy ? "Memproses..." : "Coba proses lagi"}</button>
      <button type="button" className="btn-ghost min-h-[48px] text-alert" disabled={disabled || busy} onClick={() => setConfirming(true)}>Hapus PDF gagal</button>
    </div>
    {confirming && <div className="mt-2 rounded-xl border border-coral bg-coral-soft p-3">
      <p className="break-words">Hapus PDF gagal “{material.file_name}”? File ini akan dihapus permanen.</p>
      <div className="mt-2 flex flex-wrap gap-2">
        <button type="button" className="btn-ghost min-h-[48px] text-alert" disabled={disabled || busy} onClick={() => act(true)}>Ya, hapus PDF</button>
        <button type="button" className="btn-ghost min-h-[48px]" disabled={busy} onClick={() => setConfirming(false)}>Batal</button>
      </div>
    </div>}
    {error && <p role="alert" className="mt-2 text-alert">{error}</p>}
  </div>;
}
