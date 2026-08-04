"use client";

import Link from "next/link";
import { Loader2, ArrowRight, FileDown } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardTitle } from "@/components/ui/card";
import { OnOffToggle } from "@/components/ui/on-off-toggle";
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
import { libraryCourseIdFromSource, libraryDiskFolderId } from "@/lib/sources/helpers";

const th =
  "h-11 px-3 text-fine font-bold uppercase tracking-wider text-sidebar-foreground text-center";
const td = "px-3 py-3 text-center";

export type CourseRowMeta = {
  lesson_count?: number;
  published?: boolean;
};

export function CoursesSourcesTable({
  sources,
  totalSources,
  loading,
  lessonCounts = {},
  courseMeta = {},
  exportingId = null,
  onExport,
  onStatusChange,
}: {
  sources: Source[];
  totalSources: number;
  loading: boolean;
  lessonCounts?: Record<string, number>;
  courseMeta?: Record<string, CourseRowMeta>;
  exportingId?: string | null;
  onExport?: (courseId: string, published: boolean) => void;
  onStatusChange: (id: string, status: "active" | "paused") => void;
}) {
  const colSpan = 7;

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
          <TableHeader>
            <TableRow className="hover:bg-transparent bg-card">
              <TableHead className={`${th} w-[48px]`}>#</TableHead>
              <TableHead className={`${th} w-[100px]`}>ID</TableHead>
              <TableHead className="h-11 px-5 text-fine font-bold uppercase tracking-wider text-sidebar-foreground text-left">
                Name
              </TableHead>
              <TableHead className={`${th} w-[72px]`}>On/Off</TableHead>
              <TableHead className={`${th} w-[80px]`}>Lessons</TableHead>
              <TableHead className={`${th} w-[72px]`}>DOCX</TableHead>
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
              const exportId = courseId ? libraryDiskFolderId(courseId) : null;
              const meta = exportId
                ? courseMeta[exportId] ?? courseMeta[courseId ?? ""] ?? {}
                : {};
              const lessonCount =
                exportId != null
                  ? (lessonCounts[exportId] ?? lessonCounts[courseId ?? ""] ?? meta.lesson_count)
                  : undefined;
              const coursePublished = meta.published !== false;
              const href = courseId
                ? `/courses/sources/${source.id}`
                : `/courses/sources/${source.id}`;
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
                      <OnOffToggle
                        size="sm"
                        checked={!isPaused && !isError}
                        onCheckedChange={(on) =>
                          onStatusChange(source.id, on ? "active" : "paused")
                        }
                        title={
                          isError
                            ? source.error_message || "Error — click to turn on"
                            : isPaused
                              ? "Off — click to turn on"
                              : "On — click to turn off"
                        }
                      />
                    </div>
                  </TableCell>
                  <TableCell className={`${td} tabular-nums text-sm font-medium`}>
                    {lessonCount != null ? lessonCount : "—"}
                  </TableCell>
                  <TableCell className="px-3 py-3">
                    <div className="flex justify-center">
                      {exportId && onExport ? (
                        <Button
                          type="button"
                          variant="outline"
                          size="icon"
                          className="h-8 w-8"
                          disabled={exportingId === exportId || !coursePublished}
                          title={
                            coursePublished
                              ? "Export all publishable lessons to DOCX"
                              : "Turn course Publish on before exporting"
                          }
                          onClick={() => onExport(exportId, coursePublished)}
                        >
                          {exportingId === exportId ? (
                            <Loader2 className="h-4 w-4 animate-spin" />
                          ) : (
                            <FileDown className="h-4 w-4" />
                          )}
                        </Button>
                      ) : (
                        <span className="text-muted-foreground text-xs">—</span>
                      )}
                    </div>
                  </TableCell>
                  <TableCell className="px-3 py-3">
                    <div className="flex justify-center">
                      <Link
                        href={href}
                        className="inline-flex h-8 w-8 items-center justify-center rounded-md border border-border/60 text-muted-foreground hover:text-foreground hover:bg-muted"
                        title="Open course details"
                      >
                        <ArrowRight className="w-4 h-4" />
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
