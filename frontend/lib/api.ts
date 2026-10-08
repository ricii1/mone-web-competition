import { getToken } from "./auth";
import type {
  LeaderboardEntry,
  Level,
  LiveSession,
  Material,
  Progress,
  Question,
  QuizSubmitResult,
  SchoolClass,
  User,
  UserRole,
} from "./types";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

class ApiError extends Error {
  constructor(
    public status: number,
    message: string
  ) {
    super(message);
  }
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(init.headers as Record<string, string> | undefined),
  };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(`${API_URL}${path}`, { ...init, headers });
  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }));
    throw new ApiError(res.status, body.detail ?? "Terjadi kesalahan");
  }
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

async function uploadFile<T>(path: string, file: File): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {};
  if (token) headers["Authorization"] = `Bearer ${token}`;
  const formData = new FormData();
  formData.append("file", file);

  const res = await fetch(`${API_URL}${path}`, { method: "POST", headers, body: formData });
  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }));
    throw new ApiError(res.status, body.detail ?? "Terjadi kesalahan");
  }
  return res.json() as Promise<T>;
}

export const api = {
  register: (name: string, email: string, password: string, role: UserRole) =>
    request<{ access_token: string }>("/api/v1/auth/register", {
      method: "POST",
      body: JSON.stringify({ name, email, password, role }),
    }),
  login: (email: string, password: string) =>
    request<{ access_token: string }>("/api/v1/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),
  me: () => request<User>("/api/v1/auth/me"),

  listClasses: () => request<SchoolClass[]>("/api/v1/classes"),
  listEnrolledClasses: () => request<SchoolClass[]>("/api/v1/classes/enrolled"),
  listOwnedClasses: () => request<SchoolClass[]>("/api/v1/classes/mine"),
  getClass: (classId: string) => request<SchoolClass>(`/api/v1/classes/${classId}`),
  createClass: (title: string, description: string, visibility: "public" | "private") =>
    request<SchoolClass>("/api/v1/classes", {
      method: "POST",
      body: JSON.stringify({ title, description, visibility }),
    }),
  publishClass: (classId: string) =>
    request<SchoolClass>(`/api/v1/classes/${classId}/publish`, { method: "POST" }),
  joinClass: (classId: string, inviteCode?: string) =>
    request<void>(`/api/v1/classes/${classId}/join`, {
      method: "POST",
      body: JSON.stringify({ invite_code: inviteCode ?? null }),
    }),

  listMaterials: (classId: string) => request<Material[]>(`/api/v1/classes/${classId}/materials`),
  uploadMaterial: (classId: string, file: File) =>
    uploadFile<Material>(`/api/v1/classes/${classId}/materials`, file),

  generateLevels: (classId: string) =>
    request<{ status: string }>(`/api/v1/classes/${classId}/levels/generate`, { method: "POST" }),
  listLevels: (classId: string) => request<Level[]>(`/api/v1/classes/${classId}/levels`),
  updateLevel: (levelId: string, body: Partial<Omit<Level, "sources">> & { clear_prerequisite?: boolean }) =>
    request<Level>(`/api/v1/levels/${levelId}`, { method: "PATCH", body: JSON.stringify(body) }),
  deleteLevel: (levelId: string) =>
    request<void>(`/api/v1/levels/${levelId}`, { method: "DELETE" }),

  listQuestions: (levelId: string) => request<Question[]>(`/api/v1/levels/${levelId}/questions`),
  createQuestion: (
    levelId: string,
    body: { question_text: string; options: string[]; correct_answer: string; explanation?: string }
  ) =>
    request<Question>(`/api/v1/levels/${levelId}/questions`, {
      method: "POST",
      body: JSON.stringify(body),
    }),
  updateQuestion: (questionId: string, body: Partial<Question>) =>
    request<Question>(`/api/v1/questions/${questionId}`, {
      method: "PATCH",
      body: JSON.stringify(body),
    }),
  deleteQuestion: (questionId: string) =>
    request<void>(`/api/v1/questions/${questionId}`, { method: "DELETE" }),
  submitQuiz: (levelId: string, answers: Record<string, string>) =>
    request<QuizSubmitResult>(`/api/v1/levels/${levelId}/submit`, {
      method: "POST",
      body: JSON.stringify({ answers }),
    }),

  getProgress: (classId: string) => request<Progress[]>(`/api/v1/classes/${classId}/progress`),
  getLeaderboard: (classId: string) =>
    request<LeaderboardEntry[]>(`/api/v1/classes/${classId}/leaderboard`),

  createLiveSession: (classId: string, levelId: string) =>
    request<LiveSession>(`/api/v1/classes/${classId}/live-sessions`, {
      method: "POST",
      body: JSON.stringify({ level_id: levelId }),
    }),
  getLiveSession: (sessionId: string) => request<LiveSession>(`/api/v1/live-sessions/${sessionId}`),
  lookupLiveSession: (joinCode: string) =>
    request<LiveSession>("/api/v1/live-sessions/lookup", {
      method: "POST",
      body: JSON.stringify({ join_code: joinCode }),
    }),
  joinLiveSession: (sessionId: string, joinCode: string) =>
    request<void>(`/api/v1/live-sessions/${sessionId}/join`, {
      method: "POST",
      body: JSON.stringify({ join_code: joinCode }),
    }),
  startLiveSession: (sessionId: string) =>
    request<void>(`/api/v1/live-sessions/${sessionId}/start`, { method: "POST" }),
  nextLiveQuestion: (sessionId: string) =>
    request<void>(`/api/v1/live-sessions/${sessionId}/next`, { method: "POST" }),
  endLiveSession: (sessionId: string) =>
    request<void>(`/api/v1/live-sessions/${sessionId}/end`, { method: "POST" }),
  answerLiveQuestion: (sessionId: string, questionId: string, answer: string) =>
    request<void>(`/api/v1/live-sessions/${sessionId}/answer`, {
      method: "POST",
      body: JSON.stringify({ question_id: questionId, answer }),
    }),
};

export { ApiError };
