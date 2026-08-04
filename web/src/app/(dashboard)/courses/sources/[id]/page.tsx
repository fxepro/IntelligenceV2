"use client";

import React, { Fragment, useCallback, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import {
  ArrowLeft,
  ExternalLink,
  Loader2,
  RefreshCw,
  AlertCircle,
  CheckCircle2,
  FileText,
  FileDown,
  LayoutGrid,
  List,
  Eye,
  ChevronLeft,
  ChevronRight,
  Copy,
  Check,
  Play,
  Youtube,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { OnOffToggle } from "@/components/ui/on-off-toggle";
import { Switch } from "@/components/ui/switch";
import { LibraryBreadcrumb } from "@/components/library/LibraryBreadcrumb";
import { EditCourseSourceDialog } from "@/components/sections/EditCourseSourceDialog";
import { type CourseSourceFormData } from "@/components/sections/AddCourseSourceDialog";
import { ManualImportCourseLessonsDialog } from "@/components/sections/ManualImportCourseLessonsDialog";
import { MediaDetailDialog } from "@/components/sections/MediaDetailDialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { type Platform } from "@/lib/mock-data/sources";
import { sourceTypeLabel, formatFileSize, pipelineStatusLabel, mapSource, facebookProfileIdFromUrl, libraryCourseIdFromSource, isFileBackedLibrarySource, libraryDiskFolderId } from "@/lib/sources/helpers";
import { curriculumTypeLabel, normalizeCurriculumType } from "@/lib/courses/curriculum-types";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { SourceStatusBadge } from "@/components/sections/StatusBadge";
import { PlatformBadge } from "@/components/sections/PlatformBadge";
import {
  formatDuration,
  formatPublishedDate,
  formatRelativeDate,
  formatViews,
} from "@/lib/mock-data/media-items";
import { fetchDiscoverySettings } from "@/lib/discovery-settings";
import { API_BASE } from "@/lib/api-base";
import { apiFetch, formatApiDetail } from "@/lib/api-fetch";
import { downloadCourseDocx } from "@/lib/courses/export-docx";
import { toast } from "@/hooks/use-toast";

/** Display path only for Facebook (e.g. /DarkInstinct) — full URL stays on the href. */
function displaySourcePath(url: string): string {
  try {
    const u = new URL(url);
    if (u.hostname.replace(/^www\./, "").includes("facebook.com")) {
      const path = `${u.pathname}${u.search}` || "/";
      return path.startsWith("/") ? path : `/${path}`;
    }
    return url.replace(/^https?:\/\//, "");
  } catch {
    return url.replace(/^https?:\/\/(www\.)?facebook\.com/i, "") || url;
  }
}

/** Idle pipeline cells stay blank; only show real work/done/fail states. */
function tablePipelineStatus(status: string | null | undefined): string {
  if (!status || status === "pending") return "—";
  return pipelineStatusLabel(status);
}

import type { Source } from "@/lib/mock-data/sources";

export interface SourceDetail extends Omit<Source, 'last_checked' | 'description' | 'item_count' | 'streams'> {
  description?: string | null;
  auto_transcribe?: boolean;
  vanity_url?: string | null;
  last_checked?: string | null;
  error_message?: string | null;
  item_count?: number | null;
  streams?: Array<{
    id: string;
    stream_type: string;
    stream_url?: string | null;
    enabled: boolean;
    item_count: number;
  }>;
}

interface MediaRow {
  id: string;
  source_id: string;
  platform: string;
  external_id: string;
  canonical_url: string;
  title: string | null;
  thumbnail_url: string | null;
  channel_name: string | null;
  content_type: string | null;
  stream_type: string | null;
  duration_seconds: number | null;
  file_size_bytes: number | null;
  download_status: string | null;
  transcription_status: string | null;
  view_count: number | null;
  published_at: string | null;
  discovered_at: string;
  status: string;
  error_message: string | null;
}

interface TranscriptRow {
  media_id: string;
  title: string | null;
  canonical_url: string;
  thumbnail_url: string | null;
  published_at: string | null;
  discovered_at: string | null;
  status: string;
  full_text: string;
  language: string | null;
  word_count: number | null;
  model_used: string | null;
  generated_at: string | null;
}

interface CourseLessonRow {
  id: string;
  title: string;
  category: string;
  kind: string;
  source_url: string | null;
  has_text: boolean;
  content_status: string;
  chars: number;
}

function lessonUrlKind(url: string | null | undefined): "youtube" | "article" | "page" {
  const u = (url || "").toLowerCase();
  if (u.includes("youtube.com") || u.includes("youtu.be")) return "youtube";
  if (u.includes("/learn/") || u.includes("/blog/") || u.includes("/articles")) return "article";
  return "page";
}

function moduleHeaderLabel(category: string | null | undefined): string | null {
  const value = (category || "").trim();
  if (!value || value.toLowerCase() === "general") return null;
  return value;
}

function contentStatusLabel(lesson: CourseLessonRow): string {
  if (lesson.content_status === "locked") return "Locked";
  if (lesson.content_status === "skipped") return "Video";
  if (lesson.content_status === "stub" || lesson.content_status === "index") return "Stub";
  if (lesson.content_status === "ready" && lesson.chars > 400) return "Saved";
  if (lesson.has_text && lesson.chars > 400) return "Saved";
  return "Stub";
}

function displayLessonUrl(url: string | null | undefined): string {
  if (!url) return "—";
  try {
    const parsed = new URL(url);
    const host = parsed.hostname.replace(/^www\./, "");
    const path = parsed.pathname.length > 48 ? `${parsed.pathname.slice(0, 45)}…` : parsed.pathname;
    return `${host}${path || ""}`;
  } catch {
    return url.length > 56 ? `${url.slice(0, 53)}…` : url;
  }
}



export default function SourceDetailPage() {
  const params = useParams();
  const id = String(params.id ?? "");

  const [source, setSource] = useState<SourceDetail | null>(null);
  const [courseLessons, setCourseLessons] = useState<CourseLessonRow[]>([]);
  const [items, setItems] = useState<MediaRow[]>([]);
  const [typeFilter, setTypeFilter] = useState("all");
  const [downloadFilter, setDownloadFilter] = useState("all");
  const [transcriptFilter, setTranscriptFilter] = useState("all");
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [discovering, setDiscovering] = useState(false);
  const [discoverMsg, setDiscoverMsg] = useState<string | null>(null);
  const [transcribingIds, setTranscribingIds] = useState<Set<string>>(new Set());
  const [transcribingAll, setTranscribingAll] = useState(false);
  const [showEditSource, setShowEditSource] = useState(false);
  const [showManualImport, setShowManualImport] = useState(false);
  const [detailId, setDetailId] = useState<string | null>(null);
  const [copiedAll, setCopiedAll] = useState(false);
  const [exportingDocx, setExportingDocx] = useState(false);
  const [coursePublished, setCoursePublished] = useState(true);
  const [exportMsg, setExportMsg] = useState<string | null>(null);

  const [view, setView] = useState<"items" | "grid" | "transcripts">("items");
  const [transcripts, setTranscripts] = useState<TranscriptRow[]>([]);
  const [transcriptTotal, setTranscriptTotal] = useState(0);
  const [transcriptIdx, setTranscriptIdx] = useState(0);
  const [transcriptsLoading, setTranscriptsLoading] = useState(false);

  const loadTranscripts = useCallback(async () => {
    if (!id) return;
    setTranscriptsLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/v1/sources/${id}/transcripts?page_size=200`);
      if (!res.ok) throw new Error("Failed to load transcripts");
      const data = await res.json();
      setTranscripts(data.items ?? []);
      setTranscriptTotal(data.total ?? 0);
      setTranscriptIdx((i) => {
        const len = (data.items ?? []).length;
        if (len === 0) return 0;
        return Math.min(i, len - 1);
      });
    } catch {
      setTranscripts([]);
      setTranscriptTotal(0);
    } finally {
      setTranscriptsLoading(false);
    }
  }, [id]);

  const load = useCallback(async () => {
    if (!id) return;
    setError(null);
    try {
      const discovery = await fetchDiscoverySettings();
      const srcRes = await fetch(`${API_BASE}/api/v1/sources/${id}`);
      if (!srcRes.ok) throw new Error(`Source not found (${srcRes.status})`);
      const src = await srcRes.json();
      const mapped = mapSource(src);
      setSource(mapped);

      const courseId = libraryCourseIdFromSource(mapped);
      if (mapped.domain === "courses" && courseId) {
        const diskId = libraryDiskFolderId(courseId);
        void fetch(`${API_BASE}/api/v1/courses/courses`)
          .then((r) => (r.ok ? r.json() : null))
          .then((json) => {
            const row = (json?.items ?? []).find(
              (c: { id?: string }) => c.id === diskId || c.id === courseId,
            );
            if (row) setCoursePublished(row.published !== false);
          })
          .catch(() => null);

        const lessonsRes = await fetch(`${API_BASE}/api/v1/courses/sources/${id}/lessons`);
        if (lessonsRes.ok) {
          const lessonsData = await lessonsRes.json();
          const rows: CourseLessonRow[] = (lessonsData.items ?? []).map((lesson: {
            id: string;
            title: string;
            category?: string | null;
            kind?: string | null;
            source_url?: string | null;
            has_text?: boolean;
            content_status?: string | null;
            chars?: number | null;
          }) => ({
            id: lesson.id,
            title: lesson.title,
            category: lesson.category || "General",
            kind: lesson.kind || "text",
            source_url: lesson.source_url || null,
            has_text: Boolean(lesson.has_text),
            content_status: lesson.content_status || (lesson.has_text ? "ready" : "empty"),
            chars: Number(lesson.chars ?? 0),
          }));
          setCourseLessons(rows);
          setItems([]);
          setTotal(rows.length);
          return;
        }
        setCourseLessons([]);
      } else {
        setCourseLessons([]);
      }

      const mediaRes = await fetch(
        `${API_BASE}/api/v1/media?source_id=${id}&domain=courses&page_size=${discovery.media_page_size}`,
      );
      if (mediaRes.ok) {
        const media = await mediaRes.json();
        setItems(media.items ?? []);
        setTotal(media.total ?? 0);
      } else {
        setItems([]);
        setTotal(0);
      }
    } catch (err: any) {
      setError(err.message ?? "Failed to load channel");
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    load();
  }, [load]);

  useEffect(() => {
    if (view === "transcripts") loadTranscripts();
  }, [view, loadTranscripts]);

  // Poll while anything is still processing
  const hasActive = items.some((m) =>
    ["queued", "downloading", "transcribing", "analyzing"].includes(m.status),
  );
  useEffect(() => {
    if (!hasActive) return;
    const t = setInterval(() => {
      load();
      if (view === "transcripts") loadTranscripts();
    }, 5000);
    return () => clearInterval(t);
  }, [hasActive, load, loadTranscripts, view]);

  const handleDiscover = async () => {
    if (!id || discovering) return;
    if (source?.status !== "active") {
      setDiscoverMsg("Source is off — turn it on before running Discover.");
      return;
    }
    setDiscovering(true);
    setDiscoverMsg("Queuing discovery…");
    try {
      const pollJob = async (jobId: string, label: string) => {
        for (let i = 0; i < 90; i++) {
          await new Promise((r) => setTimeout(r, 2000));
          const jr = await fetch(`${API_BASE}/api/v1/jobs/${jobId}`);
          const job = await jr.json().catch(() => ({}));
          if (!jr.ok) continue;
          if (job.status === "completed" || job.status === "failed") {
            return job;
          }
          if (i % 5 === 4) {
            setDiscoverMsg(`${label}… (${i * 2}s)`);
          }
        }
        return null;
      };

      const res = await fetch(`${API_BASE}/api/v1/sources/${id}/discover`, { method: "POST" });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        const detail = typeof data.detail === "string" ? data.detail : "Discovery failed";
        throw new Error(detail);
      }

      const jobId = data.job_id as string | undefined;
      if (!jobId) {
        throw new Error("Discovery enqueued but no job_id returned");
      }

      setDiscoverMsg("Discovering lessons…");
      const final = await pollJob(jobId, "Discovering lessons");
      if (!final) {
        setDiscoverMsg("Discovery still running — refresh in a minute.");
        await load();
        return;
      }
      if (final.status === "failed") {
        throw new Error(final.error_message || "Discovery job failed");
      }

      const result = final.result || {};
      const found = Number(result.discovered ?? result.total_found ?? 0);
      const neu = Number(result.new ?? result.lessons_written ?? 0);
      const connector = normalizeCurriculumType(source?.connector);

      if (connector === "article_hub" && isLibraryCourse) {
        setDiscoverMsg("Fetching article bodies…");
        const ar = await fetch(`${API_BASE}/api/v1/courses/sources/${id}/acquire`, { method: "POST" });
        const ad = await ar.json().catch(() => ({}));
        if (!ar.ok) {
          const detail = typeof ad.detail === "string" ? ad.detail : "Acquire failed";
          throw new Error(detail);
        }
        const acquireJobId = ad.id as string | undefined;
        if (acquireJobId) {
          const acquireFinal = await pollJob(acquireJobId, "Fetching article bodies");
          if (acquireFinal?.status === "failed") {
            throw new Error(acquireFinal.error_message || "Acquire job failed");
          }
        }
      }

      if (neu > 0) {
        setDiscoverMsg(`Scraped ${neu} lesson${neu !== 1 ? "s" : ""} (${found} found).`);
      } else if (found > 0) {
        setDiscoverMsg(`Up to date — ${found} lessons indexed.`);
      } else {
        setDiscoverMsg("No lessons found.");
      }
      await load();
    } catch (err: any) {
      setDiscoverMsg(err.message ?? "Discovery failed");
    } finally {
      setDiscovering(false);
    }
  };

  const handleAutoTranscribe = async (auto_transcribe: boolean) => {
    if (!id || !source) return;
    const prev = Boolean(source.auto_transcribe);
    setSource({ ...source, auto_transcribe });
    try {
      const res = await fetch(`${API_BASE}/api/v1/sources/${id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ auto_transcribe }),
      });
      if (!res.ok) throw new Error("Failed to update auto-transcribe");
      const updated = await res.json();
      setSource((current) =>
        current
          ? { ...current, auto_transcribe: Boolean(updated.auto_transcribe) }
          : current,
      );
    } catch (err: any) {
      setSource((current) => (current ? { ...current, auto_transcribe: prev } : current));
      setDiscoverMsg(err.message ?? "Failed to update auto-transcribe");
    }
  };

  const handleSourceOnOff = async (active: boolean) => {
    if (!id || !source) return;
    const nextStatus = active ? "active" : "paused";
    const prevStatus = source.status;
    setSource({ ...source, status: nextStatus });
    try {
      const res = await fetch(`${API_BASE}/api/v1/sources/${id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status: nextStatus }),
      });
      if (!res.ok) throw new Error("Failed to update source status");
      setSource(mapSource(await res.json()));
    } catch (err: any) {
      setSource((current) => (current ? { ...current, status: prevStatus } : current));
      setDiscoverMsg(err.message ?? "Failed to update On/Off");
    }
  };

  const handleTranscribeItem = async (mediaId: string) => {
    if (transcribingIds.has(mediaId)) return;
    setTranscribingIds((previous) => new Set(previous).add(mediaId));
    try {
      const res = await fetch(`${API_BASE}/api/v1/media/${mediaId}/transcribe`, {
        method: "POST",
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail ?? "Failed to queue transcription");
      }
      await load();
    } catch (err: any) {
      setDiscoverMsg(err.message ?? "Failed to queue transcription");
    } finally {
      setTranscribingIds((previous) => {
        const next = new Set(previous);
        next.delete(mediaId);
        return next;
      });
    }
  };

  const handleCopyAllTranscripts = async () => {
    if (transcripts.length === 0) return;
    const blob = transcripts
      .map((t, i) => {
        const title = t.title?.trim() || `Item ${i + 1}`;
        const body = (t.full_text || "").trim();
        return `${title}\n\n${body}`;
      })
      .join("\n\n---\n\n");
    try {
      await navigator.clipboard.writeText(blob);
      setCopiedAll(true);
      window.setTimeout(() => setCopiedAll(false), 2000);
    } catch {
      setDiscoverMsg("Could not copy transcripts to clipboard.");
    }
  };

  const handleTranscribeAll = async (retryFailed = false) => {
    if (!id || transcribingAll) return;
    setTranscribingAll(true);
    setDiscoverMsg(null);
    try {
      const res = await fetch(
        `${API_BASE}/api/v1/sources/${id}/transcribe-all?retry_failed=${retryFailed}`,
        { method: "POST" },
      );
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(
          typeof data.detail === "string" ? data.detail : "Failed to queue Transcribe all",
        );
      }
      const queued = Number(data.queued ?? 0);
      const completed = Number(data.already_completed ?? 0);
      const active = Number(data.already_active ?? 0);
      const failedSkip = Number(data.skipped_failed ?? 0);
      if (queued === 0 && active === 0) {
        setDiscoverMsg(
          completed > 0
            ? `Channel done — ${completed} transcript${completed !== 1 ? "s" : ""} complete.`
            : failedSkip > 0
              ? `${failedSkip} failed item${failedSkip !== 1 ? "s" : ""} skipped. Use Retry failed to re-queue.`
              : "Nothing to transcribe.",
        );
      } else {
        setDiscoverMsg(
          `Queued ${queued} item${queued !== 1 ? "s" : ""}` +
            (active > 0 ? ` · ${active} already running` : "") +
            (completed > 0 ? ` · ${completed} already done` : "") +
            (failedSkip > 0 ? ` · ${failedSkip} failed skipped` : "") +
            ". Worker will process them in order.",
        );
      }
      await load();
      if (view === "transcripts") await loadTranscripts();
    } catch (err: any) {
      setDiscoverMsg(err.message ?? "Failed to queue Transcribe all");
    } finally {
      setTranscribingAll(false);
    }
  };

  const handleEditSource = async (data: CourseSourceFormData) => {
    if (!id) return;
    setDiscoverMsg(null);
    try {
      const res = await fetch(`${API_BASE}/api/v1/sources/${id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: data.name,
          source_url: data.url,
          source_type: data.sourceType,
          course_id: data.courseId,
          connector: data.connector,
        }),
      });
      const raw = await res.text();
      if (!res.ok) {
        let message = raw;
        try {
          const parsed = JSON.parse(raw);
          message = typeof parsed.detail === "string" ? parsed.detail : raw;
        } catch {
          /* keep raw */
        }
        toast({ variant: "destructive", title: "Could not save source", description: message });
        throw new Error(message);
      }
      setSource(mapSource(JSON.parse(raw)));
      toast({ title: "Source saved" });
      setShowEditSource(false);
      await load();
    } catch (err: any) {
      if (!String(err.message || "").includes("Could not save")) {
        toast({
          variant: "destructive",
          title: "Could not save source",
          description: err.message ?? "Update failed",
        });
      }
    }
  };

  const courseLessonRows = useMemo(() => {
    let rowNum = 0;
    return courseLessons.map((lesson, index) => {
      const prev = index > 0 ? courseLessons[index - 1] : null;
      const header = moduleHeaderLabel(lesson.category);
      const prevHeader = prev ? moduleHeaderLabel(prev.category) : null;
      const showModuleHeader = Boolean(header) && header !== prevHeader;
      rowNum += 1;
      return { lesson, showModuleHeader, header, rowNum };
    });
  }, [courseLessons]);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-24 text-muted-foreground gap-2">
        <Loader2 className="w-4 h-4 animate-spin" /> Loading channel…
      </div>
    );
  }

  if (error || !source) {
    return (
      <div className="space-y-4 py-12">
        <Link href="/courses/sources" className="inline-flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground">
          <ArrowLeft className="w-4 h-4" /> Back to sources
        </Link>
        <div className="flex items-center gap-2 text-red-400 text-sm">
          <AlertCircle className="w-4 h-4" /> {error ?? "Source not found"}
        </div>
      </div>
    );
  }

  const isFacebook = source.platform === "facebook";
  const title = source.name || source.source_url;
  const destinationId = libraryCourseIdFromSource(source);
  const isLibraryCourse = source.domain === "courses" && Boolean(destinationId);
  const isFileBacked = isFileBackedLibrarySource(source);
  const diskFolderId = destinationId ? libraryDiskFolderId(destinationId) : null;
  const curriculumType = normalizeCurriculumType(source.connector);
  const isManualCurriculum = curriculumType === "manual" && !isFileBacked;
  const discoverEnabled = curriculumType !== "manual" && !isFileBacked;
  const sourceIsOn = source.status === "active";
  const canDiscover = discoverEnabled && sourceIsOn;
  const current = transcripts[transcriptIdx] ?? null;
  const pendingCount = items.filter((item) =>
    ["queued", "downloading", "transcribing", "analyzing", "failed"].includes(item.status),
  ).length;
  const transcriptCompleted = items.filter(
    (item) => item.transcription_status === "completed",
  ).length;
  const transcriptActive = items.filter((item) =>
    ["queued", "running", "transcribing"].includes(item.transcription_status || item.status),
  ).length;
  const transcriptFailed = items.filter(
    (item) => item.transcription_status === "failed",
  ).length;
  const transcriptPending = Math.max(
    0,
    items.length - transcriptCompleted - transcriptActive - transcriptFailed,
  );
  const channelTranscriptDone =
    items.length > 0 && transcriptCompleted === items.length;
  const streamTypes = Array.from(
    new Set([
      ...(source.streams ?? []).map((stream) => stream.stream_type),
      ...items.map((item) => item.stream_type).filter((value): value is string => Boolean(value)),
    ])
  );
  const typeFilteredItems =
    typeFilter === "all"
      ? items
      : items.filter((item) => item.stream_type === typeFilter);
  const filteredItems = typeFilteredItems.filter((item) => {
    const downloadDone = item.download_status === "completed";
    const transcriptDone = item.transcription_status === "completed";
    const matchesDownload =
      downloadFilter === "all" ||
      (downloadFilter === "done" ? downloadDone : !downloadDone);
    const matchesTranscript =
      transcriptFilter === "all" ||
      (transcriptFilter === "done" ? transcriptDone : !transcriptDone);
    return matchesDownload && matchesTranscript;
  });

  const exportCourseId = diskFolderId || destinationId;

  const handleExportDocx = async () => {
    if (!exportCourseId) return;
    if (!coursePublished) {
      setExportMsg("Turn course Publish on before exporting DOCX.");
      return;
    }
    setExportingDocx(true);
    setExportMsg(null);
    try {
      const filename = await downloadCourseDocx(exportCourseId);
      setExportMsg(`Exported ${filename}`);
    } catch (err: unknown) {
      setExportMsg(err instanceof Error ? err.message : "Export failed");
    } finally {
      setExportingDocx(false);
    }
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div className="space-y-3 min-w-0 flex-1">
          <LibraryBreadcrumb
            items={[
              { label: "Sources", href: "/courses/sources" },
              { label: title },
            ]}
          />
          <div className="flex flex-wrap items-center gap-2">
            <PlatformBadge platform={source.platform} variant="logo" />
            <SourceStatusBadge status={source.status} />
            <Badge variant="outline" className="gap-1.5 text-fine tracking-normal normal-case">
              <span>{isFileBacked ? "Legacy scrape" : curriculumTypeLabel(source.connector)}</span>
            </Badge>
            <Badge variant="outline" className="gap-1.5 text-fine tracking-normal normal-case">
              <span>{sourceTypeLabel(source.source_type)}</span>
              <span className="tabular-nums text-muted-foreground">
                {isLibraryCourse ? courseLessons.length : (source.item_count ?? total)}
              </span>
            </Badge>
          </div>
          <h1 className="page-title truncate">{title}</h1>
          <div className="flex flex-col gap-1.5">
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-fine font-bold uppercase tracking-wider text-muted-foreground shrink-0">
                {isFileBacked ? "Origin" : "Source URL"}
              </span>
              {isFileBacked ? (
                <div className="flex flex-wrap items-center gap-2 min-w-0">
                  <span className="text-sm text-muted-foreground font-mono truncate max-w-[420px]" title={source.source_url}>
                    File-backed · v2/data/{diskFolderId}/
                  </span>
                  {source.vanity_url ? (
                    <>
                      <span className="text-border">·</span>
                      <a
                        href={source.vanity_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-1.5 text-sm text-muted-foreground hover:text-primary"
                        title={source.vanity_url}
                      >
                        <span className="truncate max-w-[320px] font-mono">
                          {displaySourcePath(source.vanity_url)}
                        </span>
                        <ExternalLink className="w-3.5 h-3.5 shrink-0" />
                      </a>
                    </>
                  ) : null}
                </div>
              ) : (
                <a
                  href={source.source_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1.5 text-sm text-muted-foreground hover:text-primary"
                  title={source.source_url}
                >
                  <span className="truncate max-w-[420px] font-mono">
                    {displaySourcePath(source.source_url)}
                  </span>
                  <ExternalLink className="w-3.5 h-3.5 shrink-0" />
                </a>
              )}
              <span className="text-border mx-1">|</span>
              <button
                type="button"
                onClick={() => setShowEditSource(true)}
                className="text-fine font-bold uppercase tracking-wider text-primary hover:underline"
              >
                Edit source
              </button>
            </div>
            {destinationId ? (
              <p className="text-xs text-muted-foreground font-mono">
                Destination tag: {destinationId}
                {diskFolderId && diskFolderId !== destinationId ? (
                  <> · on disk: v2/data/{diskFolderId}/</>
                ) : (
                  <> · v2/data/{destinationId}/</>
                )}
                {" · "}
                <Link
                  href={`/courses/lessons?course=${encodeURIComponent(destinationId)}`}
                  className="text-primary hover:underline"
                >
                  Open lessons
                </Link>
              </p>
            ) : (
              <p className="text-xs text-amber-600">
                No destination ID — edit source and set Destination ID before importing lessons.
              </p>
            )}
          </div>
          <p className="text-xs text-muted-foreground">
            {isLibraryCourse ? (
              <>
                {courseLessons.length} lesson{courseLessons.length !== 1 ? "s" : ""} on disk
                {source.description ? ` · ${source.description}` : ""}
              </>
            ) : (
              <>
                {total} item{total !== 1 ? "s" : ""} saved
                {source.last_checked ? ` · Last checked ${formatRelativeDate(source.last_checked)}` : " · Never checked"}
              </>
            )}
          </p>
          {items.length > 0 && (
            <p
              className={`text-xs font-medium ${
                channelTranscriptDone
                  ? "text-emerald-500"
                  : transcriptActive > 0
                    ? "text-amber-500"
                    : "text-muted-foreground"
              }`}
            >
              {channelTranscriptDone ? (
                <>Channel done — {transcriptCompleted}/{items.length} transcribed</>
              ) : (
                <>
                  {transcriptCompleted}/{items.length} transcribed
                  {transcriptActive > 0 ? ` · ${transcriptActive} running` : ""}
                  {transcriptPending > 0 ? ` · ${transcriptPending} pending` : ""}
                  {transcriptFailed > 0 ? ` · ${transcriptFailed} failed` : ""}
                </>
              )}
            </p>
          )}
        </div>

        <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-2 shrink-0">
          <OnOffToggle
            checked={sourceIsOn}
            onCheckedChange={handleSourceOnOff}
            title={sourceIsOn ? "On — Discover allowed" : "Off — Discover blocked"}
          />
          {!isLibraryCourse ? (
            <>
          <div
            className="flex items-center gap-2 rounded-lg border border-border/50 px-3 h-9"
            title="After Discover, queue pending items (Settings concurrency/batch apply)"
          >
            <Switch
              checked={Boolean(source.auto_transcribe)}
              onCheckedChange={handleAutoTranscribe}
              aria-label="Auto-transcribe after Discover"
            />
            <span className="text-xs font-medium whitespace-nowrap">
              Auto-transcribe
            </span>
          </div>
          <Button
            variant="outline"
            onClick={() => handleTranscribeAll(false)}
            disabled={transcribingAll || discovering || items.length === 0 || channelTranscriptDone}
            className="gap-2"
            title={
              channelTranscriptDone
                ? "All items already transcribed"
                : "Queue transcription for every pending item on this channel"
            }
          >
            {transcribingAll ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <FileText className="w-4 h-4" />
            )}
            {transcribingAll ? "Queuing…" : "Transcribe all"}
          </Button>
          {transcriptFailed > 0 && (
            <Button
              variant="outline"
              onClick={() => handleTranscribeAll(true)}
              disabled={transcribingAll || discovering}
              className="gap-2"
              title="Re-queue failed transcriptions"
            >
              Retry failed
            </Button>
          )}
            </>
          ) : null}
          {isManualCurriculum ? (
            <Button
              variant="outline"
              onClick={() => setShowManualImport(true)}
              disabled={!destinationId}
              className="gap-2"
              title="Paste YouTube links — manual curriculum only"
            >
              <Youtube className="w-4 h-4 text-red-500" />
              Add YouTube lessons
            </Button>
          ) : null}
          {isLibraryCourse && exportCourseId ? (
            <Button
              variant="outline"
              onClick={() => void handleExportDocx()}
              disabled={exportingDocx || !coursePublished}
              className="gap-2"
              title={
                coursePublished
                  ? "Export all publishable lessons to DOCX"
                  : "Turn course Publish on before exporting"
              }
            >
              {exportingDocx ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <FileDown className="w-4 h-4" />
              )}
              Export DOCX
            </Button>
          ) : null}
          {discoverEnabled ? (
            <Button
              onClick={handleDiscover}
              disabled={discovering || !sourceIsOn}
              className="gap-2"
              title={
                !sourceIsOn
                  ? "Source is off — turn On/Off on before Discover"
                  : curriculumType === "article_hub"
                    ? "Index lesson links, then fetch full article bodies"
                    : "Scrape lesson index from source URL"
              }
            >
              {discovering ? <Loader2 className="w-4 h-4 animate-spin" /> : <RefreshCw className="w-4 h-4" />}
              {discovering ? "Scraping…" : "Discover"}
            </Button>
          ) : null}
        </div>
      </div>

      {exportMsg && (
        <div
          className={`flex items-start gap-2 text-sm rounded-xl px-4 py-3 border ${
            exportMsg.toLowerCase().includes("fail") || exportMsg.toLowerCase().includes("turn course")
              ? "text-red-400 bg-red-500/5 border-red-500/20"
              : "text-primary bg-primary/5 border-primary/20"
          }`}
        >
          <span>{exportMsg}</span>
        </div>
      )}

      {discoverMsg && (
        <div className={`flex items-start gap-2 text-sm rounded-xl px-4 py-3 border ${
          discoverMsg.toLowerCase().includes("fail") || discoverMsg.toLowerCase().includes("couldn't") || discoverMsg.toLowerCase().includes("error")
            ? "text-red-400 bg-red-500/5 border-red-500/20"
            : "text-primary bg-primary/5 border-primary/20"
        }`}>
          {discoverMsg.toLowerCase().includes("fail") || discoverMsg.toLowerCase().includes("couldn't") ? (
            <AlertCircle className="w-4 h-4 mt-0.5 shrink-0" />
          ) : (
            <CheckCircle2 className="w-4 h-4 mt-0.5 shrink-0" />
          )}
          <span>{discoverMsg}</span>
        </div>
      )}

      {source.error_message && (
        <div className="flex items-start gap-2 text-sm text-red-400 bg-red-500/5 border border-red-500/20 rounded-xl px-4 py-3">
          <AlertCircle className="w-4 h-4 mt-0.5 shrink-0" />
          {source.error_message}
        </div>
      )}

      {isLibraryCourse ? (
        courseLessons.length === 0 ? (
          <div className="rounded-2xl border border-dashed border-border/60 bg-muted/20 px-6 py-14 text-center space-y-4">
            <p className="text-sm font-medium">No lessons on disk yet</p>
            <p className="text-xs text-muted-foreground max-w-md mx-auto">
              {isFileBacked ? (
                <>
                  Legacy scrape — lessons live under{" "}
                  <code className="text-xs">v2/data/{diskFolderId}/</code>. If the table is empty, reload
                  the page or open <strong>Open lessons</strong>.
                </>
              ) : discoverEnabled ? (
                <>
                  Click <strong>Discover</strong> to scrape lessons from the source URL into{" "}
                  <code className="text-xs">v2/data/{destinationId}/</code>.
                  {curriculumType === "article_hub"
                    ? " Article hubs also fetch full bodies in the same run."
                    : null}
                </>
              ) : (
                <>
                  Manual curriculum — paste YouTube links with <strong>Add YouTube lessons</strong>. They
                  land in <code className="text-xs">v2/data/{destinationId}/</code> and appear here.
                </>
              )}
            </p>
            <div className="flex flex-wrap items-center justify-center gap-2">
              {isFileBacked ? (
                <>
                  <Button variant="outline" onClick={() => load()} className="gap-2">
                    <RefreshCw className="w-4 h-4" />
                    Reload lessons
                  </Button>
                  <Button variant="outline" asChild>
                    <Link href={`/courses/lessons?course=${encodeURIComponent(destinationId!)}`}>
                      Open in Lessons
                    </Link>
                  </Button>
                </>
              ) : discoverEnabled ? (
                <Button variant="outline" onClick={handleDiscover} disabled={discovering || !sourceIsOn} className="gap-2">
                  {discovering ? <Loader2 className="w-4 h-4 animate-spin" /> : <RefreshCw className="w-4 h-4" />}
                  Discover
                </Button>
              ) : (
                <Button
                  variant="outline"
                  onClick={() => setShowManualImport(true)}
                  disabled={!destinationId}
                  className="gap-2"
                >
                  <Youtube className="w-4 h-4 text-red-500" />
                  Add YouTube lessons
                </Button>
              )}
            </div>
          </div>
        ) : (
          <div className="space-y-3">
            <div className="flex items-center justify-between gap-3 flex-wrap">
              <h2 className="text-sm font-semibold tracking-tight">
                Lessons
                <span className="ml-2 text-muted-foreground font-normal">({courseLessons.length})</span>
              </h2>
              <Link
                href={`/courses/lessons?course=${encodeURIComponent(destinationId!)}`}
                className="text-xs text-muted-foreground hover:text-primary"
              >
                Open in Lessons →
              </Link>
            </div>
            <div className="rounded-xl border border-border/50 overflow-hidden">
              <Table>
                <TableHeader>
                  <TableRow className="hover:bg-transparent">
                    <TableHead className="h-11 px-3 text-fine font-bold uppercase tracking-wider w-[52px] text-right">#</TableHead>
                    <TableHead className="h-11 px-4 text-fine font-bold uppercase tracking-wider">Title</TableHead>
                    <TableHead className="h-11 px-4 text-fine font-bold uppercase tracking-wider w-[160px]">Module</TableHead>
                    <TableHead className="h-11 px-4 text-fine font-bold uppercase tracking-wider min-w-[240px]">Source URL</TableHead>
                    <TableHead className="h-11 px-4 text-fine font-bold uppercase tracking-wider w-[100px]">Content</TableHead>
                    <TableHead className="h-11 px-4 text-fine font-bold uppercase tracking-wider w-[80px] text-right">Open</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {courseLessonRows.map(({ lesson, showModuleHeader, header, rowNum }) => {
                    const urlKind = lessonUrlKind(lesson.source_url);
                    return (
                      <Fragment key={lesson.id}>
                        {showModuleHeader ? (
                          <TableRow className="bg-muted/40 hover:bg-muted/40">
                            <TableCell
                              colSpan={6}
                              className="px-4 py-2 text-left text-fine font-bold uppercase tracking-wider text-muted-foreground"
                            >
                              {header}
                            </TableCell>
                          </TableRow>
                        ) : null}
                        <TableRow className="h-14">
                        <TableCell className="px-3 py-3 text-right text-xs tabular-nums text-muted-foreground">
                          {rowNum}
                        </TableCell>
                        <TableCell className="px-4 py-3">
                          <Link
                            href={`/courses/lessons/${encodeURIComponent(lesson.id)}`}
                            className="text-sm font-medium leading-snug line-clamp-2 hover:text-primary"
                            title={lesson.title}
                          >
                            {lesson.title}
                          </Link>
                        </TableCell>
                        <TableCell className="px-4 py-3 text-xs text-muted-foreground">
                          {lesson.category}
                        </TableCell>
                        <TableCell className="px-4 py-3">
                          {lesson.source_url ? (
                            <a
                              href={lesson.source_url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="inline-flex items-center gap-1.5 text-xs font-mono text-muted-foreground hover:text-primary max-w-[360px]"
                              title={lesson.source_url}
                            >
                              {urlKind === "youtube" ? (
                                <Youtube className="w-3.5 h-3.5 shrink-0 text-red-500" />
                              ) : (
                                <ExternalLink className="w-3.5 h-3.5 shrink-0" />
                              )}
                              <span className="truncate">{displayLessonUrl(lesson.source_url)}</span>
                            </a>
                          ) : (
                            <span className="text-xs text-muted-foreground">—</span>
                          )}
                        </TableCell>
                        <TableCell className="px-4 py-3 text-xs text-muted-foreground">
                          {contentStatusLabel(lesson)}
                        </TableCell>
                        <TableCell className="px-4 py-3 text-right">
                          {lesson.source_url ? (
                            <Button size="sm" variant="outline" className="h-8" asChild>
                              <a href={lesson.source_url} target="_blank" rel="noopener noreferrer">
                                <ExternalLink className="w-3.5 h-3.5" />
                              </a>
                            </Button>
                          ) : null}
                        </TableCell>
                      </TableRow>
                      </Fragment>
                    );
                  })}
                </TableBody>
              </Table>
            </div>
          </div>
        )
      ) : (
        <>
      {items.length === 0 ? (
        <div className="rounded-2xl border border-dashed border-border/60 bg-muted/20 px-6 py-14 text-center space-y-4">
          <p className="text-sm font-medium">No items saved for this channel</p>
          <div className="flex flex-wrap items-center justify-center gap-2">
            {isFacebook && (
              <Button variant="outline" size="sm" onClick={() => setShowEditSource(true)}>
                Edit source
              </Button>
            )}
            <Button variant="outline" onClick={handleDiscover} disabled={discovering || !sourceIsOn} className="gap-2">
              {discovering ? <Loader2 className="w-4 h-4 animate-spin" /> : <RefreshCw className="w-4 h-4" />}
              Discover
            </Button>
          </div>
        </div>
      ) : (
        <>
          <div className="flex items-center gap-1 p-1 rounded-xl bg-muted/40 border border-border/50 w-fit">
            <button
              type="button"
              onClick={() => setView("grid")}
              className={`inline-flex items-center gap-1.5 text-xs font-medium px-3 py-1.5 rounded-lg transition-colors ${
                view === "grid" ? "bg-background text-foreground shadow-sm" : "text-muted-foreground hover:text-foreground"
              }`}
            >
              <LayoutGrid className="w-3.5 h-3.5" /> Grid
            </button>
            <button
              type="button"
              onClick={() => setView("items")}
              className={`inline-flex items-center gap-1.5 text-xs font-medium px-3 py-1.5 rounded-lg transition-colors ${
                view === "items" ? "bg-background text-foreground shadow-sm" : "text-muted-foreground hover:text-foreground"
              }`}
            >
              <List className="w-3.5 h-3.5" /> Table
            </button>
            <button
              type="button"
              onClick={() => setView("transcripts")}
              className={`inline-flex items-center gap-1.5 text-xs font-medium px-3 py-1.5 rounded-lg transition-colors ${
                view === "transcripts" ? "bg-background text-foreground shadow-sm" : "text-muted-foreground hover:text-foreground"
              }`}
            >
              <FileText className="w-3.5 h-3.5" /> Transcripts
              {transcriptTotal > 0 && (
                <span className="text-fine text-muted-foreground">({transcriptTotal})</span>
              )}
            </button>
          </div>

          {view === "transcripts" ? (
        <div className="space-y-4">
          <div className="flex items-center justify-between gap-3 flex-wrap">
            <h2 className="text-sm font-semibold tracking-tight">
              Transcripts
              <span className="ml-2 text-muted-foreground font-normal">
                ({transcriptTotal})
                {pendingCount > 0 && (
                  <span className="ml-2 text-amber-500">· {pendingCount} pending / failed</span>
                )}
              </span>
            </h2>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={handleCopyAllTranscripts}
                disabled={transcripts.length === 0}
                className="gap-1.5"
                title="Copy every title and transcript text"
              >
                {copiedAll ? <Check className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />}
                {copiedAll ? "Copied" : "Copy all"}
              </Button>
              <Button variant="outline" size="sm" onClick={loadTranscripts} disabled={transcriptsLoading} className="gap-1.5">
                {transcriptsLoading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <RefreshCw className="w-3.5 h-3.5" />}
                Refresh
              </Button>
            </div>
          </div>

          {transcriptsLoading && transcripts.length === 0 ? (
            <div className="flex items-center justify-center py-16 text-muted-foreground gap-2 text-sm">
              <Loader2 className="w-4 h-4 animate-spin" /> Loading transcripts…
            </div>
          ) : transcripts.length === 0 ? (
            <div className="rounded-2xl border border-dashed border-border/60 bg-muted/20 px-6 py-14 text-center space-y-4">
              <p className="text-sm font-medium">No transcripts yet</p>
              <p className="text-xs text-muted-foreground max-w-md mx-auto leading-relaxed">
                Use <strong>Transcribe all</strong> above, or Transcribe on individual rows.
                Completed transcripts appear here for sequential reading.
              </p>
              <div className="flex flex-wrap items-center justify-center gap-2">
                <Button
                  variant="outline"
                  onClick={() => handleTranscribeAll(false)}
                  disabled={transcribingAll || channelTranscriptDone}
                  className="gap-2"
                >
                  {transcribingAll ? <Loader2 className="w-4 h-4 animate-spin" /> : <FileText className="w-4 h-4" />}
                  Transcribe all
                </Button>
                <Button variant="outline" onClick={() => setView("items")} className="gap-2">
                  <LayoutGrid className="w-4 h-4" /> Open Items
                </Button>
              </div>
            </div>
          ) : (
            <div className="grid grid-cols-1 lg:grid-cols-[480px_1fr] gap-4">
              {/* Sidebar list */}
              <div className="rounded-xl border border-border/50 bg-muted/20 max-h-[70vh] overflow-y-auto divide-y divide-border/40">
                {transcripts.map((t, i) => (
                  <button
                    key={t.media_id}
                    type="button"
                    onClick={() => setTranscriptIdx(i)}
                    className={`w-full text-left px-3 py-2.5 transition-colors ${
                      i === transcriptIdx
                        ? "bg-primary/10 border-l-2 border-l-primary"
                        : "hover:bg-muted/50 border-l-2 border-l-transparent"
                    }`}
                  >
                    <p className="text-xs font-medium leading-snug line-clamp-2">
                      {t.title || `Item ${i + 1}`}
                    </p>
                    <p className="text-fine text-muted-foreground mt-0.5">
                      {t.word_count ?? 0} words
                      {t.language ? ` · ${t.language}` : ""}
                    </p>
                  </button>
                ))}
              </div>

              {/* Reader */}
              {current && (
                <div className="rounded-xl border border-border/50 bg-background flex flex-col min-h-[70vh]">
                  <div className="flex items-start justify-between gap-3 px-5 py-4 border-b border-border/40">
                    <div className="min-w-0 space-y-1">
                      <p className="text-fine font-bold uppercase tracking-widest text-muted-foreground">
                        {transcriptIdx + 1} of {transcripts.length}
                      </p>
                      <h3 className="text-base font-semibold leading-snug">
                        {current.title || "Untitled item"}
                      </h3>
                      <p className="text-xs text-muted-foreground">
                        {current.word_count ?? 0} words
                        {current.language ? ` · ${current.language}` : ""}
                        {current.model_used ? ` · ${current.model_used}` : ""}
                      </p>
                    </div>
                    <a
                      href={current.canonical_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1 text-xs text-muted-foreground hover:text-primary shrink-0"
                    >
                      Open <ExternalLink className="w-3 h-3" />
                    </a>
                  </div>

                  <div className="flex-1 overflow-y-auto px-5 py-5">
                    <p className="text-sm leading-relaxed whitespace-pre-wrap">
                      {current.full_text || "(empty transcript)"}
                    </p>
                  </div>

                  <div className="flex items-center justify-between gap-3 px-5 py-3 border-t border-border/40">
                    <Button
                      variant="outline"
                      size="sm"
                      disabled={transcriptIdx <= 0}
                      onClick={() => setTranscriptIdx((i) => Math.max(0, i - 1))}
                      className="gap-1.5"
                    >
                      <ChevronLeft className="w-4 h-4" /> Previous
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      disabled={transcriptIdx >= transcripts.length - 1}
                      onClick={() => setTranscriptIdx((i) => Math.min(transcripts.length - 1, i + 1))}
                      className="gap-1.5"
                    >
                      Next <ChevronRight className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      ) : view === "grid" ? (
        <div className="space-y-3">
          <div className="flex items-center justify-between gap-3 flex-wrap">
            <h2 className="text-sm font-semibold tracking-tight">
              {isFacebook ? "Reels" : "Items"}
              <span className="ml-2 text-muted-foreground font-normal">
                ({filteredItems.length}{typeFilter !== "all" ? ` of ${total}` : ""})
              </span>
            </h2>
            <Select value={typeFilter} onValueChange={setTypeFilter}>
              <SelectTrigger className="w-[220px]" aria-label="Filter channel items by type">
                <SelectValue placeholder="All types" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All types ({items.length})</SelectItem>
                {streamTypes.map((streamType) => {
                  const count = items.filter((item) => item.stream_type === streamType).length;
                  return (
                    <SelectItem key={streamType} value={streamType}>
                      {sourceTypeLabel(streamType)} ({count})
                    </SelectItem>
                  );
                })}
              </SelectContent>
            </Select>
          </div>

          <div className="grid grid-cols-3 sm:grid-cols-5 lg:grid-cols-7 gap-1.5">
            {filteredItems.map((item) => (
              <div
                key={item.id}
                className="group relative aspect-[9/16] rounded-xl overflow-hidden border border-border/50 bg-muted/40 hover:border-primary/40 transition-colors"
              >
                <a
                  href={item.canonical_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="absolute inset-0 block"
                  title={item.title ? `Play: ${item.title}` : "Play reel"}
                >
                  {item.thumbnail_url ? (
                    // eslint-disable-next-line @next/next/no-img-element
                    <img
                      src={item.thumbnail_url}
                      alt={item.title ?? ""}
                      loading="lazy"
                      referrerPolicy="no-referrer"
                      className="absolute inset-0 w-full h-full object-cover"
                    />
                  ) : (
                    <div className="absolute inset-0 bg-gradient-to-b from-muted to-muted/60" />
                  )}
                  <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/20 to-transparent" />
                  <span className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
                    <span className="inline-flex h-10 w-10 items-center justify-center rounded-full bg-black/55 text-white shadow-lg">
                      <Play className="h-5 w-5 fill-current" />
                    </span>
                  </span>
                  <div className="absolute bottom-0 left-0 right-0 p-2.5 space-y-1 pointer-events-none">
                    <p className="text-caption font-medium text-white leading-snug line-clamp-2">
                      {item.title || "Untitled"}
                    </p>
                    <div className="flex items-center gap-2 text-fine text-white/70 tabular-nums">
                      {item.view_count != null && (
                        <span className="inline-flex items-center gap-0.5">
                          <Eye className="w-3 h-3" /> {formatViews(item.view_count)}
                        </span>
                      )}
                      {item.duration_seconds != null && (
                        <span className="font-mono">{formatDuration(item.duration_seconds)}</span>
                      )}
                      {item.file_size_bytes != null && (
                        <span className="font-mono">{formatFileSize(item.file_size_bytes)}</span>
                      )}
                    </div>
                    {item.published_at && (
                      <p className="text-fine text-white/60">{formatPublishedDate(item.published_at)}</p>
                    )}
                  </div>
                </a>
                <button
                  type="button"
                  onClick={() => setDetailId(item.id)}
                  className="absolute top-2 right-2 z-10 inline-flex h-7 w-7 items-center justify-center rounded-md bg-black/50 text-white opacity-0 group-hover:opacity-100 transition-opacity hover:bg-black/70"
                  title="Open transcript"
                >
                  <FileText className="w-3.5 h-3.5" />
                </button>
              </div>
            ))}
          </div>
          {filteredItems.length === 0 && (
            <div className="h-20 flex items-center justify-center text-sm text-muted-foreground">
              No items match this type.
            </div>
          )}
        </div>
      ) : (
        <div className="space-y-3">
          <div className="flex items-center justify-between gap-3 flex-wrap">
            <h2 className="text-sm font-semibold tracking-tight">
              Items
              <span className="ml-2 text-muted-foreground font-normal">
                ({filteredItems.length}{
                  typeFilter !== "all" ||
                  downloadFilter !== "all" ||
                  transcriptFilter !== "all"
                    ? ` of ${total}`
                    : ""
                })
              </span>
            </h2>
            <div className="flex items-center gap-2 flex-wrap">
              <Select value={downloadFilter} onValueChange={setDownloadFilter}>
                <SelectTrigger className="w-[170px]" aria-label="Filter by download status">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Download: All</SelectItem>
                  <SelectItem value="done">Download: Done</SelectItem>
                  <SelectItem value="not_done">Download: Not done</SelectItem>
                </SelectContent>
              </Select>
              <Select value={transcriptFilter} onValueChange={setTranscriptFilter}>
                <SelectTrigger className="w-[175px]" aria-label="Filter by transcript status">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Transcript: All</SelectItem>
                  <SelectItem value="done">Transcript: Done</SelectItem>
                  <SelectItem value="not_done">Transcript: Not done</SelectItem>
                </SelectContent>
              </Select>
              <Select value={typeFilter} onValueChange={setTypeFilter}>
                <SelectTrigger className="w-[220px]" aria-label="Filter channel items by type">
                  <SelectValue placeholder="All types" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All types ({items.length})</SelectItem>
                  {streamTypes.map((streamType) => {
                    const count = items.filter(
                      (item) => item.stream_type === streamType
                    ).length;
                    return (
                      <SelectItem key={streamType} value={streamType}>
                        {sourceTypeLabel(streamType)} ({count})
                      </SelectItem>
                    );
                  })}
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="rounded-xl border border-border/50 overflow-hidden">
            <Table>
              <TableHeader>
                <TableRow className="hover:bg-transparent">
                  <TableHead className="h-11 px-3 text-fine font-bold uppercase tracking-wider w-[52px] text-right">#</TableHead>
                  <TableHead className="h-11 px-3 text-fine font-bold uppercase tracking-wider w-[56px]"> </TableHead>
                  <TableHead className="h-11 px-4 text-fine font-bold uppercase tracking-wider">Title</TableHead>
                  <TableHead className="h-11 px-4 text-fine font-bold uppercase tracking-wider w-[200px]">Type</TableHead>
                  <TableHead className="h-11 px-4 text-fine font-bold uppercase tracking-wider w-[90px]">Duration</TableHead>
                  <TableHead className="h-11 px-4 text-fine font-bold uppercase tracking-wider w-[130px]">Size</TableHead>
                  <TableHead className="h-11 px-4 text-fine font-bold uppercase tracking-wider w-[100px]">Download</TableHead>
                  <TableHead className="h-11 px-4 text-fine font-bold uppercase tracking-wider w-[110px]">Transcript</TableHead>
                  <TableHead className="h-11 px-4 text-fine font-bold uppercase tracking-wider w-[110px]">Published</TableHead>
                  <TableHead className="h-11 px-4 text-fine font-bold uppercase tracking-wider w-[110px] text-right">Action</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredItems.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={10} className="h-20 text-center text-sm text-muted-foreground">
                      No items match these filters.
                    </TableCell>
                  </TableRow>
                )}
                {filteredItems.map((item, index) => {
                  const busy = transcribingIds.has(item.id);
                  const canTranscribe = ["pending", "failed"].includes(
                    item.transcription_status || item.status,
                  );
                  return (
                  <TableRow key={item.id} className="h-14">
                    <TableCell className="px-3 py-3 text-right text-xs tabular-nums text-muted-foreground">
                      {index + 1}
                    </TableCell>
                    <TableCell className="px-3 py-2">
                      <a
                        href={item.canonical_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="relative block h-12 w-9 rounded-md overflow-hidden border border-border/50 bg-muted/40 shrink-0 group/thumb"
                        title="Play reel"
                      >
                        {item.thumbnail_url ? (
                          // eslint-disable-next-line @next/next/no-img-element
                          <img
                            src={item.thumbnail_url}
                            alt=""
                            loading="lazy"
                            referrerPolicy="no-referrer"
                            className="absolute inset-0 h-full w-full object-cover"
                          />
                        ) : (
                          <span className="absolute inset-0 bg-muted" />
                        )}
                        <span className="absolute inset-0 flex items-center justify-center bg-black/35 opacity-0 group-hover/thumb:opacity-100 transition-opacity">
                          <Play className="h-3.5 w-3.5 fill-current text-white" />
                        </span>
                      </a>
                    </TableCell>
                    <TableCell className="px-4 py-3">
                      <a
                        href={item.canonical_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-left text-sm font-medium hover:text-primary line-clamp-2"
                        title="Play reel"
                      >
                        {item.title || "Untitled"}
                      </a>
                    </TableCell>
                    <TableCell className="px-4 py-3 text-xs text-muted-foreground">
                      {sourceTypeLabel(item.stream_type || item.content_type || "video")}
                    </TableCell>
                    <TableCell className="px-4 py-3 text-sm tabular-nums text-muted-foreground">
                      {formatDuration(item.duration_seconds)}
                    </TableCell>
                    <TableCell className="px-4 py-3 text-sm tabular-nums text-muted-foreground whitespace-nowrap">
                      {formatFileSize(item.file_size_bytes)}
                    </TableCell>
                    <TableCell className="px-4 py-3 text-xs">
                      {tablePipelineStatus(item.download_status)}
                    </TableCell>
                    <TableCell className="px-4 py-3 text-xs">
                      {tablePipelineStatus(item.transcription_status)}
                    </TableCell>
                    <TableCell className="px-4 py-3 text-xs text-muted-foreground whitespace-nowrap">
                      {item.published_at ? (
                        <span title={formatRelativeDate(item.published_at)}>
                          {formatPublishedDate(item.published_at)}
                        </span>
                      ) : (
                        "—"
                      )}
                    </TableCell>
                    <TableCell className="px-4 py-3 text-right">
                      <div className="inline-flex items-center justify-end gap-1.5">
                        <Button
                          size="sm"
                          variant="outline"
                          className="h-8 gap-1.5 text-fine font-medium"
                          asChild
                        >
                          <a
                            href={item.canonical_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            title="Play reel"
                          >
                            <Play className="h-3.5 w-3.5 fill-current" />
                            Play
                          </a>
                        </Button>
                        {canTranscribe ? (
                          <Button
                            size="sm"
                            variant="outline"
                            disabled={busy}
                            onClick={() => handleTranscribeItem(item.id)}
                            className="h-8 gap-1.5 text-fine font-medium"
                          >
                            {busy ? (
                              <Loader2 className="w-3.5 h-3.5 animate-spin" />
                            ) : (
                              <FileText className="w-3.5 h-3.5" />
                            )}
                            {item.transcription_status === "failed" ? "Retry" : "Transcribe"}
                          </Button>
                        ) : item.transcription_status === "completed" ? (
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => setDetailId(item.id)}
                            className="h-8 gap-1.5 text-fine font-medium"
                          >
                            <FileText className="w-3.5 h-3.5" /> View
                          </Button>
                        ) : null}
                      </div>
                    </TableCell>
                  </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </div>
        </div>
      )}
        </>
      )}
        </>
      )}

      <EditCourseSourceDialog
        open={showEditSource}
        onClose={() => setShowEditSource(false)}
        onSave={handleEditSource}
        source={source ? mapSource({ ...source, last_checked: source.last_checked ?? null }) : null}
      />

      {destinationId && isManualCurriculum ? (
        <ManualImportCourseLessonsDialog
          open={showManualImport}
          onClose={() => setShowManualImport(false)}
          sourceId={id}
          courseId={destinationId}
          courseName={title}
          onImported={() => {
            setDiscoverMsg("Manual lessons imported.");
            load();
          }}
        />
      ) : null}

      <MediaDetailDialog id={detailId} onClose={() => setDetailId(null)} />
    </div>
  );
}
