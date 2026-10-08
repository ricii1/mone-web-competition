"use client";

import { usePathname } from "next/navigation";
import AuthHero from "@/components/AuthHero";

const TAGLINES: Record<string, string> = {
  "/login": "Belajar lewat peta level yang dibuat dari materi gurumu sendiri.",
  "/register": "Satu peta level untuk setiap kelas, dibuat dari materi yang gurumu unggah.",
};

export default function AuthLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const tagline = TAGLINES[pathname] ?? TAGLINES["/login"];

  return (
    <main className="grid min-h-screen md:grid-cols-2">
      <div className="flex flex-col justify-center px-6 py-12 sm:px-12 md:px-16">
        <div className="mx-auto w-full max-w-sm">{children}</div>
      </div>
      <div className="hidden md:block">
        <AuthHero tagline={tagline} />
      </div>
    </main>
  );
}
