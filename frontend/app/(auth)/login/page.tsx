"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { ApiError, api } from "@/lib/api";
import { clearToken, saveToken } from "@/lib/auth";
import type { User, UserRole } from "@/lib/types";
import PasswordField from "@/components/PasswordField";
import RoleChooser from "@/components/RoleChooser";

const ROLE_LABEL: Record<UserRole, string> = { teacher: "Guru", student: "Murid" };

export default function LoginPage() {
  const router = useRouter();
  const [expectedRole, setExpectedRole] = useState<UserRole>("student");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [mismatch, setMismatch] = useState<User | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setMismatch(null);
    setLoading(true);
    try {
      const { access_token } = await api.login(email, password);
      saveToken(access_token);
      const me = await api.me();
      if (me.role === expectedRole) {
        router.push(me.role === "teacher" ? "/teacher" : "/student");
      } else {
        // Akun valid, tapi bukan tab yang dipilih — jangan diam-diam
        // alihkan ke dashboard yang tidak diminta, minta konfirmasi dulu.
        setMismatch(me);
      }
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Gagal masuk");
    } finally {
      setLoading(false);
    }
  }

  function continueAsActualRole() {
    if (!mismatch) return;
    router.push(mismatch.role === "teacher" ? "/teacher" : "/student");
  }

  function pickDifferentAccount() {
    clearToken();
    setMismatch(null);
  }

  return (
    <>
      <h1 className="mb-1 font-display text-3xl">Masuk</h1>
      <p className="mb-8 text-ink/60">Lanjutkan belajar atau mengelola kelasmu.</p>

      {mismatch ? (
        <div className="flex flex-col gap-4 rounded-sm border border-highlight/40 bg-highlight/10 p-4">
          <p className="text-sm text-ink">
            Akun ini terdaftar sebagai <strong>{ROLE_LABEL[mismatch.role]}</strong>, bukan{" "}
            {ROLE_LABEL[expectedRole]}.
          </p>
          <div className="flex gap-3">
            <button onClick={continueAsActualRole} className="btn-primary">
              Lanjut sebagai {ROLE_LABEL[mismatch.role]}
            </button>
            <button onClick={pickDifferentAccount} className="btn-ghost">
              Pakai akun lain
            </button>
          </div>
        </div>
      ) : (
        <form onSubmit={handleSubmit} className="flex flex-col gap-5">
          <div className="field">
            <span className="field-label">Masuk sebagai</span>
            <RoleChooser value={expectedRole} onChange={setExpectedRole} />
          </div>
          <div className="field">
            <label htmlFor="email" className="field-label">
              Email
            </label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              className="input-rule"
            />
          </div>
          <PasswordField
            id="password"
            label="Kata sandi"
            value={password}
            onChange={setPassword}
            required
            autoComplete="current-password"
          />
          {error && <p className="text-sm text-alert">{error}</p>}
          <button type="submit" disabled={loading} className="btn-primary mt-2">
            {loading ? "Memproses..." : `Masuk sebagai ${ROLE_LABEL[expectedRole]}`}
          </button>
        </form>
      )}

      <p className="mt-8 text-sm text-ink/70">
        Belum punya akun?{" "}
        <Link href="/register" className="link-text">
          Daftar
        </Link>
      </p>
    </>
  );
}
