"use client";

import { FormEvent, useEffect, useRef, useState } from "react";
import Link from "next/link";
import { AppPageHeader } from "@/components/sections/AppPageHeader";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Icon } from "@/lib/icons";
import { site } from "@/config/site";
import { chromeNav } from "@/config/navigation";
import { API_BASE } from "@/lib/api-base";

type ChatRole = "user" | "assistant";

type ChatTurn = {
  role: ChatRole;
  content: string;
};

const STORAGE_KEY = "intelligence-ask-chat-v1";
const MAX_TURNS = 80;

const STARTERS = [
  "How many sources am I monitoring?",
  "Which domains have records?",
  "What are my recent catalog items?",
  "Where should I look for new channels?",
];

type PersistedChat = {
  turns: ChatTurn[];
  draft: string;
  mode: string | null;
};

function loadChat(): PersistedChat {
  if (typeof window === "undefined") {
    return { turns: [], draft: "", mode: null };
  }
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return { turns: [], draft: "", mode: null };
    const data = JSON.parse(raw) as Partial<PersistedChat>;
    const turns = Array.isArray(data.turns)
      ? data.turns
          .filter(
            (t): t is ChatTurn =>
              !!t &&
              (t.role === "user" || t.role === "assistant") &&
              typeof t.content === "string" &&
              t.content.trim().length > 0,
          )
          .slice(-MAX_TURNS)
      : [];
    return {
      turns,
      draft: typeof data.draft === "string" ? data.draft : "",
      mode: typeof data.mode === "string" ? data.mode : null,
    };
  } catch {
    return { turns: [], draft: "", mode: null };
  }
}

function saveChat(state: PersistedChat) {
  try {
    localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify({
        turns: state.turns.slice(-MAX_TURNS),
        draft: state.draft,
        mode: state.mode,
      }),
    );
  } catch {
    /* quota / private mode */
  }
}

export default function AskPage() {
  const [ready, setReady] = useState(false);
  const [turns, setTurns] = useState<ChatTurn[]>([]);
  const [draft, setDraft] = useState("");
  const [sending, setSending] = useState(false);
  const [mode, setMode] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement | null>(null);
  const inputRef = useRef<HTMLTextAreaElement | null>(null);

  useEffect(() => {
    const saved = loadChat();
    setTurns(saved.turns);
    setDraft(saved.draft);
    setMode(saved.mode);
    setReady(true);
  }, []);

  useEffect(() => {
    if (!ready) return;
    saveChat({ turns, draft, mode });
  }, [ready, turns, draft, mode]);

  useEffect(() => {
    if (!ready) return;
    bottomRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [ready, turns, sending]);

  const clearChat = () => {
    setTurns([]);
    setDraft("");
    setMode(null);
    setError(null);
    try {
      localStorage.removeItem(STORAGE_KEY);
    } catch {
      /* ignore */
    }
  };

  const send = async (text: string) => {
    const message = text.trim();
    if (!message || sending) return;

    const nextTurns: ChatTurn[] = [...turns, { role: "user", content: message }];
    setTurns(nextTurns);
    setDraft("");
    setSending(true);
    setError(null);

    try {
      const res = await fetch(`${API_BASE}/api/v1/ask`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message,
          history: nextTurns.slice(0, -1).map((t) => ({
            role: t.role,
            content: t.content,
          })),
        }),
      });
      if (!res.ok) {
        const body = await res.text();
        throw new Error(body || `Ask failed (${res.status})`);
      }
      const data = await res.json();
      setMode(data.mode ?? null);
      setTurns((prev) => [
        ...prev,
        { role: "assistant", content: String(data.reply || "No reply.") },
      ]);
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : "Ask failed");
      setTurns((prev) => [
        ...prev,
        {
          role: "assistant",
          content:
            "Could not reach Ask. Confirm the API is running, then try again.",
        },
      ]);
    } finally {
      setSending(false);
      inputRef.current?.focus();
    }
  };

  const onSubmit = (event: FormEvent) => {
    event.preventDefault();
    void send(draft);
  };

  return (
    <div className="flex min-h-[calc(100vh-6rem)] flex-col gap-6 animate-in fade-in duration-500">
      <AppPageHeader
        title="Ask"
        description={`AI chat grounded in ${site.name} — domains, sources, and catalog facts. Not a web search.`}
        icon={<Icon name="message" className="h-5 w-5 text-primary" />}
        actions={
          <div className="flex items-center gap-3">
            {turns.length > 0 ? (
              <button
                type="button"
                onClick={clearChat}
                className="text-xs font-medium text-muted-foreground hover:text-foreground"
              >
                Clear chat
              </button>
            ) : null}
            <Link
              href={chromeNav.domains.href}
              className="text-xs font-medium text-muted-foreground hover:text-foreground"
            >
              Domains
            </Link>
          </div>
        }
      />

      <Card className="flex flex-1 flex-col overflow-hidden border-border/50 rounded-2xl bg-card shadow-sm min-h-[28rem]">
        <div className="border-b border-border/50 px-4 py-3 flex items-center justify-between gap-3">
          <p className="text-fine font-bold uppercase tracking-wider text-muted-foreground">
            Platform context
          </p>
          {mode ? (
            <span className="text-fine text-muted-foreground tabular-nums">
              {mode === "openai"
                ? "Model"
                : mode === "rate_limited"
                  ? "Rate limited · local"
                  : "Local"}{" "}
              context
            </span>
          ) : null}
        </div>

        <div className="flex-1 space-y-4 overflow-y-auto px-4 py-5">
          {ready && turns.length === 0 && !sending ? (
            <div className="mx-auto flex max-w-xl flex-col gap-4 pt-6 text-center">
              <p className="text-sm text-muted-foreground leading-relaxed">
                Ask about what is already in the platform — monitored sources,
                domain coverage, recent catalog items. Answers stay inside your
                data.
              </p>
              <div className="flex flex-wrap justify-center gap-2">
                {STARTERS.map((prompt) => (
                  <button
                    key={prompt}
                    type="button"
                    onClick={() => void send(prompt)}
                    className="rounded-xl border border-border/60 bg-secondary/40 px-3 py-2 text-left text-xs font-medium text-foreground hover:border-primary/40 hover:bg-secondary/70 transition-colors"
                  >
                    {prompt}
                  </button>
                ))}
              </div>
            </div>
          ) : null}

          {turns.map((turn, index) => (
            <div
              key={`${turn.role}-${index}`}
              className={`flex ${turn.role === "user" ? "justify-end" : "justify-start"}`}
            >
              <div
                className={`max-w-[85%] rounded-2xl px-3.5 py-2.5 text-sm leading-relaxed whitespace-pre-wrap ${
                  turn.role === "user"
                    ? "bg-primary text-primary-foreground"
                    : "bg-secondary/60 text-foreground border border-border/40"
                }`}
              >
                {turn.content}
              </div>
            </div>
          ))}

          {sending ? (
            <div className="flex justify-start">
              <div className="inline-flex items-center gap-2 rounded-2xl border border-border/40 bg-secondary/60 px-3.5 py-2.5 text-sm text-muted-foreground">
                <Icon name="refresh" className="h-3.5 w-3.5 animate-spin" />
                Thinking…
              </div>
            </div>
          ) : null}
          <div ref={bottomRef} />
        </div>

        <form
          onSubmit={onSubmit}
          className="border-t border-border/50 bg-card/80 p-4 space-y-3"
        >
          {error ? (
            <p className="text-xs text-red-500">{error}</p>
          ) : null}
          <div className="flex items-end gap-2">
            <textarea
              ref={inputRef}
              value={draft}
              onChange={(event) => setDraft(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Enter" && !event.shiftKey) {
                  event.preventDefault();
                  void send(draft);
                }
              }}
              rows={2}
              placeholder="Ask about sources, domains, or catalog…"
              className="min-h-[2.75rem] flex-1 resize-none rounded-xl border border-border/60 bg-background px-3 py-2.5 text-sm outline-none focus:border-primary/50 focus:ring-1 focus:ring-primary/30"
              disabled={sending || !ready}
            />
            <Button
              type="submit"
              disabled={sending || !ready || !draft.trim()}
              className="h-11 shrink-0 px-4"
            >
              Send
            </Button>
          </div>
          <p className="text-fine text-muted-foreground">
            Enter to send · Shift+Enter for a new line · Conversation saved in
            this browser
          </p>
        </form>
      </Card>
    </div>
  );
}
