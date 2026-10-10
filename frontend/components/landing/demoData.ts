/** Hard-coded sample content for the landing demos (never sent to or read from the backend). */

export interface DemoQuestion {
  text: string;
  options: string[];
  correct: number;
  explanation: string;
}

export const DEMO_LEVEL_TITLE = "Air naik ke langit";

export const DEMO_ARTICLE = `Air di bumi tidak pernah habis begitu saja. Air terus berputar dari satu tempat ke tempat lain. Perjalanan air yang berputar ini disebut **siklus air**.

### Air berubah jadi uap

Matahari memanaskan air di laut, sungai, dan danau. Air yang panas berubah menjadi uap air yang tidak terlihat. Peristiwa ini disebut **menguap**.

### Uap menjadi awan

Uap air naik ke langit. Di atas sana udaranya dingin, jadi uap air berubah lagi menjadi titik-titik air yang sangat kecil. Titik-titik air itu berkumpul menjadi **awan**.

### Poin penting

- Panas matahari membuat air menguap.
- Uap air naik ke langit.
- Uap air yang dingin berkumpul menjadi awan.`;

export const DEMO_QUESTIONS: DemoQuestion[] = [
  {
    text: "Apa yang membuat air di laut menguap?",
    options: ["Panas matahari", "Angin malam", "Cahaya bulan", "Suara petir"],
    correct: 0,
    explanation: "Matahari memanaskan air sehingga air berubah menjadi uap.",
  },
  {
    text: "Apa nama peristiwa air berubah menjadi uap?",
    options: ["Membeku", "Menguap", "Mengalir", "Meresap"],
    correct: 1,
    explanation: "Air yang berubah menjadi uap disebut menguap.",
  },
  {
    text: "Uap air yang dingin di langit akan menjadi apa?",
    options: ["Batu", "Pelangi", "Awan", "Pasir"],
    correct: 2,
    explanation: "Titik-titik air kecil yang berkumpul di langit membentuk awan.",
  },
];

export const DEMO_DRAFT_LEVELS = [
  { title: "Air naik ke langit", note: "Menguap dan awan" },
  { title: "Awan menjadi hujan", note: "Hujan turun ke bumi" },
  { title: "Air kembali ke laut", note: "Sungai dan resapan" },
];

export const DEMO_TEACHER_QUESTION = {
  text: "Apa yang membuat air di laut menguap?",
  options: ["Panas matahari", "Angin malam", "Cahaya bulan", "Suara petir"],
  correct: 0,
};
