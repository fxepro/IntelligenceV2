"use client";

import React, { useState, useEffect } from "react";
import {
  Loader2,
  FileText,
  Sparkles,
  Tag,
  Users,
  ExternalLink,
  AlertTriangle,
  AlertCircle,
  Copy,
  Check,
  Play,
} from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { PlatformIcon } from "@/components/sections/PlatformBadge";
import { MediaStatusPill } from "@/components/sections/StatusBadge";
import type { MediaRow } from "@/components/sections/MediaList";

import { API_BASE } from "@/lib/api-base";

interface Transcript {
  full_text?: string;
  text?: string;
  language: string | null;
  word_count: number | null;
}
interface Summary {
  executive_summary: string | null;
  key_points: string[] | null;
  topics: string[] | null;
  entities: Record<string, string[]> | null;
  sentiment: string | null;
  sentiment_score: number | null;
  risk_flags: string[] | null;
}
interface MediaDetail extends MediaRow {
  transcript: Transcript | null;
  summary: Summary | null;
}

function Chips({
  items,
  tone = "bg-muted text-muted-foreground border-border/50",
}: {
  items: string[];
  tone?: string;
}) {
  return (
    <div className="flex flex-wrap gap-1.5">
      {items.map((t, i) => (
        <span key={i} className={`text-fine font-medium px-2 py-0.5 rounded-full border ${tone}`}>
          {t}
        </span>
      ))}
    </div>
  );
}

export function MediaDetailDialog({
  id,
  onClose,
  onOpened,
}: {
  id: string | null;
  onClose: () => void;
  onOpened?: (id: string) => void;
}) {
  const [detail, setDetail] = useState<MediaDetail | null>(null);
  const [loading, setLoading] = useState(false);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (!id) return;
    setLoading(true);
    setDetail(null);
    setCopied(false);
    onOpened?.(id);
    fetch(`${API_BASE}/api/v1/media/${id}`)
      .then((r) => r.json())
      .then(setDetail)
      .finally(() => setLoading(false));
  }, [id, onOpened]);

  const s = detail?.summary;
  const entities = s?.entities ?? {};
  const entityGroups = Object.entries(entities).filter(
    ([, v]) => Array.isArray(v) && v.length > 0,
  );

  const transcriptText =
    detail?.transcript?.full_text || detail?.transcript?.text || "";

  const handleCopy = async () => {
    if (!detail) return;
    const title = detail.title?.trim() || "Untitled";
    const body = transcriptText.trim();
    try {
      await navigator.clipboard.writeText(body ? `${title}\n\n${body}` : title);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 2000);
    } catch {
      /* ignore */
    }
  };

  return (
    <Dialog open={!!id} onOpenChange={(o) => !o && onClose()}>
      <DialogContent className="sm:max-w-6xl w-[95vw] max-h-[92vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="pr-8 text-lg leading-snug">
            {detail?.title ?? "Loading…"}
          </DialogTitle>
        </DialogHeader>

        {loading && (
          <div className="flex items-center justify-center py-16 text-muted-foreground gap-2">
            <Loader2 className="w-5 h-5 animate-spin" /> Loading…
          </div>
        )}

        {detail && !loading && (
          <div className="space-y-5">
            <div className="flex flex-col sm:flex-row sm:items-start gap-4">
              <a
                href={detail.canonical_url}
                target="_blank"
                rel="noopener noreferrer"
                className="relative mx-auto sm:mx-0 w-28 aspect-[9/16] rounded-lg overflow-hidden border border-border/50 bg-muted/40 group shrink-0"
                title="Play reel"
              >
                {detail.thumbnail_url ? (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img
                    src={detail.thumbnail_url}
                    alt=""
                    referrerPolicy="no-referrer"
                    className="absolute inset-0 h-full w-full object-cover"
                  />
                ) : (
                  <span className="absolute inset-0 bg-muted" />
                )}
                <span className="absolute inset-0 flex items-center justify-center bg-black/35 opacity-80 group-hover:opacity-100 transition-opacity">
                  <span className="inline-flex h-9 w-9 items-center justify-center rounded-full bg-black/55 text-white">
                    <Play className="h-4 w-4 fill-current" />
                  </span>
                </span>
              </a>
              <div className="flex-1 space-y-3 min-w-0">
                <div className="flex items-center gap-2 flex-wrap text-xs text-muted-foreground">
                  <span className="inline-flex items-center gap-1">
                    <PlatformIcon platform={detail.platform} /> {detail.platform}
                  </span>
                  {detail.content_type && <span>· {detail.content_type}</span>}
                  {detail.channel_name && <span>· {detail.channel_name}</span>}
                  <MediaStatusPill status={detail.status} variant="rich" />
                </div>
                <Button asChild className="gap-2">
                  <a href={detail.canonical_url} target="_blank" rel="noopener noreferrer">
                    <Play className="h-4 w-4 fill-current" />
                    Play reel
                    <ExternalLink className="h-3.5 w-3.5 opacity-70" />
                  </a>
                </Button>
              </div>
            </div>

            {detail.status === "failed" && (
              <div className="flex items-center gap-2 text-xs text-red-400 bg-red-500/5 border border-red-500/20 rounded-lg px-3 py-2">
                <AlertCircle className="w-4 h-4 flex-shrink-0" />{" "}
                {detail.error_message ?? "Processing failed"}
              </div>
            )}

            {!s && !detail.transcript && (
              <div className="text-sm text-muted-foreground py-6 text-center">
                No transcript yet — use <strong>Transcribe</strong> on this item.
              </div>
            )}

            {s && (
              <div className="space-y-4">
                {s.executive_summary && (
                  <div>
                    <h4 className="text-fine font-bold uppercase tracking-widest text-primary flex items-center gap-1.5 mb-1.5">
                      <Sparkles className="w-3.5 h-3.5" /> Executive Summary
                    </h4>
                    <p className="text-sm leading-relaxed">{s.executive_summary}</p>
                  </div>
                )}
                {s.key_points && s.key_points.length > 0 && (
                  <div>
                    <h4 className="text-fine font-bold uppercase tracking-widest text-muted-foreground mb-1.5">
                      Key Points
                    </h4>
                    <ul className="space-y-1">
                      {s.key_points.map((k, i) => (
                        <li key={i} className="text-sm flex gap-2">
                          <span className="text-primary">•</span> {k}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
                <div className="flex flex-wrap gap-6">
                  {s.topics && s.topics.length > 0 && (
                    <div>
                      <h4 className="text-fine font-bold uppercase tracking-widest text-muted-foreground mb-1.5 flex items-center gap-1.5">
                        <Tag className="w-3 h-3" /> Topics
                      </h4>
                      <Chips items={s.topics} tone="bg-primary/10 text-primary border-primary/20" />
                    </div>
                  )}
                  {s.sentiment && (
                    <div>
                      <h4 className="text-fine font-bold uppercase tracking-widest text-muted-foreground mb-1.5">
                        Sentiment
                      </h4>
                      <span className="text-sm capitalize">
                        {s.sentiment}
                        {s.sentiment_score != null ? ` (${s.sentiment_score.toFixed(2)})` : ""}
                      </span>
                    </div>
                  )}
                </div>
                {entityGroups.length > 0 && (
                  <div>
                    <h4 className="text-fine font-bold uppercase tracking-widest text-muted-foreground mb-1.5 flex items-center gap-1.5">
                      <Users className="w-3 h-3" /> Entities
                    </h4>
                    <div className="space-y-1.5">
                      {entityGroups.map(([group, vals]) => (
                        <div key={group} className="flex gap-2 items-baseline">
                          <span className="text-fine uppercase tracking-wider text-muted-foreground w-24 flex-shrink-0">
                            {group}
                          </span>
                          <Chips items={vals} />
                        </div>
                      ))}
                    </div>
                  </div>
                )}
                {s.risk_flags && s.risk_flags.length > 0 && (
                  <div>
                    <h4 className="text-fine font-bold uppercase tracking-widest text-red-400 mb-1.5 flex items-center gap-1.5">
                      <AlertTriangle className="w-3 h-3" /> Risk Flags
                    </h4>
                    <Chips items={s.risk_flags} tone="bg-red-500/10 text-red-400 border-red-500/20" />
                  </div>
                )}
              </div>
            )}

            {detail.transcript && (
              <div>
                <div className="flex items-center justify-between gap-3 mb-2">
                  <h4 className="text-fine font-bold uppercase tracking-widest text-muted-foreground flex items-center gap-1.5">
                    <FileText className="w-3.5 h-3.5" /> Transcript
                    <span className="font-normal normal-case tracking-normal">
                      · {detail.transcript.word_count} words
                      {detail.transcript.language ? ` · ${detail.transcript.language}` : ""}
                    </span>
                  </h4>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleCopy}
                    className="gap-1.5 shrink-0"
                    title="Copy title and transcript text"
                  >
                    {copied ? <Check className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />}
                    {copied ? "Copied" : "Copy"}
                  </Button>
                </div>
                <div className="text-base leading-7 bg-muted/40 border border-border/40 rounded-lg p-5 min-h-[40vh] max-h-[70vh] overflow-y-auto whitespace-pre-wrap">
                  {transcriptText || "—"}
                </div>
              </div>
            )}
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
