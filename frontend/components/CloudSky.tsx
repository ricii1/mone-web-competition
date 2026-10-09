import type { CSSProperties } from "react";

// Decorative drifting clouds for the auth pages (CSS only, see ".sky-*" in globals.css).
// Each cloud has a size, height, speed and a negative delay so they start spread across the sky.
const CLOUDS = [
  { top: 6, w: 150, dur: 70, delay: -12, rest: 18, o: 0.9 },
  { top: 20, w: 210, dur: 95, delay: -60, rest: 62, o: 0.75 },
  { top: 38, w: 120, dur: 55, delay: -30, rest: 40, o: 0.95 },
  { top: 57, w: 240, dur: 110, delay: -20, rest: 8, o: 0.65 },
  { top: 74, w: 140, dur: 62, delay: -48, rest: 70, o: 0.85 },
  { top: 88, w: 180, dur: 85, delay: -5, rest: 33, o: 0.7 },
] as const;

function Cloud({ width }: { width: number }) {
  return (
    <svg width={width} height={width * 0.45} viewBox="0 0 200 90" aria-hidden="true" focusable="false">
      <path
        d="M40 78a30 30 0 0 1-4-59 40 40 0 0 1 74-8 34 34 0 0 1 56 20 26 26 0 0 1-6 47z"
        fill="#fff"
        stroke="#CFE6F8"
        strokeWidth="3"
        strokeLinejoin="round"
      />
    </svg>
  );
}

export default function CloudSky() {
  return (
    <div aria-hidden="true" className="sky pointer-events-none absolute inset-0 overflow-hidden">
      {CLOUDS.map((c, i) => (
        <div
          key={i}
          className="sky-cloud absolute left-0"
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
          <Cloud width={c.w} />
        </div>
      ))}
    </div>
  );
}
