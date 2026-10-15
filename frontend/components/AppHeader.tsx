"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import Avatar from "@/components/Avatar";
import HelpButton from "@/components/HelpButton";
import { LogoutIcon, StarIcon } from "@/components/icons";
import { api } from "@/lib/api";
import { clearToken } from "@/lib/auth";
import type { User } from "@/lib/types";

export default function AppHeader({ homeHref }: { homeHref: string }) {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const isTeacher = homeHref.startsWith("/teacher");
  const roleLabel = isTeacher ? "Guru" : "Murid";
  const otherLabel = isTeacher ? "Murid" : "Guru";
  const otherHref = isTeacher ? "/student" : "/teacher";

  useEffect(() => {
    api
      .me()
      .then(setUser)
      .catch(() => {});
  }, []);

  function handleLogout() {
    clearToken();
    router.push("/login");
  }

  return (
    <header className="sticky top-0 z-30 border-b-2 border-rule bg-paper/95 backdrop-blur">
      <div className="mx-auto flex min-h-[64px] max-w-6xl items-center justify-between gap-1 px-2 sm:gap-3 sm:px-6 lg:px-8">
        <div className="flex shrink-0 items-center gap-1 sm:gap-3">
          <Link
            href={homeHref}
            aria-label="Peta Pintar, halaman awal"
            className="flex min-h-[48px] min-w-[48px] items-center justify-center gap-2 font-display text-2xl font-extrabold"
          >
            <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-highlight text-ink shadow-[0_3px_0_0_#c98f00]">
              <StarIcon size={22} />
            </span>
            <span className="hidden sm:inline">Peta Pintar</span>
          </Link>
          <span className="badge-sky">{roleLabel}</span>
        </div>
        <div className="flex shrink-0 items-center gap-1 sm:gap-3">
          {user && (
            <span className="hidden min-w-0 items-center gap-2 font-bold lg:flex">
              <Avatar name={user.name} size={36} />
              <span className="hidden max-w-[12rem] truncate lg:block">
                {user.name}
              </span>
            </span>
          )}
          <Link
            href={otherHref}
            className="btn-ghost min-w-[48px] !px-3 sm:!px-5"
            aria-label={`Ganti ke mode ${otherLabel}`}
          >
            <span className="lg:hidden">{otherLabel}</span>
            <span className="hidden lg:inline">Ganti ke {otherLabel}</span>
          </Link>
          <HelpButton initialMode={isTeacher ? "teacher" : "student"} />
          <button
            onClick={handleLogout}
            className="btn-ghost min-w-[48px] !px-3 sm:!px-5"
            aria-label="Keluar"
          >
            <LogoutIcon size={20} />
            <span className="hidden lg:inline">Keluar</span>
          </button>
        </div>
      </div>
    </header>
  );
}
