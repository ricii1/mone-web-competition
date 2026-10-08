"use client";

import { useParams } from "next/navigation";
import LevelPlayer from "@/components/LevelPlayer";

export default function StudentLevelPage() {
  const { classId, levelId } = useParams<{ classId: string; levelId: string }>();
  return <LevelPlayer classId={classId} levelId={levelId} mode="student" />;
}
