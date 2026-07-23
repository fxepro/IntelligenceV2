"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { ArrowUpRight, Loader2 } from "lucide-react";
import { AppPageHeader } from "@/components/sections/AppPageHeader";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { LessonBody } from "@/components/library/LessonBody";
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
  body: string;
  assets: { kind: string; url?: string | null; file?: string | null }[];
  fetched_at?: string | null;
  lock_reason?: string | null;
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
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!id) return;
    let cancelled = false;
    (async () => {
      try {
        const res = await fetch(`${API_BASE}/api/v1/library/lessons/${encodeURIComponent(id)}`);
        if (!res.ok) throw new Error(`Failed to load lesson (${res.status})`);
        const data = await res.json();
        if (!cancelled) setLesson(data);
      } catch (err: unknown) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Failed to load lesson");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [id]);

  const courseHref = lesson?.course_id
    ? `/library/lessons?course=${encodeURIComponent(lesson.course_id)}`
    : "/library/lessons";
  const locked = lesson?.content_status === "locked";
  const body = (lesson?.body || "").trim();
  const showVideo = !locked && (lesson?.kind === "video" || Boolean(lesson?.has_video));
  const showText = !locked && (Boolean(body) || lesson?.kind === "text" || lesson?.kind === "quiz" || lesson?.kind === "pdf");

  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      <AppPageHeader
        title={lesson?.title || "Lesson"}
        description={
          lesson
            ? [lesson.course, lesson.category].filter(Boolean).join(" · ")
            : "Library"
        }
        icon={<Icon name="library" className="h-5 w-5 text-primary" />}
        actions={
          <div className="flex items-center gap-3 text-xs font-medium">
            <Link href="/library/lessons" className="text-muted-foreground hover:text-foreground">
              Courses
            </Link>
            {lesson?.course_id ? (
              <Link href={courseHref} className="text-muted-foreground hover:text-foreground">
                {lesson.course}
              </Link>
            ) : null}
          </div>
        }
      />

      {loading ? (
        <p className="inline-flex items-center gap-2 text-sm text-muted-foreground">
          <Loader2 className="h-4 w-4 animate-spin" /> Loading…
        </p>
      ) : null}
      {error ? <p className="text-sm text-red-500">{error}</p> : null}

      {lesson ? (
        <div className="space-y-4">
          <Card className="rounded-2xl border-border/50 p-5 space-y-3">
            <div className="flex flex-wrap items-center gap-2">
              <Badge className="border-transparent bg-secondary text-secondary-foreground text-fine font-medium normal-case tracking-normal">
                {KIND_LABEL[lesson.kind] || lesson.kind}
              </Badge>
              {locked ? (
                <Badge className="border-transparent bg-amber-500/15 text-amber-700 dark:text-amber-400 text-fine font-medium normal-case tracking-normal">
                  Locked
                </Badge>
              ) : null}
              <span className="text-xs text-muted-foreground">{lesson.course}</span>
              <span className="text-xs text-muted-foreground">·</span>
              <span className="text-xs text-muted-foreground">{lesson.category}</span>
            </div>

            {lesson.source_url ? (
              <div>
                <Button asChild variant="outline" size="sm" className="gap-2">
                  <a href={lesson.source_url} target="_blank" rel="noopener noreferrer">
                    Open on source site
                    <ArrowUpRight className="h-3.5 w-3.5" />
                  </a>
                </Button>
              </div>
            ) : null}
          </Card>

          {locked ? (
            <Card className="rounded-2xl border-border/50 p-5 space-y-2">
              <p className="text-fine font-bold uppercase tracking-wider text-muted-foreground">
                Content not captured
              </p>
              <p className="text-sm text-foreground max-w-2xl leading-relaxed">
                {lesson.lock_reason ||
                  "This page was locked by course prerequisites when it was downloaded. The prerequisite dialog is not lesson content."}
              </p>
              <p className="text-xs text-muted-foreground max-w-2xl leading-relaxed">
                Re-run the Scytale download after Module 1 is completed on the source site (or use the
                updated downloader, which marks lessons complete in order and retries locked pages).
              </p>
            </Card>
          ) : null}

          {showVideo ? (
            <Card className="rounded-2xl border-border/50 p-5 space-y-3">
              <p className="text-fine font-bold uppercase tracking-wider text-muted-foreground">
                Video
              </p>
              {lesson.source_url ? (
                <div className="overflow-hidden rounded-xl border border-border/60 bg-black/90 aspect-video">
                  <iframe
                    title={lesson.title}
                    src={lesson.source_url}
                    className="h-full w-full"
                    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                    allowFullScreen
                    referrerPolicy="no-referrer-when-downgrade"
                  />
                </div>
              ) : (
                <p className="text-sm text-muted-foreground">No video URL on this lesson.</p>
              )}
              <p className="text-xs text-muted-foreground">
                If the player is blank (login wall), use Open on source site.
              </p>
            </Card>
          ) : null}

          {showText ? (
            <Card className="rounded-2xl border-border/50 p-5">
              <p className="text-fine font-bold uppercase tracking-wider text-muted-foreground mb-3">
                {lesson.kind === "quiz" ? "Quiz" : "Text"}
              </p>
              {body ? (
                <LessonBody body={body} />
              ) : (
                <p className="text-sm text-muted-foreground">
                  No text captured for this lesson yet.
                  {lesson.source_url ? " Open the source site for the full content." : null}
                </p>
              )}
            </Card>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}
