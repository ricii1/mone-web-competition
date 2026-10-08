const COLORS = ["bg-highlight", "bg-sky", "bg-grass", "bg-coral", "bg-grape"];

/** CSS-only confetti. Hidden entirely when the user prefers reduced motion. */
export default function Confetti() {
  return (
    <div aria-hidden="true" className="pointer-events-none absolute inset-x-0 top-0 h-56 overflow-hidden">
      {Array.from({ length: 18 }, (_, i) => (
        <span
          key={i}
          className={`confetti-piece absolute top-0 h-3 w-2 rounded-sm ${COLORS[i % COLORS.length]}`}
          style={
            {
              left: `${(i * 37) % 100}%`,
              "--d": `${(i % 6) * 120}ms`,
              "--x": `${((i % 5) - 2) * 18}px`,
              "--r": `${180 + i * 25}deg`,
            } as React.CSSProperties
          }
        />
      ))}
    </div>
  );
}
