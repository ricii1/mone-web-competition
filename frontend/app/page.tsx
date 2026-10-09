import Link from "next/link";
import AuthHero from "@/components/AuthHero";
import CloudSky from "@/components/CloudSky";
import { PlayIcon, UsersIcon } from "@/components/icons";
import Mascot from "@/components/Mascot";

export default function HomePage() {
  return (
    <main className="kid auth-bg grid min-h-screen md:grid-cols-2">
      <div className="relative flex flex-col justify-center overflow-hidden px-5 py-10 sm:px-12 md:px-16">
        <CloudSky />
        <div className="relative mx-auto w-full max-w-md">
          <Mascot mood="happy" size={110} className="bob mb-2 md:hidden" />
          <h1 className="mb-2 text-5xl font-extrabold">EduMap</h1>
          <p className="mb-8 text-xl text-ink/80">Belajar jadi seru! Ikuti peta level dari gurumu dan kumpulkan bintang.</p>
          <div className="flex flex-col gap-4 sm:flex-row">
            <Link href="/login" className="btn-primary">
              <PlayIcon size={22} />
              Ayo masuk
            </Link>
            <Link href="/register" className="btn-ghost">
              <UsersIcon size={22} />
              Daftar baru
            </Link>
          </div>
        </div>
      </div>

      <div className="hidden md:block">
        <AuthHero tagline="Satu peta, banyak level. Siapa yang paling banyak bintang?" />
      </div>
    </main>
  );
}
