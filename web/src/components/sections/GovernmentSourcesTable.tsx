"use client";

import Link from "next/link";
import { AlertCircle, ArrowUpRight, CheckCircle2, Loader2 } from "lucide-react";
import { Card, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
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
import type { Source, SourcePriority } from "@/lib/mock-data/sources";
import { PRIORITY_OPTIONS } from "@/lib/sources/helpers";
import { Icon, type IconName } from "@/lib/icons";

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

export function GovernmentSourcesTable({
  sources,
  totalSources,
  loading,
  onPriorityChange,
  onStatusChange,
  title = "Government sources",
  icon = "building",
  detailBasePath = "/government/sources",
  emptyMessage = "No government sources yet. Seed the catalog to populate this list.",
}: {
  sources: Source[];
  totalSources: number;
  loading: boolean;
  onPriorityChange: (id: string, priority: SourcePriority) => void;
  onStatusChange: (id: string, status: "active" | "paused") => void;
  title?: string;
  icon?: IconName;
  detailBasePath?: string;
  emptyMessage?: string;
}) {
  const colSpan = 8;

  return (
    <Card className="shadow-sm border border-border/50 overflow-hidden rounded-2xl bg-card">
      <CardHeader className="bg-card border-b border-border/50 py-4">
        <CardTitle className="text-sm font-medium flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Icon name={icon} className="w-4 h-4 text-muted-foreground" />
            {title}
          </div>
          <span className="text-fine bg-secondary text-secondary-foreground px-3 py-1 rounded-full font-bold">
            {sources.length} / {totalSources} SOURCE{totalSources !== 1 ? "S" : ""}
          </span>
        </CardTitle>
      </CardHeader>

      <div className="overflow-x-auto bg-card">
        <Table className="bg-card">
          <TableHeader className="bg-card">
            <TableRow className="hover:bg-transparent bg-card">
              <TableHead className={`${th} w-[48px]`}>#</TableHead>
              <TableHead className={`${th} w-[100px]`}>ID</TableHead>
              <TableHead className="h-11 px-5 text-fine font-bold uppercase tracking-wider text-muted-foreground text-left">
                Name
              </TableHead>
              <TableHead className="h-11 px-3 text-fine font-bold uppercase tracking-wider text-muted-foreground text-left w-[160px]">
                Category
              </TableHead>
              <TableHead className={`${th} w-[64px]`} title="1 = highest, 5 = lowest">
                Priority
              </TableHead>
              <TableHead className="h-11 px-3 text-fine font-bold uppercase tracking-wider text-muted-foreground text-left min-w-[200px]">
                Access
              </TableHead>
              <TableHead className={`${th} w-[72px]`}>Status</TableHead>
              <TableHead className={`${th} w-[72px]`}>Open</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {loading && (
              <TableRow>
                <TableCell colSpan={colSpan} className="h-24 text-center text-muted-foreground">
                  <span className="inline-flex items-center gap-2 text-sm">
                    <Loader2 className="w-4 h-4 animate-spin" /> Loading sources…
                  </span>
                </TableCell>
              </TableRow>
            )}
            {!loading && sources.length === 0 && (
              <TableRow>
                <TableCell colSpan={colSpan} className="h-24 text-center text-muted-foreground text-sm">
                  {totalSources === 0 ? emptyMessage : "No sources match this filter."}
                </TableCell>
              </TableRow>
            )}
            {sources.map((source, index) => {
              const priority = source.priority ?? "normal";
              const category = (source.category || "").trim();
              const isPaused = source.status === "paused";
              const isError = source.status === "error" || Boolean(source.error_message);

              return (
                <TableRow key={source.id} className="h-14 bg-card">
                  <TableCell className={`${td} tabular-nums text-xs font-medium text-muted-foreground`}>
                    {index + 1}
                  </TableCell>
                  <TableCell className={`${td} tabular-nums text-xs font-medium text-muted-foreground`}>
                    {source.catalog_id ?? "—"}
                  </TableCell>

                  <TableCell className="px-5 py-3 text-left">
                    <div className="min-w-0">
                      <p className="truncate text-sm font-medium" title={source.name}>
                        {source.name}
                      </p>
                      {source.description ? (
                        <p
                          className="truncate text-xs text-muted-foreground mt-0.5 max-w-md"
                          title={source.description}
                        >
                          {source.description}
                        </p>
                      ) : null}
                    </div>
                  </TableCell>

                  <TableCell className="px-3 py-3 text-left">
                    <div className="flex flex-wrap items-center justify-start gap-1">
                      {category ? (
                        <Badge className="border-transparent bg-secondary text-secondary-foreground text-fine font-medium normal-case tracking-normal">
                          {category}
                        </Badge>
                      ) : (
                        <span className="text-fine text-muted-foreground/50">—</span>
                      )}
                    </div>
                  </TableCell>

                  <TableCell className="px-3 py-3">
                    <div className="flex justify-center">
                      <Select
                        value={priority}
                        onValueChange={(value) =>
                          onPriorityChange(source.id, value as SourcePriority)
                        }
                      >
                        <SelectTrigger
                          className={`h-8 w-[52px] px-1.5 justify-center text-fine font-medium tabular-nums ${PRIORITY_CLASS[priority]}`}
                          aria-label={`Priority for ${source.name}`}
                        >
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {PRIORITY_OPTIONS.map((option) => (
                            <SelectItem
                              key={option.value}
                              value={option.value!}
                              className="text-fine font-medium tabular-nums justify-center"
                            >
                              {option.label}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                  </TableCell>

                  <TableCell className="px-3 py-3 text-left">
                    <a
                      href={source.source_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex max-w-[280px] items-center gap-1 truncate text-xs text-primary hover:underline"
                      title={source.source_url}
                    >
                      <span className="truncate">{source.source_url.replace(/^https?:\/\//, "")}</span>
                      <ArrowUpRight className="w-3.5 h-3.5 shrink-0" />
                    </a>
                  </TableCell>

                  <TableCell className="px-3 py-3">
                    <div className="flex justify-center">
                      <button
                        type="button"
                        onClick={() =>
                          onStatusChange(
                            source.id,
                            isPaused || isError ? "active" : "paused",
                          )
                        }
                        title={
                          isError
                            ? source.error_message || "Error — click to resume"
                            : isPaused
                              ? "Paused — click to activate"
                              : "Active — click to pause"
                        }
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
                  </TableCell>

                  <TableCell className="px-3 py-3">
                    <div className="flex justify-center">
                      <Link
                        href={`${detailBasePath}/${source.id}`}
                        className="inline-flex h-8 w-8 items-center justify-center rounded-md border border-border/60 text-muted-foreground hover:text-foreground hover:bg-muted"
                        title="Open source"
                      >
                        <Icon name="arrowRight" className="w-4 h-4" />
                      </Link>
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
