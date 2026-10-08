const NODES = [
  { x: 40, y: 220, label: "Mulai", state: "done" },
  { x: 130, y: 160, label: "Bab 1", state: "done" },
  { x: 100, y: 80, label: "Bab 2", state: "active" },
  { x: 200, y: 40, label: "Boss", state: "locked" },
] as const;

const STATE_FILL: Record<(typeof NODES)[number]["state"], string> = {
  done: "#3F7D58",
  active: "#E3A23C",
  locked: "#3A4C66",
};

export default function AuthHero({ tagline }: { tagline: string }) {
  const path = NODES.map((n, i) => `${i === 0 ? "M" : "L"}${n.x},${n.y}`).join(" ");

  return (
    <div className="ink-panel flex h-full flex-col justify-between bg-ink px-10 py-12 text-chalk">
      <p className="font-display text-xl">EduMap</p>

      <svg viewBox="0 0 260 260" className="w-full max-w-xs self-center" aria-hidden="true">
        <path d={path} fill="none" stroke="#3A4C66" strokeWidth="2" strokeDasharray="1 10" strokeLinecap="round" />
        {NODES.map((n) => (
          <g key={n.label}>
            <circle cx={n.x} cy={n.y} r={10} fill={STATE_FILL[n.state]} />
            <text x={n.x} y={n.y - 18} textAnchor="middle" fill="#B9C2CE" fontSize="11" fontFamily="var(--font-body)">
              {n.label}
            </text>
          </g>
        ))}
      </svg>

      <p key={tagline} className="tagline-fade max-w-xs text-balance font-display text-2xl leading-snug">
        {tagline}
      </p>
    </div>
  );
}
