"use client";

import { usePathname } from "next/navigation";
import AuthHero from "@/components/AuthHero";
import CloudSky from "@/components/CloudSky";
import Mascot from "@/components/Mascot";

const TAGLINES: Record<string, string> = {
  "/login": "Ayo belajar sambil bermain. Selesaikan level, kumpulkan bintang!",
  "/register": "Buat akunmu dan mulai petualangan belajar bersama EduMap.",
};

export default function AuthLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const tagline = TAGLINES[pathname] ?? TAGLINES["/login"];

  return (
    <main className="kid auth-bg grid min-h-screen md:grid-cols-2">
      <div className="relative flex flex-col justify-center overflow-hidden px-5 py-8 sm:px-12 md:px-16 md:py-12">
        <CloudSky />
        <div className="relative mx-auto w-full max-w-md">
          <div className="mb-6 flex items-center gap-3 md:hidden">
            <Mascot mood="happy" size={72} className="shrink-0" />
            <div>
              <p className="font-display text-2xl font-extrabold">EduMap</p>
              <p className="text-base leading-snug text-ink/75">{tagline}</p>
            </div>
          </div>
          {children}
        </div>
      </div>
      <div className="hidden md:block">
        <AuthHero tagline={tagline} />
      </div>
    </main>
  );
}
