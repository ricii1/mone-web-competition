"use client";

import Link from "next/link";
import PageShell from "@/components/PageShell";
import { useParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { ApiError, api } from "@/lib/api";
import { CheckIcon, ClockIcon, EyeIcon, LightbulbIcon, MapIcon, PencilIcon, PlusIcon, ScrollIcon, TrashIcon } from "@/components/icons";
import Markdown from "@/components/Markdown";
import { countWords, formatSource, readMinutes } from "@/lib/levels";
import { useClassTitle } from "@/lib/useClassTitle";
import type { Level, Question } from "@/lib/types";

type Tab = "material" | "questions";

function errMsg(err: unknown, fallback: string): string {
  return err instanceof ApiError ? err.message : fallback;
}

export default function TeacherLevelPage() {
  const { classId, levelId } = useParams<{ classId: string; levelId: string }>();
  const classTitle = useClassTitle(classId);
  const backLabel = classTitle ? `Kembali ke ${classTitle}` : "Kembali ke class";
  const [level, setLevel] = useState<Level | null>(null);
  const [questions, setQuestions] = useState<Question[]>([]);
  const [tab, setTab] = useState<Tab>("material");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [headerError, setHeaderError] = useState<string | null>(null);

  const [title, setTitle] = useState("");
  const [content, setContent] = useState("");
  const [showPreview, setShowPreview] = useState(false);
  const [summary, setSummary] = useState("");
  const [keyPoints, setKeyPoints] = useState<string[]>([]);
  const [sourceNote, setSourceNote] = useState("");
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);

  const applyLevel = useCallback((l: Level) => {
    setLevel(l);
    setTitle(l.title);
    setContent(l.content ?? "");
    setSummary(l.summary ?? "");
    setKeyPoints(l.key_points ?? []);
    setSourceNote(l.source_note ?? "");
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
      .catch((err) => setError(errMsg(err, "Level belum bisa dimuat. Coba lagi ya.")))
      .finally(() => setLoading(false));
  }, [classId, levelId, applyLevel]);

  useEffect(() => {
    if (window.location.hash === "#soal") setTab("questions");
  }, []);

  function selectTab(next: Tab) {
    setTab(next);
    window.history.replaceState(null, "", next === "questions" ? "#soal" : "#materi");
  }

  async function saveSummary() {
    setSaving(true);
    setSaved(false);
    setSaveError(null);
    try {
      const updated = await api.updateLevel(levelId, {
        title: title.trim(),
        content,
        summary,
        key_points: keyPoints.map((p) => p.trim()).filter(Boolean),
        source_note: sourceNote,
      });
      applyLevel(updated);
      setSaved(true);
    } catch (err) {
      setSaveError(errMsg(err, "Belum tersimpan. Coba lagi ya."));
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
      setHeaderError(errMsg(err, "Status level belum bisa diubah."));
    }
  }

  if (loading) {
    return (
      <PageShell back={{ href: `/teacher/classes/${classId}`, label: backLabel }}>
        <p role="status" className="text-ink/75">Memuat level...</p>
      </PageShell>
    );
  }
  if (error || !level) {
    return (
      <PageShell back={{ href: `/teacher/classes/${classId}`, label: backLabel }}>
        <p role="alert" className="note border-coral bg-coral-soft text-alert">{error ?? "Level tidak ditemukan"}</p>
      </PageShell>
    );
  }

  const words = countWords(content);
  const wordWarning =
    content.trim() === ""
      ? null
      : words < 250
        ? "Artikel agak pendek. Sekitar 450 sampai 650 kata biasanya pas untuk murid SD."
        : words > 900
          ? "Artikel cukup panjang. Coba dipersingkat agar murid tidak bosan."
          : null;
  const approvedCount = questions.filter((q) => q.status === "approved").length;

  return (
    <PageShell
      back={{ href: `/teacher/classes/${classId}`, label: backLabel }}
    >
      <div className="surface mb-6">
        <label htmlFor="level-title" className="field-label">
          Nama level
        </label>
        <input
          id="level-title"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          className="input-box mb-3 font-display text-xl"
        />
        <div className="flex flex-wrap items-center gap-2">
          <span className={level.type === "boss" ? "badge-grape" : "badge"}>
            {level.type === "boss" ? "Level bos" : "Level belajar"}
          </span>
          <span className={level.status === "approved" ? "badge-success" : "badge"}>
            {level.status === "approved" ? "Disetujui" : "Draft"}
          </span>
          <button
            onClick={toggleApprove}
            className={`${level.status === "approved" ? "btn-ghost" : "btn-primary"} btn-sm`}
          >
            {level.status === "approved" ? <>Batalkan persetujuan</> : <><CheckIcon size={20} />Setujui level</>}
          </button>
          <Link href={`/teacher/classes/${classId}/levels/${levelId}/preview`} className="btn-ghost btn-sm">
            <MapIcon size={20} />
            Lihat seperti murid
          </Link>
        </div>
        {headerError && (
          <p role="alert" className="mt-2 text-alert">
            {headerError}
          </p>
        )}
      </div>

      <div role="tablist" className="mb-6 flex gap-2 border-b-4 border-rule">
        {(
          [
            ["material", "Materi"],
            ["questions", "Soal"],
          ] as const
        ).map(([key, label]) => (
          <button
            key={key}
            role="tab"
            id={`tab-${key}`}
            aria-selected={tab === key}
            aria-controls={`panel-${key}`}
            tabIndex={tab === key ? 0 : -1}
            onKeyDown={(event) => {
              let next: Tab;
              if (event.key === "ArrowRight" || event.key === "ArrowLeft") next = key === "material" ? "questions" : "material";
              else if (event.key === "Home") next = "material";
              else if (event.key === "End") next = "questions";
              else return;
              event.preventDefault();
              selectTab(next);
              document.getElementById(`tab-${next}`)?.focus();
            }}
            onClick={() => selectTab(key)}
            className={`-mb-1 min-h-[48px] border-b-4 px-4 font-display text-lg font-bold ${
              tab === key ? "border-sky-dark text-sky-dark" : "border-transparent text-ink/75 hover:text-ink"
            }`}
          >
            {label}
          </button>
        ))}
      </div>

      {tab === "material" ? (
        <section role="tabpanel" id="panel-material" aria-labelledby="tab-material" className="flex flex-col gap-6">
          <div className="surface flex flex-col gap-6">
          <div>
            <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
              <label htmlFor="level-content" className="field-label flex items-center gap-2">
                <PencilIcon size={20} />
                Artikel materi
              </label>
              <button
                type="button"
                onClick={() => setShowPreview((v) => !v)}
                aria-pressed={showPreview}
                className="btn-ghost btn-sm"
              >
                <EyeIcon size={20} />
                {showPreview ? "Kembali menulis" : "Pratinjau"}
              </button>
            </div>
            <p id="content-hint" className="mb-2 text-base text-ink/75">
              Tips menulis: <code className="rounded bg-ink/10 px-1">###</code> untuk subjudul,{" "}
              <code className="rounded bg-ink/10 px-1">-</code> untuk daftar,{" "}
              <code className="rounded bg-ink/10 px-1">**tebal**</code> untuk huruf tebal.
            </p>
            {showPreview ? (
              <div className="min-h-[200px] rounded-2xl border-2 border-dashed border-sky bg-sky-soft/40 p-4 sm:p-6">
                {content.trim() ? (
                  <Markdown source={content} />
                ) : (
                  <p className="text-ink/75">Artikel masih kosong. Tulis dulu, lalu lihat pratinjaunya di sini.</p>
                )}
              </div>
            ) : (
              <textarea
                id="level-content"
                rows={22}
                value={content}
                onChange={(e) => setContent(e.target.value)}
                aria-describedby="content-hint"
                className="input-box leading-relaxed"
              />
            )}
            <p
              className={`mt-2 flex items-center gap-2 font-bold ${wordWarning ? "text-alert" : "text-ink/80"}`}
              role="status"
            >
              <ClockIcon size={20} />
              {words} kata, ± {readMinutes(words)} menit baca
            </p>
            {wordWarning && <p className="text-base text-alert">{wordWarning}</p>}
          </div>

          <div>
            <label htmlFor="level-summary" className="field-label flex items-center gap-2">
              <ScrollIcon size={20} />
              Rangkuman
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
            <p className="field-label flex items-center gap-2"><LightbulbIcon size={20} />Poin penting</p>
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
                    className="btn-danger btn-sm"
                    aria-label={`Hapus poin ${i + 1}`}
                  >
                    <TrashIcon size={20} />
                    <span className="hidden sm:inline">Hapus</span>
                  </button>
                </li>
              ))}
              {keyPoints.length === 0 && <li className="text-ink/75">Belum ada poin penting.</li>}
            </ul>
            {keyPoints.length < 8 && (
              <button onClick={() => setKeyPoints((pts) => [...pts, ""])} className="btn-ghost mt-3 btn-sm">
                <PlusIcon size={20} />
                Tambah poin
              </button>
            )}
          </div>

          </div>

          <div className="surface">
            <p className="field-label flex items-center gap-2"><ScrollIcon size={20} />Sumber</p>
            <label htmlFor="level-source" className="sr-only">
              Sumber materi
            </label>
            <textarea
              id="level-source"
              rows={3}
              maxLength={1000}
              value={sourceNote}
              onChange={(e) => setSourceNote(e.target.value)}
              placeholder="Contoh: Buku IPA Kelas 4, bab Siklus Air, hal. 12-15"
              aria-describedby="source-hint"
              className="input-box"
            />
            <p id="source-hint" className="mt-2 text-base text-ink/75">
              Tulis dari mana materi ini berasal. Bebas, boleh nama buku, bab, atau halaman.
            </p>
            {level.sources.length > 0 && (
              <details className="mt-3">
                <summary className="cursor-pointer font-bold text-ink/80">
                  Bagian PDF yang dipakai AI ({level.sources.length})
                </summary>
                <ul className="mt-2 list-disc pl-5 text-ink/80">
                  {level.sources.map((s, i) => (
                    <li key={i}>{formatSource(s)}</li>
                  ))}
                </ul>
              </details>
            )}
          </div>

          {/* Sticky so Simpan stays reachable while scrolling a long article. */}
          <div className="surface sticky bottom-3 z-20 flex flex-wrap items-center gap-3">
            <button onClick={saveSummary} disabled={saving || !title.trim()} className="btn-primary">
              <CheckIcon size={22} />
              {saving ? "Menyimpan..." : "Simpan"}
            </button>
            {saved && (
              <span role="status" className="font-bold text-correct-dark">
                Sudah tersimpan
              </span>
            )}
            {saveError && (
              <span role="alert" className="font-bold text-alert">
                {saveError}
              </span>
            )}
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
      setError(errMsg(err, "Status soal belum bisa diubah."));
    }
  }

  async function remove(q: Question) {
    setError(null);
    try {
      await api.deleteQuestion(q.id);
      setConfirmId(null);
      await reload();
    } catch (err) {
      setError(errMsg(err, "Soal belum bisa dihapus."));
    }
  }

  return (
    <div>
      <p className="mb-4 text-base font-bold text-ink/80">
        {approvedCount} dari {questions.length} soal sudah disetujui
      </p>
      {error && (
        <p role="alert" className="mb-4 text-alert">
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
              <ul className="mb-3 flex flex-col gap-1">
                {q.options.map((opt, i) => (
                  <li key={i} className={opt === q.correct_answer ? "font-semibold text-correct-dark" : "text-ink/80"}>
                    {opt}
                  </li>
                ))}
              </ul>
              {q.explanation && <p className="mb-3 text-ink/75">{q.explanation}</p>}
              <div className="flex flex-wrap items-center gap-2">
                <span className={q.status === "approved" ? "badge-success" : "badge"}>
                  {q.status === "approved" ? "Disetujui" : "Draft"}
                </span>
                <button onClick={() => toggle(q)} className="btn-primary btn-sm">
                  {q.status === "approved" ? "Batalkan persetujuan" : "Setujui"}
                </button>
                <button onClick={() => setEditingId(q.id)} className="btn-ghost btn-sm">
                  <PencilIcon size={20} />
                  Ubah
                </button>
                {confirmId === q.id ? (
                  <span className="flex flex-wrap items-center gap-2 text-base">
                    Hapus soal ini?
                    <button onClick={() => remove(q)} className="btn-danger btn-sm">
                      Ya, hapus
                    </button>
                    <button onClick={() => setConfirmId(null)} className="btn-ghost btn-sm">
                      Batal
                    </button>
                  </span>
                ) : (
                  <button onClick={() => setConfirmId(q.id)} className="btn-danger btn-sm">
                    <TrashIcon size={20} />
                    Hapus
                  </button>
                )}
              </div>
            </li>
          )
        )}
        {questions.length === 0 && <li className="text-ink/75">Belum ada soal.</li>}
      </ul>

      <div className="mt-6">
        {adding ? (
          <div className="card">
            <h2 className="mb-3 text-xl">Tambah soal sendiri</h2>
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
            <PlusIcon size={22} />
            Tambah soal sendiri
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
      setError(errMsg(err, "Soal belum tersimpan. Coba lagi ya."));
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
        <legend className="field-label">Pilihan jawaban (tandai yang benar)</legend>
        <div className="flex flex-col gap-2">
          {options.map((opt, i) => (
            <div key={i} className="flex items-center gap-2">
              <input
                type="radio"
                name={`correct-${initial?.id ?? "new"}`}
                checked={correctIndex === i}
                onChange={() => setCorrectIndex(i)}
                aria-label={`Pilihan ${i + 1} adalah jawaban benar`}
                className="h-6 w-6 accent-sky-dark"
              />
              <input
                aria-label={`Pilihan ${i + 1}`}
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
        <button onClick={submit} disabled={busy || !valid} className="btn-primary btn-sm">
          {busy ? "Menyimpan..." : submitLabel}
        </button>
        <button onClick={onCancel} className="btn-ghost btn-sm">
          Batal
        </button>
      </div>
    </div>
  );
}
