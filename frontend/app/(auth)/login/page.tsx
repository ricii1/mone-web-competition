"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { ApiError, api } from "@/lib/api";
import { saveToken } from "@/lib/auth";
import type { UserRole } from "@/lib/types";
import PasswordField from "@/components/PasswordField";
import RoleChooser from "@/components/RoleChooser";

const ROLE_LABEL: Record<UserRole, string> = {
  teacher: "Guru",
  student: "Murid",
};

export default function LoginPage() {
  const router = useRouter();
  const [expectedRole, setExpectedRole] = useState<UserRole>("student");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const { access_token } = await api.login(email, password);
      saveToken(access_token);
      // One account can teach and learn; the chosen tab only picks the start page.
      router.push(expectedRole === "teacher" ? "/teacher" : "/student");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Gagal masuk");
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <h1 className="mb-1 text-4xl">Halo! Ayo masuk</h1>
      <p className="mb-6 text-ink/75">Lanjutkan belajar atau urus kelasmu.</p>

      <form onSubmit={handleSubmit} className="flex flex-col gap-5">
        <div className="field">
          <span className="field-label">Mau masuk sebagai apa?</span>
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
          <p
            role="alert"
            className="note border-coral bg-coral-soft text-alert"
          >
            {error}
          </p>
        )}
        <button
          type="submit"
          disabled={loading}
          className="btn-primary mt-2 w-full"
        >
          {loading
            ? "Tunggu sebentar..."
            : `Masuk sebagai ${ROLE_LABEL[expectedRole]}`}
        </button>
      </form>

      <p className="mt-6 flex min-h-[48px] items-center gap-2 text-base text-ink/75">
        Belum punya akun?
        <Link href="/register" className="link-text">
          Daftar di sini
        </Link>
      </p>
    </>
  );
}
