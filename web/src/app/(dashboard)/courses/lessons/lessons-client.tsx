"use client";

import { Fragment, useCallback, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { ArrowLeft, FileDown, Loader2, Search, X } from "lucide-react";
import { AppPageHeader } from "@/components/sections/AppPageHeader";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import { Textarea } from "@/components/ui/textarea";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { LibraryBreadcrumb } from "@/components/library/LibraryBreadcrumb";
import { Icon } from "@/lib/icons";
import { API_BASE } from "@/lib/api-base";
import { Label } from "@/components/ui/label";
import { downloadCourseDocx } from "@/lib/courses/export-docx";

type LessonKind = "text" | "video" | "pdf" | "quiz";

interface CourseSummary {
  id: string;
  name: string;
  lesson_count: number;
  kinds: Record<string, number>;
  modules: string[];
  published: boolean;
  unpublished_count?: number;
}

interface LessonSummary {
  id: string;
  title: string;
  course_id: string;
  course: string;
  category: string;
  kind: LessonKind | string;
  label: string;
  source_url?: string | null;
  chars: number;
  has_text: boolean;
  has_video: boolean;
  has_pdf: boolean;
  content_status?: string;
  published?: boolean;
}

interface LessonListResponse {
  items: LessonSummary[];
  total: number;
  kinds: Record<string, number>;
  categories: string[];
}

const KIND_LABEL: Record<string, string> = {
  text: "Text",
  video: "Video",
  pdf: "PDF",
  quiz: "Quiz",
};

export default function LibraryLessonsPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const courseId = (searchParams.get("course") || "").trim();

  const [courses, setCourses] = useState<CourseSummary[]>([]);
  const [data, setData] = useState<LessonListResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [flash, setFlash] = useState<string | null>(null);
  const [exportingId, setExportingId] = useState<string | null>(null);
  const [savingPublishId, setSavingPublishId] = useState<string | null>(null);
  const [addOpen, setAddOpen] = useState(false);
  const [adding, setAdding] = useState(false);
  const [newTitle, setNewTitle] = useState("");
  const [newPlace, setNewPlace] = useState<"start" | "end">("start");
  const [newBody, setNewBody] = useState("");
  const [kind, setKind] = useState("all");
  const [category, setCategory] = useState("all");
  const [q, setQ] = useState("");

  const activeCourse = useMemo(
    () => courses.find((c) => c.id === courseId) || null,
    [courses, courseId]
  );

  useEffect(() => {
    if (!courseId) {
      router.replace("/courses/sources");
    }
  }, [courseId, router]);

  const fetchCourses = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/api/v1/courses/courses`);
      if (!res.ok) throw new Error(`Failed to load courses (${res.status})`);
      const json = await res.json();
      setCourses(json.items ?? []);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load courses");
      setCourses([]);
    }
  }, []);

  const fetchLessons = useCallback(async (opts?: { silent?: boolean }) => {
    if (!courseId) {
      setData(null);
      setLoading(false);
      return;
    }
    setError(null);
    if (!opts?.silent) setLoading(true);
    try {
      const params = new URLSearchParams();
      params.set("course", courseId);
      if (kind !== "all") params.set("kind", kind);
      if (category !== "all") params.set("category", category);
      if (q.trim()) params.set("q", q.trim());
      const res = await fetch(`${API_BASE}/api/v1/courses/lessons?${params}`);
      if (!res.ok) throw new Error(`Failed to load lessons (${res.status})`);
      setData(await res.json());
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load lessons");
      if (!opts?.silent) setData(null);
    } finally {
      if (!opts?.silent) setLoading(false);
    }
  }, [courseId, kind, category, q]);

  useEffect(() => {
    void fetchCourses();
  }, [fetchCourses]);

  useEffect(() => {
    if (!courseId) {
      setLoading(false);
      return;
    }
    const t = setTimeout(() => {
      void fetchLessons();
    }, q ? 200 : 0);
    return () => clearTimeout(t);
  }, [fetchLessons, q, courseId]);

  const items = data?.items ?? [];
  const kinds = data?.kinds ?? {};
  const categories = data?.categories ?? [];
  const lockedCount = useMemo(
    () => items.filter((l) => l.content_status === "locked").length,
    [items]
  );

  const kindOptions = useMemo(() => {
    const keys = Object.keys(kinds).sort();
    return keys.length ? keys : ["text", "video", "pdf", "quiz"];
  }, [kinds]);

  const backToSources = () => {
    setKind("all");
    setCategory("all");
    setQ("");
    setFlash(null);
    router.push("/courses/sources");
  };

  const patchLessonPublish = async (lesson: LessonSummary, published: boolean) => {
    setSavingPublishId(lesson.id);
    setError(null);
    try {
      const res = await fetch(
        `${API_BASE}/api/v1/courses/lessons/${encodeURIComponent(lesson.id)}/publish`,
        {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ published }),
        },
      );
      const body = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(
          typeof body.detail === "string" ? body.detail : `Update failed (${res.status})`,
        );
      }
      setData((prev) =>
        prev
          ? {
              ...prev,
              items: prev.items.map((row) =>
                row.id === lesson.id ? { ...row, published: Boolean(body.published) } : row,
              ),
            }
          : prev,
      );
      await fetchCourses();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Publish update failed");
      await fetchLessons({ silent: true });
    } finally {
      setSavingPublishId(null);
    }
  };

  const createLesson = async () => {
    if (!courseId || adding) return;
    const title = newTitle.trim();
    if (!title) {
      setError("Lesson title is required.");
      return;
    }
    setAdding(true);
    setError(null);
    try {
      const res = await fetch(
        `${API_BASE}/api/v1/courses/courses/${encodeURIComponent(courseId)}/lessons`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            title,
            category: "Overview",
            kind: "text",
            body: newBody,
            place: newPlace,
          }),
        },
      );
      const body = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(
          typeof body.detail === "string" ? body.detail : `Create failed (${res.status})`,
        );
      }
      setAddOpen(false);
      setNewTitle("");
      setNewBody("");
      setNewPlace("start");
      setFlash(`Created “${title}”.`);
      await Promise.all([fetchLessons(), fetchCourses()]);
      if (body.id) {
        router.push(`/courses/lessons/${encodeURIComponent(body.id)}`);
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Create failed";
      setError(
        msg.includes("404") || msg.includes("Not Found")
          ? "Create failed — API is running old code. Restart MI API 8000, then try again."
          : msg,
      );
    } finally {
      setAdding(false);
    }
  };

  const exportCourseDocx = async (id: string, published: boolean) => {
    if (!published) {
      setError("Turn Publish on before exporting DOCX.");
      return;
    }
    setExportingId(id);
    setError(null);
    setFlash(null);
    try {
      const filename = await downloadCourseDocx(id);
      setFlash(`Exported ${filename}`);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Export failed");
    } finally {
      setExportingId(null);
    }
  };

  const lessonRows = useMemo(() => {
    let n = 0;
    return items.map((lesson, index) => {
      const prev = index > 0 ? items[index - 1] : null;
      const showModuleHeader = !prev || prev.category !== lesson.category;
      n += 1;
      return { lesson, showModuleHeader, rowNum: n };
    });
  }, [items]);

  if (!courseId) {
    return (
      <div className="space-y-6 animate-in fade-in duration-500">
        <p className="text-sm text-muted-foreground">Opening sources…</p>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      <div className="space-y-3">
        <LibraryBreadcrumb
          items={[
            { label: "Sources", href: "/courses/sources" },
            { label: activeCourse?.name || courseId || "Course" },
          ]}
        />
        <AppPageHeader
          title={activeCourse?.name || courseId || "Course"}
          description="Edit lessons and turn Publish off on anything you don’t want in export."
          icon={<Icon name="library" className="h-5 w-5 text-primary" />}
          actions={
            <div className="flex flex-wrap items-center gap-2">
              <Button
                type="button"
                size="sm"
                variant={addOpen ? "secondary" : "default"}
                onClick={() => {
                  setAddOpen((v) => !v);
                  setError(null);
                }}
              >
                {addOpen ? "Cancel" : "New lesson"}
              </Button>
              <Button
                type="button"
                variant="outline"
                size="sm"
                className="gap-1.5"
                onClick={backToSources}
              >
                <ArrowLeft className="h-4 w-4" />
                Sources
              </Button>
              <Button
                type="button"
                variant="outline"
                size="sm"
                className="gap-1.5"
                disabled={
                  exportingId === courseId ||
                  (activeCourse ? !activeCourse.published : false)
                }
                onClick={() =>
                  void exportCourseDocx(
                    courseId,
                    activeCourse?.published !== false,
                  )
                }
                title="Export all publishable lessons to DOCX"
              >
                {exportingId === courseId ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <FileDown className="h-4 w-4" />
                )}
                Export DOCX
              </Button>
            </div>
          }
        />
      </div>

      {error ? <p className="text-sm text-red-500">{error}</p> : null}
      {flash ? <p className="text-sm text-muted-foreground">{flash}</p> : null}

      <div className="space-y-3">
        {lockedCount > 0 ? (
          <Badge className="border-transparent bg-amber-500/15 text-amber-700 dark:text-amber-400 text-fine font-medium normal-case tracking-normal">
            {lockedCount} locked
          </Badge>
        ) : null}

        <div className="flex flex-col gap-3 sm:flex-row sm:flex-wrap sm:items-center">
            <div className="relative flex-1 min-w-[200px] max-w-md">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                value={q}
                onChange={(e) => setQ(e.target.value)}
                placeholder="Search lesson name or module…"
                className="pl-9 pr-9"
              />
              {q ? (
                <button
                  type="button"
                  onClick={() => setQ("")}
                  className="absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                  aria-label="Clear search"
                >
                  <X className="h-4 w-4" />
                </button>
              ) : null}
            </div>

            <Select value={kind} onValueChange={setKind}>
              <SelectTrigger className="w-full sm:w-[160px]" aria-label="Filter by kind">
                <SelectValue placeholder="All kinds" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All kinds</SelectItem>
                {kindOptions.map((k) => (
                  <SelectItem key={k} value={k}>
                    {KIND_LABEL[k] || k} {kinds[k] != null ? `(${kinds[k]})` : ""}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            <Select value={category} onValueChange={setCategory}>
              <SelectTrigger className="w-full sm:w-[240px]" aria-label="Filter by module">
                <SelectValue placeholder="All modules" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All modules</SelectItem>
                {categories.map((c) => (
                  <SelectItem key={c} value={c}>
                    {c}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
      </div>

              <Card className="shadow-sm border border-border/50 overflow-hidden rounded-2xl bg-card">
          <CardHeader className="bg-card border-b border-border/50 py-4">
            <CardTitle className="text-sm font-medium flex items-center justify-between gap-3">
              <div className="flex items-center gap-2 min-w-0">
                <Icon name="library" className="w-4 h-4 text-muted-foreground shrink-0" />
                <span className="truncate">
                  Lessons
                  {activeCourse ? (
                    <span className="text-muted-foreground font-normal"> · {activeCourse.name}</span>
                  ) : null}
                </span>
              </div>
              <span className="text-fine bg-secondary text-secondary-foreground px-3 py-1 rounded-full font-bold shrink-0">
                {loading ? "…" : `${items.length} LESSON${items.length !== 1 ? "S" : ""}`}
              </span>
            </CardTitle>
          </CardHeader>

          {addOpen ? (
            <div className="border-b border-border/50 bg-muted/20 px-5 py-4 space-y-3">
              <p className="text-sm font-medium">New lesson</p>
              <p className="text-xs text-muted-foreground">
                  Manual lesson for this course (TOC, notes).
              </p>
              <div className="grid gap-3 sm:grid-cols-2">
                <div className="space-y-1.5 sm:col-span-2">
                  <Label htmlFor="new-lesson-title">Title</Label>
                  <Input
                    id="new-lesson-title"
                    value={newTitle}
                    onChange={(e) => setNewTitle(e.target.value)}
                    placeholder="Table of Contents"
                    autoFocus
                  />
                </div>
                <div className="space-y-1.5">
                  <Label>Position</Label>
                  <Select
                    value={newPlace}
                    onValueChange={(v) => setNewPlace(v as "start" | "end")}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="start">Start of course</SelectItem>
                      <SelectItem value="end">End of course</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-1.5 sm:col-span-2">
                  <Label htmlFor="new-lesson-body">Text (optional)</Label>
                  <Textarea
                    id="new-lesson-body"
                    value={newBody}
                    onChange={(e) => setNewBody(e.target.value)}
                    placeholder="Paste content now, or leave blank and edit after."
                    className="min-h-[7rem]"
                  />
                </div>
              </div>
              <div className="flex flex-wrap gap-2">
                <Button type="button" disabled={adding} onClick={() => void createLesson()}>
                  {adding ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin" />
                      Creating…
                    </>
                  ) : (
                    "Create"
                  )}
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  disabled={adding}
                  onClick={() => setAddOpen(false)}
                >
                  Cancel
                </Button>
              </div>
            </div>
          ) : null}

          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow className="hover:bg-transparent">
                  <TableHead className="h-11 px-3 text-fine font-bold uppercase tracking-wider text-sidebar-foreground text-center w-[48px]">
                    #
                  </TableHead>
                  <TableHead className="h-11 px-5 text-fine font-bold uppercase tracking-wider text-sidebar-foreground text-left">
                    Lesson
                  </TableHead>
                  <TableHead className="h-11 px-3 text-fine font-bold uppercase tracking-wider text-sidebar-foreground text-left w-[200px]">
                    Module
                  </TableHead>
                  <TableHead className="h-11 px-3 text-fine font-bold uppercase tracking-wider text-sidebar-foreground text-center w-[88px]">
                    Kind
                  </TableHead>
                  <TableHead className="h-11 px-3 text-fine font-bold uppercase tracking-wider text-sidebar-foreground text-center w-[110px]">
                    Publish
                  </TableHead>
                  <TableHead className="h-11 px-3 text-fine font-bold uppercase tracking-wider text-sidebar-foreground text-center w-[72px]">
                    Open
                  </TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {loading && (
                  <TableRow>
                    <TableCell colSpan={6} className="h-24 text-center text-muted-foreground">
                      <span className="inline-flex items-center gap-2 text-sm">
                        <Loader2 className="w-4 h-4 animate-spin" /> Loading lessons…
                      </span>
                    </TableCell>
                  </TableRow>
                )}
                {!loading && items.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={6} className="h-24 text-center text-sm text-muted-foreground">
                      No lessons in this course.
                    </TableCell>
                  </TableRow>
                )}
                {!loading &&
                  lessonRows.map(({ lesson, showModuleHeader, rowNum }) => {
                    const isPublished = lesson.published !== false;
                    return (
                      <Fragment key={lesson.id}>
                        {showModuleHeader ? (
                          <TableRow className="bg-muted/40 hover:bg-muted/40">
                            <TableCell
                              colSpan={6}
                              className="px-5 py-2 text-left text-fine font-bold uppercase tracking-wider text-muted-foreground"
                            >
                              {lesson.category || "General"}
                            </TableCell>
                          </TableRow>
                        ) : null}
                        <TableRow className={`h-14 ${!isPublished ? "opacity-60" : ""}`}>
                          <TableCell className="px-3 py-3 text-center tabular-nums text-xs text-muted-foreground">
                            {rowNum}
                          </TableCell>
                          <TableCell className="px-5 py-3 text-left">
                            <Link
                              href={`/courses/lessons/${encodeURIComponent(lesson.id)}`}
                              className="text-sm font-medium hover:text-primary truncate block max-w-xl"
                              title={lesson.title}
                            >
                              {lesson.title}
                            </Link>
                          </TableCell>
                          <TableCell className="px-3 py-3 text-left">
                            <span className="text-xs text-muted-foreground">{lesson.category}</span>
                          </TableCell>
                          <TableCell className="px-3 py-3 text-center">
                            <div className="inline-flex flex-col items-center gap-1">
                              <Badge className="border-transparent bg-secondary text-secondary-foreground text-fine font-medium normal-case tracking-normal">
                                {KIND_LABEL[lesson.kind] || lesson.kind}
                              </Badge>
                              {lesson.content_status === "locked" ? (
                                <Badge className="border-transparent bg-amber-500/15 text-amber-700 dark:text-amber-400 text-fine font-medium normal-case tracking-normal">
                                  Locked
                                </Badge>
                              ) : null}
                            </div>
                          </TableCell>
                          <TableCell className="px-3 py-3 text-center">
                            <div className="inline-flex items-center justify-center gap-2">
                              <Switch
                                checked={isPublished}
                                disabled={savingPublishId === lesson.id}
                                onCheckedChange={(checked) =>
                                  void patchLessonPublish(lesson, checked)
                                }
                                aria-label={`Publish ${lesson.title}`}
                              />
                              <span
                                className={`text-fine font-medium ${
                                  isPublished ? "text-primary" : "text-muted-foreground"
                                }`}
                              >
                                {isPublished ? "On" : "Off"}
                              </span>
                            </div>
                          </TableCell>
                          <TableCell className="px-3 py-3 text-center">
                            <Link
                              href={`/courses/lessons/${encodeURIComponent(lesson.id)}`}
                              className="inline-flex h-8 w-8 items-center justify-center rounded-md border border-border/60 text-muted-foreground hover:text-foreground hover:bg-muted"
                              title="Open lesson"
                            >
                              <Icon name="arrowRight" className="w-4 h-4" />
                            </Link>
                          </TableCell>
                        </TableRow>
                      </Fragment>
                    );
                  })}
              </TableBody>
            </Table>
          </div>
        </Card>
    </div>
  );
}
