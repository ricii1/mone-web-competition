"use client";

import PageShell from "@/components/PageShell";
import { useParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { ApiError, api } from "@/lib/api";
import { formatSource } from "@/lib/levels";
import type { Level, Question } from "@/lib/types";

type Tab = "summary" | "questions";

function errMsg(err: unknown, fallback: string): string {
  return err instanceof ApiError ? err.message : fallback;
}

export default function TeacherLevelPage() {
  const { classId, levelId } = useParams<{ classId: string; levelId: string }>();
  const [level, setLevel] = useState<Level | null>(null);
  const [questions, setQuestions] = useState<Question[]>([]);
  const [tab, setTab] = useState<Tab>("summary");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [headerError, setHeaderError] = useState<string | null>(null);

  const [title, setTitle] = useState("");
  const [summary, setSummary] = useState("");
  const [keyPoints, setKeyPoints] = useState<string[]>([]);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);

  const applyLevel = useCallback((l: Level) => {
    setLevel(l);
    setTitle(l.title);
    setSummary(l.summary ?? "");
    setKeyPoints(l.key_points ?? []);
  }, []);

  const loadQuestions = useCallback(async () => {
    setQuestions(await api.listQuestions(levelId));
  }, [levelId]);

  useEffect(() => {
    Promise.all([api.listLevels(classId), api.listQuestions(levelId)])
      .then(([levels, qs]) => {
        const found = levels.find((l) => l.id === levelId);
        if (!found) {
          setError("Level tidak ditemukan");
          return;
        }
        applyLevel(found);
        setQuestions(qs);
      })
      .catch((err) => setError(errMsg(err, "Gagal memuat level")))
      .finally(() => setLoading(false));
  }, [classId, levelId, applyLevel]);

  useEffect(() => {
    if (window.location.hash === "#soal") setTab("questions");
  }, []);

  function selectTab(next: Tab) {
    setTab(next);
    window.history.replaceState(null, "", next === "questions" ? "#soal" : "#rangkuman");
  }

  async function saveSummary() {
    setSaving(true);
    setSaved(false);
    setSaveError(null);
    try {
      const updated = await api.updateLevel(levelId, {
        title: title.trim(),
        summary,
        key_points: keyPoints.map((p) => p.trim()).filter(Boolean),
      });
      applyLevel(updated);
      setSaved(true);
    } catch (err) {
      setSaveError(errMsg(err, "Gagal menyimpan"));
    } finally {
      setSaving(false);
    }
  }

  async function toggleApprove() {
    if (!level) return;
    setHeaderError(null);
    try {
      const updated = await api.updateLevel(levelId, {
        status: level.status === "approved" ? "draft" : "approved",
      });
      setLevel((prev) => (prev ? { ...prev, status: updated.status } : prev));
    } catch (err) {
      setHeaderError(errMsg(err, "Gagal mengubah status level"));
    }
  }

  if (loading) {
    return (
      <PageShell back={{ href: `/teacher/classes/${classId}`, label: "Kembali ke class" }}>
        <p className="text-sm text-ink/60">Memuat level...</p>
      </PageShell>
    );
  }
  if (error || !level) {
    return (
      <PageShell back={{ href: `/teacher/classes/${classId}`, label: "Kembali ke class" }}>
        <p className="text-sm text-alert">{error ?? "Level tidak ditemukan"}</p>
      </PageShell>
    );
  }

  const approvedCount = questions.filter((q) => q.status === "approved").length;

  return (
    <PageShell
      back={{ href: `/teacher/classes/${classId}`, label: "Kembali ke class" }}
      crumbs={[
        { label: "Class saya", href: "/teacher" },
        { label: "Class", href: `/teacher/classes/${classId}` },
        { label: level.title },
      ]}
    >
      <div className="surface mb-6">
        <label htmlFor="level-title" className="field-label">
          Judul level
        </label>
        <input
          id="level-title"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          className="input-box mb-3 font-display text-xl"
        />
        <div className="flex flex-wrap items-center gap-2 text-xs">
          <span className={level.type === "boss" ? "badge-alert" : "badge"}>
            {level.type === "boss" ? "Boss" : "Lesson"}
          </span>
          <span className={level.status === "approved" ? "badge-success" : "badge"}>
            {level.status === "approved" ? "Approved" : "Draft"}
          </span>
          <button
            onClick={toggleApprove}
            className={`${level.status === "approved" ? "btn-ghost" : "btn-primary"} px-3 py-1 text-xs`}
          >
            {level.status === "approved" ? "Batalkan approve" : "Approve level"}
          </button>
        </div>
        {headerError && (
          <p role="alert" className="mt-2 text-sm text-alert">
            {headerError}
          </p>
        )}
      </div>

      <div role="tablist" className="mb-6 flex gap-4 border-b border-ink/15">
        {(
          [
            ["summary", "Rangkuman"],
            ["questions", "Soal"],
          ] as const
        ).map(([key, label]) => (
          <button
            key={key}
            role="tab"
            id={`tab-${key}`}
            aria-selected={tab === key}
            aria-controls={`panel-${key}`}
            onClick={() => selectTab(key)}
            className={`-mb-px min-h-[44px] border-b-2 px-2 text-sm ${
              tab === key ? "border-highlight font-semibold" : "border-transparent text-ink/65 hover:text-ink"
            }`}
          >
            {label}
          </button>
        ))}
      </div>

      {tab === "summary" ? (
        <section role="tabpanel" id="panel-summary" aria-labelledby="tab-summary" className="grid gap-6 lg:grid-cols-[minmax(0,3fr)_minmax(0,2fr)] lg:items-start">
          <div className="surface flex flex-col gap-6">
          <div>
            <label htmlFor="level-summary" className="field-label">
              Ringkasan materi
            </label>
            <textarea
              id="level-summary"
              rows={8}
              value={summary}
              onChange={(e) => setSummary(e.target.value)}
              className="input-box"
            />
          </div>

          <div>
            <p className="field-label">Poin penting</p>
            <ul className="flex flex-col gap-2">
              {keyPoints.map((point, i) => (
                <li key={i} className="flex gap-2">
                  <input
                    aria-label={`Poin penting ${i + 1}`}
                    value={point}
                    onChange={(e) => setKeyPoints((pts) => pts.map((p, j) => (j === i ? e.target.value : p)))}
                    className="input-box min-w-0 flex-1"
                  />
                  <button
                    onClick={() => setKeyPoints((pts) => pts.filter((_, j) => j !== i))}
                    className="btn-danger px-3 py-1 text-xs"
                    aria-label={`Hapus poin ${i + 1}`}
                  >
                    Hapus
                  </button>
                </li>
              ))}
              {keyPoints.length === 0 && <li className="text-sm text-ink/60">Belum ada poin penting.</li>}
            </ul>
            {keyPoints.length < 8 && (
              <button onClick={() => setKeyPoints((pts) => [...pts, ""])} className="btn-ghost mt-3 px-3 py-1 text-xs">
                Tambah poin
              </button>
            )}
          </div>

          </div>

          <div className="flex flex-col gap-6 lg:sticky lg:top-20">
          <div className="surface">
            <p className="field-label">Sumber materi</p>
            {level.sources.length > 0 ? (
              <ul className="list-disc pl-5 text-sm text-ink/80">
                {level.sources.map((s, i) => (
                  <li key={i}>{formatSource(s)}</li>
                ))}
              </ul>
            ) : (
              <p className="text-sm text-ink/60">Belum ada sumber.</p>
            )}
          </div>

          <div className="surface flex flex-wrap items-center gap-3">
            <button onClick={saveSummary} disabled={saving || !title.trim()} className="btn-primary">
              {saving ? "Menyimpan..." : "Simpan"}
            </button>
            {saved && (
              <span role="status" className="text-sm text-correct">
                Tersimpan
              </span>
            )}
            {saveError && (
              <span role="alert" className="text-sm text-alert">
                {saveError}
              </span>
            )}
          </div>
          </div>
        </section>
      ) : (
        <section role="tabpanel" id="panel-questions" aria-labelledby="tab-questions" className="mx-auto max-w-3xl">
          <QuestionsPanel
            levelId={levelId}
            questions={questions}
            approvedCount={approvedCount}
            reload={loadQuestions}
          />
        </section>
      )}
    </PageShell>
  );
}

interface QuestionsPanelProps {
  levelId: string;
  questions: Question[];
  approvedCount: number;
  reload: () => Promise<void>;
}

function QuestionsPanel({ levelId, questions, approvedCount, reload }: QuestionsPanelProps) {
  const [error, setError] = useState<string | null>(null);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [confirmId, setConfirmId] = useState<string | null>(null);
  const [adding, setAdding] = useState(false);

  async function toggle(q: Question) {
    setError(null);
    try {
      await api.updateQuestion(q.id, { status: q.status === "approved" ? "draft" : "approved" });
      await reload();
    } catch (err) {
      setError(errMsg(err, "Gagal mengubah status soal"));
    }
  }

  async function remove(q: Question) {
    setError(null);
    try {
      await api.deleteQuestion(q.id);
      setConfirmId(null);
      await reload();
    } catch (err) {
      setError(errMsg(err, "Gagal menghapus soal"));
    }
  }

  return (
    <div>
      <p className="mb-4 text-sm text-ink/70">
        {approvedCount} dari {questions.length} soal approved
      </p>
      {error && (
        <p role="alert" className="mb-4 text-sm text-alert">
          {error}
        </p>
      )}
      <ul className="flex flex-col gap-4">
        {questions.map((q) =>
          editingId === q.id ? (
            <li key={q.id} className="card">
              <QuestionForm
                initial={q}
                submitLabel="Simpan soal"
                onCancel={() => setEditingId(null)}
                onSubmit={async (v) => {
                  await api.updateQuestion(q.id, v);
                  setEditingId(null);
                  await reload();
                }}
              />
            </li>
          ) : (
            <li key={q.id} className="card">
              <p className="mb-3 font-medium">{q.question_text}</p>
              <ul className="mb-3 flex flex-col gap-1 text-sm">
                {q.options.map((opt, i) => (
                  <li key={i} className={opt === q.correct_answer ? "font-semibold text-correct" : "text-ink/80"}>
                    {opt}
                  </li>
                ))}
              </ul>
              {q.explanation && <p className="mb-3 text-sm text-ink/60">{q.explanation}</p>}
              <div className="flex flex-wrap items-center gap-2">
                <span className={q.status === "approved" ? "badge-success" : "badge"}>
                  {q.status === "approved" ? "Approved" : "Draft"}
                </span>
                <button onClick={() => toggle(q)} className="btn-primary px-3 py-1 text-xs">
                  {q.status === "approved" ? "Batalkan approve" : "Approve"}
                </button>
                <button onClick={() => setEditingId(q.id)} className="btn-ghost px-3 py-1 text-xs">
                  Edit
                </button>
                {confirmId === q.id ? (
                  <span className="flex items-center gap-2 text-xs">
                    Hapus soal ini?
                    <button onClick={() => remove(q)} className="btn-danger px-3 py-1 text-xs">
                      Ya, hapus
                    </button>
                    <button onClick={() => setConfirmId(null)} className="btn-ghost px-3 py-1 text-xs">
                      Batal
                    </button>
                  </span>
                ) : (
                  <button onClick={() => setConfirmId(q.id)} className="btn-danger px-3 py-1 text-xs">
                    Hapus
                  </button>
                )}
              </div>
            </li>
          )
        )}
        {questions.length === 0 && <li className="text-sm text-ink/60">Belum ada soal.</li>}
      </ul>

      <div className="mt-6">
        {adding ? (
          <div className="card">
            <h2 className="mb-3 font-display text-lg">Tambah soal manual</h2>
            <QuestionForm
              submitLabel="Tambah soal"
              onCancel={() => setAdding(false)}
              onSubmit={async (v) => {
                await api.createQuestion(levelId, {
                  question_text: v.question_text,
                  options: v.options,
                  correct_answer: v.correct_answer,
                  explanation: v.explanation || undefined,
                });
                setAdding(false);
                await reload();
              }}
            />
          </div>
        ) : (
          <button onClick={() => setAdding(true)} className="btn-ghost">
            Tambah soal manual
          </button>
        )}
      </div>
    </div>
  );
}

interface QuestionFormValues {
  question_text: string;
  options: string[];
  correct_answer: string;
  explanation: string;
}

interface QuestionFormProps {
  initial?: Question;
  submitLabel: string;
  onSubmit: (values: QuestionFormValues) => Promise<void>;
  onCancel: () => void;
}

function QuestionForm({ initial, submitLabel, onSubmit, onCancel }: QuestionFormProps) {
  const initialOptions = initial ? [...initial.options] : [];
  while (initialOptions.length < 4) initialOptions.push("");
  const [text, setText] = useState(initial?.question_text ?? "");
  const [options, setOptions] = useState<string[]>(initialOptions);
  const [correctIndex, setCorrectIndex] = useState(() => {
    const idx = initial ? initial.options.indexOf(initial.correct_answer ?? "") : -1;
    return idx >= 0 ? idx : 0;
  });
  const [explanation, setExplanation] = useState(initial?.explanation ?? "");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const valid = text.trim() !== "" && options.every((o) => o.trim() !== "");

  async function submit() {
    setBusy(true);
    setError(null);
    try {
      const cleaned = options.map((o) => o.trim());
      await onSubmit({
        question_text: text.trim(),
        options: cleaned,
        correct_answer: cleaned[correctIndex],
        explanation: explanation.trim(),
      });
    } catch (err) {
      setError(errMsg(err, "Gagal menyimpan soal"));
      setBusy(false);
    }
  }

  return (
    <div className="flex flex-col gap-3">
      <div>
        <label className="field-label">Pertanyaan</label>
        <textarea rows={3} value={text} onChange={(e) => setText(e.target.value)} className="input-box" />
      </div>
      <fieldset>
        <legend className="field-label">Opsi jawaban (pilih yang benar)</legend>
        <div className="flex flex-col gap-2">
          {options.map((opt, i) => (
            <div key={i} className="flex items-center gap-2">
              <input
                type="radio"
                name={`correct-${initial?.id ?? "new"}`}
                checked={correctIndex === i}
                onChange={() => setCorrectIndex(i)}
                aria-label={`Opsi ${i + 1} adalah jawaban benar`}
                className="accent-highlight"
              />
              <input
                aria-label={`Opsi ${i + 1}`}
                value={opt}
                onChange={(e) => setOptions((os) => os.map((o, j) => (j === i ? e.target.value : o)))}
                className="input-box min-w-0 flex-1"
              />
            </div>
          ))}
        </div>
      </fieldset>
      <div>
        <label className="field-label">Pembahasan</label>
        <textarea rows={2} value={explanation} onChange={(e) => setExplanation(e.target.value)} className="input-box" />
      </div>
      {error && (
        <p role="alert" className="text-sm text-alert">
          {error}
        </p>
      )}
      <div className="flex gap-2">
        <button onClick={submit} disabled={busy || !valid} className="btn-primary px-4 py-2 text-sm">
          {busy ? "Menyimpan..." : submitLabel}
        </button>
        <button onClick={onCancel} className="btn-ghost px-4 py-2 text-sm">
          Batal
        </button>
      </div>
    </div>
  );
}
