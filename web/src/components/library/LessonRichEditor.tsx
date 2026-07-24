"use client";

import {
  forwardRef,
  useCallback,
  useEffect,
  useImperativeHandle,
  useRef,
} from "react";
import {
  Bold,
  Heading1,
  Heading2,
  Heading3,
  Italic,
  List,
  ListOrdered,
  Quote,
  Sparkles,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  editorHtmlToMarkdown,
  markdownToEditorHtml,
  normalizeLessonBody,
} from "@/lib/library-markdown";
import { cn } from "@/lib/utils";

type Props = {
  value: string;
  onChange: (md: string) => void;
  className?: string;
};

export type LessonRichEditorHandle = {
  /** Read live DOM → markdown (call before Save). */
  flush: () => string;
};

/**
 * Visual rich-text editor. Toolbar applies real bold/italic/headings
 * (not raw ** markers). Value is still stored as markdown on disk.
 */
export const LessonRichEditor = forwardRef<LessonRichEditorHandle, Props>(
  function LessonRichEditor({ value, onChange, className }, ref) {
    const elRef = useRef<HTMLDivElement>(null);
    const lastMd = useRef(value);
    const primed = useRef(false);

    const syncFromDom = useCallback(() => {
      const el = elRef.current;
      if (!el) return lastMd.current;
      const md = editorHtmlToMarkdown(el);
      lastMd.current = md;
      onChange(md);
      return md;
    }, [onChange]);

    useImperativeHandle(
      ref,
      () => ({
        flush: () => syncFromDom(),
      }),
      [syncFromDom],
    );

    useEffect(() => {
      const el = elRef.current;
      if (!el) return;
      if (!primed.current || value !== lastMd.current) {
        el.innerHTML = markdownToEditorHtml(value);
        lastMd.current = value;
        primed.current = true;
      }
    }, [value]);

    const run = (command: string, arg?: string) => {
      const el = elRef.current;
      if (!el) return;
      el.focus();
      try {
        const value =
          command === "formatBlock" && arg && !arg.startsWith("<")
            ? `<${arg}>`
            : arg;
        document.execCommand(command, false, value);
      } catch {
        /* ignore unsupported commands */
      }
      syncFromDom();
    };

    const onPaste = (e: React.ClipboardEvent<HTMLDivElement>) => {
      e.preventDefault();
      const text = e.clipboardData.getData("text/plain");
      document.execCommand("insertText", false, text);
      syncFromDom();
    };

    const toolbarBtn =
      "h-8 px-2 text-xs gap-1 border-border/60 text-muted-foreground hover:text-foreground";

    return (
      <div className={cn("space-y-2", className)}>
        <div className="flex flex-wrap gap-1 rounded-xl border border-border/60 bg-secondary/30 p-1.5">
          <Button
            type="button"
            variant="ghost"
            size="sm"
            className={toolbarBtn}
            title="Heading 1"
            onMouseDown={(e) => e.preventDefault()}
            onClick={() => run("formatBlock", "h1")}
          >
            <Heading1 className="h-3.5 w-3.5" />
            H1
          </Button>
          <Button
            type="button"
            variant="ghost"
            size="sm"
            className={toolbarBtn}
            title="Heading 2"
            onMouseDown={(e) => e.preventDefault()}
            onClick={() => run("formatBlock", "h2")}
          >
            <Heading2 className="h-3.5 w-3.5" />
            H2
          </Button>
          <Button
            type="button"
            variant="ghost"
            size="sm"
            className={toolbarBtn}
            title="Heading 3"
            onMouseDown={(e) => e.preventDefault()}
            onClick={() => run("formatBlock", "h3")}
          >
            <Heading3 className="h-3.5 w-3.5" />
            H3
          </Button>
          <Button
            type="button"
            variant="ghost"
            size="sm"
            className={toolbarBtn}
            title="Bold"
            onMouseDown={(e) => e.preventDefault()}
            onClick={() => run("bold")}
          >
            <Bold className="h-3.5 w-3.5" />
          </Button>
          <Button
            type="button"
            variant="ghost"
            size="sm"
            className={toolbarBtn}
            title="Italic"
            onMouseDown={(e) => e.preventDefault()}
            onClick={() => run("italic")}
          >
            <Italic className="h-3.5 w-3.5" />
          </Button>
          <Button
            type="button"
            variant="ghost"
            size="sm"
            className={toolbarBtn}
            title="Bullet list"
            onMouseDown={(e) => e.preventDefault()}
            onClick={() => run("insertUnorderedList")}
          >
            <List className="h-3.5 w-3.5" />
          </Button>
          <Button
            type="button"
            variant="ghost"
            size="sm"
            className={toolbarBtn}
            title="Numbered list"
            onMouseDown={(e) => e.preventDefault()}
            onClick={() => run("insertOrderedList")}
          >
            <ListOrdered className="h-3.5 w-3.5" />
          </Button>
          <Button
            type="button"
            variant="ghost"
            size="sm"
            className={toolbarBtn}
            title="Quote"
            onMouseDown={(e) => e.preventDefault()}
            onClick={() => run("formatBlock", "blockquote")}
          >
            <Quote className="h-3.5 w-3.5" />
          </Button>
          <Button
            type="button"
            variant="ghost"
            size="sm"
            className={cn(toolbarBtn, "ml-auto")}
            title="Clean up whitespace"
            onMouseDown={(e) => e.preventDefault()}
            onClick={() => {
              const cleaned = normalizeLessonBody(lastMd.current);
              if (elRef.current) {
                elRef.current.innerHTML = markdownToEditorHtml(cleaned);
              }
              lastMd.current = cleaned;
              onChange(cleaned);
            }}
          >
            <Sparkles className="h-3.5 w-3.5" />
            Clean up
          </Button>
        </div>

        <div
          ref={elRef}
          contentEditable
          role="textbox"
          aria-multiline
          aria-label="Lesson body"
          suppressContentEditableWarning
          spellCheck
          onInput={syncFromDom}
          onBlur={syncFromDom}
          onPaste={onPaste}
          className={cn(
            "min-h-[28rem] rounded-xl border border-border/60 bg-background px-4 py-3",
            "text-[15px] leading-7 text-foreground outline-none focus-visible:ring-2 focus-visible:ring-ring",
            "[&_h1]:mb-3 [&_h1]:mt-2 [&_h1]:text-2xl [&_h1]:font-semibold",
            "[&_h2]:mb-3 [&_h2]:mt-6 [&_h2]:text-xl [&_h2]:font-semibold",
            "[&_h3]:mb-2 [&_h3]:mt-5 [&_h3]:text-lg [&_h3]:font-semibold",
            "[&_p]:mb-3 [&_p]:leading-7",
            "[&_ul]:my-3 [&_ul]:list-disc [&_ul]:space-y-1.5 [&_ul]:pl-5",
            "[&_ol]:my-3 [&_ol]:list-decimal [&_ol]:space-y-1.5 [&_ol]:pl-5",
            "[&_blockquote]:my-4 [&_blockquote]:border-l-2 [&_blockquote]:border-border [&_blockquote]:pl-4 [&_blockquote]:italic [&_blockquote]:text-muted-foreground",
            "[&_strong]:font-semibold [&_b]:font-semibold",
            "[&_em]:italic [&_i]:italic",
            "[&_code]:rounded [&_code]:bg-muted [&_code]:px-1 [&_code]:py-0.5 [&_code]:font-mono [&_code]:text-[0.9em]",
            "[&_img]:my-3 [&_img]:max-h-[28rem] [&_img]:max-w-full [&_img]:rounded-lg [&_img]:border [&_img]:border-border/50",
            "[&_table]:my-4 [&_table]:w-full [&_table]:border-collapse [&_table]:text-sm",
            "[&_th]:border [&_th]:border-border/60 [&_th]:bg-muted/40 [&_th]:px-2 [&_th]:py-1.5 [&_th]:text-left",
            "[&_td]:border [&_td]:border-border/40 [&_td]:px-2 [&_td]:py-1.5",
          )}
        />
        <p className="text-xs text-muted-foreground">
          Select text, then Bold — it looks bold here. Markdown is written on save.
        </p>
      </div>
    );
  },
);
