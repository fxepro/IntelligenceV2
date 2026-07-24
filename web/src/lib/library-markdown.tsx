/** Shared Library markdown helpers — inline render + HTML ↔ markdown for the rich editor. */

import type { ReactNode } from "react";
import { createElement, Fragment } from "react";

export type LessonBlock =
  | { type: "h"; level: 1 | 2 | 3 | 4; text: string }
  | { type: "p"; text: string }
  | { type: "ul"; items: string[] }
  | { type: "ol"; items: string[]; start?: number }
  | { type: "quote"; text: string }
  | { type: "code"; text: string }
  | { type: "img"; alt: string; src: string }
  | { type: "table"; headers: string[]; rows: string[][] };

function numberedItemText(line: string): string | null {
  const m = line.trim().match(/^(\d+)\.(\s*)(.+)$/);
  if (!m) return null;
  return m[3].trim();
}

function bulletItemText(line: string): string | null {
  const m = line.trim().match(/^[-*•·–—]\s+(.+)$/);
  return m ? m[1].trim() : null;
}

function looksLikeSectionHeading(line: string): boolean {
  const s = line.trim();
  if (s.length < 3 || s.length > 90) return false;
  if (/^#{1,6}\s/.test(s) || s.startsWith("> ") || s.startsWith("```")) return false;
  if (/^\d+\.\s*\S/.test(s)) return false;
  if (bulletItemText(s)) return false;
  if (/[.!;:]$/.test(s) && !s.endsWith("?")) return false;
  if (s.length > 70 && s.includes(",")) return false;

  const words = s.split(/\s+/).filter(Boolean);
  if (words.length < 1 || words.length > 12) return false;
  if (words.length === 1) {
    return /^[A-Z][A-Za-z0-9/'()-]{2,}$/.test(words[0]);
  }
  const caps = words.filter((w) => /^[A-Z0-9(]/.test(w) || /^[A-Z]{2,}$/.test(w)).length;
  if (caps / words.length < 0.5) return false;
  if (s.endsWith("?") && words.length >= 8) return false;
  return true;
}

function headingLevelFor(line: string, index: number): 1 | 2 | 3 {
  if (index === 0) return 1;
  const words = line.trim().split(/\s+/).filter(Boolean).length;
  if (words <= 4) return 3;
  return 2;
}

function isPipeRow(line: string): boolean {
  const s = line.trim();
  return s.startsWith("|") && s.includes("|", 1);
}

function isTableSeparator(line: string): boolean {
  const s = line.trim();
  if (!s.includes("-")) return false;
  return /^\|?[\s:|-]+\|?$/.test(s) && /-/.test(s);
}

function splitPipeRow(line: string): string[] {
  let s = line.trim();
  if (s.startsWith("|")) s = s.slice(1);
  if (s.endsWith("|")) s = s.slice(0, -1);
  return s.split("|").map((c) => c.trim());
}

function parsePipeTable(
  lines: string[],
): { headers: string[]; rows: string[][] } | null {
  if (!lines.length) return null;
  const headers = splitPipeRow(lines[0]);
  if (!headers.length) return null;
  let start = 1;
  if (lines[1] && isTableSeparator(lines[1])) start = 2;
  const rows = lines
    .slice(start)
    .filter((l) => !isTableSeparator(l))
    .map(splitPipeRow)
    .map((cells) => {
      while (cells.length < headers.length) cells.push("");
      return cells.slice(0, Math.max(headers.length, cells.length));
    });
  return { headers, rows };
}

/** Parse lesson markdown / scraped text into display blocks. */
export function parseLessonBlocks(raw: string): LessonBlock[] {
  const text = (raw || "").replace(/\r\n/g, "\n").trim();
  if (!text) return [];

  const hasMdHeadings = /^#{1,6}\s/m.test(text);
  const lines = text.split("\n");
  const blocks: LessonBlock[] = [];
  let i = 0;
  let headingCount = 0;

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

    const imgOnly = trimmed.match(/^!\[([^\]]*)\]\(([^)]+)\)$/);
    if (imgOnly) {
      blocks.push({ type: "img", alt: imgOnly[1], src: imgOnly[2].trim() });
      i += 1;
      continue;
    }

    if (isPipeRow(trimmed)) {
      const tableLines: string[] = [];
      while (i < lines.length && isPipeRow(lines[i].trim())) {
        tableLines.push(lines[i].trim());
        i += 1;
      }
      const table = parsePipeTable(tableLines);
      if (table && (table.headers.length > 1 || table.rows.length > 0)) {
        blocks.push({ type: "table", headers: table.headers, rows: table.rows });
      } else {
        // Fallback: keep as paragraph junk rather than drop
        pushPara(tableLines);
      }
      continue;
    }

    const md = trimmed.match(/^(#{1,4})\s+(.+)$/);
    if (md) {
      blocks.push({
        type: "h",
        level: Math.min(4, md[1].length) as 1 | 2 | 3 | 4,
        text: md[2].trim(),
      });
      headingCount += 1;
      i += 1;
      continue;
    }

    if (trimmed.startsWith("> ")) {
      const quoteLines: string[] = [trimmed.slice(2)];
      i += 1;
      while (i < lines.length && lines[i].trim().startsWith("> ")) {
        quoteLines.push(lines[i].trim().slice(2));
        i += 1;
      }
      blocks.push({ type: "quote", text: quoteLines.join(" ").trim() });
      continue;
    }

    if (trimmed.startsWith("```")) {
      const codeLines: string[] = [];
      i += 1;
      while (i < lines.length && !lines[i].trim().startsWith("```")) {
        codeLines.push(lines[i]);
        i += 1;
      }
      if (i < lines.length) i += 1;
      blocks.push({ type: "code", text: codeLines.join("\n") });
      continue;
    }

    const bullet = bulletItemText(trimmed);
    if (bullet) {
      const items: string[] = [bullet];
      i += 1;
      while (i < lines.length) {
        const b = bulletItemText(lines[i]);
        if (!b) break;
        items.push(b);
        i += 1;
      }
      blocks.push({ type: "ul", items });
      continue;
    }

    const numbered = numberedItemText(trimmed);
    if (numbered !== null) {
      const startMatch = trimmed.match(/^(\d+)\./);
      const start = startMatch ? Number(startMatch[1]) : 1;
      const items: string[] = [numbered];
      i += 1;
      while (i < lines.length) {
        const n = numberedItemText(lines[i]);
        if (n === null) break;
        items.push(n);
        i += 1;
      }
      blocks.push({ type: "ol", items, start });
      continue;
    }

    if (!hasMdHeadings && looksLikeSectionHeading(trimmed)) {
      const level = headingLevelFor(trimmed, headingCount);
      blocks.push({ type: "h", level, text: trimmed });
      headingCount += 1;
      i += 1;
      continue;
    }

    const buf: string[] = [trimmed];
    i += 1;
    while (i < lines.length) {
      const t = lines[i].trim();
      if (!t) break;
      if (
        /^#{1,4}\s/.test(t)
        || bulletItemText(t)
        || t.startsWith("> ")
        || t.startsWith("```")
        || /^\d+\.\s*\S/.test(t)
        || isPipeRow(t)
        || /^!\[[^\]]*\]\([^)]+\)$/.test(t)
      ) {
        break;
      }
      if (looksLikeSectionHeading(t)) {
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

/** Render inline markdown: **bold**, *italic*, `code`, ![img](src). */
export function renderInlineMarkdown(text: string): ReactNode {
  if (!text) return null;
  const nodes: ReactNode[] = [];
  const re =
    /(!\[([^\]]*)\]\(([^)]+)\)|\*\*\*(.+?)\*\*\*|\*\*(.+?)\*\*|__(.+?)__|\*((?:[^*]|\*(?!\*))+?)\*|_([^_]+?)_|`([^`]+)`)/g;
  let last = 0;
  let m: RegExpExecArray | null;
  let key = 0;
  while ((m = re.exec(text)) !== null) {
    if (m.index > last) {
      nodes.push(text.slice(last, m.index));
    }
    if (m[3] != null) {
      nodes.push(
        createElement("img", {
          key: key++,
          src: m[3],
          alt: m[2] || "",
          className: "inline-block max-h-48 max-w-full rounded-md border border-border/40 my-1",
        }),
      );
    } else if (m[4] != null) {
      nodes.push(createElement("strong", { key: key++ }, createElement("em", null, m[4])));
    } else if (m[5] != null || m[6] != null) {
      nodes.push(createElement("strong", { key: key++ }, m[5] ?? m[6]));
    } else if (m[7] != null || m[8] != null) {
      nodes.push(createElement("em", { key: key++ }, m[7] ?? m[8]));
    } else if (m[9] != null) {
      nodes.push(
        createElement(
          "code",
          {
            key: key++,
            className: "rounded bg-muted px-1 py-0.5 text-[0.9em] font-mono",
          },
          m[9],
        ),
      );
    }
    last = m.index + m[0].length;
  }
  if (last < text.length) nodes.push(text.slice(last));
  return createElement(Fragment, null, ...nodes);
}

function escapeHtml(s: string): string {
  return s
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function inlineMarkdownToHtml(text: string): string {
  let t = escapeHtml(text);
  t = t.replace(/\*\*\*(.+?)\*\*\*/g, "<strong><em>$1</em></strong>");
  t = t.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
  t = t.replace(/__(.+?)__/g, "<strong>$1</strong>");
  t = t.replace(/\*((?:[^*]|\*(?!\*))+?)\*/g, "<em>$1</em>");
  t = t.replace(/_([^_]+?)_/g, "<em>$1</em>");
  t = t.replace(/`([^`]+)`/g, "<code>$1</code>");
  return t;
}

/** Markdown → HTML for contentEditable. */
export function markdownToEditorHtml(md: string): string {
  const blocks = parseLessonBlocks(md);
  if (!blocks.length) return "<p><br></p>";
  return blocks
    .map((block) => {
      if (block.type === "h") {
        return `<h${block.level}>${inlineMarkdownToHtml(block.text)}</h${block.level}>`;
      }
      if (block.type === "ul") {
        return `<ul>${block.items.map((item) => `<li>${inlineMarkdownToHtml(item)}</li>`).join("")}</ul>`;
      }
      if (block.type === "ol") {
        const start = block.start && block.start > 1 ? ` start="${block.start}"` : "";
        return `<ol${start}>${block.items.map((item) => `<li>${inlineMarkdownToHtml(item)}</li>`).join("")}</ol>`;
      }
      if (block.type === "quote") {
        return `<blockquote>${inlineMarkdownToHtml(block.text)}</blockquote>`;
      }
      if (block.type === "code") {
        return `<pre><code>${escapeHtml(block.text)}</code></pre>`;
      }
      if (block.type === "img") {
        const alt = escapeHtml(block.alt || "");
        const src = escapeHtml(block.src || "");
        return `<p><img src="${src}" alt="${alt}"></p>`;
      }
      if (block.type === "table") {
        const head = `<tr>${block.headers.map((h) => `<th>${inlineMarkdownToHtml(h)}</th>`).join("")}</tr>`;
        const body = block.rows
          .map((row) => `<tr>${row.map((c) => `<td>${inlineMarkdownToHtml(c)}</td>`).join("")}</tr>`)
          .join("");
        return `<table><thead>${head}</thead><tbody>${body}</tbody></table>`;
      }
      return `<p>${inlineMarkdownToHtml(block.text)}</p>`;
    })
    .join("");
}

function collapseWs(s: string): string {
  return s.replace(/\u00a0/g, " ").replace(/[ \t]+\n/g, "\n").replace(/\n{3,}/g, "\n\n").trim();
}

function inlineNodesToMd(parent: Node): string {
  let out = "";
  parent.childNodes.forEach((node) => {
    if (node.nodeType === Node.TEXT_NODE) {
      out += node.textContent || "";
      return;
    }
    if (node.nodeType !== Node.ELEMENT_NODE) return;
    const el = node as HTMLElement;
    const tag = el.tagName.toLowerCase();
    const inner = inlineNodesToMd(el);
    if (tag === "strong" || tag === "b") {
      out += inner ? `**${inner}**` : "";
      return;
    }
    if (tag === "em" || tag === "i") {
      out += inner ? `*${inner}*` : "";
      return;
    }
    if (tag === "code") {
      out += inner ? `\`${inner}\`` : "";
      return;
    }
    if (tag === "br") {
      out += "\n";
      return;
    }
    if (tag === "a") {
      const href = el.getAttribute("href") || "";
      out += href ? `[${inner}](${href})` : inner;
      return;
    }
    if (tag === "img") {
      const src = el.getAttribute("src") || "";
      const alt = el.getAttribute("alt") || "";
      if (src) out += `![${alt}](${src})`;
      return;
    }
    // Nested bold from font-weight styles
    const weight = el.style?.fontWeight || "";
    if (weight === "bold" || weight === "700" || Number(weight) >= 600) {
      out += inner ? `**${inner}**` : "";
      return;
    }
    if (el.style?.fontStyle === "italic") {
      out += inner ? `*${inner}*` : "";
      return;
    }
    out += inner;
  });
  return out;
}

/** contentEditable root → markdown stored on disk. */
export function editorHtmlToMarkdown(root: HTMLElement): string {
  const parts: string[] = [];

  const walkBlocks = (nodes: NodeListOf<ChildNode> | ChildNode[]) => {
    Array.from(nodes).forEach((node) => {
      if (node.nodeType === Node.TEXT_NODE) {
        const t = (node.textContent || "").trim();
        if (t) parts.push(t);
        return;
      }
      if (node.nodeType !== Node.ELEMENT_NODE) return;
      const el = node as HTMLElement;
      const tag = el.tagName.toLowerCase();

      if (tag === "h1" || tag === "h2" || tag === "h3" || tag === "h4") {
        const level = Number(tag[1]);
        const text = inlineNodesToMd(el).trim();
        if (text) parts.push(`${"#".repeat(level)} ${text}`);
        return;
      }
      if (tag === "p" || tag === "div") {
        // Skip empty div wrappers that only hold nested blocks
        const hasBlockChild = Array.from(el.children).some((c) =>
          /^(H[1-4]|UL|OL|BLOCKQUOTE|PRE|P|DIV|TABLE|FIGURE)$/i.test(c.tagName),
        );
        if (hasBlockChild) {
          walkBlocks(el.childNodes);
          return;
        }
        const onlyImg =
          el.childNodes.length === 1
          && el.firstElementChild?.tagName.toLowerCase() === "img";
        if (onlyImg) {
          const img = el.firstElementChild as HTMLImageElement;
          const src = img.getAttribute("src") || "";
          const alt = img.getAttribute("alt") || "";
          if (src) parts.push(`![${alt}](${src})`);
          return;
        }
        const text = inlineNodesToMd(el).trim();
        if (text) parts.push(text);
        return;
      }
      if (tag === "img") {
        const src = el.getAttribute("src") || "";
        const alt = el.getAttribute("alt") || "";
        if (src) parts.push(`![${alt}](${src})`);
        return;
      }
      if (tag === "table") {
        const rows: string[][] = [];
        el.querySelectorAll("tr").forEach((tr) => {
          const cells = Array.from(tr.querySelectorAll("th,td")).map((c) =>
            inlineNodesToMd(c).trim().replace(/\|/g, "\\|"),
          );
          if (cells.length) rows.push(cells);
        });
        if (rows.length) {
          const colCount = Math.max(...rows.map((r) => r.length), 1);
          const norm = rows.map((r) => {
            const copy = [...r];
            while (copy.length < colCount) copy.push("");
            return copy.slice(0, colCount);
          });
          const header = norm[0];
          const sep = Array.from({ length: colCount }, () => "---");
          const lines = [
            `| ${header.join(" | ")} |`,
            `| ${sep.join(" | ")} |`,
            ...norm.slice(1).map((r) => `| ${r.join(" | ")} |`),
          ];
          parts.push(lines.join("\n"));
        }
        return;
      }
      if (tag === "ul") {
        Array.from(el.children).forEach((li) => {
          if (li.tagName.toLowerCase() !== "li") return;
          const text = inlineNodesToMd(li).trim();
          if (text) parts.push(`- ${text}`);
        });
        return;
      }
      if (tag === "ol") {
        let n = Number(el.getAttribute("start") || "1") || 1;
        Array.from(el.children).forEach((li) => {
          if (li.tagName.toLowerCase() !== "li") return;
          const text = inlineNodesToMd(li).trim();
          if (text) parts.push(`${n}. ${text}`);
          n += 1;
        });
        return;
      }
      if (tag === "blockquote") {
        const text = inlineNodesToMd(el).trim();
        if (text) {
          parts.push(
            text
              .split("\n")
              .map((line) => `> ${line}`)
              .join("\n"),
          );
        }
        return;
      }
      if (tag === "pre") {
        const text = el.textContent || "";
        parts.push(`\`\`\`\n${text.replace(/\n$/, "")}\n\`\`\``);
        return;
      }
      if (tag === "br") {
        return;
      }
      walkBlocks(el.childNodes);
    });
  };

  walkBlocks(root.childNodes);
  return collapseWs(parts.join("\n\n"));
}

export function normalizeLessonBody(raw: string): string {
  return (raw || "")
    .replace(/\r\n/g, "\n")
    .replace(/[ \t]+\n/g, "\n")
    .replace(/\n{3,}/g, "\n\n")
    .trim();
}
