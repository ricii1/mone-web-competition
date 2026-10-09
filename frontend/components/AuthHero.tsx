import type { CSSProperties } from "react";
import Mascot from "@/components/Mascot";

// Motion graphic (CSS only, see ".ah-*" in globals.css): a player walks the level path,
// each stop pops with stars, then the boss level unlocks. The loop is 12s; with reduced
// motion the finished scene is shown instead.
const ROAD = "M36 120 Q72 60 108 76 T188 112 T262 56";
const STOPS = [
  { x: 36, y: 120, label: "1" },
  { x: 108, y: 76, label: "2" },
  { x: 188, y: 112, label: "3" },
] as const;
const BOSS = { x: 262, y: 56 };
const STAR = "M0 -8l2.4 5 5.4.8-3.9 3.8.9 5.4L0 4.3l-4.8 2.7.9-5.4-3.9-3.8 5.4-.8z";
const BUBBLES = ["Ayo mulai petualangan!", "Hebat! Kamu dapat bintang!", "Terus semangat!", "Level boss terbuka!"];
const CONFETTI = [
  { dx: -34, dy: -30, c: "#FFC83D" },
  { dx: 0, dy: -42, c: "#3FBF6A" },
  { dx: 34, dy: -30, c: "#FF6B6B" },
  { dx: 44, dy: 2, c: "#46A8F5" },
  { dx: 30, dy: 34, c: "#FFC83D" },
  { dx: -4, dy: 40, c: "#9B6BFF" },
  { dx: -34, dy: 30, c: "#3FBF6A" },
  { dx: -44, dy: 0, c: "#FF6B6B" },
] as const;
const TWINKLES = [
  { x: 22, y: 28, d: "0s" },
  { x: 150, y: 18, d: "1.2s" },
  { x: 232, y: 112, d: "2.1s" },
  { x: 70, y: 156, d: "0.6s" },
  { x: 286, y: 150, d: "1.8s" },
] as const;

function Stars({ x, y, cls }: { x: number; y: number; cls: string }) {
  return (
    <g className={`ah-stars ${cls}`}>
      {[-13, 0, 13].map((dx, i) => (
        <path key={dx} d={STAR} transform={`translate(${x + dx} ${y - (i === 1 ? 36 : 31)})`} fill="#FFC83D" />
      ))}
    </g>
  );
}

export default function AuthHero({ tagline }: { tagline: string }) {
  return (
    <div className="ink-panel relative flex h-full flex-col justify-between overflow-hidden bg-ink px-10 py-10 text-chalk">
      <div aria-hidden="true" className="absolute -right-16 -top-16 h-64 w-64 rounded-full bg-sky/20" />
      <div aria-hidden="true" className="absolute -bottom-24 -left-20 h-72 w-72 rounded-full bg-grape/20" />

      <p className="relative flex items-center gap-2 font-display text-2xl font-extrabold">
        <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-highlight text-ink">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
            <path d="M12 2.8l2.8 5.8 6.3.9-4.6 4.4 1.1 6.3L12 17.1l-5.6 3.1 1.1-6.3L2.9 9.5l6.3-.9z" />
          </svg>
        </span>
        EduMap
      </p>

      <div className="relative flex flex-col items-center gap-1" aria-hidden="true">
        <div className="relative">
          <Mascot mood="cheering" size={200} className="bob" />
          <div className="absolute -right-24 top-0 grid">
            {BUBBLES.map((text, i) => (
              <span
                key={text}
                className={`ah-bubble ah-bubble-${i} col-start-1 row-start-1 w-max max-w-[170px] self-start rounded-2xl rounded-bl-sm bg-white px-3 py-1.5 text-sm font-bold leading-snug text-ink shadow-lg`}
              >
                {text}
              </span>
            ))}
          </div>
        </div>

        <svg viewBox="0 0 300 180" className="w-full max-w-md overflow-visible">
          {TWINKLES.map((t) => (
            <path
              key={`${t.x}-${t.y}`}
              d={STAR}
              transform={`translate(${t.x} ${t.y}) scale(0.7)`}
              fill="#B9C2CE"
              className="twinkle"
              style={{ animationDelay: t.d, transformBox: "fill-box", transformOrigin: "center" }}
            />
          ))}
          <g className="ah-stage">
            <g className="ah-drift" opacity=".12">
              <ellipse cx="60" cy="30" rx="26" ry="9" fill="#fff" />
              <ellipse cx="200" cy="22" rx="20" ry="7" fill="#fff" />
            </g>

            <path d={ROAD} fill="none" stroke="#3A4C66" strokeWidth="5" strokeDasharray="2 11" strokeLinecap="round" />
            <path
              className="ah-trail"
              d={ROAD}
              pathLength={100}
              fill="none"
              stroke="#FFC83D"
              strokeWidth="5"
              strokeLinecap="round"
            />

            {STOPS.map((s, i) => (
              <g key={s.label}>
                <g className={`ah-node ah-node-${i}`}>
                  <circle cx={s.x} cy={s.y + 4} r="19" fill="#000" opacity=".25" />
                  <circle cx={s.x} cy={s.y} r="19" fill="#3FBF6A" stroke="#fff" strokeWidth="3" />
                  <text x={s.x} y={s.y + 6} textAnchor="middle" fontSize="18" fontWeight="800" fill="#1B2A41" fontFamily="sans-serif">
                    {s.label}
                  </text>
                </g>
                <Stars x={s.x} y={s.y} cls={`ah-stars-${i}`} />
                {i > 0 && (
                  <text
                    x={s.x + 26}
                    y={s.y - 8}
                    fontSize="12"
                    fontWeight="800"
                    fill="#FFC83D"
                    fontFamily="sans-serif"
                    className={`ah-xp ah-xp-${i}`}
                  >
                    +100
                  </text>
                )}
              </g>
            ))}

            <g className="ah-node ah-node-3">
              <circle cx={BOSS.x} cy={BOSS.y + 4} r="19" fill="#000" opacity=".25" />
              <circle cx={BOSS.x} cy={BOSS.y} r="19" className="ah-boss-fill" stroke="#fff" strokeWidth="3" />
              <g className="ah-lock" fill="none" stroke="#fff" strokeWidth="3" strokeLinecap="round">
                <rect x={BOSS.x - 7} y={BOSS.y - 2} width="14" height="11" rx="3" fill="#fff" stroke="none" />
                <path d={`M${BOSS.x - 4} ${BOSS.y - 2} v-4 a4 4 0 0 1 8 0 v4`} />
              </g>
              <path
                className="ah-crown"
                d={`M${BOSS.x - 9} ${BOSS.y + 7}l-2-14 6 5 5-9 5 9 6-5-2 14z`}
                fill="#fff"
              />
            </g>
            <circle cx={BOSS.x} cy={BOSS.y} r="19" fill="none" stroke="#FFC83D" strokeWidth="4" className="ah-burst" />
            {CONFETTI.map((c, i) => (
              <circle
                key={i}
                cx={BOSS.x}
                cy={BOSS.y}
                r="3"
                fill={c.c}
                className="ah-confetti"
                style={{ "--dx": c.dx, "--dy": c.dy } as CSSProperties}
              />
            ))}

            <g className="ah-player">
              <circle r="9" fill="#fff" stroke="#1B2A41" strokeWidth="2.5" />
              <path d={STAR} transform="scale(0.75)" fill="#FFC83D" />
            </g>
          </g>
        </svg>
      </div>

      <p key={tagline} className="tagline-fade relative max-w-sm text-balance font-display text-3xl font-bold leading-snug">
        {tagline}
      </p>
    </div>
  );
}
