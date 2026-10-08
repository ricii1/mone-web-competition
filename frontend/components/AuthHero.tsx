import Mascot from "@/components/Mascot";

const STOPS = [
  { x: 36, y: 120, fill: "#3FBF6A", label: "1" },
  { x: 108, y: 76, fill: "#3FBF6A", label: "2" },
  { x: 188, y: 112, fill: "#FFC83D", label: "3" },
  { x: 262, y: 56, fill: "#9B6BFF", label: "" },
];

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

      <div className="relative flex flex-col items-center gap-2">
        <Mascot mood="cheering" size={230} className="bob" />
        <svg viewBox="0 0 300 170" className="w-full max-w-sm" aria-hidden="true">
          <path
            d="M36 120 Q72 60 108 76 T188 112 T262 56"
            fill="none"
            stroke="#FFC83D"
            strokeWidth="5"
            strokeDasharray="2 11"
            strokeLinecap="round"
            opacity=".8"
          />
          {STOPS.map((s, i) => (
            <g key={i} className={i === 2 ? "twinkle" : undefined} style={{ transformBox: "fill-box", transformOrigin: "center" }}>
              <circle cx={s.x} cy={s.y + 4} r="19" fill="#000" opacity=".25" />
              <circle cx={s.x} cy={s.y} r="19" fill={s.fill} stroke="#fff" strokeWidth="3" />
              {s.label ? (
                <text x={s.x} y={s.y + 6} textAnchor="middle" fontSize="18" fontWeight="800" fill="#1B2A41" fontFamily="sans-serif">
                  {s.label}
                </text>
              ) : (
                <path d={`M${s.x - 9} ${s.y + 7}l-2-14 6 5 5-9 5 9 6-5-2 14z`} fill="#fff" />
              )}
            </g>
          ))}
        </svg>
      </div>

      <p key={tagline} className="tagline-fade relative max-w-sm text-balance font-display text-3xl font-bold leading-snug">
        {tagline}
      </p>
    </div>
  );
}
