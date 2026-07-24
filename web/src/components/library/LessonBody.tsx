"use client";

import {
  parseLessonBlocks,
  renderInlineMarkdown,
} from "@/lib/library-markdown";

const headingClass: Record<number, string> = {
  1: "text-2xl font-semibold tracking-tight text-foreground mt-2 mb-3",
  2: "text-xl font-semibold tracking-tight text-foreground mt-8 mb-3 first:mt-2",
  3: "text-lg font-semibold text-foreground mt-6 mb-2",
  4: "text-base font-semibold text-foreground mt-5 mb-2",
};

export function LessonBody({ body }: { body: string }) {
  const blocks = parseLessonBlocks(body);
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
              {renderInlineMarkdown(block.text)}
            </Tag>
          );
        }
        if (block.type === "img") {
          return (
            <figure key={idx} className="my-6">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={block.src}
                alt={block.alt || ""}
                className="max-w-full h-auto rounded-lg border border-border/50 bg-muted/20"
                loading="lazy"
              />
              {block.alt ? (
                <figcaption className="mt-2 text-sm text-muted-foreground italic">
                  {block.alt}
                </figcaption>
              ) : null}
            </figure>
          );
        }
        if (block.type === "table") {
          return (
            <div key={idx} className="my-5 overflow-x-auto rounded-lg border border-border/60">
              <table className="w-full min-w-[20rem] border-collapse text-sm">
                <thead>
                  <tr className="bg-muted/50">
                    {block.headers.map((h, j) => (
                      <th
                        key={j}
                        className="border-b border-border/60 px-3 py-2 text-left font-semibold align-top"
                      >
                        {renderInlineMarkdown(h)}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {block.rows.map((row, ri) => (
                    <tr key={ri} className="odd:bg-background even:bg-muted/20">
                      {row.map((cell, ci) => (
                        <td
                          key={ci}
                          className="border-b border-border/40 px-3 py-2 align-top leading-relaxed"
                        >
                          {renderInlineMarkdown(cell)}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          );
        }
        if (block.type === "ul") {
          return (
            <ul key={idx} className="my-3 list-disc space-y-1.5 pl-5">
              {block.items.map((item, j) => (
                <li key={j} className="leading-relaxed">
                  {renderInlineMarkdown(item)}
                </li>
              ))}
            </ul>
          );
        }
        if (block.type === "ol") {
          return (
            <ol
              key={idx}
              start={block.start && block.start > 1 ? block.start : undefined}
              className="my-3 list-decimal space-y-1.5 pl-5"
            >
              {block.items.map((item, j) => (
                <li key={j} className="leading-relaxed">
                  {renderInlineMarkdown(item)}
                </li>
              ))}
            </ol>
          );
        }
        if (block.type === "quote") {
          return (
            <blockquote
              key={idx}
              className="my-4 border-l-2 border-border pl-4 text-[15px] italic text-muted-foreground"
            >
              {renderInlineMarkdown(block.text)}
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
            {renderInlineMarkdown(block.text)}
          </p>
        );
      })}
    </div>
  );
}
