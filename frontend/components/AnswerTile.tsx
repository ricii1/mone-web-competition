import { CheckIcon, CircleIcon, CrossIcon, DiamondIcon, SquareIcon, TriangleIcon } from "@/components/icons";

// Kahoot-style tiles: each has its own color AND shape plus a letter, so color is never the only cue.
export const TILE_STYLES = [
  { Shape: TriangleIcon, bg: "bg-coral-dark", edge: "#8f2d24", name: "A" },
  { Shape: DiamondIcon, bg: "bg-sky-dark", edge: "#14568d", name: "B" },
  { Shape: CircleIcon, bg: "bg-[#B07A00]", edge: "#7a5300", name: "C" },
  { Shape: SquareIcon, bg: "bg-grass-dark", edge: "#1b6a38", name: "D" },
] as const;

export type TileState = "idle" | "chosen" | "correct" | "wrong" | "dim";

export default function AnswerTile({
  index,
  label,
  state = "idle",
  disabled,
  onClick,
  count,
}: {
  index: number;
  label: string;
  state?: TileState;
  disabled?: boolean;
  onClick?: () => void;
  count?: number;
}) {
  const style = TILE_STYLES[index % TILE_STYLES.length];
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      aria-pressed={state === "chosen"}
      style={{ boxShadow: state === "dim" ? "none" : `0 5px 0 0 ${style.edge}` }}
      className={`relative flex min-h-[84px] w-full items-center gap-4 rounded-3xl px-5 py-4 text-left font-display text-xl font-bold leading-snug text-white transition-[transform,opacity] duration-100 enabled:active:translate-y-[5px] enabled:active:!shadow-none disabled:cursor-default sm:min-h-[110px] sm:text-2xl ${style.bg} ${
        state === "dim" ? "opacity-45" : ""
      } ${state === "chosen" || state === "correct" ? "ring-4 ring-ink ring-offset-2 ring-offset-paper" : ""}`}
    >
      <span className="flex h-12 w-12 shrink-0 flex-col items-center justify-center rounded-2xl bg-white/25">
        <style.Shape size={20} />
        <span className="text-sm leading-none">{style.name}</span>
      </span>
      <span className="min-w-0 flex-1">{label}</span>
      {typeof count === "number" && <span className="rounded-full bg-white/25 px-3 py-1 text-lg">{count}</span>}
      {state === "chosen" && (
        <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-white text-ink">
          <CheckIcon size={24} />
        </span>
      )}
      {state === "correct" && (
        <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-white text-grass-dark">
          <CheckIcon size={24} />
        </span>
      )}
      {state === "wrong" && (
        <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-white text-coral-dark">
          <CrossIcon size={24} />
        </span>
      )}
    </button>
  );
}
