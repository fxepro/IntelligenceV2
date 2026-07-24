"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { ArrowLeft, ArrowRight, Loader2 } from "lucide-react";
import { AppPageHeader } from "@/components/sections/AppPageHeader";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { LessonTextEditor } from "@/components/library/LessonTextEditor";
import { LibraryBreadcrumb } from "@/components/library/LibraryBreadcrumb";
import { Icon } from "@/lib/icons";
import { API_BASE } from "@/lib/api-base";

interface LessonDetail {
  id: string;
  title: string;
  course_id: string;
  course: string;
  category: string;
  kind: string;
  label: string;
  source_url?: string | null;
  chars: number;
  has_text: boolean;
  has_video: boolean;
  has_pdf: boolean;
  content_status?: string;
  published?: boolean;
  body: string;
  assets: { kind: string; url?: string | null; file?: string | null }[];
  fetched_at?: string | null;
  lock_reason?: string | null;
  prev_id?: string | null;
  prev_title?: string | null;
  next_id?: string | null;
  next_title?: string | null;
}

const KIND_LABEL: Record<string, string> = {
  text: "Text",
  video: "Video",
  pdf: "PDF",
  quiz: "Quiz",
};


export default function LibraryLessonDetailPage() {
  const params = useParams();
  const id = decodeURIComponent(String(params?.id || ""));
  const [lesson, setLesson] = useState<LessonDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [flash, setFlash] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const loadLesson = useCallback(async () => {
    if (!id) return;
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/api/v1/library/lessons/${encodeURIComponent(id)}`);
      if (!res.ok) throw new Error(`Failed to load lesson (${res.status})`);
      setLesson(await res.json());
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load lesson");
      setLesson(null);
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    void loadLesson();
  }, [loadLesson]);

  const courseHref = lesson?.course_id
    ? `/library/lessons?course=${encodeURIComponent(lesson.course_id)}`
    : "/library/sources";

  // No auto-skip: unpublished lessons stay open so you can edit or review them.
  // Next/Prev and DOCX already skip Publish Off rows.

  const locked = lesson?.content_status === "locked";
  const body = lesson?.body || "";
  const showText =
    !locked
    && (
      Boolean(body.trim())
      || lesson?.kind === "text"
      || lesson?.kind === "quiz"
      || lesson?.kind === "pdf"
      || Boolean(lesson?.has_text)
      || lesson?.kind === "video"
    );

  const onBodySaved = (next: { body: string; title: string; course: string }) => {
    setLesson((prev) =>
      prev
        ? {
            ...prev,
            body: next.body,
            title: next.title,
            course: next.course,
            chars: next.body.length,
            has_text: Boolean(next.body.trim()),
            content_status: next.body.trim() ? "ready" : "empty",
          }
        : prev,
    );
  };
  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      <div className="space-y-3">
        <LibraryBreadcrumb
          items={[
            { label: "Sources", href: "/library/sources" },
            ...(lesson?.course_id
              ? [{ label: lesson.course || lesson.course_id, href: courseHref }]
              : []),
            { label: lesson?.title || (loading ? "…" : "Lesson") },
          ]}
        />
        <AppPageHeader
          title={lesson?.title || "Lesson"}
          description={
            lesson
              ? [KIND_LABEL[lesson.kind] || lesson.kind, lesson.category].filter(Boolean).join(" · ")
              : "Course lesson"
          }
          icon={<Icon name="library" className="h-5 w-5 text-primary" />}
          actions={
            <div className="flex flex-wrap items-center gap-2">
              <Button asChild variant="outline" size="sm" className="gap-1.5">
                <Link href={courseHref}>
                  <ArrowLeft className="h-4 w-4" />
                  Back to course
                </Link>
              </Button>
            </div>
          }
        />
      </div>

      {loading ? (
        <p className="inline-flex items-center gap-2 text-sm text-muted-foreground">
          <Loader2 className="h-4 w-4 animate-spin" />
          Loading…
        </p>
      ) : null}
      {error ? <p className="text-sm text-red-500">{error}</p> : null}
      {flash ? <p className="text-sm text-muted-foreground">{flash}</p> : null}

      {lesson ? (
        <div className="space-y-4">
          <Card className="rounded-2xl border-border/50 p-5">
            <div className="flex flex-wrap items-center gap-2">
              <Badge className="border-transparent bg-secondary text-secondary-foreground text-fine font-medium normal-case tracking-normal">
                {KIND_LABEL[lesson.kind] || lesson.kind}
              </Badge>
              {locked ? (
                <Badge className="border-transparent bg-amber-500/15 text-amber-700 dark:text-amber-400 text-fine font-medium normal-case tracking-normal">
                  Locked
                </Badge>
              ) : null}
              {lesson.published === false ? (
                <Badge className="border-transparent bg-muted text-muted-foreground text-fine font-medium normal-case tracking-normal">
                  Unpublished
                </Badge>
              ) : null}
              <span className="text-xs text-muted-foreground">{lesson.category}</span>
            </div>
          </Card>

          {locked ? (
            <Card className="rounded-2xl border-border/50 p-5 space-y-3">
              <p className="text-fine font-bold uppercase tracking-wider text-muted-foreground">
                Content not captured
              </p>
              <p className="text-sm text-foreground max-w-2xl leading-relaxed">
                {lesson.lock_reason ||
                  "This page was locked by course prerequisites when it was downloaded. The prerequisite dialog is not lesson content."}
              </p>
            </Card>
          ) : null}

          {showText ? (
            <Card className="rounded-2xl border-border/50 p-5">
              <LessonTextEditor
                lessonId={lesson.id}
                title={lesson.title}
                course={lesson.course}
                body={body}
                kindLabel={lesson.kind === "quiz" ? "Quiz" : "Text"}
                onSaved={onBodySaved}
              />
            </Card>
          ) : null}

          <div className="flex flex-wrap items-center justify-between gap-3 pt-2 border-t border-border/40">
            <div className="flex flex-wrap items-center gap-2">
              <Button asChild variant="outline" className="gap-2">
                <Link href={courseHref}>
                  <ArrowLeft className="h-4 w-4 shrink-0" />
                  Course
                </Link>
              </Button>
              {lesson.prev_id ? (
                <Button asChild variant="ghost" className="gap-2 max-w-[14rem]">
                  <Link href={`/library/lessons/${encodeURIComponent(lesson.prev_id)}`}>
                    <ArrowLeft className="h-4 w-4 shrink-0" />
                    <span className="truncate">{lesson.prev_title || "Previous"}</span>
                  </Link>
                </Button>
              ) : null}
            </div>
            {lesson.next_id ? (
              <Button asChild className="gap-2 max-w-[48%]">
                <Link href={`/library/lessons/${encodeURIComponent(lesson.next_id)}`}>
                  <span className="truncate">
                    Next{lesson.next_title ? `: ${lesson.next_title}` : ""}
                  </span>
                  <ArrowRight className="h-4 w-4 shrink-0" />
                </Link>
              </Button>
            ) : (
              <Button asChild variant="outline" className="gap-2">
                <Link href={courseHref}>Back to course</Link>
              </Button>
            )}
          </div>
        </div>
      ) : null}
    </div>
  );
}
