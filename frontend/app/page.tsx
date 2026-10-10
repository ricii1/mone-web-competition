import type { Metadata } from "next";
import Link from "next/link";
import AuthHero from "@/components/AuthHero";
import CloudSky from "@/components/CloudSky";
import {
  ArrowRightIcon,
  BookIcon,
  LightbulbIcon,
  MapIcon,
  PlayIcon,
  RefreshIcon,
  RocketIcon,
  StarIcon,
  TrophyIcon,
  UploadIcon,
  UsersIcon,
} from "@/components/icons";
import DemoTabs from "@/components/landing/DemoTabs";
import Mascot from "@/components/Mascot";

export const metadata: Metadata = {
  title: "EduMap - Belajar jadi petualangan seru",
  description: "Guru SD unggah materi PDF, EduMap menyusun peta level. Murid bermain, kumpulkan bintang, dan naik level.",
};

const FEATURES = [
  {
    Icon: UploadIcon,
    tone: "bg-sky-soft text-sky-dark",
    title: "Unggah PDF, jadi peta level",
    text: "Guru cukup mengunggah materi. AI menyusun peta level sebagai draf. Guru yang memeriksa dan menyetujui.",
  },
  {
    Icon: BookIcon,
    tone: "bg-grass-soft text-grass-dark",
    title: "Bacaan pendek dan kuis",
    text: "Tiap level punya bacaan 2-3 menit, rangkuman, poin penting, lalu kuis pilihan ganda.",
  },
  {
    Icon: StarIcon,
    tone: "bg-highlight/40 text-ink",
    title: "Bintang dan papan juara",
    text: "Murid mengumpulkan bintang dan melihat siapa yang paling rajin di kelas.",
  },
  {
    Icon: UsersIcon,
    tone: "bg-coral-soft text-coral-dark",
    title: "Kelas langsung ala Kahoot",
    text: "Guru memulai kuis serentak. Semua murid menjawab bersama dan skor naik seketika.",
  },
  {
    Icon: RefreshIcon,
    tone: "bg-grape-soft text-grape-dark",
    title: "Satu akun, dua peran",
    text: "Email yang sama bisa jadi guru untuk kelasnya dan murid di kelas orang lain.",
  },
  {
    Icon: LightbulbIcon,
    tone: "bg-sky-soft text-sky-dark",
    title: "Hanya dari materi guru",
    text: "AI hanya memakai materi yang diunggah guru. Kalau jawabannya tidak ada, AI bilang tidak tahu.",
  },
] as const;

const STEPS = [
  { Icon: UploadIcon, title: "Guru unggah", text: "Guru mengunggah materi PDF dan membuat kelas." },
  { Icon: MapIcon, title: "AI menyusun peta", text: "AI membuat level dan soal. Guru memeriksa lalu menerbitkan." },
  { Icon: PlayIcon, title: "Murid bermain", text: "Murid membaca, menjawab kuis, dan membuka level berikutnya." },
] as const;

function Logo() {
  return (
    <span className="flex items-center gap-2 font-display text-2xl font-extrabold">
      <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-highlight text-ink">
        <StarIcon size={22} />
      </span>
      EduMap
    </span>
  );
}

export default function HomePage() {
  return (
    <div className="kid">
      <CloudSky variant="page" />

      <header className="sticky top-0 z-30 border-b-2 border-rule bg-paper/95 backdrop-blur">
        <nav aria-label="Menu utama" className="mx-auto flex max-w-6xl items-center justify-between gap-2 px-4 py-2 sm:px-6">
          <Link href="/" aria-label="EduMap, halaman awal" className="inline-flex min-h-[48px] items-center">
            <Logo />
          </Link>
          <div className="flex items-center gap-2">
            <Link href="/login" className="btn-ghost btn-sm">
              Masuk
            </Link>
            <Link href="/register" className="btn-primary btn-sm">
              Daftar
            </Link>
          </div>
        </nav>
      </header>

      <main>
        <section aria-labelledby="hero-title" className="mx-auto grid max-w-6xl items-center gap-8 px-4 py-10 sm:px-6 lg:grid-cols-2 lg:py-16">
          <div>
            <Mascot mood="cheering" size={120} className="hop mb-2 lg:hidden" />
            <h1 id="hero-title" className="mb-3 text-balance text-4xl font-extrabold sm:text-5xl">
              Belajar jadi petualangan seru!
            </h1>
            <p className="mb-6 max-w-xl text-xl text-ink/85">
              Guru unggah materi PDF, EduMap menyusun peta level. Murid bermain, menjawab kuis, dan mengumpulkan bintang.
            </p>
            <div className="flex flex-col gap-3 sm:flex-row sm:flex-wrap">
              <Link href="/register" className="btn-primary">
                <RocketIcon size={22} />
                Daftar gratis
              </Link>
              <Link href="/login" className="btn-ghost">
                Masuk
              </Link>
              <a href="#demo" className="btn-ghost">
                <PlayIcon size={20} />
                Coba dulu
              </a>
            </div>
          </div>
          <div className="hidden min-h-[520px] overflow-hidden rounded-4xl border-2 border-rule-dark lg:block">
            <AuthHero tagline="Satu peta, banyak level. Siapa yang paling banyak bintang?" />
          </div>
        </section>

        <section aria-labelledby="features-title" className="mx-auto max-w-6xl px-4 py-10 sm:px-6">
          <h2 id="features-title" className="mb-2 text-3xl font-extrabold sm:text-4xl">
            Apa saja yang bisa dilakukan?
          </h2>
          <p className="mb-6 max-w-2xl text-lg text-ink/85">Dibuat untuk guru dan murid SD. Mudah dipakai, seru dipelajari.</p>
          <ul className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {FEATURES.map(({ Icon, tone, title, text }) => (
              <li key={title} className="surface">
                <span className={`mb-3 flex h-12 w-12 items-center justify-center rounded-2xl ${tone}`}>
                  <Icon size={28} />
                </span>
                <h3 className="mb-1 text-xl font-bold">{title}</h3>
                <p className="text-base text-ink/85">{text}</p>
              </li>
            ))}
          </ul>
        </section>

        <section aria-labelledby="steps-title" className="mx-auto max-w-6xl px-4 py-10 sm:px-6">
          <h2 id="steps-title" className="mb-6 text-3xl font-extrabold sm:text-4xl">
            Cara kerja
          </h2>
          <ol className="grid gap-4 md:grid-cols-3">
            {STEPS.map(({ Icon, title, text }, i) => (
              <li key={title} className="surface relative">
                <span className="absolute -top-4 left-5 flex h-9 w-9 items-center justify-center rounded-full bg-highlight font-display text-lg font-extrabold">
                  {i + 1}
                </span>
                <Icon size={32} className="mb-2 mt-2 text-sky-dark" />
                <h3 className="mb-1 text-xl font-bold">{title}</h3>
                <p className="text-base text-ink/85">{text}</p>
              </li>
            ))}
          </ol>
        </section>

        <section id="demo" aria-labelledby="demo-title" className="mx-auto max-w-4xl scroll-mt-20 px-4 py-10 sm:px-6">
          <h2 id="demo-title" className="mb-2 text-3xl font-extrabold sm:text-4xl">
            Coba sekarang
          </h2>
          <p className="mb-5 text-lg text-ink/85">Tanpa daftar dan tanpa menyimpan apa pun. Pilih peranmu lalu mulai.</p>
          <DemoTabs />
        </section>

        <section aria-labelledby="cta-title" className="mx-auto max-w-6xl px-4 py-10 sm:px-6">
          <div className="rounded-4xl bg-ink px-6 py-10 text-center text-chalk sm:px-10">
            <Mascot mood="happy" size={90} className="bob mx-auto" />
            <h2 id="cta-title" className="mb-2 text-3xl font-extrabold sm:text-4xl">
              Siap mulai petualangan?
            </h2>
            <p className="mx-auto mb-6 max-w-xl text-lg text-chalk-dim">Gratis untuk guru dan murid. Buat kelas pertamamu hari ini.</p>
            <div className="flex flex-col justify-center gap-3 sm:flex-row">
              <Link href="/register" className="btn-primary">
                Daftar gratis
                <ArrowRightIcon size={22} />
              </Link>
              <Link href="/login" className="btn-ghost">
                <TrophyIcon size={20} />
                Masuk
              </Link>
            </div>
          </div>
        </section>
      </main>

      <footer className="border-t-2 border-rule bg-paper">
        <div className="mx-auto flex max-w-6xl flex-col gap-3 px-4 py-8 sm:flex-row sm:items-center sm:justify-between sm:px-6">
          <div>
            <Logo />
            <p className="mt-1 text-base text-ink/80">Dibuat untuk lomba Innovating Education Through Technology</p>
          </div>
          <nav aria-label="Menu bawah" className="flex gap-4">
            <Link href="/login" className="link-text">
              Masuk
            </Link>
            <Link href="/register" className="link-text">
              Daftar
            </Link>
          </nav>
        </div>
      </footer>
    </div>
  );
}
