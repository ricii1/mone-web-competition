import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#1B2A41",
        "ink-panel": "#24374F",
        paper: "#FFF8E7",
        chalk: "#FFF8E7",
        "chalk-dim": "#B9C2CE",
        rule: "#E6DCC0",
        "rule-dark": "#3A4C66",
        highlight: "#FFC83D",
        "highlight-dark": "#E5A800",
        correct: "#2E9E58",
        "correct-dark": "#1E7A40",
        alert: "#C93B3B",
        sky: { DEFAULT: "#3BA7F0", dark: "#1F78C4", soft: "#DDF0FD" },
        grass: { DEFAULT: "#3FBF6A", dark: "#2A9450", soft: "#DDF6E5" },
        coral: { DEFAULT: "#FF6F61", dark: "#D4483B", soft: "#FFE3DF" },
        grape: { DEFAULT: "#9B6BFF", dark: "#6F43D6", soft: "#EBE1FF" },
      },
      fontFamily: {
        display: ["var(--font-display)", "system-ui", "sans-serif"],
        sans: ["var(--font-body)", "system-ui", "sans-serif"],
      },
      borderRadius: {
        "4xl": "2rem",
      },
    },
  },
  plugins: [],
};

export default config;
