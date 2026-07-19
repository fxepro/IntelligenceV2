"use client";

import { Telescope, Search, Loader2 } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

/** Platform → real (searchable) or stub. */
export const RESEARCH_PLATFORMS: { id: string; label: string; real: boolean }[] = [
  { id: "youtube", label: "YouTube", real: true },
  { id: "podcast", label: "Podcasts", real: true },
  { id: "website", label: "Web / RSS", real: true },
  { id: "facebook", label: "Facebook", real: true },
  { id: "tiktok", label: "TikTok", real: false },
  { id: "instagram", label: "Instagram", real: false },
];

export function ResearchSearchPanel({
  query,
  onQueryChange,
  selected,
  onTogglePlatform,
  loading,
  onSearch,
}: {
  query: string;
  onQueryChange: (value: string) => void;
  selected: Set<string>;
  onTogglePlatform: (id: string) => void;
  loading: boolean;
  onSearch: () => void;
}) {
  return (
    <Card className="p-4 rounded-2xl border-border/50 shadow-sm space-y-3">
      <div className="flex items-center gap-2">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <Input
            value={query}
            onChange={(e) => onQueryChange(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && onSearch()}
            placeholder='e.g. "independent journalists covering US-China tariffs"'
            className="pl-9 h-11"
          />
        </div>
        <Button onClick={onSearch} disabled={loading || !query.trim()} className="h-11 px-5 gap-2">
          {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Telescope className="w-4 h-4" />}
          {loading ? "Researching…" : "Research"}
        </Button>
      </div>

      <div className="flex items-center gap-2 flex-wrap">
        <span className="text-fine font-bold text-muted-foreground/60 uppercase tracking-widest mr-1">
          Platforms
        </span>
        {RESEARCH_PLATFORMS.map((p) => {
          const on = selected.has(p.id);
          return (
            <button
              key={p.id}
              onClick={() => onTogglePlatform(p.id)}
              title={p.real ? undefined : "No public search API — best-effort / manual"}
              className={`text-fine font-bold uppercase tracking-widest px-3 py-1.5 rounded-full border transition-all ${
                on
                  ? "bg-primary text-primary-foreground border-primary shadow-sm"
                  : "border-border/60 text-muted-foreground hover:border-primary/40 hover:text-foreground"
              } ${!p.real ? "opacity-70" : ""}`}
            >
              {p.label}
              {!p.real && " *"}
            </button>
          );
        })}
      </div>
      <p className="text-fine text-muted-foreground/60">
        * TikTok / Instagram have limited public search — Facebook uses web lookup. Matching
        Sources already in your catalog always appear in results.
      </p>
    </Card>
  );
}
