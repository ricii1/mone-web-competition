"use client";

import { Background, Handle, Position, ReactFlow, type Edge, type Node, type NodeProps } from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { useRouter } from "next/navigation";
import { useMemo } from "react";
import type { Level, Progress } from "@/lib/types";

const STATUS_STYLE: Record<string, { bg: string; text: string }> = {
  locked: { bg: "#DCD5C2", text: "#1B2A41" },
  unlocked: { bg: "#E3A23C", text: "#1B2A41" },
  completed: { bg: "#3F7D58", text: "#F3EFE3" },
};

function LevelNode({ data }: NodeProps<Node<{ label: string; status: string; type: string }>>) {
  const style = STATUS_STYLE[data.status] ?? STATUS_STYLE.locked;
  return (
    <div
      className="rounded-sm border-2 px-4 py-2 text-center font-sans text-sm font-medium"
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

const nodeTypes = { level: LevelNode };

export default function LevelMap({
  classId,
  levels,
  progress,
}: {
  classId: string;
  levels: Level[];
  progress: Progress[];
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
    data: { label: l.title, status: statusByLevel(l.id), type: l.type },
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
    <div className="card overflow-hidden p-0" style={{ height: "70vh" }}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        fitView
        onNodeClick={(_, node) => {
          if (statusByLevel(node.id) !== "locked") {
            router.push(`/student/classes/${classId}/levels/${node.id}`);
          }
        }}
      >
        <Background color="#DCD5C2" />
      </ReactFlow>
    </div>
  );
}
