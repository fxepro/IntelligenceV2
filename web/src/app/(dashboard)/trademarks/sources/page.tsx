"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { Search, X } from "lucide-react";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { AppPageHeader } from "@/components/sections/AppPageHeader";
import { TrademarkSourcesTable } from "@/components/sections/TrademarkSourcesTable";
import { Icon } from "@/lib/icons";
import type { Source, SourcePriority } from "@/lib/mock-data/sources";
import { mapSource, PRIORITY_OPTIONS } from "@/lib/sources/helpers";
import { API_BASE } from "@/lib/api-base";

export default function TrademarkSourcesPage() {
  const [sources, setSources] = useState<Source[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [tagFilter, setTagFilter] = useState("all");
  const [priorityFilter, setPriorityFilter] = useState("all");
  const [statusFilter, setStatusFilter] = useState("all");
  const [connectFilter, setConnectFilter] = useState("all");

  const fetchSources = useCallback(async () => {
    setLoadError(null);
    try {
      const [res, readyRes] = await Promise.all([
        fetch(`${API_BASE}/api/v1/sources?domain=trademarks`),
        fetch(`${API_BASE}/api/v1/trademarks/connect-readiness`),
      ]);
      if (!res.ok) throw new Error(`Failed to load sources (${res.status})`);
      const data = await res.json();
      const readyMap = new Map<string, "api" | "bulk" | "api_bulk">();
      if (readyRes.ok) {
        const readyData = await readyRes.json();
        for (const item of readyData.items ?? []) {
          readyMap.set(String(item.source_id), item.connect_readiness);
        }
      }
      setSources(
        (data.items ?? []).map((raw: unknown) => {
          const mapped = mapSource(raw);
          const readiness = readyMap.get(mapped.id) ?? null;
          return { ...mapped, connect_readiness: readiness };
        }),
      );
    } catch (err: unknown) {
      setLoadError(err instanceof Error ? err.message : "Failed to load sources");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void fetchSources();
  }, [fetchSources]);

  const availableCategories = useMemo(() => {
    const cats = new Set<string>();
    for (const source of sources) {
      const c = (source.category || "").trim();
      if (c) cats.add(c);
    }
    return Array.from(cats).sort((a, b) => a.localeCompare(b));
  }, [sources]);

  const filtered = useMemo(() => {
    const q = searchQuery.trim().toLowerCase();
    return sources
      .filter((source) => {
        if (statusFilter !== "all" && source.status !== statusFilter) return false;
        if (priorityFilter !== "all" && (source.priority ?? "normal") !== priorityFilter) {
          return false;
        }
        if (tagFilter !== "all" && (source.category || "").trim() !== tagFilter) {
          return false;
        }
        if (connectFilter === "ready" && !source.connect_readiness) return false;
        if (
          connectFilter === "api" &&
          source.connect_readiness !== "api" &&
          source.connect_readiness !== "api_bulk"
        ) {
          return false;
        }
        if (
          connectFilter === "bulk" &&
          source.connect_readiness !== "bulk" &&
          source.connect_readiness !== "api_bulk"
        ) {
          return false;
        }
        if (!q) return true;
        const hay = [
          source.catalog_id,
          source.name,
          source.description,
          source.category,
          source.source_url,
          ...(source.tags ?? []),
        ]
          .filter(Boolean)
          .join(" ")
          .toLowerCase();
        return hay.includes(q);
      })
      .sort((a, b) =>
        String(a.catalog_id || "").localeCompare(String(b.catalog_id || ""), undefined, {
          numeric: true,
        }),
      );
  }, [sources, searchQuery, tagFilter, priorityFilter, statusFilter, connectFilter]);

  const patchSource = async (id: string, body: Record<string, unknown>) => {
    const res = await fetch(`${API_BASE}/api/v1/sources/${id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    if (!res.ok) {
      const text = await res.text();
      throw new Error(text || `Update failed (${res.status})`);
    }
    const data = await res.json();
    const mapped = mapSource(data);
    setSources((prev) =>
      prev.map((s) =>
        s.id === id
          ? { ...mapped, connect_readiness: s.connect_readiness ?? mapped.connect_readiness }
          : s,
      ),
    );
  };

  const handlePriority = async (id: string, priority: SourcePriority) => {
    try {
      await patchSource(id, { priority });
    } catch {
      void fetchSources();
    }
  };

  const handleStatus = async (id: string, status: "active" | "paused") => {
    try {
      await patchSource(id, { status });
    } catch {
      void fetchSources();
    }
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      <AppPageHeader
        title="Trademark sources"
        description="National and international trademark registries, gazettes, APIs and classification tools. Detail connectors come later — Batch1 catalog is live."
        icon={<Icon name="landmark" className="h-5 w-5 text-primary" />}
      />

      {loadError ? (
        <p className="text-sm text-red-500">{loadError}</p>
      ) : null}

      <div className="flex flex-col gap-3 sm:flex-row sm:flex-wrap sm:items-center">
        <div className="relative flex-1 min-w-[200px] max-w-md">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search ID, name, URL, category…"
            className="pl-9 pr-9"
          />
          {searchQuery ? (
            <button
              type="button"
              onClick={() => setSearchQuery("")}
              className="absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
              aria-label="Clear search"
            >
              <X className="h-4 w-4" />
            </button>
          ) : null}
        </div>

        <Select value={tagFilter} onValueChange={setTagFilter}>
          <SelectTrigger className="w-full sm:w-[180px]" aria-label="Filter by category">
            <SelectValue placeholder="All categories" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All categories</SelectItem>
            {availableCategories.map((tag) => (
              <SelectItem key={tag} value={tag}>
                {tag}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        <Select value={priorityFilter} onValueChange={setPriorityFilter}>
          <SelectTrigger className="w-full sm:w-[160px]" aria-label="Filter by priority">
            <SelectValue placeholder="All priorities" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All priorities</SelectItem>
            {PRIORITY_OPTIONS.map((option) => (
              <SelectItem key={option.value} value={option.value!} title={option.title}>
                {option.title}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        <Select value={statusFilter} onValueChange={setStatusFilter}>
          <SelectTrigger className="w-full sm:w-[140px]" aria-label="Filter by status">
            <SelectValue placeholder="All statuses" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All statuses</SelectItem>
            <SelectItem value="paused">Paused</SelectItem>
            <SelectItem value="active">Active</SelectItem>
            <SelectItem value="error">Error</SelectItem>
          </SelectContent>
        </Select>

        <Select value={connectFilter} onValueChange={setConnectFilter}>
          <SelectTrigger className="w-full sm:w-[160px]" aria-label="Filter by connect readiness">
            <SelectValue placeholder="Connect" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All connect</SelectItem>
            <SelectItem value="ready">Connect ready</SelectItem>
            <SelectItem value="api">API ready</SelectItem>
            <SelectItem value="bulk">Bulk ready</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <TrademarkSourcesTable
        sources={filtered}
        totalSources={sources.length}
        loading={loading}
        onPriorityChange={handlePriority}
        onStatusChange={handleStatus}
      />
    </div>
  );
}
