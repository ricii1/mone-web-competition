import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#1B2A41",
        "ink-panel": "#24374F",
        paper: "#F3EFE3",
        chalk: "#F3EFE3",
        "chalk-dim": "#B9C2CE",
        rule: "#DCD5C2",
        "rule-dark": "#3A4C66",
        highlight: "#E3A23C",
        "highlight-dark": "#C7872A",
        correct: "#3F7D58",
        alert: "#B23A2E",
      },
      fontFamily: {
        display: ["var(--font-display)"],
        sans: ["var(--font-body)"],
      },
    },
  },
  plugins: [],
};

export default config;
