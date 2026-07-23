"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Loader2, Search, X } from "lucide-react";
import { AppPageHeader } from "@/components/sections/AppPageHeader";
import { Badge } from "@/components/ui/badge";
import { Card, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Icon } from "@/lib/icons";
import { API_BASE } from "@/lib/api-base";

type LessonKind = "text" | "video" | "pdf" | "quiz";

interface CourseSummary {
  id: string;
  name: string;
  lesson_count: number;
  kinds: Record<string, number>;
  modules: string[];
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
}

interface LessonListResponse {
  items: LessonSummary[];
  total: number;
  kinds: Record<string, number>;
  categories: string[];
}

/** Library subtypes — same role as Media platform tabs. */
const LIBRARY_SUBTYPE_OPTIONS = [
  { id: "lessons", label: "Lessons", hint: "Courses → lessons → text / video" },
] as const;

type LibrarySubtype = (typeof LIBRARY_SUBTYPE_OPTIONS)[number]["id"];

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
  const [subtypeTab, setSubtypeTab] = useState<LibrarySubtype>("lessons");
  const [kind, setKind] = useState("all");
  const [category, setCategory] = useState("all");
  const [q, setQ] = useState("");

  const activeCourse = useMemo(
    () => courses.find((c) => c.id === courseId) || null,
    [courses, courseId]
  );

  const fetchCourses = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/api/v1/library/courses`);
      if (!res.ok) throw new Error(`Failed to load courses (${res.status})`);
      const json = await res.json();
      setCourses(json.items ?? []);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load courses");
      setCourses([]);
    }
  }, []);

  const fetchLessons = useCallback(async () => {
    if (!courseId) {
      setData(null);
      setLoading(false);
      return;
    }
    setError(null);
    setLoading(true);
    try {
      const params = new URLSearchParams();
      params.set("course", courseId);
      if (kind !== "all") params.set("kind", kind);
      if (category !== "all") params.set("category", category);
      if (q.trim()) params.set("q", q.trim());
      const res = await fetch(`${API_BASE}/api/v1/library/lessons?${params}`);
      if (!res.ok) throw new Error(`Failed to load lessons (${res.status})`);
      setData(await res.json());
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load lessons");
      setData(null);
    } finally {
      setLoading(false);
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
  const subtypeCounts = useMemo(
    () => ({
      lessons: courses.reduce((sum, c) => sum + c.lesson_count, 0),
    }),
    [courses]
  );

  const kindOptions = useMemo(() => {
    const keys = Object.keys(kinds).sort();
    return keys.length ? keys : ["text", "video", "pdf", "quiz"];
  }, [kinds]);

  const openCourse = (id: string) => {
    setKind("all");
    setCategory("all");
    setQ("");
    router.push(`/library/lessons?course=${encodeURIComponent(id)}`);
  };

  const backToCourses = () => {
    setKind("all");
    setCategory("all");
    setQ("");
    router.push("/library/lessons");
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      <AppPageHeader
        title="Library"
        description="Courses → lessons → text and video content."
        icon={<Icon name="library" className="h-5 w-5 text-primary" />}
      />

      {error ? <p className="text-sm text-red-500">{error}</p> : null}

      <div className="space-y-3">
        <Tabs
          value={subtypeTab}
          onValueChange={(value) => {
            setSubtypeTab(value as LibrarySubtype);
            backToCourses();
          }}
        >
          <TabsList className="h-auto w-full justify-start overflow-x-auto rounded-xl border border-border/60 bg-secondary/40 p-1">
            {LIBRARY_SUBTYPE_OPTIONS.map((subtype) => (
              <TabsTrigger
                key={subtype.id}
                value={subtype.id}
                title={subtype.hint}
                className="group gap-2 rounded-lg px-4 py-2 data-[state=active]:bg-accent data-[state=active]:text-accent-foreground data-[state=active]:shadow-sm"
              >
                {subtype.label}
                <span className="text-fine tabular-nums text-muted-foreground group-data-[state=active]:text-accent-foreground/85">
                  {subtypeCounts[subtype.id] ?? 0}
                </span>
              </TabsTrigger>
            ))}
          </TabsList>
        </Tabs>

        {courseId ? (
          <div className="flex flex-wrap items-center gap-2 text-sm">
            <button
              type="button"
              onClick={backToCourses}
              className="text-muted-foreground hover:text-foreground"
            >
              Courses
            </button>
            <span className="text-muted-foreground">/</span>
            <span className="font-medium">{activeCourse?.name || courseId}</span>
          </div>
        ) : null}

        {courseId ? (
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
        ) : null}
      </div>

      {!courseId ? (
        <Card className="shadow-sm border border-border/50 overflow-hidden rounded-2xl bg-card">
          <CardHeader className="bg-card border-b border-border/50 py-4">
            <CardTitle className="text-sm font-medium flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Icon name="library" className="w-4 h-4 text-muted-foreground" />
                Courses
              </div>
              <span className="text-fine bg-secondary text-secondary-foreground px-3 py-1 rounded-full font-bold">
                {courses.length} COURSE{courses.length !== 1 ? "S" : ""}
              </span>
            </CardTitle>
          </CardHeader>
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow className="hover:bg-transparent">
                  <TableHead className="h-11 px-3 text-fine font-bold uppercase tracking-wider text-muted-foreground text-center w-[48px]">
                    #
                  </TableHead>
                  <TableHead className="h-11 px-5 text-fine font-bold uppercase tracking-wider text-muted-foreground text-left">
                    Course
                  </TableHead>
                  <TableHead className="h-11 px-3 text-fine font-bold uppercase tracking-wider text-muted-foreground text-center w-[100px]">
                    Lessons
                  </TableHead>
                  <TableHead className="h-11 px-3 text-fine font-bold uppercase tracking-wider text-muted-foreground text-left">
                    Kinds
                  </TableHead>
                  <TableHead className="h-11 px-3 text-fine font-bold uppercase tracking-wider text-muted-foreground text-center w-[72px]">
                    Open
                  </TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {courses.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={5} className="h-24 text-center text-sm text-muted-foreground">
                      No courses yet. Download a course into the Library.
                    </TableCell>
                  </TableRow>
                )}
                {courses.map((course, index) => (
                  <TableRow
                    key={course.id}
                    className="h-14 cursor-pointer"
                    onClick={() => openCourse(course.id)}
                  >
                    <TableCell className="px-3 py-3 text-center tabular-nums text-xs text-muted-foreground">
                      {index + 1}
                    </TableCell>
                    <TableCell className="px-5 py-3 text-left">
                      <span className="text-sm font-medium">{course.name}</span>
                    </TableCell>
                    <TableCell className="px-3 py-3 text-center tabular-nums text-sm">
                      {course.lesson_count}
                    </TableCell>
                    <TableCell className="px-3 py-3 text-left">
                      <div className="inline-flex flex-wrap gap-1">
                        {Object.entries(course.kinds).map(([k, n]) => (
                          <Badge key={k} variant="outline" className="text-fine">
                            {KIND_LABEL[k] || k} {n}
                          </Badge>
                        ))}
                      </div>
                    </TableCell>
                    <TableCell className="px-3 py-3 text-center">
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation();
                          openCourse(course.id);
                        }}
                        className="inline-flex h-8 w-8 items-center justify-center rounded-md border border-border/60 text-muted-foreground hover:text-foreground hover:bg-muted"
                        title="Open course"
                      >
                        <Icon name="arrowRight" className="w-4 h-4" />
                      </button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </Card>
      ) : (
        <Card className="shadow-sm border border-border/50 overflow-hidden rounded-2xl bg-card">
          <CardHeader className="bg-card border-b border-border/50 py-4">
            <CardTitle className="text-sm font-medium flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Icon name="library" className="w-4 h-4 text-muted-foreground" />
                Lessons
                {activeCourse ? (
                  <span className="text-muted-foreground font-normal">· {activeCourse.name}</span>
                ) : null}
              </div>
              <span className="text-fine bg-secondary text-secondary-foreground px-3 py-1 rounded-full font-bold">
                {loading ? "…" : `${items.length} LESSON${items.length !== 1 ? "S" : ""}`}
              </span>
            </CardTitle>
          </CardHeader>

          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow className="hover:bg-transparent">
                  <TableHead className="h-11 px-3 text-fine font-bold uppercase tracking-wider text-muted-foreground text-center w-[48px]">
                    #
                  </TableHead>
                  <TableHead className="h-11 px-5 text-fine font-bold uppercase tracking-wider text-muted-foreground text-left">
                    Lesson
                  </TableHead>
                  <TableHead className="h-11 px-3 text-fine font-bold uppercase tracking-wider text-muted-foreground text-left w-[220px]">
                    Module
                  </TableHead>
                  <TableHead className="h-11 px-3 text-fine font-bold uppercase tracking-wider text-muted-foreground text-center w-[88px]">
                    Kind
                  </TableHead>
                  <TableHead className="h-11 px-3 text-fine font-bold uppercase tracking-wider text-muted-foreground text-center w-[72px]">
                    Open
                  </TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {loading && (
                  <TableRow>
                    <TableCell colSpan={5} className="h-24 text-center text-muted-foreground">
                      <span className="inline-flex items-center gap-2 text-sm">
                        <Loader2 className="w-4 h-4 animate-spin" /> Loading lessons…
                      </span>
                    </TableCell>
                  </TableRow>
                )}
                {!loading && items.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={5} className="h-24 text-center text-sm text-muted-foreground">
                      No lessons in this course.
                    </TableCell>
                  </TableRow>
                )}
                {!loading &&
                  items.map((lesson, index) => (
                    <TableRow key={lesson.id} className="h-14">
                      <TableCell className="px-3 py-3 text-center tabular-nums text-xs text-muted-foreground">
                        {index + 1}
                      </TableCell>
                      <TableCell className="px-5 py-3 text-left">
                        <Link
                          href={`/library/lessons/${encodeURIComponent(lesson.id)}`}
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
                        <Link
                          href={`/library/lessons/${encodeURIComponent(lesson.id)}`}
                          className="inline-flex h-8 w-8 items-center justify-center rounded-md border border-border/60 text-muted-foreground hover:text-foreground hover:bg-muted"
                          title="Open lesson"
                        >
                          <Icon name="arrowRight" className="w-4 h-4" />
                        </Link>
                      </TableCell>
                    </TableRow>
                  ))}
              </TableBody>
            </Table>
          </div>
        </Card>
      )}
    </div>
  );
}
