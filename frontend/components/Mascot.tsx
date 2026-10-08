export type MascotMood = "happy" | "thinking" | "cheering" | "sleepy" | "oops";

const BODY = "#46A8F5";
const WING = "#2F86D6";
const INK = "#1B2A41";

function Eyes({ mood }: { mood: MascotMood }) {
  if (mood === "cheering") {
    return <path d="M34 54q6-9 12 0M74 54q6-9 12 0" fill="none" stroke={INK} strokeWidth="4" strokeLinecap="round" />;
  }
  if (mood === "sleepy") {
    return <path d="M33 53q6 6 13 0M74 53q6 6 13 0" fill="none" stroke={INK} strokeWidth="4" strokeLinecap="round" />;
  }
  const look = mood === "thinking" ? { x: 3, y: -4 } : mood === "oops" ? { x: 0, y: 4 } : { x: 0, y: 0 };
  return (
    <>
      <circle cx="42" cy="52" r="14" fill="#fff" stroke={INK} strokeWidth="3" />
      <circle cx="78" cy="52" r="14" fill="#fff" stroke={INK} strokeWidth="3" />
      <circle cx={42 + look.x} cy={52 + look.y} r="6.5" fill={INK} />
      <circle cx={78 + look.x} cy={52 + look.y} r="6.5" fill={INK} />
      <circle cx={44 + look.x} cy={49.5 + look.y} r="2" fill="#fff" />
      <circle cx={80 + look.x} cy={49.5 + look.y} r="2" fill="#fff" />
      {mood === "oops" && (
        <path d="M28 36l16 5M92 36l-16 5" stroke={INK} strokeWidth="3.5" strokeLinecap="round" />
      )}
      {mood === "thinking" && <path d="M66 36l16-4" stroke={INK} strokeWidth="3.5" strokeLinecap="round" />}
    </>
  );
}

/** Owl mascot "Bu Hoo": small inline SVG with a handful of moods. */
export default function Mascot({
  mood = "happy",
  size = 120,
  className,
}: {
  mood?: MascotMood;
  size?: number;
  className?: string;
}) {
  const cheer = mood === "cheering";
  return (
    <svg width={size} height={size} viewBox="0 0 120 124" className={className} aria-hidden="true" focusable="false">
      <ellipse cx="46" cy="116" rx="9" ry="5" fill="#FF9F1C" />
      <ellipse cx="74" cy="116" rx="9" ry="5" fill="#FF9F1C" />
      <path d="M26 42L22 12l28 16zM94 42l4-30-28 16z" fill={BODY} />
      <ellipse cx="60" cy="72" rx="42" ry="44" fill={BODY} />
      <ellipse cx="60" cy="88" rx="27" ry="27" fill="#FFF8E7" />
      <path d="M48 84q4 4 8 0M64 84q4 4 8 0M52 96q4 4 8 0M68 96q4 4 8 0" fill="none" stroke="#E6DCC0" strokeWidth="3" strokeLinecap="round" />
      {cheer ? (
        <>
          <ellipse cx="17" cy="52" rx="9" ry="21" fill={WING} transform="rotate(-25 17 52)" />
          <ellipse cx="103" cy="52" rx="9" ry="21" fill={WING} transform="rotate(25 103 52)" />
        </>
      ) : (
        <>
          <ellipse cx="19" cy="82" rx="9" ry="22" fill={WING} transform="rotate(10 19 82)" />
          <ellipse cx="101" cy="82" rx="9" ry="22" fill={WING} transform="rotate(-10 101 82)" />
        </>
      )}
      <Eyes mood={mood} />
      <circle cx="26" cy="68" r="6" fill="#FF6F61" opacity=".5" />
      <circle cx="94" cy="68" r="6" fill="#FF6F61" opacity=".5" />
      <path d="M53 62h14l-7 13z" fill="#FF9F1C" stroke="#E5800A" strokeWidth="2" strokeLinejoin="round" />
      {cheer && (
        <g fill="#FFC83D">
          <path d="M10 14l2 5 5 1-4 3 1 5-4-3-4 3 1-5-4-3 5-1z" className="twinkle" />
          <path d="M108 8l1.5 4 4 .800-3 2.5.800 4-3.3-2.3-3.3 2.3.800-4-3-2.5 4-.800z" className="twinkle" />
        </g>
      )}
      {mood === "sleepy" && (
        <text x="92" y="30" fontSize="18" fontWeight="800" fill={INK} fontFamily="sans-serif">
          z<tspan fontSize="13" dx="2">z</tspan>
        </text>
      )}
      {mood === "thinking" && (
        <g fill="#fff" stroke={INK} strokeWidth="2">
          <circle cx="100" cy="22" r="3" />
          <circle cx="108" cy="12" r="4.5" />
        </g>
      )}
      {mood === "oops" && <path d="M104 40q-4 7 0 10t0-10z" fill="#9AD4FF" stroke="#2F86D6" strokeWidth="1.5" />}
    </svg>
  );
}
