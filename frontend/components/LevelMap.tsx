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

function LevelNode({
  data,
}: NodeProps<Node<{ label: string; status: string; type: string; teacher: boolean }>>) {
  const palette = data.teacher ? TEACHER_STATUS_STYLE : STATUS_STYLE;
  const style = palette[data.status] ?? palette.draft ?? STATUS_STYLE.locked;
  return (
    <div
      className="node-appear rounded-sm border-2 px-4 py-2 text-center font-sans text-sm font-medium"
      style={{
        background: style.bg,
        color: style.text,
        borderColor: data.type === "boss" ? "#B23A2E" : "transparent",
      }}
    >
      <Handle type="target" position={Position.Top} />
      {data.label}
      <Handle type="source" position={Position.Bottom} />
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
}: {
  classId: string;
  levels: Level[];
  progress?: Progress[];
  teacher?: boolean;
}) {
  const router = useRouter();
  const statusByLevel = useMemo(() => {
    const map = new Map(progress.map((p) => [p.level_id, p.status]));
    return (levelId: string) => map.get(levelId) ?? "locked";
  }, [progress]);

  const nodes: Node[] = levels.map((l, i) => ({
    id: l.id,
    type: "level",
    position: { x: (i % 3) * 200, y: Math.floor(i / 3) * 120 },
    data: { label: l.title, status: teacher ? l.status : statusByLevel(l.id), type: l.type, teacher },
  }));

  const edges: Edge[] = levels
    .filter((l) => l.prerequisite_id)
    .map((l) => ({
      id: `${l.prerequisite_id}-${l.id}`,
      source: l.prerequisite_id as string,
      target: l.id,
      style: { stroke: "#1B2A41", strokeWidth: 2, strokeDasharray: "1 7", opacity: 0.4 },
    }));

  return (
    <div className="card overflow-hidden p-0" style={{ height: teacher ? "50vh" : "70vh" }}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        fitView
        fitViewOptions={{ maxZoom: 1 }}
        onNodeClick={(_, node) => {
          if (teacher) {
            router.push(`/teacher/classes/${classId}/levels/${node.id}`);
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
