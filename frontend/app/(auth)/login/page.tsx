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
      <h1 className="mb-1 text-4xl">Halo! Ayo masuk</h1>
      <p className="mb-6 text-ink/75">Lanjutkan belajar atau urus kelasmu.</p>

      {mismatch ? (
        <div className="flex flex-col gap-4 rounded-2xl border-2 border-highlight bg-highlight/20 p-4">
          <p className="text-base text-ink">
            Akun ini akun <strong>{ROLE_LABEL[mismatch.role]}</strong>, bukan akun {ROLE_LABEL[expectedRole]}.
          </p>
          <div className="flex flex-col gap-3 sm:flex-row">
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
            <span className="field-label">Kamu siapa?</span>
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
          {error && (
            <p role="alert" className="note border-coral bg-coral-soft text-alert">
              {error}
            </p>
          )}
          <button type="submit" disabled={loading} className="btn-primary mt-2 w-full">
            {loading ? "Tunggu sebentar..." : `Masuk sebagai ${ROLE_LABEL[expectedRole]}`}
          </button>
        </form>
      )}

      <p className="mt-6 flex min-h-[48px] items-center gap-2 text-base text-ink/75">
        Belum punya akun?
        <Link href="/register" className="link-text">
          Daftar di sini
        </Link>
      </p>
    </>
  );
}
