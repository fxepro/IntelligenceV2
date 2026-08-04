"use client";

import React, { useState, useEffect, useCallback } from "react";
import { AlertCircle, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { AppPageHeader } from "@/components/sections/AppPageHeader";
import { CoursesSourcesTable } from "@/components/sections/CoursesSourcesTable";
import { Icon } from "@/lib/icons";
import type { Source } from "@/lib/mock-data/sources";
import { mapSource, slugifyCourseId } from "@/lib/sources/helpers";
import { API_BASE } from "@/lib/api-base";
import { AddCourseSourceDialog, type CourseSourceFormData } from "@/components/sections/AddCourseSourceDialog";
import { ManualImportCourseLessonsDialog } from "@/components/sections/ManualImportCourseLessonsDialog";
import { libraryCourseIdFromSource } from "@/lib/sources/helpers";
import { downloadCourseDocx } from "@/lib/courses/export-docx";
import type { CourseRowMeta } from "@/components/sections/CoursesSourcesTable";
import { toast } from "@/hooks/use-toast";

export default function CoursesSourcesPage() {
  const [sources, setSources] = useState<Source[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [showAddDialog, setShowAddDialog] = useState(false);
  const [manualSource, setManualSource] = useState<Source | null>(null);
  const [lessonCounts, setLessonCounts] = useState<Record<string, number>>({});
  const [courseMeta, setCourseMeta] = useState<Record<string, CourseRowMeta>>({});
  const [exportingId, setExportingId] = useState<string | null>(null);
  const [exportError, setExportError] = useState<string | null>(null);

  const fetchSources = useCallback(async () => {
    setLoadError(null);
    try {
      const [srcRes, coursesRes] = await Promise.all([
        fetch(`${API_BASE}/api/v1/sources?domain=courses`),
        fetch(`${API_BASE}/api/v1/courses/courses`),
      ]);
      if (!srcRes.ok) throw new Error(`Failed to load course sources (${srcRes.status})`);
      const data = await srcRes.json();
      setSources((data.items ?? []).map(mapSource));
      if (coursesRes.ok) {
        const courses = await coursesRes.json();
        const counts: Record<string, number> = {};
        const meta: Record<string, CourseRowMeta> = {};
        for (const course of courses.items ?? []) {
          if (course.id) {
            counts[course.id] = Number(course.lesson_count ?? 0);
            meta[course.id] = {
              lesson_count: Number(course.lesson_count ?? 0),
              published: course.published !== false,
            };
          }
        }
        setLessonCounts(counts);
        setCourseMeta(meta);
      }
    } catch (err: any) {
      setLoadError(err.message ?? "Failed to load sources");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchSources();
  }, [fetchSources]);

  const handleAddSource = async (data: CourseSourceFormData) => {
    const courseId = slugifyCourseId(data.courseId) || slugifyCourseId(data.name);
    if (!courseId) {
      toast({
        variant: "destructive",
        title: "Destination ID required",
        description: "Enter a course name or destination ID.",
      });
      throw new Error("Destination ID is required.");
    }
    if (!data.url?.trim()) {
      toast({
        variant: "destructive",
        title: "Source URL required",
        description: "Paste the curriculum or hub page URL.",
      });
      throw new Error("Source URL is required.");
    }

    const res = await fetch(`${API_BASE}/api/v1/sources`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        domain: "courses",
        platform: "website",
        source_type: data.sourceType,
        source_url: data.url.trim(),
        name: data.name.trim(),
        category: "course",
        course_id: courseId,
        connector: data.connector,
      }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: "Failed to add course" }));
      const message = typeof err.detail === "string" ? err.detail : "Failed to add course";
      toast({ variant: "destructive", title: "Could not add course", description: message });
      throw new Error(message);
    }
    const created = await res.json();
    const mapped = mapSource(created);
    setSources((prev) => [mapped, ...prev]);
    toast({ title: "Course saved", description: `${mapped.name} · ${courseId} · ${data.connector}` });

    if (data.connector !== "manual") {
      void fetch(`${API_BASE}/api/v1/sources/${mapped.id}/discover`, { method: "POST" }).catch(
        () => {
          toast({
            variant: "destructive",
            title: "Discover failed to start",
            description: "Source saved — open it and click Discover.",
          });
        },
      );
    }
  };

  const handleStatus = async (id: string, status: "active" | "paused") => {
    const previous = sources.find((source) => source.id === id)?.status;
    setSources((list) =>
      list.map((source) => (source.id === id ? { ...source, status } : source))
    );
    try {
      const res = await fetch(`${API_BASE}/api/v1/sources/${id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status }),
      });
      if (!res.ok) throw new Error("Failed to update status");
      const updated = await res.json();
      setSources((list) =>
        list.map((source) => (source.id === id ? mapSource(updated) : source))
      );
    } catch {
      if (!previous) return;
      setSources((list) =>
        list.map((source) =>
          source.id === id ? { ...source, status: previous } : source
        )
      );
    }
  };

  const handleExport = async (courseId: string, published: boolean) => {
    if (!published) {
      setExportError("Turn course Publish on before exporting DOCX.");
      return;
    }
    setExportingId(courseId);
    setExportError(null);
    try {
      await downloadCourseDocx(courseId);
    } catch (err: unknown) {
      setExportError(err instanceof Error ? err.message : "Export failed");
    } finally {
      setExportingId(null);
    }
  };

  return (
    <div className="space-y-8 animate-in fade-in duration-500">
      <AppPageHeader
        title="Course Sources"
        description="Add course sources to discover and parse lessons."
        actions={
          <Button
            onClick={() => setShowAddDialog(true)}
            className="gap-2 shadow-lg shadow-primary/10 hover:scale-[1.02] transition-transform"
          >
            <Icon name="plus" className="w-4 h-4" /> Add Course Source
          </Button>
        }
      />

      {loadError && (
        <div className="flex items-center justify-between gap-2 text-sm text-red-400 bg-red-500/5 border border-red-500/20 rounded-xl px-4 py-3">
          <span className="flex items-center gap-2">
            <AlertCircle className="w-4 h-4 flex-shrink-0" /> {loadError}
          </span>
          <Button size="sm" variant="outline" onClick={fetchSources} className="h-7 text-xs">
            Retry
          </Button>
        </div>
      )}

      {exportError && (
        <div className="flex items-center gap-2 text-sm text-red-400 bg-red-500/5 border border-red-500/20 rounded-xl px-4 py-3">
          <AlertCircle className="w-4 h-4 flex-shrink-0" /> {exportError}
        </div>
      )}

      <CoursesSourcesTable
        sources={sources}
        totalSources={sources.length}
        loading={loading}
        lessonCounts={lessonCounts}
        courseMeta={courseMeta}
        exportingId={exportingId}
        onExport={handleExport}
        onStatusChange={handleStatus}
      />

      <AddCourseSourceDialog
        open={showAddDialog}
        onClose={() => setShowAddDialog(false)}
        onAdd={handleAddSource}
      />

      {manualSource && libraryCourseIdFromSource(manualSource) ? (
        <ManualImportCourseLessonsDialog
          open={Boolean(manualSource)}
          onClose={() => setManualSource(null)}
          sourceId={manualSource.id}
          courseId={libraryCourseIdFromSource(manualSource)!}
          courseName={manualSource.name}
        />
      ) : null}
    </div>
  );
}
