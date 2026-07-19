"use client";

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { PlatformIcon } from "@/components/sections/PlatformBadge";

export type ReadFilter = "all" | "unread" | "read";

export function IntelligenceFilters({
  platformFilter,
  onPlatformFilterChange,
  readFilter,
  onReadFilterChange,
  platforms,
  platformCounts,
  itemsLength,
  unreadCount,
  readCount,
  filteredCount,
}: {
  platformFilter: string;
  onPlatformFilterChange: (value: string) => void;
  readFilter: ReadFilter;
  onReadFilterChange: (value: ReadFilter) => void;
  platforms: string[];
  platformCounts: Record<string, number>;
  itemsLength: number;
  unreadCount: number;
  readCount: number;
  filteredCount: number;
}) {
  return (
    <div className="flex flex-col sm:flex-row sm:items-end gap-3 sm:gap-4">
      <div className="space-y-1.5 min-w-[180px]">
        <label className="text-fine font-bold uppercase tracking-widest text-muted-foreground">Platform</label>
        <Select value={platformFilter} onValueChange={onPlatformFilterChange}>
          <SelectTrigger className="h-9">
            <SelectValue placeholder="All platforms" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All platforms ({itemsLength})</SelectItem>
            {platforms.map((p) => (
              <SelectItem key={p} value={p}>
                <span className="inline-flex items-center gap-2 capitalize">
                  <PlatformIcon platform={p} className="w-3.5 h-3.5" />
                  {p} ({platformCounts[p] ?? 0})
                </span>
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <div className="space-y-1.5 min-w-[180px]">
        <label className="text-fine font-bold uppercase tracking-widest text-muted-foreground">Read status</label>
        <Select value={readFilter} onValueChange={(v) => onReadFilterChange(v as ReadFilter)}>
          <SelectTrigger className="h-9">
            <SelectValue placeholder="All" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All ({itemsLength})</SelectItem>
            <SelectItem value="unread">Unread ({unreadCount})</SelectItem>
            <SelectItem value="read">Read ({readCount})</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <p className="text-xs text-muted-foreground sm:ml-auto sm:pb-2">
        Showing {filteredCount} of {itemsLength}
      </p>
    </div>
  );
}
