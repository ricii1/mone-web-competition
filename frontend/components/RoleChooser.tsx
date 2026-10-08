import type { UserRole } from "@/lib/types";

const ROLES: { value: UserRole; label: string; hint: string }[] = [
  { value: "student", label: "Murid", hint: "Belajar lewat peta level & kuis" },
  { value: "teacher", label: "Guru", hint: "Unggah materi, buat kelas" },
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
      {ROLES.map((r) => (
        <button
          key={r.value}
          type="button"
          onClick={() => onChange(r.value)}
          aria-pressed={value === r.value}
          className={`rounded-sm border px-4 py-3 text-left transition-colors ${
            value === r.value ? "border-highlight bg-highlight/10" : "border-rule hover:border-ink/30"
          }`}
        >
          <span className="block font-medium">{r.label}</span>
          <span className="block text-xs text-ink/60">{r.hint}</span>
        </button>
      ))}
    </div>
  );
}

export { ROLES };
