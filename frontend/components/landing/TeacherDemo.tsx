"use client";

import { useEffect, useState } from "react";
import { CheckIcon, FileIcon, PencilIcon, RocketIcon, SparklesIcon, UploadIcon } from "@/components/icons";
import Markdown from "@/components/Markdown";
import { DEMO_ARTICLE, DEMO_DRAFT_LEVELS, DEMO_TEACHER_QUESTION } from "./demoData";

type Stage = "upload" | "processing" | "review" | "published";

const PROCESS_STEPS = ["Membaca PDF", "Memecah materi", "Menyusun level"];
const STEP_MS = 900;
const LEVEL_MS = 700;

const SAMPLE_ARTICLES = [
  DEMO_ARTICLE,
  "### Awan menjadi hujan\n\nTitik-titik air di awan berkumpul. Saat makin berat, air jatuh ke bumi sebagai hujan. Air hujan mengisi sungai, danau, dan tanah.",
  "### Air kembali ke laut\n\nAir hujan mengalir melalui sungai menuju laut. Sebagian air meresap ke dalam tanah. Matahari dapat memanaskan air lagi sehingga siklus air terus berulang.",
];
const SAMPLE_QUESTIONS = [
  DEMO_TEACHER_QUESTION,
  { text: "Apa yang terjadi saat titik-titik air di awan makin berat?", options: ["Jatuh sebagai hujan", "Menjadi pasir", "Berubah menjadi matahari", "Berhenti bergerak"], correct: 0 },
  { text: "Ke mana air sungai mengalir?", options: ["Ke laut", "Ke matahari", "Ke bulan", "Ke awan langsung"], correct: 0 },
];

const STEP_LABELS = ["Unggah", "Cek draft", "Publish"];

export default function TeacherDemo() {
  const [stage, setStage] = useState<Stage>("upload");
  const [step, setStep] = useState(0);
  const [levelsShown, setLevelsShown] = useState(0);
  const [activeLevel, setActiveLevel] = useState(0);
  const [articles, setArticles] = useState(SAMPLE_ARTICLES);
  const [materialApprovals, setMaterialApprovals] = useState<boolean[]>([false, false, false]);
  const [questionApprovals, setQuestionApprovals] = useState<boolean[]>([false, false, false]);
  const article = articles[activeLevel];
  const approved = questionApprovals[activeLevel];
  const question = SAMPLE_QUESTIONS[activeLevel];
  const canPublish = materialApprovals.every(Boolean) && questionApprovals.every(Boolean);

  // Fake processing: advance through the stages with timers, then reveal draft levels one by one.
  useEffect(() => {
    if (stage !== "processing") return;
    const id = window.setInterval(() => {
      setStep((s) => {
        if (s < PROCESS_STEPS.length) return s + 1;
        return s;
      });
    }, STEP_MS);
    return () => window.clearInterval(id);
  }, [stage]);

  useEffect(() => {
    if (stage !== "processing" || step < PROCESS_STEPS.length) return;
    const id = window.setInterval(() => {
      setLevelsShown((n) => {
        if (n >= DEMO_DRAFT_LEVELS.length) return n;
        return n + 1;
      });
    }, LEVEL_MS);
    return () => window.clearInterval(id);
  }, [stage, step]);

  useEffect(() => {
    if (stage === "processing" && levelsShown >= DEMO_DRAFT_LEVELS.length) {
      const id = window.setTimeout(() => setStage("review"), 600);
      return () => window.clearTimeout(id);
    }
  }, [stage, levelsShown]);

  function start() {
    setStep(0);
    setLevelsShown(0);
    setStage("processing");
  }

  function reset() {
    setStage("upload");
    setStep(0);
    setLevelsShown(0);
    setActiveLevel(0);
    setArticles(SAMPLE_ARTICLES);
    setMaterialApprovals([false, false, false]);
    setQuestionApprovals([false, false, false]);
  }

  const current = stage === "upload" || stage === "processing" ? 0 : stage === "review" ? 1 : 2;

  return (
    <div className="kid" data-testid="teacher-demo" data-stage={stage}>
      <p className="note mb-4 border-sky bg-sky-soft text-sky-dark">
        <SparklesIcon size={22} />
        <span>Ini hanya contoh, belum menyimpan apa pun.</span>
      </p>

      <ol className="mb-5 flex flex-wrap gap-2" aria-label="Langkah guru">
        {STEP_LABELS.map((label, i) => (
          <li
            key={label}
            aria-current={i === current ? "step" : undefined}
            className={`inline-flex items-center gap-2 rounded-full px-3 py-1 text-sm font-bold ${
              i < current ? "bg-grass-soft text-correct-dark" : i === current ? "bg-highlight/50 text-ink" : "bg-ink/10 text-ink/70"
            }`}
          >
            <span className="flex h-6 w-6 items-center justify-center rounded-full bg-white text-xs">
              {i < current ? <CheckIcon size={14} /> : i + 1}
            </span>
            {label}
          </li>
        ))}
      </ol>

      {stage === "upload" && (
        <div className="rounded-3xl border-2 border-dashed border-rule bg-paper p-6 text-center">
          <FileIcon size={40} className="mx-auto text-sky-dark" />
          <p className="mt-2 font-display text-xl font-bold">Contoh - IPA Siklus Air.pdf</p>
          <p className="mb-4 text-base text-ink/80">Materi contoh sudah siap. Tidak ada file sungguhan yang diunggah.</p>
          <button type="button" className="btn-primary" onClick={start}>
            <UploadIcon size={22} />
            Unggah PDF
          </button>
        </div>
      )}

      {stage === "processing" && (
        <div aria-live="polite">
          <ul className="flex flex-col gap-2">
            {PROCESS_STEPS.map((label, i) => (
              <li key={label} className="flex items-center gap-3 font-bold">
                <span
                  className={`flex h-8 w-8 items-center justify-center rounded-full ${
                    i < step ? "bg-grass-dark text-white" : i === step ? "bg-highlight text-ink" : "bg-ink/10 text-ink/60"
                  }`}
                >
                  {i < step ? <CheckIcon size={18} /> : i + 1}
                </span>
                <span className={i > step ? "text-ink/60" : ""}>
                  {label}
                  {i === step && "..."}
                </span>
              </li>
            ))}
          </ul>
          {levelsShown > 0 && (
            <ul className="mt-4 flex flex-col gap-2" aria-label="Level yang dibuat AI">
              {DEMO_DRAFT_LEVELS.slice(0, levelsShown).map((l, i) => (
                <li key={l.title} className="card flex items-center gap-3 !p-3">
                  <span className="flex h-9 w-9 items-center justify-center rounded-full bg-grass font-display font-bold text-ink">{i + 1}</span>
                  <span className="min-w-0 flex-1 font-bold">{l.title}</span>
                  <span className="badge-highlight">Draft</span>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}

      {stage === "review" && (
        <div className="grid gap-5 lg:grid-cols-[minmax(0,1fr)_minmax(0,1fr)]">
          <div className="lg:col-span-2">
            <h4 className="font-display text-xl font-bold">AI membuat 3 level draf. Cek dulu ya, Bu/Pak Guru.</h4>
            <ul className="mt-2 grid gap-2 sm:grid-cols-3">
              {DEMO_DRAFT_LEVELS.map((l, i) => (
                <li key={l.title} className="card !p-3">
                  <p className="font-bold">
                    {i + 1}. {l.title}
                  </p>
                  <p className="text-sm text-ink/80">{l.note}</p>
                  <span className={materialApprovals[i] && questionApprovals[i] ? "badge-success mt-1" : "badge-highlight mt-1"}>
                    {materialApprovals[i] && questionApprovals[i] ? "Siap terbit" : "Draft"}
                  </span>
                  <button type="button" className="btn-ghost btn-sm mt-2" aria-pressed={activeLevel === i} onClick={() => setActiveLevel(i)}>
                    Tinjau level {i + 1}
                  </button>
                </li>
              ))}
            </ul>
          </div>

          <div className="min-w-0">
            <label htmlFor="demo-article" className="field-label mb-1 flex items-center gap-2">
              <PencilIcon size={18} />
              Ubah bacaan level {activeLevel + 1}
            </label>
            <textarea
              id="demo-article"
              rows={12} className="input-box font-mono !text-base"
              value={article}
              onChange={(e) => {
                setArticles((items) => items.map((item, i) => i === activeLevel ? e.target.value : item));
                setMaterialApprovals((items) => items.map((item, i) => i === activeLevel ? false : item));
              }}
            />
          </div>
          <div className="min-w-0">
            <p className="field-label mb-1">Tampilan untuk murid</p>
            <div className="max-h-[320px] overflow-y-auto rounded-2xl border-2 border-rule bg-paper p-4">
              <Markdown source={article} className="!text-base !leading-relaxed" />
            </div>
          </div>

          <div className="lg:col-span-2">
            <button type="button" className="btn-ghost" aria-pressed={materialApprovals[activeLevel]} disabled={!article.trim()}
              onClick={() => setMaterialApprovals((items) => items.map((item, i) => i === activeLevel ? !item : item))}>
              {materialApprovals[activeLevel] ? "Batalkan persetujuan materi" : "Setujui materi"} level {activeLevel + 1}
            </button>
          </div>
          <div className="card lg:col-span-2">
            <p className="field-label">Soal contoh level {activeLevel + 1} dari AI</p>
            <p className="font-bold">{question.text}</p>
            <ul className="my-2 grid gap-1 sm:grid-cols-2">
              {question.options.map((o, i) => (
                <li key={o} className={i === question.correct ? "font-bold text-correct-dark" : ""}>
                  {String.fromCharCode(65 + i)}. {o}
                  {i === question.correct && " (jawaban benar)"}
                </li>
              ))}
            </ul>
            <div className="flex flex-wrap items-center gap-3">
              <span className={approved ? "badge-success" : "badge-highlight"}>{approved ? "Disetujui" : "Draft"}</span>
              <button type="button" className="btn-ghost btn-sm" aria-pressed={approved} onClick={() => setQuestionApprovals((items) => items.map((item, i) => i === activeLevel ? !item : item))}>
                {approved ? "Kembalikan ke draft" : "Setujui soal"}
              </button>
            </div>
          </div>

          <div className="lg:col-span-2">
            <button type="button" className="btn-green" disabled={!canPublish} onClick={() => setStage("published")}>
              <RocketIcon size={22} />
              Publish kelas
            </button>
            <p className="mt-2 text-base text-ink/80">{materialApprovals.filter(Boolean).length} dari 3 materi dan {questionApprovals.filter(Boolean).length} dari 3 soal disetujui. Semua materi level dan minimal satu soal di setiap level harus disetujui sebelum kelas diterbitkan.</p>
          </div>
        </div>
      )}

      {stage === "published" && (
        <div className="text-center" aria-live="polite">
          <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-grass-soft text-grass-dark">
            <CheckIcon size={36} />
          </div>
          <h4 className="mt-2 font-display text-3xl font-extrabold">Kelas terbit!</h4>
          <p className="mb-4 text-lg">Murid sekarang bisa membuka peta level &quot;Siklus Air&quot;. (Contoh saja, tidak ada yang tersimpan.)</p>
          <button type="button" className="btn-ghost" onClick={reset}>
            Ulangi contoh
          </button>
        </div>
      )}
    </div>
  );
}
