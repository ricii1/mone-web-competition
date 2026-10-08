import Link from "next/link";
import { ArrowLeftIcon } from "@/components/icons";

export default function BackLink({ href, children }: { href: string; children: React.ReactNode }) {
  return (
    <Link
      href={href}
      className="-ml-2 inline-flex min-h-[48px] max-w-full items-center gap-2 rounded-2xl px-3 text-base font-bold text-sky-dark transition-colors hover:bg-sky-soft"
    >
      <ArrowLeftIcon size={20} className="shrink-0" />
      <span className="min-w-0 truncate">{children}</span>
    </Link>
  );
}
