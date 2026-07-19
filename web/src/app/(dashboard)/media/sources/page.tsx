"use client";

import React, { useState, useEffect, useCallback } from "react";
import { CheckCircle2, AlertCircle, Loader2, Search, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { AppPageHeader } from "@/components/sections/AppPageHeader";
import { SourcesTable } from "@/components/sections/SourcesTable";
import { AddSourceDialog } from "@/components/sections/AddSourceDialog";
import { DiscoveryResultsDialog } from "@/components/sections/DiscoveryResultsDialog";
import { Icon } from "@/lib/icons";
import { ctas } from "@/config/ctas";
import type { Source, Platform, SourcePriority } from "@/lib/mock-data/sources";
import type { MediaItem } from "@/lib/mock-data/media-items";
import {
  mapSource,
  mapDiscoveredItems,
  PLATFORM_OPTIONS,
  PRIORITY_OPTIONS,
  SOURCE_TYPES_BY_PLATFORM,
} from "@/lib/sources/helpers";

import { API_BASE } from "@/lib/api-base";

export default function SourcesPage() {
  const [sources, setSources] = useState<Source[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [discovering, setDiscovering] = useState<Set<string>>(new Set());
  const [discoveryResults, setDiscoveryResults] = useState<Record<string, MediaItem[]>>({});
  const [discoveryMeta, setDiscoveryMeta] = useState<Record<string, { newCount: number; totalFound: number }>>({});
  const [discoveryErrors, setDiscoveryErrors] = useState<Record<string, string>>({});
  const [itemsDialogId, setItemsDialogId] = useState<string | null>(null);
  const [discoveringAll, setDiscoveringAll] = useState(false);
  const [discoverAllSummary, setDiscoverAllSummary] = useState<string | null>(null);

  const [showAdd, setShowAdd] = useState(false);
  const [platformTab, setPlatformTab] = useState<Platform>("facebook");
  const [typeFilter, setTypeFilter] = useState("all");
  const [tagFilter, setTagFilter] = useState("all");
  const [priorityFilter, setPriorityFilter] = useState("all");
  const [searchQuery, setSearchQuery] = useState("");

  const fetchSources = useCallback(async () => {
    setLoadError(null);
    try {
      const res = await fetch(`${API_BASE}/api/v1/sources`);
      if (!res.ok) throw new Error(`Failed to load sources (${res.status})`);
      const data = await res.json();
      setSources((data.items ?? []).map(mapSource));
    } catch (err: any) {
      setLoadError(err.message ?? "Failed to load sources");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchSources();
  }, [fetchSources]);

  const platformItemCounts = sources.reduce<Record<string, number>>((acc, source) => {
    acc[source.platform] =
      (acc[source.platform] ?? 0) + Number(source.item_count ?? 0);
    return acc;
  }, {});

  const platformSources = sources.filter((source) => source.platform === platformTab);
  const availableTags = Array.from(
    new Set(
      platformSources.flatMap((source) => source.tags ?? []).map((tag) => tag.trim()).filter(Boolean)
    )
  ).sort((a, b) => a.localeCompare(b));
  const platformItemTotal = platformSources.reduce(
    (sum, source) => sum + Number(source.item_count ?? 0),
    0
  );
  const streamCount = (source: Source, streamType: string) =>
    source.streams?.find((stream) => stream.stream_type === streamType)?.item_count ??
    (source.source_type === streamType ? source.item_count ?? 0 : 0);
  const typeFiltered =
    typeFilter === "all"
      ? platformSources
      : platformSources.filter(
          (source) =>
            source.streams?.some((stream) => stream.stream_type === typeFilter) ||
            source.source_type === typeFilter
        );
  const tagFiltered =
    tagFilter === "all"
      ? typeFiltered
      : typeFiltered.filter((source) =>
          (source.tags ?? []).some((tag) => tag.toLowerCase() === tagFilter.toLowerCase())
        );
  const priorityFiltered =
    priorityFilter === "all"
      ? tagFiltered
      : tagFiltered.filter((source) => (source.priority ?? "normal") === priorityFilter);
  const normalizedSearch = searchQuery.trim().toLowerCase();
  const filtered = normalizedSearch
    ? priorityFiltered.filter((source) =>
        [source.name, source.source_url, source.description, ...(source.tags ?? [])]
          .filter(Boolean)
          .some((value) => String(value).toLowerCase().includes(normalizedSearch))
      )
    : priorityFiltered;
  const typeOptions = SOURCE_TYPES_BY_PLATFORM[platformTab];
  const handleTrigger = async (id: string, sourceOverride?: Source) => {
    // sourceOverride is required right after create — React state won't have it yet.
    const source = sourceOverride ?? sources.find((s) => s.id === id);
    if (!source) return;

    setDiscovering((prev) => new Set(prev).add(id));
    setDiscoveryErrors((prev) => { const n = { ...prev }; delete n[id]; return n; });

    try {
      const res = await fetch(`${API_BASE}/api/v1/discover/source/${id}`, { method: "POST" });
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: "Unknown error" }));
        throw new Error(err.detail ?? "Discovery failed");
      }

      const data = await res.json();
      const jobId = data.job_id as string | undefined;

      // Wait for worker (enqueue alone always returns new=0)
      if (jobId) {
        for (let i = 0; i < 90; i++) {
          await new Promise((r) => setTimeout(r, 2000));
          const jr = await fetch(`${API_BASE}/api/v1/jobs/${jobId}`);
          const job = await jr.json().catch(() => ({}));
          if (!jr.ok) continue;
          if (job.status === "completed" || job.status === "failed") {
            if (job.status === "failed") {
              throw new Error(job.error_message || "Discovery job failed");
            }
            const result = job.result || {};
            setDiscoveryMeta((prev) => ({
              ...prev,
              [id]: {
                newCount: Number(result.new ?? 0),
                totalFound: Number(result.total_found ?? result.discovered ?? 0),
              },
            }));
            break;
          }
        }
      } else {
        setDiscoveryMeta((prev) => ({
          ...prev,
          [id]: { newCount: data.new ?? 0, totalFound: data.total_found ?? 0 },
        }));
      }

      // Load saved media items for the results dialog.
      const mediaRes = await fetch(
        `${API_BASE}/api/v1/media?source_id=${id}&page_size=50`
      );
      const media = mediaRes.ok ? await mediaRes.json() : { items: [] };
      const items = (media.items ?? []).map((m: any) => ({
        ...m,
        source_id: id,
      }));
      setDiscoveryResults((prev) => ({ ...prev, [id]: items }));
      if (items.length) setItemsDialogId(id);
      await fetchSources(); // Refresh stream and item counts.
    } catch (err: any) {
      setDiscoveryErrors((prev) => ({ ...prev, [id]: err.message ?? "Discovery failed" }));
    } finally {
      setDiscovering((prev) => { const n = new Set(prev); n.delete(id); return n; });
    }
  };

  const handleDiscoverAll = async () => {
    setDiscoveringAll(true);
    setDiscoverAllSummary(null);
    try {
      const res = await fetch(`${API_BASE}/api/v1/discover/all`, { method: "POST" });
      if (!res.ok) throw new Error("Discover All failed");
      const data = await res.json();

      const newResults: Record<string, MediaItem[]> = {};
      const newMeta: Record<string, { newCount: number; totalFound: number }> = {};
      const errs: Record<string, string> = {};
      for (const r of data.results ?? []) {
        if (r.error) { errs[r.source_id] = r.error; continue; }
        const source = sources.find((s) => s.id === r.source_id);
        if (!source) continue;
        newResults[r.source_id] = mapDiscoveredItems(r.items, source);
        newMeta[r.source_id] = { newCount: r.new, totalFound: r.total_found };
      }

      setDiscoveryResults((prev) => ({ ...prev, ...newResults }));
      setDiscoveryMeta((prev) => ({ ...prev, ...newMeta }));
      setDiscoveryErrors((prev) => ({ ...prev, ...errs }));
      setDiscoverAllSummary(
        `Checked ${data.sources_checked} source${data.sources_checked !== 1 ? "s" : ""} — ${data.total_new} new item${data.total_new !== 1 ? "s" : ""} saved.`
      );
      fetchSources(); // refresh last_checked
    } catch (err: any) {
      setDiscoverAllSummary(err.message ?? "Discover All failed");
    } finally {
      setDiscoveringAll(false);
    }
  };

  const handleAddSource = async (
    data: Partial<Source> & {
      discover?: boolean;
      stream_urls?: Record<string, string>;
    }
  ) => {
    const res = await fetch(`${API_BASE}/api/v1/sources`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        platform: data.platform ?? "website",
        source_type:
          data.source_type ??
          SOURCE_TYPES_BY_PLATFORM[data.platform ?? "website"][0].value,
        source_url: data.source_url ?? "",
        stream_urls: data.stream_urls ?? {},
        name: data.name || null,
        description: data.description || null,
        tags: data.tags ?? [],
        priority: data.priority ?? "normal",
      }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: "Failed to add source" }));
      throw new Error(typeof err.detail === "string" ? err.detail : "Failed to add source");
    }
    const created = await res.json();
    const mapped = mapSource(created);
    setSources((prev) => [mapped, ...prev]);

    if (data.discover) {
      // Pass the just-created source — setSources hasn't flushed into `sources` yet,
      // so handleTrigger(id) alone would no-op on sources.find.
      void handleTrigger(mapped.id, mapped);
    }
  };

  const handleDelete = async (id: string) => {
    const prev = sources;
    setSources((s) => s.filter((x) => x.id !== id)); // optimistic
    const res = await fetch(`${API_BASE}/api/v1/sources/${id}`, { method: "DELETE" });
    if (!res.ok) setSources(prev); // rollback on failure
  };

  const handleAutorun = async (id: string, autorun: boolean) => {
    const prev = sources.find((s) => s.id === id)?.autorun;
    setSources((list) => list.map((s) => (s.id === id ? { ...s, autorun } : s)));
    try {
      const res = await fetch(`${API_BASE}/api/v1/sources/${id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ autorun }),
      });
      if (!res.ok) throw new Error("Failed to update autorun");
      const updated = await res.json();
      setSources((list) => list.map((s) => (s.id === id ? mapSource(updated) : s)));
    } catch {
      setSources((list) => list.map((s) => (s.id === id ? { ...s, autorun: Boolean(prev) } : s)));
    }
  };

  const handleAutoTranscribe = async (id: string, auto_transcribe: boolean) => {
    const prev = sources.find((s) => s.id === id)?.auto_transcribe;
    setSources((list) => list.map((s) => (s.id === id ? { ...s, auto_transcribe } : s)));
    try {
      const res = await fetch(`${API_BASE}/api/v1/sources/${id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ auto_transcribe }),
      });
      if (!res.ok) throw new Error("Failed to update auto-transcribe");
      const updated = await res.json();
      setSources((list) => list.map((s) => (s.id === id ? mapSource(updated) : s)));
    } catch {
      setSources((list) =>
        list.map((s) => (s.id === id ? { ...s, auto_transcribe: Boolean(prev) } : s)),
      );
    }
  };

  const handleStatus = async (id: string, status: "active" | "paused") => {
    const previous = sources.find((source) => source.id === id)?.status;
    setSources((list) =>
      list.map((source) => (source.id === id ? { ...source, status } : source))
    );
    try {
      const res = await fetch(`${API_BASE}/api/v1/sources/${id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status }),
      });
      if (!res.ok) throw new Error("Failed to update source status");
      const updated = await res.json();
      setSources((list) =>
        list.map((source) => (source.id === id ? mapSource(updated) : source))
      );
    } catch {
      if (!previous) return;
      setSources((list) =>
        list.map((source) =>
          source.id === id ? { ...source, status: previous } : source
        )
      );
    }
  };

  const handlePriority = async (id: string, priority: SourcePriority) => {
    const previous = sources.find((source) => source.id === id)?.priority ?? "normal";
    setSources((list) =>
      list.map((source) => (source.id === id ? { ...source, priority } : source))
    );
    try {
      const res = await fetch(`${API_BASE}/api/v1/sources/${id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ priority }),
      });
      if (!res.ok) throw new Error("Failed to update priority");
      const updated = await res.json();
      setSources((list) =>
        list.map((source) => (source.id === id ? mapSource(updated) : source))
      );
    } catch {
      setSources((list) =>
        list.map((source) =>
          source.id === id ? { ...source, priority: previous } : source
        )
      );
    }
  };

  const handleTags = async (id: string, tags: string[]) => {
    const previous = sources.find((source) => source.id === id)?.tags ?? [];
    setSources((list) =>
      list.map((source) => (source.id === id ? { ...source, tags } : source))
    );
    try {
      const res = await fetch(`${API_BASE}/api/v1/sources/${id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ tags }),
      });
      if (!res.ok) throw new Error("Failed to update tags");
      const updated = await res.json();
      setSources((list) =>
        list.map((source) => (source.id === id ? mapSource(updated) : source))
      );
    } catch {
      setSources((list) =>
        list.map((source) =>
          source.id === id ? { ...source, tags: previous } : source
        )
      );
    }
  };

  return (
    <div className="space-y-8 animate-in fade-in duration-500">
      <AppPageHeader
        title="Sources"
        description="Platform layer — channels and pages with manual or scheduled discovery. Autorun periodically checks enabled sources for new items."
        actions={
          <>
            <Button
              variant="outline"
              onClick={handleDiscoverAll}
              disabled={discoveringAll || sources.length === 0}
              className="gap-2"
            >
              {discoveringAll ? <Loader2 className="w-4 h-4 animate-spin" /> : <Icon name="refresh" className="w-4 h-4" />}
              {discoveringAll ? "Discovering…" : ctas.discoverAll.label}
            </Button>
            <Button onClick={() => setShowAdd(true)} className="gap-2 shadow-lg shadow-primary/10 hover:scale-[1.02] transition-transform">
              <Icon name="plus" className="w-4 h-4" /> {ctas.addSource.label}
            </Button>
          </>
        }
      />

      {discoverAllSummary && (
        <div className="flex items-center gap-2 text-sm text-primary bg-primary/5 border border-primary/20 rounded-xl px-4 py-3">
          <CheckCircle2 className="w-4 h-4 flex-shrink-0" /> {discoverAllSummary}
        </div>
      )}

      {loadError && (
        <div className="flex items-center justify-between gap-2 text-sm text-red-400 bg-red-500/5 border border-red-500/20 rounded-xl px-4 py-3">
          <span className="flex items-center gap-2"><AlertCircle className="w-4 h-4 flex-shrink-0" /> {loadError}</span>
          <Button size="sm" variant="outline" onClick={fetchSources} className="h-7 text-xs">Retry</Button>
        </div>
      )}

      <div className="space-y-3">
        <Tabs
          value={platformTab}
          onValueChange={(value) => {
            setPlatformTab(value as Platform);
            setTypeFilter("all");
            setTagFilter("all");
            setPriorityFilter("all");
          }}
        >
          <TabsList className="h-auto w-full justify-start overflow-x-auto rounded-xl border border-border/60 bg-secondary/40 p-1">
            {PLATFORM_OPTIONS.map((platform) => (
              <TabsTrigger
                key={platform.id}
                value={platform.id}
                className="group gap-2 rounded-lg px-4 py-2 data-[state=active]:bg-accent data-[state=active]:text-accent-foreground data-[state=active]:shadow-sm"
              >
                {platform.label}
                <span className="text-fine tabular-nums text-muted-foreground group-data-[state=active]:text-accent-foreground/85">
                  {platformItemCounts[platform.id] ?? 0}
                </span>
              </TabsTrigger>
            ))}
          </TabsList>
        </Tabs>

        <div className="flex flex-col gap-3">
          <div className="relative w-full sm:max-w-md">
            <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              value={searchQuery}
              onChange={(event) => setSearchQuery(event.target.value)}
              placeholder="Search channels by name, URL, or tag…"
              aria-label="Search channels"
              className={`border border-border/60 bg-card pl-9 focus-visible:ring-ring ${searchQuery ? "pr-9" : ""}`}
            />
            {searchQuery ? (
              <button
                type="button"
                onClick={() => setSearchQuery("")}
                className="absolute right-2 top-1/2 -translate-y-1/2 inline-flex h-7 w-7 items-center justify-center rounded-md text-muted-foreground hover:bg-muted hover:text-foreground"
                aria-label="Clear search"
                title="Clear search"
              >
                <X className="h-4 w-4" />
              </button>
            ) : null}
          </div>
          <div className="flex flex-col sm:flex-row sm:flex-wrap gap-3">
            <Select value={typeFilter} onValueChange={setTypeFilter}>
              <SelectTrigger
                className="w-full border border-border/60 bg-card sm:w-[220px] focus:ring-ring"
                aria-label="Filter by content type"
              >
                <SelectValue placeholder="All content types" />
              </SelectTrigger>
              <SelectContent className="border-border/60">
                <SelectItem value="all">All content types ({platformItemTotal})</SelectItem>
                {typeOptions.map((type) => {
                  const count = platformSources.reduce(
                    (sum, source) => sum + streamCount(source, type.value),
                    0
                  );
                  return (
                    <SelectItem key={type.value} value={type.value}>
                      {type.label} ({count})
                    </SelectItem>
                  );
                })}
              </SelectContent>
            </Select>
            <Select value={tagFilter} onValueChange={setTagFilter}>
              <SelectTrigger
                className="w-full border border-border/60 bg-card sm:w-[200px] focus:ring-ring"
                aria-label="Filter by tag"
              >
                <SelectValue placeholder="All tags" />
              </SelectTrigger>
              <SelectContent className="border-border/60">
                <SelectItem value="all">All tags</SelectItem>
                {availableTags.map((tag) => (
                  <SelectItem key={tag} value={tag}>
                    {tag}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Select value={priorityFilter} onValueChange={setPriorityFilter}>
              <SelectTrigger
                className="w-full border border-border/60 bg-card sm:w-[180px] focus:ring-ring"
                aria-label="Filter by priority"
              >
                <SelectValue placeholder="All priorities" />
              </SelectTrigger>
              <SelectContent className="border-border/60">
                <SelectItem value="all">All priorities</SelectItem>
                {PRIORITY_OPTIONS.map((option) => (
                  <SelectItem key={option.value} value={option.value!} title={option.title}>
                    {option.title}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>
      </div>

      <SourcesTable
        sources={filtered}
        streamFilter={typeFilter === "all" ? null : typeFilter}
        totalSources={sources.length}
        loading={loading}
        discovering={discovering}
        discoveryResults={discoveryResults}
        discoveryMeta={discoveryMeta}
        discoveryErrors={discoveryErrors}
        onDiscover={handleTrigger}
        onDelete={handleDelete}
        onAutorunChange={handleAutorun}
        onAutoTranscribeChange={handleAutoTranscribe}
        onStatusChange={handleStatus}
        onPriorityChange={handlePriority}
        onTagsChange={handleTags}
        onOpenItems={setItemsDialogId}
      />

      <AddSourceDialog open={showAdd} onClose={() => setShowAdd(false)} onAdd={handleAddSource} />

      <DiscoveryResultsDialog
        open={!!itemsDialogId}
        onClose={() => setItemsDialogId(null)}
        source={itemsDialogId ? sources.find((s) => s.id === itemsDialogId) : undefined}
        items={itemsDialogId ? discoveryResults[itemsDialogId] ?? [] : []}
        meta={itemsDialogId ? discoveryMeta[itemsDialogId] : undefined}
      />
    </div>
  );
}
