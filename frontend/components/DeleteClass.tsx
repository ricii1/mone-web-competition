"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { ApiError, api } from "@/lib/api";

export default function DeleteClass({ classId, title, disabled }: { classId: string; title: string; disabled: boolean }) {
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [name, setName] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  async function remove() {
    setBusy(true);
    setError(null);
    try {
      await api.deleteClass(classId, name);
      router.replace("/teacher");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Kelas belum bisa dihapus. Coba lagi ya.");
      setBusy(false);
    }
  }
  return <section className="surface mt-6 border-coral">
    <h2 className="text-xl">Hapus kelas</h2>
    <p className="mt-2 text-ink/75">Penghapusan menghapus semua PDF, level, soal, progres murid, dan hasil kuis di kelas ini.</p>
    {!open ? <button type="button" className="btn-ghost mt-3 min-h-[48px] text-alert" disabled={disabled} onClick={() => setOpen(true)}>Hapus kelas</button>
      : <form className="mt-3" onSubmit={(event) => { event.preventDefault(); if (!disabled && !busy && name === title) void remove(); }}>
        <p className="mb-2 font-semibold text-alert">Kelas tidak bisa dikembalikan setelah dihapus.</p>
        <label className="block">Ketik nama kelas: <strong className="break-words">{title}</strong>
          <input className="input-box mt-2 w-full" value={name} onChange={(event) => setName(event.target.value)} disabled={busy} autoComplete="off" />
        </label>
        <div className="mt-3 flex flex-wrap gap-2">
          <button type="submit" className="btn-ghost min-h-[48px] text-alert" disabled={disabled || busy || name !== title}>{busy ? "Menghapus..." : "Hapus kelas permanen"}</button>
          <button type="button" className="btn-ghost min-h-[48px]" disabled={busy} onClick={() => { setOpen(false); setName(""); setError(null); }}>Batal</button>
        </div>
        {error && <p role="alert" className="mt-2 text-alert">{error}</p>}
      </form>}
    {disabled && <p className="mt-2 text-sm text-ink/75">Tunggu proses materi atau level selesai sebelum menghapus.</p>}
  </section>;
}
