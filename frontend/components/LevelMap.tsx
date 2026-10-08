"use client";

import { Background, Handle, Position, ReactFlow, useReactFlow, type Edge, type Node, type NodeProps } from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { useRouter } from "next/navigation";
import { useEffect, useMemo } from "react";
import type { Level, Progress } from "@/lib/types";

const TEACHER_STATUS_STYLE: Record<string, { bg: string; text: string }> = {
  draft: { bg: "#DCD5C2", text: "#1B2A41" },
  approved: { bg: "#3F7D58", text: "#F3EFE3" },
};

const STATUS_STYLE: Record<string, { bg: string; text: string }> = {
  locked: { bg: "#DCD5C2", text: "#1B2A41" },
  unlocked: { bg: "#E3A23C", text: "#1B2A41" },
  completed: { bg: "#3F7D58", text: "#F3EFE3" },
};

const ICON_PROPS = {
  width: 16,
  height: 16,
  viewBox: "0 0 16 16",
  fill: "none",
  stroke: "currentColor",
  strokeWidth: 2,
  strokeLinecap: "round" as const,
  strokeLinejoin: "round" as const,
  "aria-hidden": true,
};

function StatusIcon({ status, teacher }: { status: string; teacher: boolean }) {
  if (status === "completed" || (teacher && status === "approved")) {
    return (
      <svg {...ICON_PROPS}>
        <path d="m3 8.5 3.2 3L13 4.5" />
      </svg>
    );
  }
  if (status === "locked") {
    return (
      <svg {...ICON_PROPS}>
        <rect x="3.5" y="7" width="9" height="6.5" rx="1.5" />
        <path d="M5.5 7V5.5a2.5 2.5 0 0 1 5 0V7" />
      </svg>
    );
  }
  if (status === "unlocked") {
    return (
      <svg {...ICON_PROPS} fill="currentColor">
        <path d="M5 3.5v9l7.5-4.5z" />
      </svg>
    );
  }
  return null;
}

const STATUS_LABEL: Record<string, string> = {
  locked: "Terkunci",
  unlocked: "Terbuka",
  completed: "Selesai",
  draft: "Draft",
  approved: "Disetujui",
};

function LevelNode({
  data,
}: NodeProps<Node<{ label: string; status: string; type: string; teacher: boolean; preview: boolean }>>) {
  const palette = data.teacher ? TEACHER_STATUS_STYLE : STATUS_STYLE;
  const style = palette[data.status] ?? palette.draft ?? STATUS_STYLE.locked;
  const current = !data.teacher && !data.preview && data.status === "unlocked";
  return (
    <div className="flex flex-col items-center gap-1">
      <div
        role="img"
        aria-label={`${data.label}, ${STATUS_LABEL[data.status] ?? data.status}${data.type === "boss" ? ", level boss" : ""}`}
        className={`node-appear flex min-w-[150px] max-w-[200px] items-center gap-2 rounded-2xl border-2 px-4 py-3 text-sm font-medium shadow-md shadow-ink/10 ${
          current ? "node-current" : ""
        } ${!data.teacher && data.status === "locked" ? "opacity-70" : ""}`}
        style={{
          background: style.bg,
          color: style.text,
          borderColor: data.type === "boss" ? "#B23A2E" : "rgba(27,42,65,0.12)",
        }}
      >
        <Handle type="target" position={Position.Top} style={{ opacity: 0 }} />
        <StatusIcon status={data.status} teacher={data.teacher} />
        <span className="leading-tight">{data.label}</span>
        <Handle type="source" position={Position.Bottom} style={{ opacity: 0 }} />
      </div>
      {current && (
        <span className="rounded-full bg-ink px-3 py-0.5 text-xs font-semibold text-chalk">Mulai</span>
      )}
    </div>
  );
}

// Re-fit the viewport when nodes are added (levels arrive one by one).
function FitOnChange({ count }: { count: number }) {
  const { fitView } = useReactFlow();
  useEffect(() => {
    fitView({ duration: 0, maxZoom: 1 });
  }, [count, fitView]);
  return null;
}

const nodeTypes = { level: LevelNode };

export default function LevelMap({
  classId,
  levels,
  progress = [],
  teacher = false,
  preview = false,
  height,
}: {
  classId: string;
  levels: Level[];
  progress?: Progress[];
  teacher?: boolean;
  /** Teacher preview of the student map: every level is open and links to the preview player. */
  preview?: boolean;
  height?: string;
}) {
  const router = useRouter();
  const statusByLevel = useMemo(() => {
    const map = new Map(progress.map((p) => [p.level_id, p.status]));
    return (levelId: string) => (preview ? "unlocked" : (map.get(levelId) ?? "locked"));
  }, [progress, preview]);

  const nodes: Node[] = levels.map((l, i) => ({
    id: l.id,
    type: "level",
    position: { x: [0, 150, 0, -150][i % 4], y: i * 110 },
    data: { label: l.title, status: teacher ? l.status : statusByLevel(l.id), type: l.type, teacher, preview },
  }));

  const edges: Edge[] = levels
    .filter((l) => l.prerequisite_id)
    .map((l) => ({
      id: `${l.prerequisite_id}-${l.id}`,
      source: l.prerequisite_id as string,
      target: l.id,
      style: { stroke: "#1B2A41", strokeWidth: 2, strokeDasharray: "2 8", strokeLinecap: "round" as const, opacity: 0.45 },
    }));

  return (
    <div className="card overflow-hidden p-0" style={{ height: height ?? (teacher ? "50vh" : "70vh") }}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        fitView
        fitViewOptions={{ maxZoom: 1 }}
        onNodeClick={(_, node) => {
          if (teacher) {
            router.push(`/teacher/classes/${classId}/levels/${node.id}`);
          } else if (preview) {
            router.push(`/teacher/classes/${classId}/levels/${node.id}/preview`);
          } else if (statusByLevel(node.id) !== "locked") {
            router.push(`/student/classes/${classId}/levels/${node.id}`);
          }
        }}
      >
        <Background color="#DCD5C2" />
        <FitOnChange count={levels.length} />
      </ReactFlow>
    </div>
  );
}
