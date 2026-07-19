"use client";

import {
  Library,
  Loader2,
  RefreshCw,
  CheckCircle2,
  Circle,
  FileText,
} from "lucide-react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { PlatformIcon } from "@/components/sections/PlatformBadge";
import { MediaStatusPill } from "@/components/sections/StatusBadge";
import { ContentTypePill } from "@/components/sections/ContentTypePill";

export interface MediaRow {
  id: string;
  source_id: string;
  platform: string;
  canonical_url: string;
  title: string | null;
  thumbnail_url: string | null;
  channel_name: string | null;
  content_type: string | null;
  duration_seconds: number | null;
  published_at: string | null;
  status: string;
  error_message: string | null;
}

export function MediaList({
  items,
  loading,
  readIds,
  processing,
  onView,
  onProcess,
}: {
  items: MediaRow[];
  loading: boolean;
  readIds: Set<string>;
  processing: Set<string>;
  onView: (id: string) => void;
  onProcess: (id: string) => void;
}) {
  if (loading) {
    return (
      <div className="flex items-center justify-center py-20 text-muted-foreground gap-2">
        <Loader2 className="w-6 h-6 animate-spin" /> Loading…
      </div>
    );
  }

  if (items.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-muted-foreground gap-2">
        <Library className="w-10 h-10 opacity-30" />
        <p className="text-sm">No items match these filters.</p>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {items.map((m) => {
        const busy = processing.has(m.id);
        const isRead = readIds.has(m.id);
        return (
          <Card
            key={m.id}
            className={`p-3 rounded-xl border-border/50 flex items-center gap-3 hover:shadow-sm transition-shadow ${
              !isRead ? "bg-card" : "bg-card/60 opacity-90"
            }`}
          >
            <span className="flex-shrink-0" title={isRead ? "Read" : "Unread"}>
              {isRead ? (
                <CheckCircle2 className="w-3.5 h-3.5 text-muted-foreground/50" />
              ) : (
                <Circle className="w-3.5 h-3.5 text-primary fill-primary/20" />
              )}
            </span>
            {m.thumbnail_url ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img
                src={m.thumbnail_url}
                alt=""
                className="w-16 h-10 rounded object-cover bg-muted flex-shrink-0"
              />
            ) : (
              <div className="w-16 h-10 rounded bg-muted flex items-center justify-center flex-shrink-0">
                <PlatformIcon platform={m.platform} />
              </div>
            )}
            <div className="flex-1 min-w-0">
              <div className={`text-sm truncate ${isRead ? "font-medium" : "font-semibold"}`}>
                {m.title ?? m.canonical_url}
              </div>
              <div className="flex items-center gap-2 mt-0.5 text-caption text-muted-foreground">
                <span className="inline-flex items-center gap-1">
                  <PlatformIcon platform={m.platform} className="w-3 h-3" /> {m.platform}
                </span>
                {m.content_type && <ContentTypePill contentType={m.content_type} />}
                {m.channel_name && <span className="truncate">· {m.channel_name}</span>}
              </div>
            </div>
            <MediaStatusPill status={m.status} variant="rich" />
            <div className="flex items-center gap-1.5 flex-shrink-0">
              {m.status === "completed" && (
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => onView(m.id)}
                  className="h-8 text-fine font-bold uppercase tracking-wider gap-1.5"
                >
                  <FileText className="w-3.5 h-3.5" /> View
                </Button>
              )}
              {["pending", "skipped", "failed"].includes(m.status) && (
                <Button
                  size="sm"
                  variant="outline"
                  disabled={busy}
                  onClick={() => onProcess(m.id)}
                  className="h-8 text-fine font-bold uppercase tracking-wider gap-1.5"
                >
                  {busy ? (
                    <>
                      <Loader2 className="w-3.5 h-3.5 animate-spin" /> Working…
                    </>
                  ) : m.status === "failed" ? (
                    <>
                      <RefreshCw className="w-3.5 h-3.5" /> Retry
                    </>
                  ) : (
                    <>
                      <FileText className="w-3.5 h-3.5" /> Transcribe
                    </>
                  )}
                </Button>
              )}
            </div>
          </Card>
        );
      })}
    </div>
  );
}
