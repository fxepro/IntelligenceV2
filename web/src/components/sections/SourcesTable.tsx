"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  RefreshCw,
  Trash2,
  AlertCircle,
  Loader2,
  ArrowRight,
  ArrowUpRight,
  CheckCircle2,
  Radio,
} from "lucide-react";
import { Card, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { PlatformBadge } from "@/components/sections/PlatformBadge";
import type { Source, SourcePriority } from "@/lib/mock-data/sources";
import type { MediaItem } from "@/lib/mock-data/media-items";
import { formatRelativeDate } from "@/lib/mock-data/media-items";
import {
  formatTagsInput,
  parseTagsInput,
  PRIORITY_OPTIONS,
  sourceTypeLabel,
} from "@/lib/sources/helpers";
import { Badge } from "@/components/ui/badge";

const PRIORITY_CLASS: Record<SourcePriority, string> = {
  urgent: "text-red-500",
  high: "text-amber-600 dark:text-amber-400",
  normal: "text-foreground",
  low: "text-muted-foreground",
  lowest: "text-muted-foreground/70",
};

const th =
  "h-11 px-3 text-fine font-bold uppercase tracking-wider text-muted-foreground text-center";
const td = "px-3 py-3 text-center";
const tdCenterFlex = "px-3 py-3";
const centerInner = "flex items-center justify-center";

function TagsEditor({
  tags,
  onSave,
}: {
  tags: string[];
  onSave: (tags: string[]) => void;
}) {
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(formatTagsInput(tags));

  useEffect(() => {
    if (!editing) setDraft(formatTagsInput(tags));
  }, [tags, editing]);

  if (!editing) {
    return (
      <button
        type="button"
        onClick={() => setEditing(true)}
        className="inline-flex flex-wrap gap-1 max-w-[200px] justify-start text-left hover:opacity-80"
        title="Click to edit tags"
      >
        {tags.length === 0 ? (
          <span className="inline-block min-h-4 min-w-[1.5rem] text-fine text-muted-foreground/40">
            —
          </span>
        ) : (
          tags.map((tag) => (
            <Badge
              key={tag}
              className="border-transparent bg-secondary text-secondary-foreground hover:bg-secondary/90 text-fine font-medium normal-case tracking-normal"
            >
              {tag}
            </Badge>
          ))
        )}
      </button>
    );
  }

  return (
    <Input
      autoFocus
      value={draft}
      onChange={(event) => setDraft(event.target.value)}
      onBlur={() => {
        const next = parseTagsInput(draft);
        setEditing(false);
        if (formatTagsInput(next) !== formatTagsInput(tags)) onSave(next);
      }}
      onKeyDown={(event) => {
        if (event.key === "Enter") {
          event.currentTarget.blur();
        }
        if (event.key === "Escape") {
          setDraft(formatTagsInput(tags));
          setEditing(false);
        }
      }}
      placeholder="tag1, tag2"
      className="h-8 min-w-[140px] text-xs text-left"
    />
  );
}

export function SourcesTable({
  sources,
  streamFilter = null,
  totalSources,
  loading,
  discovering,
  discoveryResults,
  discoveryMeta,
  discoveryErrors,
  onDiscover,
  onDelete,
  onAutorunChange,
  onAutoTranscribeChange,
  onStatusChange,
  onPriorityChange,
  onTagsChange,
  onOpenItems,
}: {
  sources: Source[];
  streamFilter?: string | null;
  totalSources: number;
  loading: boolean;
  discovering: Set<string>;
  discoveryResults: Record<string, MediaItem[]>;
  discoveryMeta: Record<string, { newCount: number; totalFound: number }>;
  discoveryErrors: Record<string, string>;
  onDiscover: (id: string) => void;
  onDelete: (id: string) => void;
  onAutorunChange: (id: string, autorun: boolean) => void;
  onAutoTranscribeChange: (id: string, auto_transcribe: boolean) => void;
  onStatusChange: (id: string, status: "active" | "paused") => void;
  onPriorityChange: (id: string, priority: SourcePriority) => void;
  onTagsChange: (id: string, tags: string[]) => void;
  onOpenItems: (id: string) => void;
}) {
  const colSpan = 13;

  return (
    <Card className="shadow-sm border border-border/50 overflow-hidden rounded-2xl bg-card">
      <CardHeader className="bg-card border-b border-border/50 py-4">
        <CardTitle className="text-sm font-medium flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Radio className="w-4 h-4 text-muted-foreground" />
            Monitored Sources
          </div>
          <span className="text-fine bg-secondary text-secondary-foreground px-3 py-1 rounded-full font-bold">
            {sources.length} SOURCE{sources.length !== 1 ? "S" : ""}
          </span>
        </CardTitle>
      </CardHeader>

      <div className="overflow-x-auto bg-card">
        <Table className="bg-card">
          <TableHeader className="bg-card">
            <TableRow className="hover:bg-transparent bg-card">
              <TableHead className={`${th} w-[48px]`}>#</TableHead>
              <TableHead className={`${th} w-[72px]`}>Platform</TableHead>
              <TableHead className="h-11 px-5 text-fine font-bold uppercase tracking-wider text-muted-foreground text-left">
                Name
              </TableHead>
              <TableHead className="h-11 px-3 text-fine font-bold uppercase tracking-wider text-muted-foreground text-left w-[160px]">
                Tags
              </TableHead>
              <TableHead className={`${th} w-[56px]`} title="1 = highest, 5 = lowest">
                Priority
              </TableHead>
              <TableHead className={th}>Streams</TableHead>
              <TableHead className={`${th} w-[110px]`}>Autorun</TableHead>
              <TableHead
                className={`${th} w-[120px]`}
                title="Auto-transcribe after Discover"
              >
                Auto TX
              </TableHead>
              <TableHead
                className={`${th} w-[56px]`}
                title="Whether all catalog items on this channel are transcribed"
              >
                TRx
              </TableHead>
              <TableHead className={`${th} w-[64px]`}>Status</TableHead>
              <TableHead className={`${th} w-[140px]`}>Checked</TableHead>
              <TableHead className={`${th} w-[100px]`}>Items</TableHead>
              <TableHead className={`${th} w-[120px]`}>Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {loading && (
              <TableRow>
                <TableCell colSpan={colSpan} className="h-24 text-center text-muted-foreground">
                  <span className="inline-flex items-center gap-2 text-sm"><Loader2 className="w-4 h-4 animate-spin" /> Loading sources…</span>
                </TableCell>
              </TableRow>
            )}
            {!loading && sources.length === 0 && (
              <TableRow>
                <TableCell colSpan={colSpan} className="h-24 text-center text-muted-foreground text-sm">
                  {totalSources === 0
                    ? "No sources yet. Add one above, or promote candidates from Research."
                    : "No sources match this filter."}
                </TableCell>
              </TableRow>
            )}
            {sources.map((source, index) => {
              const isDiscovering = discovering.has(source.id);
              const items = discoveryResults[source.id] ?? [];
              const meta = discoveryMeta[source.id];
              const discoveryError = discoveryErrors[source.id];
              const hasNewItems = items.length > 0;
              const isUpToDate = !!meta && !hasNewItems && !discoveryError;
              const priority = source.priority ?? "normal";
              const tags = source.tags ?? [];

              const displayItemCount =
                streamFilter && source.streams?.length
                  ? source.streams.find((s) => s.stream_type === streamFilter)?.item_count ?? 0
                  : source.item_count ?? 0;

              return (
                <TableRow
                  key={source.id}
                  className={`h-14 bg-card ${isDiscovering ? "opacity-90" : ""}`}
                >
                  <TableCell className={`${td} tabular-nums text-xs text-muted-foreground`}>
                    {index + 1}
                  </TableCell>
                  <TableCell className={tdCenterFlex}>
                    <div className={centerInner}>
                      <PlatformBadge platform={source.platform} variant="logo" />
                    </div>
                  </TableCell>

                  <TableCell className="px-5 py-3 text-left">
                    <div className="flex items-center gap-2 min-w-0">
                      <Link
                        href={`/media/sources/${source.id}`}
                        className="truncate text-sm font-medium hover:text-primary transition-colors"
                        title={source.name}
                      >
                        {source.name}
                      </Link>
                      {discoveryError && (
                        <span
                          title={discoveryError}
                          className="shrink-0 text-red-400"
                        >
                          <AlertCircle className="w-3.5 h-3.5" />
                        </span>
                      )}
                      {isUpToDate && (
                        <span
                          title={`Up to date · ${meta.totalFound} found, all saved`}
                          className="shrink-0 text-emerald-500"
                        >
                          <CheckCircle2 className="w-3.5 h-3.5" />
                        </span>
                      )}
                      {hasNewItems && (
                        <button
                          type="button"
                          onClick={() => onOpenItems(source.id)}
                          title={`${items.length} new item${items.length !== 1 ? "s" : ""} — view results`}
                          className="shrink-0 text-primary hover:text-primary/80"
                        >
                          <CheckCircle2 className="w-3.5 h-3.5" />
                        </button>
                      )}
                    </div>
                  </TableCell>

                  <TableCell className="px-3 py-3 text-left">
                    <TagsEditor
                      tags={tags}
                      onSave={(next) => onTagsChange(source.id, next)}
                    />
                  </TableCell>

                  <TableCell className={tdCenterFlex}>
                    <div className={centerInner}>
                      <Select
                        value={priority}
                        onValueChange={(value) =>
                          onPriorityChange(source.id, value as SourcePriority)
                        }
                      >
                        <SelectTrigger
                          className={`h-8 w-[52px] px-1.5 justify-center text-fine font-medium tabular-nums ${PRIORITY_CLASS[priority]}`}
                          aria-label={`Priority for ${source.name}`}
                          title={
                            PRIORITY_OPTIONS.find((o) => o.value === priority)?.title ??
                            "Priority"
                          }
                        >
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {PRIORITY_OPTIONS.map((option) => (
                            <SelectItem
                              key={option.value}
                              value={option.value!}
                              title={option.title}
                              className="text-fine font-medium tabular-nums justify-center"
                            >
                              {option.label}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                  </TableCell>

                  <TableCell className={tdCenterFlex}>
                    <div className={`${centerInner} flex-wrap gap-2.5 max-w-[280px] mx-auto`}>
                      {(source.streams?.length ? source.streams : [{ stream_type: source.source_type, item_count: source.item_count ?? 0, enabled: true }]).map((stream) => (
                        <Badge
                          key={String(stream.stream_type)}
                          className="gap-1.5 border-transparent bg-secondary text-secondary-foreground hover:bg-secondary/90 text-fine font-medium normal-case tracking-normal"
                        >
                          <span>
                            {sourceTypeLabel(String(stream.stream_type)).replace(
                              /^Facebook |^YouTube |^Instagram |^TikTok /,
                              "",
                            )}
                          </span>
                          <span className="tabular-nums text-secondary-foreground/75">
                            {stream.item_count ?? 0}
                          </span>
                        </Badge>
                      ))}
                    </div>
                  </TableCell>

                  <TableCell className={tdCenterFlex}>
                    <div
                      className={`${centerInner} gap-2`}
                      title={source.autorun ? "Periodically check this source for new items" : "Only check when Discover is clicked"}
                    >
                      <Switch
                        checked={Boolean(source.autorun)}
                        onCheckedChange={(checked) => onAutorunChange(source.id, checked)}
                        aria-label={`Autorun for ${source.name}`}
                      />
                      <span className={`text-fine font-medium ${source.autorun ? "text-primary" : "text-muted-foreground"}`}>
                        {source.autorun ? "On" : "Off"}
                      </span>
                    </div>
                  </TableCell>

                  <TableCell className={tdCenterFlex}>
                    <div
                      className={`${centerInner} gap-2`}
                      title={
                        source.auto_transcribe
                          ? "After Discover, queue pending items for transcription (Settings caps apply)"
                          : "Discover only catalogs — use Transcribe all or turn Auto TX on"
                      }
                    >
                      <Switch
                        checked={Boolean(source.auto_transcribe)}
                        onCheckedChange={(checked) => onAutoTranscribeChange(source.id, checked)}
                        aria-label={`Auto-transcribe for ${source.name}`}
                      />
                      <span className={`text-fine font-medium ${source.auto_transcribe ? "text-primary" : "text-muted-foreground"}`}>
                        {source.auto_transcribe ? "On" : "Off"}
                      </span>
                    </div>
                  </TableCell>

                  <TableCell className={td}>
                    {(() => {
                      const total = Number(source.item_count ?? 0);
                      const done = Number(source.transcription_completed ?? 0);
                      const yes = Boolean(source.transcription_done);
                      return (
                        <span
                          className={`text-fine font-medium ${yes ? "text-primary" : "text-muted-foreground"}`}
                          title={
                            total === 0
                              ? "No catalog items yet"
                              : `${done}/${total} items transcribed`
                          }
                        >
                          {yes ? "Yes" : "No"}
                        </span>
                      );
                    })()}
                  </TableCell>

                  <TableCell className={tdCenterFlex}>
                    {(() => {
                      const isPaused = source.status === "paused";
                      const isError = source.status === "error" || Boolean(source.error_message);
                      const statusTitle = isError
                        ? source.error_message || "Error — click to resume"
                        : isPaused
                          ? "Paused — click to resume"
                          : "Active — click to pause";
                      return (
                        <div className={centerInner}>
                          <button
                            type="button"
                            onClick={() =>
                              onStatusChange(source.id, isPaused || isError ? "active" : "paused")
                            }
                            title={statusTitle}
                            aria-label={statusTitle}
                            className={`inline-flex h-8 w-8 items-center justify-center rounded-md transition-colors ${
                              isError
                                ? "text-red-500 hover:bg-red-500/10"
                                : isPaused
                                  ? "text-muted-foreground hover:bg-muted"
                                  : "text-emerald-500 hover:bg-emerald-500/10"
                            }`}
                          >
                            {isError ? (
                              <AlertCircle className="w-4 h-4" />
                            ) : isPaused ? (
                              <span className="block h-2.5 w-2.5 rounded-full bg-muted-foreground/50" />
                            ) : (
                              <CheckCircle2 className="w-4 h-4" />
                            )}
                          </button>
                        </div>
                      );
                    })()}
                  </TableCell>

                  <TableCell className={`${td} whitespace-nowrap text-xs text-muted-foreground`}>
                    {source.last_checked ? formatRelativeDate(source.last_checked) : "Never"}
                  </TableCell>

                  <TableCell className={`${td} tabular-nums`}>
                    <Link
                      href={`/media/sources/${source.id}`}
                      className="text-sm font-semibold text-foreground hover:text-primary"
                    >
                      {displayItemCount}
                    </Link>
                  </TableCell>

                  <TableCell className={tdCenterFlex}>
                    <div className={`${centerInner} gap-1.5`}>
                      <Button
                        size="icon"
                        variant="outline"
                        className="h-8 w-8"
                        title="Open channel"
                        asChild
                      >
                        <Link href={`/media/sources/${source.id}`}>
                          <ArrowRight className="w-4 h-4" />
                        </Link>
                      </Button>
                      <Button
                        size="icon"
                        variant="ghost"
                        className="h-8 w-8 text-muted-foreground hover:text-foreground"
                        title="Open source page"
                        asChild
                      >
                        <a
                          href={source.source_url}
                          target="_blank"
                          rel="noopener noreferrer"
                        >
                          <ArrowUpRight className="w-4 h-4" />
                        </a>
                      </Button>
                      {(() => {
                        const discoverFailed = Boolean(discoveryError) || source.status === "error" || Boolean(source.error_message);
                        const discoverOk = !discoverFailed && (isUpToDate || Boolean(source.last_checked));
                        const discoverTitle = isDiscovering
                          ? "Discovering…"
                          : source.status === "paused"
                            ? "Paused — resume to discover"
                            : discoverFailed
                              ? discoveryError || source.error_message || "Discover failed — click to retry"
                              : discoverOk
                                ? "Up to date — click to discover again"
                                : "Discover";
                        return (
                          <Button
                            size="icon"
                            variant="ghost"
                            disabled={isDiscovering || source.status === "paused"}
                            onClick={() => onDiscover(source.id)}
                            title={discoverTitle}
                            aria-label={discoverTitle}
                            className={`h-8 w-8 ${
                              isDiscovering
                                ? "text-muted-foreground"
                                : discoverFailed
                                  ? "text-red-500 hover:text-red-400 hover:bg-red-500/10"
                                  : discoverOk
                                    ? "text-emerald-500 hover:text-emerald-400 hover:bg-emerald-500/10"
                                    : "text-muted-foreground hover:text-foreground"
                            }`}
                          >
                            {isDiscovering ? (
                              <Loader2 className="w-4 h-4 animate-spin" />
                            ) : discoverFailed ? (
                              <AlertCircle className="w-4 h-4" />
                            ) : discoverOk ? (
                              <CheckCircle2 className="w-4 h-4" />
                            ) : (
                              <RefreshCw className="w-4 h-4" />
                            )}
                          </Button>
                        );
                      })()}
                      <Button
                        size="icon"
                        variant="ghost"
                        onClick={() => onDelete(source.id)}
                        title="Delete source"
                        className="h-8 w-8 text-muted-foreground hover:text-red-500"
                      >
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      </div>
    </Card>
  );
}
