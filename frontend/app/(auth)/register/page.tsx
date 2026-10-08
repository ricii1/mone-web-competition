"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { ApiError, api } from "@/lib/api";
import { saveToken } from "@/lib/auth";
import type { UserRole } from "@/lib/types";
import PasswordField from "@/components/PasswordField";
import RoleChooser from "@/components/RoleChooser";

export default function RegisterPage() {
  const router = useRouter();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState<UserRole>("student");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const { access_token } = await api.register(name, email, password, role);
      saveToken(access_token);
      router.push(role === "teacher" ? "/teacher" : "/student");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Gagal mendaftar");
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <h1 className="mb-1 font-display text-3xl">Daftar</h1>
      <p className="mb-8 text-ink/60">Buat akun untuk mulai memakai EduMap.</p>

      <form onSubmit={handleSubmit} className="flex flex-col gap-5">
        <fieldset className="field">
          <legend className="field-label mb-1">Daftar sebagai</legend>
          <RoleChooser value={role} onChange={setRole} />
        </fieldset>

        <div className="field">
          <label htmlFor="name" className="field-label">
            Nama
          </label>
          <input
            id="name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
            className="input-rule"
          />
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
          minLength={8}
          autoComplete="new-password"
        />
        {error && <p className="text-sm text-alert">{error}</p>}
        <button type="submit" disabled={loading} className="btn-primary mt-2">
          {loading ? "Memproses..." : "Daftar"}
        </button>
      </form>

      <p className="mt-8 text-sm text-ink/70">
        Sudah punya akun?{" "}
        <Link href="/login" className="link-text">
          Masuk
        </Link>
      </p>
    </>
  );
}
