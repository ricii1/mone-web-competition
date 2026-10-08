const PATH = "M40,220 L130,160 L100,80 L200,40";

const DOTS = [
  { cx: 30, cy: 40, r: 2, cls: "hero-float-a" },
  { cx: 225, cy: 110, r: 2.5, cls: "hero-float-b" },
  { cx: 160, cy: 235, r: 2, cls: "hero-float-c" },
  { cx: 60, cy: 130, r: 1.5, cls: "hero-float-b" },
  { cx: 235, cy: 205, r: 1.5, cls: "hero-float-a" },
  { cx: 150, cy: 20, r: 2, cls: "hero-float-c" },
];

export default function AuthHero({ tagline }: { tagline: string }) {
  return (
    <div className="ink-panel flex h-full flex-col justify-between overflow-hidden bg-ink px-10 py-12 text-chalk">
      <p className="font-display text-xl">EduMap</p>

      <svg viewBox="0 0 260 260" className="w-full max-w-sm self-center" aria-hidden="true">
        {DOTS.map((d, i) => (
          <circle key={i} cx={d.cx} cy={d.cy} r={d.r} fill="#B9C2CE" className={`hero-dot ${d.cls}`} />
        ))}

        <g className="hero-stage">
          <path d={PATH} fill="none" stroke="#3A4C66" strokeWidth="2" strokeDasharray="1 10" strokeLinecap="round" />
          <path
            d={PATH}
            pathLength={100}
            fill="none"
            stroke="#E3A23C"
            strokeWidth="2.5"
            strokeLinecap="round"
            strokeLinejoin="round"
            className="hero-trail"
          />

          <g className="hero-node hero-node-a">
            <circle cx="40" cy="220" r="10" fill="#3F7D58" />
            <text x="40" y="202" textAnchor="middle" fill="#B9C2CE" fontSize="11">Mulai</text>
          </g>

          <g className="hero-node hero-node-b">
            <circle cx="130" cy="160" r="10" fill="#3F7D58" />
            <text x="130" y="142" textAnchor="middle" fill="#B9C2CE" fontSize="11">Bab 1</text>
          </g>
          <text x="130" y="150" textAnchor="middle" fill="#E3A23C" fontSize="10" fontWeight="700" className="hero-xp hero-xp-b">
            +100
          </text>

          <g className="hero-node hero-node-c">
            <circle cx="100" cy="80" r="10" fill="#E3A23C" className="hero-pulse" />
            <circle cx="100" cy="80" r="10" fill="#E3A23C" />
            <text x="100" y="62" textAnchor="middle" fill="#B9C2CE" fontSize="11">Bab 2</text>
          </g>
          <text x="100" y="70" textAnchor="middle" fill="#E3A23C" fontSize="10" fontWeight="700" className="hero-xp hero-xp-c">
            +100
          </text>

          <g className="hero-node hero-node-d">
            <circle cx="200" cy="40" r="10" fill="#E3A23C" className="hero-burst" />
            <circle cx="200" cy="40" r="10" className="hero-boss-fill" />
            <text x="200" y="22" textAnchor="middle" fill="#B9C2CE" fontSize="11">Boss</text>
          </g>

          <circle r="5" fill="#F3EFE3" className="hero-player" />
        </g>
      </svg>

      <p key={tagline} className="tagline-fade max-w-xs text-balance font-display text-2xl leading-snug">
        {tagline}
      </p>
    </div>
  );
}
