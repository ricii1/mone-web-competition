const COLORS = [
  "bg-sky-dark text-white",
  "bg-grass-dark text-white",
  "bg-coral-dark text-white",
  "bg-grape-dark text-white",
  "bg-highlight text-ink",
];

function hash(text: string): number {
  let h = 0;
  for (let i = 0; i < text.length; i++) h = (h * 31 + text.charCodeAt(i)) >>> 0;
  return h;
}

/** Colorful initial-letter avatar generated on the client. */
export default function Avatar({ name, size = 40, className = "" }: { name: string; size?: number; className?: string }) {
  const initial = (name.trim()[0] ?? "?").toUpperCase();
  return (
    <span
      aria-hidden="true"
      style={{ width: size, height: size, fontSize: size * 0.48 }}
      className={`inline-flex shrink-0 items-center justify-center rounded-full border-2 border-white font-display font-bold shadow-sm ${COLORS[hash(name) % COLORS.length]} ${className}`}
    >
      {initial}
    </span>
  );
}
