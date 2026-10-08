import type { LevelSource } from "./types";

export function formatSource(source: LevelSource): string {
  const pages =
    source.page_start === source.page_end
      ? `Hal. ${source.page_start}`
      : `Hal. ${source.page_start}-${source.page_end}`;
  return source.section_title ? `${pages} - ${source.section_title}` : pages;
}

/** Counts words in Markdown text, ignoring bare markers such as "###" and "-". */
export function countWords(text: string | null | undefined): number {
  if (!text) return 0;
  return text.split(/\s+/).filter((w) => /[\p{L}\p{N}]/u.test(w)).length;
}

/** Reading time in minutes at 200 words per minute, at least 1. */
export function readMinutes(words: number): number {
  return Math.max(1, Math.ceil(words / 200));
}
