"use client";

import { Background, Handle, Panel, Position, ReactFlow, useReactFlow, type Edge, type Node, type NodeProps } from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import { CheckIcon, CrownIcon, LockIcon, MonsterIcon, PlayIcon, TargetIcon } from "@/components/icons";
import Stars from "@/components/Stars";
import type { Level, Progress } from "@/lib/types";

type NodeStatus = "locked" | "unlocked" | "completed" | "draft" | "approved";

interface LevelNodeData extends Record<string, unknown> {
  label: string;
  status: NodeStatus;
  type: Level["type"];
  number: number;
  score: number;
  teacher: boolean;
  preview: boolean;
}

const STATUS_LABEL: Record<NodeStatus, string> = {
  locked: "Terkunci",
  unlocked: "Terbuka",
  completed: "Selesai",
  draft: "Draft",
  approved: "Disetujui",
};

// Circle colors per state. Boss levels get coral/purple so they stand out.
const LESSON_STYLE: Record<NodeStatus, string> = {
  locked: "bg-[#D9D2BD] text-ink/70 shadow-[0_6px_0_0_#B3AA90]",
  unlocked: "bg-highlight text-ink shadow-[0_6px_0_0_#c98f00]",
  completed: "bg-grass-dark text-white shadow-[0_6px_0_0_#1b6a38]",
  draft: "bg-[#D9D2BD] text-ink shadow-[0_6px_0_0_#B3AA90]",
  approved: "bg-grass-dark text-white shadow-[0_6px_0_0_#1b6a38]",
};
const BOSS_STYLE: Record<NodeStatus, string> = {
  locked: "bg-grape-soft text-grape-dark/70 shadow-[0_6px_0_0_#b9a4ee]",
  unlocked: "bg-coral-dark text-white shadow-[0_6px_0_0_#8f2d24]",
  completed: "bg-grape-dark text-white shadow-[0_6px_0_0_#46288f]",
  draft: "bg-grape-soft text-grape-dark shadow-[0_6px_0_0_#b9a4ee]",
  approved: "bg-grape-dark text-white shadow-[0_6px_0_0_#46288f]",
};

function NodeIcon({ status, boss, teacher }: { status: NodeStatus; boss: boolean; teacher: boolean }) {
  if (teacher) return boss ? <CrownIcon size={30} /> : <span />;
  if (status === "locked") return <LockIcon size={30} />;
  if (status === "completed") return boss ? <CrownIcon size={34} /> : <CheckIcon size={34} />;
  return boss ? <MonsterIcon size={36} /> : <PlayIcon size={32} />;
}

function LevelNode({ data }: NodeProps<Node<LevelNodeData>>) {
  const boss = data.type === "boss";
  const palette = boss ? BOSS_STYLE : LESSON_STYLE;
  const current = !data.teacher && !data.preview && data.status === "unlocked";
  const aria = `Level ${data.number}: ${data.label}, ${STATUS_LABEL[data.status]}${boss ? ", level bos" : ""}`;

  if (data.teacher) {
    return (
      <div
        role="img"
        aria-label={aria}
        className={`node-appear flex w-[200px] items-center gap-3 rounded-2xl border-2 bg-white px-3 py-2.5 text-left shadow-[0_4px_0_0_#E6DCC0] ${
          boss ? "border-grape" : "border-rule"
        }`}
      >
        <Handle type="target" position={Position.Top} style={{ opacity: 0 }} />
        <span className={`flex h-11 w-11 shrink-0 items-center justify-center rounded-xl font-display text-xl font-bold ${palette[data.status]}`}>
          {boss ? <CrownIcon size={26} /> : data.number}
        </span>
        <span className="min-w-0">
          <span className="line-clamp-2 block font-display text-base font-bold leading-tight">{data.label}</span>
          <span className={`text-sm font-bold ${data.status === "approved" ? "text-correct-dark" : "text-ink/70"}`}>
            {STATUS_LABEL[data.status]}
          </span>
        </span>
        <Handle type="source" position={Position.Bottom} style={{ opacity: 0 }} />
      </div>
    );
  }

  const size = boss ? "h-[104px] w-[104px] rounded-[34px]" : "h-[88px] w-[88px] rounded-full";
  return (
    <div role="img" aria-label={aria} className="node-appear flex w-[170px] flex-col items-center gap-2">
      <Handle type="target" position={Position.Top} style={{ opacity: 0 }} />
      {current && (
        <span className="bounce-bubble relative rounded-2xl bg-ink px-4 py-1.5 font-display text-lg font-bold text-chalk after:absolute after:-bottom-1.5 after:left-1/2 after:h-3 after:w-3 after:-translate-x-1/2 after:rotate-45 after:bg-ink">
          Mulai!
        </span>
      )}
      <div className="relative">
        {current && <span aria-hidden="true" className={`node-ring absolute inset-0 border-4 border-highlight ${boss ? "rounded-[34px]" : "rounded-full"}`} />}
        <div className={`relative flex items-center justify-center border-4 border-white ${size} ${palette[data.status]}`}>
          <NodeIcon status={data.status} boss={boss} teacher={false} />
          <span className="absolute -left-2 -top-2 flex h-8 w-8 items-center justify-center rounded-full border-2 border-white bg-ink font-display text-base font-bold text-chalk">
            {data.number}
          </span>
        </div>
      </div>
      {data.status === "completed" && <Stars percent={data.score} size={22} />}
      <span
        className={`line-clamp-2 rounded-xl bg-white/95 px-2.5 py-1 text-center font-display text-base font-bold leading-tight ${
          data.status === "locked" ? "text-ink/70" : "text-ink"
        }`}
      >
        {data.label}
      </span>
      <Handle type="source" position={Position.Bottom} style={{ opacity: 0 }} />
    </div>
  );
}

// Frame the whole map in teacher mode, but zoom near the student's current level otherwise.
function useDefaultView(focusIds: string[]) {
  const { fitView } = useReactFlow();
  return (duration: number) => {
    if (focusIds.length > 0) {
      fitView({ nodes: focusIds.map((id) => ({ id })), duration, maxZoom: 1, minZoom: 0.8, padding: 0.3 });
    } else {
      fitView({ duration, maxZoom: 1, padding: 0.2 });
    }
  };
}

function InitialView({ count, focusIds }: { count: number; focusIds: string[] }) {
  const goDefault = useDefaultView(focusIds);
  const key = focusIds.join(",");
  useEffect(() => {
    goDefault(0);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [count, key]);
  return null;
}

// Like the "my location" button on a map: jumps back to the default view when the map is lost.
function ResetViewButton({ focusIds }: { focusIds: string[] }) {
  const goDefault = useDefaultView(focusIds);
  return (
    <Panel position="bottom-left">
      <button type="button" onClick={() => goDefault(300)} className="btn-ghost" aria-label="Kembali ke tampilan awal">
        <TargetIcon size={20} />
        Tampilan awal
      </button>
    </Panel>
  );
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
  const [narrow, setNarrow] = useState(false);
  useEffect(() => {
    const mq = window.matchMedia("(max-width: 639px)");
    const update = () => setNarrow(mq.matches);
    update();
    mq.addEventListener("change", update);
    return () => mq.removeEventListener("change", update);
  }, []);

  const progressByLevel = useMemo(() => new Map(progress.map((p) => [p.level_id, p])), [progress]);
  const statusOf = (levelId: string): NodeStatus =>
    preview ? "unlocked" : (progressByLevel.get(levelId)?.status ?? "locked");

  const rowHeight = teacher ? 100 : 190;
  const swing = teacher ? (narrow ? 0 : 130) : narrow ? 40 : 200;
  const nodes: Node<LevelNodeData>[] = levels.map((l, i) => ({
    id: l.id,
    type: "level",
    position: { x: [0, swing, 0, -swing][i % 4], y: i * rowHeight },
    data: {
      label: l.title,
      status: teacher ? l.status : statusOf(l.id),
      type: l.type,
      number: i + 1,
      score: progressByLevel.get(l.id)?.best_score ?? 0,
      teacher,
      preview,
    },
  }));

  const currentIndex = !teacher && !preview ? levels.findIndex((l) => statusOf(l.id) === "unlocked") : -1;
  // Zoom near the current level (or the last one when all are done, or the start in preview).
  const focusIndex = teacher ? -1 : currentIndex >= 0 ? currentIndex : preview ? 1 : levels.length - 2;
  const focusIds =
    focusIndex >= 0 || (!teacher && levels.length > 0)
      ? levels.slice(Math.max(0, focusIndex - 1), Math.max(0, focusIndex) + 2).map((l) => l.id)
      : [];

  const edges: Edge[] = levels
    .filter((l) => l.prerequisite_id)
    .map((l) => ({
      id: `${l.prerequisite_id}-${l.id}`,
      source: l.prerequisite_id as string,
      target: l.id,
      style: { stroke: "#E5A800", strokeWidth: 5, strokeDasharray: "1 12", strokeLinecap: "round" as const },
    }));

  return (
    <div
      className="overflow-hidden rounded-3xl border-2 border-rule bg-gradient-to-b from-sky-soft via-white to-grass-soft"
      style={{ height: height ?? "clamp(360px, 60vh, 640px)", boxShadow: "0 4px 0 0 #e6dcc0" }}
    >
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        fitView
        minZoom={0.3}
        maxZoom={1.5}
        zoomOnDoubleClick={false}
        nodesDraggable={false}
        nodesConnectable={false}
        panOnScroll={!teacher}
        proOptions={{ hideAttribution: true }}
        onNodeClick={(_, node) => {
          if (teacher) {
            router.push(`/teacher/classes/${classId}/levels/${node.id}`);
          } else if (preview) {
            router.push(`/teacher/classes/${classId}/levels/${node.id}/preview`);
          } else if (statusOf(node.id) !== "locked") {
            router.push(`/student/classes/${classId}/levels/${node.id}`);
          }
        }}
      >
        <Background color="#E6DCC0" gap={26} size={2} />
        <InitialView count={levels.length + (narrow ? 1000 : 0)} focusIds={focusIds} />
        <ResetViewButton focusIds={focusIds} />
      </ReactFlow>
    </div>
  );
}
