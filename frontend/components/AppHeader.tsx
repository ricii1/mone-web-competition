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

  useEffect(() => {
    api.me().then(setUser).catch(() => {});
  }, []);

  function handleLogout() {
    clearToken();
    router.push("/login");
  }

  return (
    <header className="flex items-center justify-between border-b border-rule px-4 py-4 sm:px-6">
      <Link href={homeHref} className="font-display text-xl">
        EduMap
      </Link>
      <div className="flex items-center gap-4 text-sm text-ink/70">
        {user && <span>{user.name}</span>}
        <button onClick={handleLogout} className="link-text">
          Keluar
        </button>
      </div>
    </header>
  );
}
