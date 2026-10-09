import type { CSSProperties } from "react";

// Decorative drifting clouds (CSS only, see ".sky-*" in globals.css).
// variant="auth": full sky inside a panel. variant="page": fixed behind app pages, only 4 faint
// clouds (2 on phones), transform-only animation so it stays on the compositor and costs no layout.
// Tops are kept low enough that every cloud fits fully inside the panel vertically.
// Each cloud has a size, height, speed and a negative delay so they start spread across the sky.
const CLOUDS = [
  { top: 4, w: 150, dur: 70, delay: -12, rest: 18, o: 0.9 },
  { top: 17, w: 210, dur: 95, delay: -60, rest: 62, o: 0.75 },
  { top: 31, w: 120, dur: 55, delay: -30, rest: 40, o: 0.95 },
  { top: 45, w: 240, dur: 110, delay: -20, rest: 8, o: 0.65 },
  { top: 59, w: 140, dur: 62, delay: -48, rest: 70, o: 0.85 },
  { top: 73, w: 180, dur: 85, delay: -5, rest: 33, o: 0.7 },
] as const;

// ViewBox fitted to the path's real bounding box (plus stroke and margin) so no edge is clipped.
const CLOUD_X = 8;
const CLOUD_Y = -14;
const CLOUD_W = 176;
const CLOUD_H = 96;

function Cloud({ width, page }: { width: number; page: boolean }) {
  return (
    <svg
      width={width}
      height={width * (CLOUD_H / CLOUD_W)}
      viewBox={`${CLOUD_X} ${CLOUD_Y} ${CLOUD_W} ${CLOUD_H}`}
      aria-hidden="true"
      focusable="false"
    >
      <path
        d="M40 78a30 30 0 0 1-4-59 40 40 0 0 1 74-8 34 34 0 0 1 56 20 26 26 0 0 1-6 47z"
        fill={page ? "#E6F3FF" : "#fff"}
        stroke={page ? "#A9D2F2" : "#CFE6F8"}
        strokeWidth="3"
        strokeLinejoin="round"
      />
    </svg>
  );
}

// Spread over the whole viewport (the header and hero hide the top), big enough to notice.
const PAGE_CLOUDS = [
  { top: 22, w: 190, dur: 80, delay: -25, rest: 20, o: 0.9 },
  { top: 48, w: 150, dur: 60, delay: -40, rest: 55, o: 0.9 },
  { top: 68, w: 220, dur: 100, delay: -10, rest: 30, o: 0.85 },
  { top: 84, w: 170, dur: 70, delay: -55, rest: 70, o: 0.9 },
] as const;

export default function CloudSky({
  variant = "auth",
}: {
  variant?: "auth" | "page";
}) {
  const isPage = variant === "page";
  const clouds = isPage ? PAGE_CLOUDS : CLOUDS;
  return (
    <div
      aria-hidden="true"
      className={`sky pointer-events-none overflow-hidden ${
        isPage ? "sky-page fixed inset-0 -z-10 opacity-100" : "absolute inset-0"
      }`}
    >
      {clouds.map((c, i) => (
        <div
          key={i}
          className={`sky-cloud absolute left-0 ${isPage && i >= 2 ? "max-sm:hidden" : ""}`}
          style={
            {
              top: `${c.top}%`,
              opacity: c.o,
              "--dur": `${c.dur}s`,
              "--delay": `${c.delay}s`,
              "--rest": `${c.rest}cqw`,
            } as CSSProperties
          }
        >
          <Cloud width={c.w} page={isPage} />
        </div>
      ))}
    </div>
  );
}
