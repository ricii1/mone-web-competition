"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import Avatar from "@/components/Avatar";
import { LogoutIcon, StarIcon } from "@/components/icons";
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
    <header className="sticky top-0 z-30 border-b-2 border-rule bg-paper/95 backdrop-blur">
      <div className="mx-auto flex min-h-[64px] max-w-6xl items-center justify-between gap-3 px-4 sm:px-6 lg:px-8">
        <div className="flex min-w-0 items-center gap-3">
          <Link href={homeHref} className="flex min-h-[48px] items-center gap-2 font-display text-2xl font-extrabold">
            <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-highlight text-ink shadow-[0_3px_0_0_#c98f00]">
              <StarIcon size={22} />
            </span>
            <span className="hidden min-[400px]:inline">EduMap</span>
          </Link>
          <span className="badge-sky">{roleLabel}</span>
        </div>
        <div className="flex min-w-0 items-center gap-3">
          {user && (
            <span className="flex min-w-0 items-center gap-2 font-bold">
              <Avatar name={user.name} size={36} />
              <span className="hidden max-w-[12rem] truncate sm:block">{user.name}</span>
            </span>
          )}
          <button onClick={handleLogout} className="btn-ghost" aria-label="Keluar">
            <LogoutIcon size={20} />
            <span className="hidden sm:inline">Keluar</span>
          </button>
        </div>
      </div>
    </header>
  );
}
