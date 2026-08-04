"use client";

import { useEffect, useRef, useState } from "react";
import { Loader2, Pencil, Save, X } from "lucide-react";
import { LessonBody } from "@/components/library/LessonBody";
import {
  LessonRichEditor,
  type LessonRichEditorHandle,
} from "@/components/library/LessonRichEditor";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { API_BASE } from "@/lib/api-base";

type Props = {
  lessonId: string;
  title?: string;
  course?: string;
  body: string;
  kindLabel?: string;
  onSaved?: (next: { body: string; title: string; course: string }) => void;
};

function apiError(data: unknown, status: number): string {
  if (data && typeof data === "object" && "detail" in data) {
    const detail = (data as { detail: unknown }).detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail)) {
      return detail
        .map((d) => (typeof d === "object" && d && "msg" in d ? String((d as { msg: string }).msg) : String(d)))
        .join("; ");
    }
  }
  return `Save failed (${status})`;
}

export function LessonTextEditor({
  lessonId,
  title = "",
  course = "",
  body,
  kindLabel = "Text",
  onSaved,
}: Props) {
  const [editing, setEditing] = useState(false);
  const [editorKey, setEditorKey] = useState(0);
  const [draft, setDraft] = useState(body);
  const [draftTitle, setDraftTitle] = useState(title);
  const [draftCourse, setDraftCourse] = useState(course);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [flash, setFlash] = useState<string | null>(null);
  const editorRef = useRef<LessonRichEditorHandle>(null);

  useEffect(() => {
    if (!editing) {
      setDraft(body);
      setDraftTitle(title);
      setDraftCourse(course);
    }
  }, [body, title, course, editing]);

  const save = async () => {
    if (saving) return;
    const nextTitle = draftTitle.trim();
    const nextCourse = draftCourse.trim();
    if (!nextTitle) {
      setError("Lesson title is required.");
      return;
    }
    if (!nextCourse) {
      setError("Course name is required.");
      return;
    }
    // Always pull latest content from the editor DOM before POST.
    const liveBody = editorRef.current?.flush() ?? draft;
    setDraft(liveBody);

    setSaving(true);
    setError(null);
    setFlash(null);
    try {
      const payload: { body: string; title: string; course?: string } = {
        body: liveBody,
        title: nextTitle,
      };
      // Only send course when renamed — avoids rewriting every lesson file.
      if (nextCourse !== course.trim()) {
        payload.course = nextCourse;
      }
      const res = await fetch(
        `${API_BASE}/api/v1/courses/lessons/${encodeURIComponent(lessonId)}`,
        {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        },
      );
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(apiError(data, res.status));
      }
      const savedBody = typeof data.body === "string" ? data.body : liveBody;
      const savedTitle = typeof data.title === "string" ? data.title : nextTitle;
      const savedCourse = typeof data.course === "string" ? data.course : nextCourse;
      setDraft(savedBody);
      setDraftTitle(savedTitle);
      setDraftCourse(savedCourse);
      setEditing(false);
      setFlash(
        course.trim() !== savedCourse
          ? "Saved — course name updated for all lessons in this course."
          : "Saved.",
      );
      onSaved?.({ body: savedBody, title: savedTitle, course: savedCourse });
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Save failed");
    } finally {
      setSaving(false);
    }
  };

  const cancel = () => {
    setDraft(body);
    setDraftTitle(title);
    setDraftCourse(course);
    setEditing(false);
    setError(null);
  };

  const startEdit = () => {
    setDraft(body);
    setDraftTitle(title);
    setDraftCourse(course);
    setEditorKey((k) => k + 1);
    setEditing(true);
    setFlash(null);
    setError(null);
  };

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <p className="text-fine font-bold uppercase tracking-wider text-muted-foreground">
          {kindLabel}
        </p>
        <div className="flex flex-wrap items-center gap-2">
          {!editing ? (
            <Button
              type="button"
              variant="outline"
              size="sm"
              className="gap-1.5"
              onClick={startEdit}
            >
              <Pencil className="h-3.5 w-3.5" />
              Edit
            </Button>
          ) : (
            <>
              <Button
                type="button"
                variant="outline"
                size="sm"
                className="gap-1.5"
                disabled={saving}
                onClick={cancel}
              >
                <X className="h-3.5 w-3.5" />
                Cancel
              </Button>
              <Button
                type="button"
                size="sm"
                className="gap-1.5"
                disabled={saving}
                onClick={() => void save()}
              >
                {saving ? (
                  <Loader2 className="h-3.5 w-3.5 animate-spin" />
                ) : (
                  <Save className="h-3.5 w-3.5" />
                )}
                {saving ? "Saving…" : "Save"}
              </Button>
            </>
          )}
        </div>
      </div>

      {error ? <p className="text-sm text-red-500">{error}</p> : null}
      {flash ? <p className="text-sm text-muted-foreground">{flash}</p> : null}

      {editing ? (
        <div className="space-y-3">
          <div className="grid gap-3 sm:grid-cols-2">
            <label className="space-y-1.5">
              <span className="text-fine font-bold uppercase tracking-wider text-muted-foreground">
                Course name
              </span>
              <Input
                value={draftCourse}
                onChange={(e) => setDraftCourse(e.target.value)}
                placeholder="Course name"
              />
              <span className="text-xs text-muted-foreground">
                Only rewritten across the course when you change it.
              </span>
            </label>
            <label className="space-y-1.5">
              <span className="text-fine font-bold uppercase tracking-wider text-muted-foreground">
                Lesson title
              </span>
              <Input
                value={draftTitle}
                onChange={(e) => setDraftTitle(e.target.value)}
                placeholder="Lesson title"
              />
            </label>
          </div>

          <LessonRichEditor
            key={editorKey}
            ref={editorRef}
            value={draft}
            onChange={setDraft}
          />
        </div>
      ) : body.trim() ? (
        <LessonBody body={body} />
      ) : (
        <div className="space-y-2">
          <p className="text-sm text-muted-foreground">
            No text captured for this lesson yet. Use Edit to paste or write content.
          </p>
        </div>
      )}
    </div>
  );
}
