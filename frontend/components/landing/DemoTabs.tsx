"use client";

import dynamic from "next/dynamic";
import { useRef, useState, type KeyboardEvent } from "react";

const loading = () => <p className="py-8 text-center text-lg font-semibold text-ink/70">Sebentar ya...</p>;
const StudentDemo = dynamic(() => import("./StudentDemo"), { ssr: false, loading });
const TeacherDemo = dynamic(() => import("./TeacherDemo"), { ssr: false, loading });

const TABS = [
  { id: "student", label: "Coba sebagai Murid" },
  { id: "teacher", label: "Coba sebagai Guru" },
] as const;

type TabId = (typeof TABS)[number]["id"];

/** Accessible two-tab switcher (roving tabindex, arrow keys). Only the active demo is mounted. */
export default function DemoTabs() {
  const [active, setActive] = useState<TabId>("student");
  const refs = useRef<Record<TabId, HTMLButtonElement | null>>({ student: null, teacher: null });

  function onKeyDown(e: KeyboardEvent<HTMLButtonElement>) {
    const i = TABS.findIndex((t) => t.id === active);
    let n = i;
    if (e.key === "ArrowRight") n = (i + 1) % TABS.length;
    else if (e.key === "ArrowLeft") n = (i - 1 + TABS.length) % TABS.length;
    else if (e.key === "Home") n = 0;
    else if (e.key === "End") n = TABS.length - 1;
    else return;
    e.preventDefault();
    setActive(TABS[n].id);
    refs.current[TABS[n].id]?.focus();
  }

  return (
    <div className="surface !p-4 sm:!p-6">
      <div role="tablist" aria-label="Pilih contoh" className="mb-5 grid grid-cols-2 gap-2 rounded-2xl bg-ink/5 p-1.5">
        {TABS.map((t) => (
          <button
            key={t.id}
            ref={(el) => {
              refs.current[t.id] = el;
            }}
            type="button"
            role="tab"
            id={`demo-tab-${t.id}`}
            aria-selected={active === t.id}
            aria-controls={`demo-panel-${t.id}`}
            tabIndex={active === t.id ? 0 : -1}
            onClick={() => setActive(t.id)}
            onKeyDown={onKeyDown}
            className={`min-h-[48px] rounded-xl px-2 py-2 font-display text-base font-bold leading-tight sm:text-lg ${
              active === t.id ? "bg-white text-ink shadow" : "text-ink/70 hover:bg-white/60"
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>
      <div role="tabpanel" id={`demo-panel-${active}`} aria-labelledby={`demo-tab-${active}`} tabIndex={0} className="min-h-[320px]">
        {active === "student" ? <StudentDemo /> : <TeacherDemo />}
      </div>
    </div>
  );
}
