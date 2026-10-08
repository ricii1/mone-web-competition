import { BookIcon, PencilIcon } from "@/components/icons";
import type { UserRole } from "@/lib/types";

const ROLES: { value: UserRole; label: string; hint: string }[] = [
  { value: "student", label: "Murid", hint: "Belajar dan main kuis" },
  { value: "teacher", label: "Guru", hint: "Buat kelas dan materi" },
];

export default function RoleChooser({
  value,
  onChange,
}: {
  value: UserRole;
  onChange: (role: UserRole) => void;
}) {
  return (
    <div className="grid grid-cols-2 gap-3">
      {ROLES.map((r) => {
        const active = value === r.value;
        return (
          <button
            key={r.value}
            type="button"
            onClick={() => onChange(r.value)}
            aria-pressed={active}
            className={`flex min-h-[88px] flex-col items-start gap-1 rounded-2xl border-2 px-4 py-3 text-left transition-colors ${
              active ? "border-sky-dark bg-sky-soft" : "border-rule bg-white hover:border-sky"
            }`}
          >
            <span className="flex items-center gap-2 font-display text-xl font-bold">
              <span className={active ? "text-sky-dark" : "text-ink/60"}>
                {r.value === "student" ? <BookIcon size={22} /> : <PencilIcon size={22} />}
              </span>
              {r.label}
            </span>
            <span className="text-base leading-tight text-ink/75">{r.hint}</span>
          </button>
        );
      })}
    </div>
  );
}

export { ROLES };
