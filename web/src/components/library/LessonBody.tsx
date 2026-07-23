"use client";

type Block =
  | { type: "h"; level: 1 | 2 | 3 | 4; text: string }
  | { type: "p"; text: string }
  | { type: "ul"; items: string[] }
  | { type: "quote"; text: string }
  | { type: "code"; text: string };

function looksLikeHeading(line: string): boolean {
  const s = line.trim();
  if (s.length < 8 || s.length > 110) return false;
  if (/^#{1,6}\s/.test(s) || s.startsWith("- ") || s.startsWith("> ")) return false;
  if (/[.!;:]$/.test(s) && !s.endsWith("?")) return false;
  // Title-ish: ends with ?, or mostly capitalized words
  if (s.endsWith("?")) return true;
  const words = s.split(/\s+/).filter(Boolean);
  if (words.length < 2 || words.length > 14) return false;
  const caps = words.filter((w) => /^[A-Z0-9]/.test(w)).length;
  return caps / words.length >= 0.55;
}

function parseBlocks(raw: string): Block[] {
  const text = (raw || "").replace(/\r\n/g, "\n").trim();
  if (!text) return [];

  const hasMdHeadings = /^#{1,6}\s/m.test(text);
  const lines = text.split("\n");
  const blocks: Block[] = [];
  let i = 0;

  const pushPara = (buf: string[]) => {
    const p = buf.join(" ").replace(/\s+/g, " ").trim();
    if (p) blocks.push({ type: "p", text: p });
    buf.length = 0;
  };

  while (i < lines.length) {
    const line = lines[i];
    const trimmed = line.trim();

    if (!trimmed) {
      i += 1;
      continue;
    }

    const md = trimmed.match(/^(#{1,4})\s+(.+)$/);
    if (md) {
      blocks.push({
        type: "h",
        level: Math.min(4, md[1].length) as 1 | 2 | 3 | 4,
        text: md[2].trim(),
      });
      i += 1;
      continue;
    }

    if (trimmed.startsWith("> ")) {
      blocks.push({ type: "quote", text: trimmed.replace(/^>\s?/, "").trim() });
      i += 1;
      continue;
    }

    if (trimmed.startsWith("```")) {
      i += 1;
      const code: string[] = [];
      while (i < lines.length && !lines[i].trim().startsWith("```")) {
        code.push(lines[i]);
        i += 1;
      }
      if (i < lines.length) i += 1;
      blocks.push({ type: "code", text: code.join("\n") });
      continue;
    }

    if (trimmed.startsWith("- ") || trimmed.startsWith("* ")) {
      const items: string[] = [];
      while (i < lines.length) {
        const t = lines[i].trim();
        if (!t) break;
        if (t.startsWith("- ") || t.startsWith("* ")) {
          items.push(t.slice(2).trim());
          i += 1;
          continue;
        }
        break;
      }
      if (items.length) blocks.push({ type: "ul", items });
      continue;
    }

    // Heuristic headings for plain-text dumps (Scytale / older Drata)
    if (!hasMdHeadings && looksLikeHeading(trimmed)) {
      const prev = i === 0 || !lines[i - 1].trim();
      const next = i + 1 >= lines.length || !lines[i + 1].trim() || lines[i + 1].trim().length > trimmed.length;
      if (prev && next) {
        blocks.push({ type: "h", level: 2, text: trimmed });
        i += 1;
        continue;
      }
    }

    // Paragraph: gather until blank / heading / list
    const buf: string[] = [trimmed];
    i += 1;
    while (i < lines.length) {
      const t = lines[i].trim();
      if (!t) break;
      if (/^#{1,4}\s/.test(t) || t.startsWith("- ") || t.startsWith("* ") || t.startsWith("> ") || t.startsWith("```")) {
        break;
      }
      if (!hasMdHeadings && looksLikeHeading(t)) {
        const prevBlank = !lines[i - 1]?.trim();
        if (prevBlank) break;
      }
      buf.push(t);
      i += 1;
    }
    pushPara(buf);
  }

  return blocks;
}

const headingClass: Record<number, string> = {
  1: "text-2xl font-semibold tracking-tight text-foreground mt-2 mb-3",
  2: "text-xl font-semibold tracking-tight text-foreground mt-8 mb-3 first:mt-2",
  3: "text-lg font-semibold text-foreground mt-6 mb-2",
  4: "text-base font-semibold text-foreground mt-5 mb-2",
};

export function LessonBody({ body }: { body: string }) {
  const blocks = parseBlocks(body);
  if (!blocks.length) {
    return <p className="text-sm text-muted-foreground">No text captured for this lesson yet.</p>;
  }

  return (
    <div className="max-w-3xl text-[15px] leading-7 text-foreground">
      {blocks.map((block, idx) => {
        if (block.type === "h") {
          const Tag = (`h${block.level}` as "h1" | "h2" | "h3" | "h4");
          return (
            <Tag key={idx} className={headingClass[block.level]}>
              {block.text}
            </Tag>
          );
        }
        if (block.type === "ul") {
          return (
            <ul key={idx} className="my-3 list-disc space-y-1.5 pl-5">
              {block.items.map((item, j) => (
                <li key={j} className="leading-relaxed">
                  {item}
                </li>
              ))}
            </ul>
          );
        }
        if (block.type === "quote") {
          return (
            <blockquote
              key={idx}
              className="my-4 border-l-2 border-border pl-4 text-[15px] italic text-muted-foreground"
            >
              {block.text}
            </blockquote>
          );
        }
        if (block.type === "code") {
          return (
            <pre
              key={idx}
              className="my-4 overflow-x-auto rounded-lg border border-border/60 bg-muted/40 p-3 text-[13px] leading-6"
            >
              <code>{block.text}</code>
            </pre>
          );
        }
        return (
          <p key={idx} className="mb-4 last:mb-0 leading-7 text-foreground/95">
            {block.text}
          </p>
        );
      })}
    </div>
  );
}
