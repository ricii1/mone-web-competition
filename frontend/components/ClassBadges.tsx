import type { SchoolClass } from "@/lib/types";

export default function ClassBadges({ cls }: { cls: SchoolClass }) {
  return (
    <span className="flex flex-wrap items-center gap-1.5">
      {cls.is_example && <span className="badge-highlight">Contoh</span>}
      <span className="badge">{cls.visibility === "private" ? "Pakai kode" : "Terbuka"}</span>
      <span className={cls.status === "published" ? "badge-success" : "badge"}>
        {cls.status === "published" ? "Terbit" : "Draft"}
      </span>
    </span>
  );
}
