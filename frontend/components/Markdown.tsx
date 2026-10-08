import type { ReactNode } from "react";
import { StarIcon } from "@/components/icons";

/**
 * Tiny safe renderer for a Markdown subset: "### " headings, paragraphs, "- " lists,
 * **bold** and *italic*. Everything is parsed into React elements (text is escaped by React);
 * any other syntax is shown as plain text.
 */

type Block =
  | { kind: "heading"; text: string }
  | { kind: "list"; items: string[] }
  | { kind: "paragraph"; text: string };

function parseBlocks(source: string): Block[] {
  const blocks: Block[] = [];
  let para: string[] = [];
  let list: string[] | null = null;

  const flushPara = () => {
    if (para.length) blocks.push({ kind: "paragraph", text: para.join(" ") });
    para = [];
  };
  const flushList = () => {
    if (list) blocks.push({ kind: "list", items: list });
    list = null;
  };

  for (const raw of source.replace(/\r\n?/g, "\n").split("\n")) {
    const line = raw.trim();
    if (line === "") {
      flushPara();
      flushList();
    } else if (line.startsWith("### ") && line.slice(4).trim() !== "") {
      flushPara();
      flushList();
      blocks.push({ kind: "heading", text: line.slice(4).trim() });
    } else if (line.startsWith("- ") && line.slice(2).trim() !== "") {
      flushPara();
      (list ??= []).push(line.slice(2).trim());
    } else {
      flushList();
      para.push(line);
    }
  }
  flushPara();
  flushList();
  return blocks;
}

const INLINE = /(\*\*[^*]+\*\*|\*[^*\s][^*]*\*)/g;

function renderInline(text: string): ReactNode[] {
  return text.split(INLINE).map((part, i) => {
    if (part.startsWith("**") && part.endsWith("**") && part.length > 4) {
      return <strong key={i}>{part.slice(2, -2)}</strong>;
    }
    if (part.startsWith("*") && part.endsWith("*") && part.length > 2 && !part.startsWith("**")) {
      return <em key={i}>{part.slice(1, -1)}</em>;
    }
    return part;
  });
}

const ACCENTS = [
  { bar: "bg-sky", text: "text-sky-dark" },
  { bar: "bg-grass", text: "text-grass-dark" },
  { bar: "bg-coral", text: "text-coral-dark" },
  { bar: "bg-grape", text: "text-grape-dark" },
];
const STAR_COLORS = ["text-highlight-dark", "text-sky", "text-grass", "text-coral"];

export default function Markdown({ source, className = "" }: { source: string; className?: string }) {
  const blocks = parseBlocks(source);
  let headingIndex = 0;
  return (
    <div className={`max-w-[65ch] text-[1.1875rem] leading-[1.85] text-ink/90 ${className}`}>
      {blocks.map((b, i) => {
        if (b.kind === "heading") {
          const accent = ACCENTS[headingIndex++ % ACCENTS.length];
          return (
            <h3 key={i} className={`mb-2 mt-8 flex items-center gap-3 text-2xl first:mt-0 ${accent.text}`}>
              <span className={`inline-block h-7 w-2 shrink-0 rounded-full ${accent.bar}`} aria-hidden="true" />
              {renderInline(b.text)}
            </h3>
          );
        }
        if (b.kind === "list") {
          return (
            <ul key={i} className="my-4 flex flex-col gap-2">
              {b.items.map((item, j) => (
                <li key={j} className="flex items-start gap-3">
                  <span className={`mt-[0.45rem] shrink-0 ${STAR_COLORS[j % STAR_COLORS.length]}`}>
                    <StarIcon size={18} />
                  </span>
                  <span className="min-w-0">{renderInline(item)}</span>
                </li>
              ))}
            </ul>
          );
        }
        return (
          <p key={i} className="my-4 first:mt-0">
            {renderInline(b.text)}
          </p>
        );
      })}
    </div>
  );
}
