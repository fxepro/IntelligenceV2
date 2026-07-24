"use client";

import Link from "next/link";
import { CheckCircle2, Loader2, AlertCircle } from "lucide-react";
import { Card, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import type { Source } from "@/lib/mock-data/sources";
import { Icon } from "@/lib/icons";
import { libraryCourseIdFromSource } from "@/lib/sources/helpers";

const th =
  "h-11 px-3 text-fine font-bold uppercase tracking-wider text-muted-foreground text-center";
const td = "px-3 py-3 text-center";

export function CoursesSourcesTable({
  sources,
  totalSources,
  loading,
  onStatusChange,
}: {
  sources: Source[];
  totalSources: number;
  loading: boolean;
  onStatusChange: (id: string, status: "active" | "paused") => void;
}) {
  const colSpan = 5;

  return (
    <Card className="shadow-sm border border-border/50 overflow-hidden rounded-2xl bg-card">
      <CardHeader className="bg-card border-b border-border/50 py-4">
        <CardTitle className="text-sm font-medium flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Icon name="library" className="w-4 h-4 text-muted-foreground" />
            Sources
          </div>
          <span className="text-fine bg-secondary text-secondary-foreground px-3 py-1 rounded-full font-bold">
            {sources.length} / {totalSources} COURSE{totalSources !== 1 ? "S" : ""}
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
              <TableHead className={`${th} w-[72px]`}>On/Off</TableHead>
              <TableHead className={`${th} w-[72px]`}>Open</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {loading ? (
              <TableRow>
                <TableCell colSpan={colSpan} className="h-24 text-center text-muted-foreground">
                  <span className="inline-flex items-center gap-2 text-sm">
                    <Loader2 className="w-4 h-4 animate-spin" /> Loading sources…
                  </span>
                </TableCell>
              </TableRow>
            ) : null}
            {!loading && sources.length === 0 ? (
              <TableRow>
                <TableCell colSpan={colSpan} className="h-24 text-center text-muted-foreground text-sm">
                  {totalSources === 0
                    ? "No courses on disk yet. Import or scrape content into Courses data first."
                    : "No sources match this filter."}
                </TableCell>
              </TableRow>
            ) : null}
            {sources.map((source, index) => {
              const courseId = libraryCourseIdFromSource(source);
              const href = courseId
                ? `/library/lessons?course=${encodeURIComponent(courseId)}`
                : `/library/sources/${source.id}`;
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
                      <Link
                        href={href}
                        className="truncate text-sm font-medium hover:text-primary hover:underline"
                        title={source.name}
                      >
                        {source.name}
                      </Link>
                      {source.description ? (
                        <p className="truncate text-xs text-muted-foreground mt-0.5 max-w-md">
                          {source.description}
                        </p>
                      ) : null}
                    </div>
                  </TableCell>
                  <TableCell className="px-3 py-3">
                    <div className="flex justify-center">
                      <button
                        type="button"
                        onClick={() =>
                          onStatusChange(source.id, isPaused || isError ? "active" : "paused")
                        }
                        title={
                          isError
                            ? source.error_message || "Error — click to turn on"
                            : isPaused
                              ? "Off — click to turn on"
                              : "On — click to turn off"
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
                        href={href}
                        className="inline-flex h-8 w-8 items-center justify-center rounded-md border border-border/60 text-muted-foreground hover:text-foreground hover:bg-muted"
                        title="Open course"
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
