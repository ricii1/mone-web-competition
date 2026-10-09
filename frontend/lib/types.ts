export type UserRole = "teacher" | "student";

export interface User {
  id: string;
  name: string;
  email: string;
  role: UserRole;
}

export type ClassVisibility = "public" | "private";
export type ClassStatus = "draft" | "published";

export type GenerationStatus = "idle" | "generating" | "done" | "failed";

export interface SchoolClass {
  id: string;
  teacher_id: string;
  title: string;
  description: string | null;
  visibility: ClassVisibility;
  status: ClassStatus;
  invite_code: string | null;
  is_example: boolean;
  generation_status: GenerationStatus;
  generation_error: string | null;
}

export type VectorStatus = "pending" | "processing" | "ready" | "failed";

export interface Material {
  id: string;
  class_id: string;
  file_name: string;
  vector_status: VectorStatus;
  error_message: string | null;
}

export type LevelType = "lesson_quiz" | "boss";
export type LevelStatus = "draft" | "approved";

export interface LevelSource {
  chunk_id: string;
  section_title: string | null;
  page_start: number;
  page_end: number;
}

/** A material section a teacher can pick as a level source. */
export interface ChunkOption extends Omit<LevelSource, "chunk_id"> {
  id: string;
  material_name: string;
}

export interface Level {
  id: string;
  class_id: string;
  prerequisite_id: string | null;
  title: string;
  type: LevelType;
  order_index: number;
  summary: string | null;
  content: string | null;
  key_points: string[];
  sources: LevelSource[];
  status: LevelStatus;
}

export type QuestionStatus = "draft" | "approved";

export interface Question {
  id: string;
  level_id: string;
  question_text: string;
  question_type: "multiple_choice";
  options: string[];
  explanation: string | null;
  status: QuestionStatus;
  correct_answer?: string;
}

export type ProgressStatus = "locked" | "unlocked" | "completed";

export interface Progress {
  level_id: string;
  status: ProgressStatus;
  best_score: number;
}

export interface QuizQuestionResult {
  question_id: string;
  your_answer: string | null;
  is_correct: boolean;
  correct_answer: string;
  explanation: string | null;
}

export interface QuizSubmitResult {
  score_percent: number;
  passed: boolean;
  correct_count: number;
  total_count: number;
  results: QuizQuestionResult[];
}

export interface LeaderboardEntry {
  rank: number;
  user_id: string;
  name: string;
  score: number;
}

export type LiveSessionStatus = "waiting" | "running" | "finished";

export interface LiveSession {
  id: string;
  class_id: string;
  level_id: string;
  host_id: string;
  join_code: string;
  status: LiveSessionStatus;
  current_question_index: number;
}

