"use client";

import type { Platform, Source } from "@/lib/mock-data/sources";

const FILTER_OPTIONS = [
  "all",
  "youtube",
  "facebook",
  "tiktok",
  "instagram",
  "rss",
  "podcast",
  "website",
] as const;

export function PlatformFilterPills({
  filter,
  onFilterChange,
  sources,
  platformCounts,
}: {
  filter: Platform | "all";
  onFilterChange: (filter: Platform | "all") => void;
  sources: Source[];
  platformCounts: Record<string, number>;
}) {
  return (
    <div className="flex items-center gap-2 flex-wrap">
      {FILTER_OPTIONS.map((p) => (
        <button
          key={p}
          type="button"
          onClick={() => onFilterChange(p)}
          className={`text-fine font-bold uppercase tracking-widest px-3 py-1.5 rounded-full border transition-all ${
            filter === p
              ? "bg-primary text-primary-foreground border-primary shadow-sm"
              : "border-border/60 text-muted-foreground hover:border-primary/40 hover:text-foreground"
          }`}
        >
          {p === "all" ? `All (${sources.length})` : `${p} (${platformCounts[p] ?? 0})`}
        </button>
      ))}
    </div>
  );
}
