"use client";

import {
  Plus,
  X,
  Check,
  Users,
  Film,
  Eye,
  Clock,
  Sparkles,
  ExternalLink,
  Loader2,
} from "lucide-react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { PlatformBadge, PlatformIcon } from "@/components/sections/PlatformBadge";

export interface Candidate {
  id: string;
  query: string;
  platform: string;
  external_id: string | null;
  name: string | null;
  url: string;
  thumbnail_url: string | null;
  description: string | null;
  suggested_source_type: string | null;
  subscriber_count: number | null;
  item_count: number | null;
  total_views: number | null;
  last_active_at: string | null;
  relevance_score: number | null;
  ai_reason: string | null;
  status: "suggested" | "promoted" | "dismissed";
}

function compact(n: number | null | undefined): string {
  if (n == null) return "—";
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`;
  return String(n);
}

function recency(iso: string | null): { label: string; tone: string } {
  if (!iso) return { label: "Unknown", tone: "bg-muted text-muted-foreground border-border/50" };
  const days = Math.floor((Date.now() - new Date(iso).getTime()) / 86_400_000);
  if (days <= 30)
    return {
      label: `Active ${days}d ago`,
      tone: "bg-emerald-500/10 text-emerald-500 border-emerald-500/20",
    };
  if (days <= 180)
    return {
      label: `${Math.round(days / 30)}mo ago`,
      tone: "bg-amber-500/10 text-amber-400 border-amber-500/20",
    };
  if (days <= 365)
    return {
      label: `${Math.round(days / 30)}mo ago`,
      tone: "bg-orange-500/10 text-orange-400 border-orange-500/20",
    };
  return {
    label: `Stale · ${Math.round(days / 365)}y`,
    tone: "bg-red-500/10 text-red-400 border-red-500/20",
  };
}

export function CandidateCard({
  c,
  onPromote,
  onDismiss,
  busy,
}: {
  c: Candidate;
  onPromote: (id: string) => void;
  onDismiss: (id: string) => void;
  busy: boolean;
}) {
  const rec = recency(c.last_active_at);
  const promoted = c.status === "promoted";

  return (
    <Card className="p-4 rounded-2xl border-border/50 shadow-sm hover:shadow-md transition-shadow flex flex-col gap-3">
      <div className="flex items-start gap-3">
        {c.thumbnail_url ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={c.thumbnail_url}
            alt=""
            className="w-12 h-12 rounded-xl object-cover bg-muted flex-shrink-0"
          />
        ) : (
          <div className="w-12 h-12 rounded-xl bg-muted flex items-center justify-center flex-shrink-0">
            <PlatformIcon platform={c.platform} className="w-5 h-5 text-muted-foreground" />
          </div>
        )}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <PlatformBadge platform={c.platform} />
            {c.relevance_score != null && (
              <span className="inline-flex items-center gap-1 text-fine font-bold uppercase tracking-widest px-2 py-0.5 rounded-md bg-primary/10 text-primary border border-primary/20">
                <Sparkles className="w-3 h-3" />
                {Math.round(c.relevance_score)}
              </span>
            )}
          </div>
          <h3 className="font-bold text-sm leading-tight truncate">{c.name ?? c.url}</h3>
          <a
            href={c.url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-caption text-muted-foreground hover:text-primary flex items-center gap-1 truncate"
          >
            <span className="truncate">{c.url.replace(/^https?:\/\//, "")}</span>
            <ExternalLink className="w-3 h-3 flex-shrink-0" />
          </a>
        </div>
      </div>

      <div className="flex items-center flex-wrap gap-x-3 gap-y-1 text-caption text-muted-foreground">
        {c.subscriber_count != null && (
          <span className="inline-flex items-center gap-1">
            <Users className="w-3 h-3" /> {compact(c.subscriber_count)}
          </span>
        )}
        {c.item_count != null && (
          <span className="inline-flex items-center gap-1">
            <Film className="w-3 h-3" /> {compact(c.item_count)} items
          </span>
        )}
        {c.total_views != null && (
          <span className="inline-flex items-center gap-1">
            <Eye className="w-3 h-3" /> {compact(c.total_views)}
          </span>
        )}
        <span
          className={`inline-flex items-center gap-1 text-fine font-bold uppercase tracking-wider px-2 py-0.5 rounded-full border ${rec.tone}`}
        >
          <Clock className="w-3 h-3" /> {rec.label}
        </span>
      </div>

      {c.ai_reason && (
        <p className="text-caption leading-snug text-muted-foreground bg-muted/40 rounded-lg px-2.5 py-1.5 border border-border/40">
          {c.ai_reason}
        </p>
      )}

      <div className="flex items-center gap-2 mt-auto pt-1">
        {promoted ? (
          <span className="flex-1 inline-flex items-center justify-center gap-1.5 text-fine font-bold uppercase tracking-wider text-emerald-500 bg-emerald-500/10 border border-emerald-500/20 rounded-lg py-2">
            <Check className="w-3.5 h-3.5" /> Added to Sources
          </span>
        ) : (
          <Button
            size="sm"
            disabled={busy}
            onClick={() => onPromote(c.id)}
            className="flex-1 h-8 text-fine font-bold uppercase tracking-wider gap-1.5"
          >
            {busy ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Plus className="w-3.5 h-3.5" />}
            Add to Sources
          </Button>
        )}
        <Button
          size="icon"
          variant="ghost"
          disabled={busy || promoted}
          onClick={() => onDismiss(c.id)}
          className="h-8 w-8 text-muted-foreground hover:text-red-500"
          title="Dismiss"
        >
          <X className="w-4 h-4" />
        </Button>
      </div>
    </Card>
  );
}
