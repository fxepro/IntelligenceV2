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
import { CoursesSourcesTable } from "@/components/sections/CoursesSourcesTable";
import { LibraryBreadcrumb } from "@/components/library/LibraryBreadcrumb";
import { Icon } from "@/lib/icons";
import type { Source } from "@/lib/mock-data/sources";
import { mapSource } from "@/lib/sources/helpers";
import { API_BASE } from "@/lib/api-base";

export default function CoursesSourcesPage() {
  const [sources, setSources] = useState<Source[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");

  const fetchSources = useCallback(async () => {
    setLoadError(null);
    try {
      // Best-effort sync; older APIs may not have this route yet.
      await fetch(`${API_BASE}/api/v1/library/sources/ensure`, { method: "POST" }).catch(
        () => null,
      );
      const res = await fetch(`${API_BASE}/api/v1/sources?domain=library`);
      if (!res.ok) throw new Error(`Failed to load sources (${res.status})`);
      const data = await res.json();
      setSources((data.items ?? []).map(mapSource));
    } catch (err: unknown) {
      setLoadError(err instanceof Error ? err.message : "Failed to load sources");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void fetchSources();
  }, [fetchSources]);

  const filtered = useMemo(() => {
    const q = searchQuery.trim().toLowerCase();
    return sources
      .filter((source) => {
        if (statusFilter === "on" && source.status !== "active") return false;
        if (statusFilter === "off" && source.status !== "paused") return false;
        if (!q) return true;
        const hay = [source.catalog_id, source.name, source.description, ...(source.tags ?? [])]
          .filter(Boolean)
          .join(" ")
          .toLowerCase();
        return hay.includes(q);
      })
      .sort((a, b) => (a.name || "").localeCompare(b.name || "", undefined, { sensitivity: "base" }));
  }, [sources, searchQuery, statusFilter]);

  const handleStatus = async (id: string, status: "active" | "paused") => {
    try {
      const res = await fetch(`${API_BASE}/api/v1/sources/${id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status }),
      });
      if (!res.ok) throw new Error(`Update failed (${res.status})`);
      const data = await res.json();
      const mapped = mapSource(data);
      setSources((prev) => prev.map((s) => (s.id === id ? mapped : s)));
    } catch {
      void fetchSources();
    }
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      <div className="space-y-3">
        <LibraryBreadcrumb items={[{ label: "Sources" }]} />
        <AppPageHeader
          title="Sources"
          description="Courses in this domain. Turn On/Off, then open a course to edit lessons."
          icon={<Icon name="library" className="h-5 w-5 text-primary" />}
        />
      </div>

      {loadError ? <p className="text-sm text-red-500">{loadError}</p> : null}

      <div className="flex flex-col gap-3 sm:flex-row sm:flex-wrap sm:items-center">
        <div className="relative flex-1 min-w-[200px] max-w-md">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search course name…"
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

        <Select value={statusFilter} onValueChange={setStatusFilter}>
          <SelectTrigger className="w-full sm:w-[140px]" aria-label="Filter by On/Off">
            <SelectValue placeholder="All" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All</SelectItem>
            <SelectItem value="on">On</SelectItem>
            <SelectItem value="off">Off</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <CoursesSourcesTable
        sources={filtered}
        totalSources={sources.length}
        loading={loading}
        onStatusChange={handleStatus}
      />
    </div>
  );
}
