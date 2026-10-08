"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { clearToken } from "@/lib/auth";
import type { User } from "@/lib/types";

export default function AppHeader({ homeHref }: { homeHref: string }) {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const roleLabel = homeHref.startsWith("/teacher") ? "Guru" : "Murid";

  useEffect(() => {
    api.me().then(setUser).catch(() => {});
  }, []);

  function handleLogout() {
    clearToken();
    router.push("/login");
  }

  return (
    <header className="sticky top-0 z-30 border-b border-rule bg-paper/90 backdrop-blur">
      <div className="mx-auto flex h-14 max-w-6xl items-center justify-between gap-3 px-4 sm:px-6 lg:px-8">
        <div className="flex min-w-0 items-center gap-3">
          <Link href={homeHref} className="flex items-center gap-2 font-display text-xl">
            <span className="inline-block h-2.5 w-2.5 rounded-full bg-highlight" aria-hidden="true" />
            EduMap
          </Link>
          <span className="badge-highlight">{roleLabel}</span>
        </div>
        <div className="flex min-w-0 items-center gap-3 text-sm">
          {user && <span className="hidden max-w-[12rem] truncate text-ink/75 sm:block">{user.name}</span>}
          <button
            onClick={handleLogout}
            className="inline-flex min-h-[40px] items-center rounded-lg border border-rule px-3 font-medium text-ink transition-colors hover:border-ink/40"
          >
            Keluar
          </button>
        </div>
      </div>
    </header>
  );
}
