import Link from "next/link";
import AuthHero from "@/components/AuthHero";

export default function HomePage() {
  return (
    <main className="grid min-h-screen md:grid-cols-2">
      <div className="flex flex-col justify-center px-6 py-12 sm:px-12 md:px-16">
        <div className="mx-auto w-full max-w-sm">
          <h1 className="mb-1 font-display text-3xl">EduMap</h1>
          <p className="mb-8 text-ink/60">Belajar lewat peta level yang dibuat dari materi gurumu.</p>
          <div className="flex gap-3">
            <Link href="/login" className="btn-primary">
              Masuk
            </Link>
            <Link href="/register" className="btn-ghost">
              Daftar
            </Link>
          </div>
        </div>
      </div>

      <div className="hidden md:block">
        <AuthHero tagline="Satu peta, banyak level, dibuat dari materi yang gurumu unggah sendiri." />
      </div>
    </main>
  );
}
