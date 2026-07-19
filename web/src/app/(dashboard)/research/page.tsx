"use client";

import React, { useState } from "react";
import { AlertTriangle } from "lucide-react";
import { AppPageHeader } from "@/components/sections/AppPageHeader";
import {
  ResearchSearchPanel,
  RESEARCH_PLATFORMS,
} from "@/components/sections/ResearchSearchPanel";
import { ResearchResults } from "@/components/sections/ResearchResults";
import type { Candidate } from "@/components/sections/CandidateCard";
import { Icon } from "@/lib/icons";

import { API_BASE } from "@/lib/api-base";

export default function ResearchPage() {
  const [query, setQuery] = useState("");
  const [selected, setSelected] = useState<Set<string>>(
    new Set(RESEARCH_PLATFORMS.filter((p) => p.real).map((p) => p.id)),
  );
  const [loading, setLoading] = useState(false);
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [notices, setNotices] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<string | null>(null);
  const [searched, setSearched] = useState(false);

  const togglePlatform = (id: string) =>
    setSelected((prev) => {
      const n = new Set(prev);
      n.has(id) ? n.delete(id) : n.add(id);
      return n;
    });

  const runSearch = async () => {
    if (!query.trim()) return;
    setLoading(true);
    setError(null);
    setSearched(true);
    try {
      const res = await fetch(`${API_BASE}/api/v1/research`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query: query.trim(),
          platforms: Array.from(selected),
          max_per_platform: 10,
        }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: "Research failed" }));
        throw new Error(err.detail ?? "Research failed");
      }
      const data = await res.json();
      setCandidates(data.candidates ?? []);
      setNotices(data.notices ?? []);
    } catch (err: any) {
      setError(err.message ?? "Research failed");
      setCandidates([]);
    } finally {
      setLoading(false);
    }
  };

  const promote = async (id: string) => {
    setBusyId(id);
    try {
      const res = await fetch(`${API_BASE}/api/v1/research/candidates/${id}/promote`, {
        method: "POST",
      });
      if (!res.ok) throw new Error();
      setCandidates((prev) =>
        prev.map((c) => (c.id === id ? { ...c, status: "promoted" } : c)),
      );
    } catch {
      setError("Failed to add source.");
    } finally {
      setBusyId(null);
    }
  };

  const dismiss = async (id: string) => {
    setBusyId(id);
    try {
      await fetch(`${API_BASE}/api/v1/research/candidates/${id}/dismiss`, { method: "POST" });
      setCandidates((prev) => prev.filter((c) => c.id !== id));
    } catch {
      setError("Failed to dismiss.");
    } finally {
      setBusyId(null);
    }
  };

  return (
    <div className="space-y-8 animate-in fade-in duration-500">
      <AppPageHeader
        title="Research"
        icon={
          <div className="p-1.5 bg-primary/10 rounded-lg">
            <Icon name="telescope" className="w-5 h-5 text-primary" />
          </div>
        }
        description="Discover new sources to monitor. Matching names already in Sources appear first; then the engine searches platforms and ranks who else is worth watching."
      />

      <ResearchSearchPanel
        query={query}
        onQueryChange={setQuery}
        selected={selected}
        onTogglePlatform={togglePlatform}
        loading={loading}
        onSearch={runSearch}
      />

      {error && (
        <div className="flex items-center gap-2 text-sm text-red-400 bg-red-500/5 border border-red-500/20 rounded-xl px-4 py-3">
          <AlertTriangle className="w-4 h-4 flex-shrink-0" /> {error}
        </div>
      )}

      {notices.length > 0 && (
        <div className="space-y-1.5">
          {notices.map((n, i) => (
            <div
              key={i}
              className="flex items-center gap-2 text-caption text-muted-foreground bg-muted/40 border border-border/40 rounded-lg px-3 py-2"
            >
              <AlertTriangle className="w-3.5 h-3.5 flex-shrink-0 opacity-60" /> {n}
            </div>
          ))}
        </div>
      )}

      <ResearchResults
        loading={loading}
        searched={searched}
        candidates={candidates}
        busyId={busyId}
        onPromote={promote}
        onDismiss={dismiss}
      />
    </div>
  );
}
