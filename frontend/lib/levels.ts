import type { LevelSource } from "./types";

export function formatSource(source: LevelSource): string {
  const pages =
    source.page_start === source.page_end
      ? `Hal. ${source.page_start}`
      : `Hal. ${source.page_start}-${source.page_end}`;
  return source.section_title ? `${pages} - ${source.section_title}` : pages;
}
