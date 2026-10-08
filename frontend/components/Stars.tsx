import { StarIcon } from "@/components/icons";
import { starsFor } from "@/lib/stars";

/** Three stars; filled ones depend on the score percentage. */
export default function Stars({
  percent,
  size = 20,
  animate = false,
  className = "",
}: {
  percent: number;
  size?: number;
  animate?: boolean;
  className?: string;
}) {
  const count = starsFor(percent);
  return (
    <span className={`inline-flex items-center gap-0.5 ${className}`} role="img" aria-label={`${count} dari 3 bintang`}>
      {[0, 1, 2].map((i) => (
        <span
          key={i}
          className={`${animate && i < count ? "star-pop" : ""} ${i < count ? "text-highlight-dark" : "text-ink/20"}`}
          style={animate ? { animationDelay: `${i * 160}ms` } : undefined}
        >
          <StarIcon size={size} />
        </span>
      ))}
    </span>
  );
}
