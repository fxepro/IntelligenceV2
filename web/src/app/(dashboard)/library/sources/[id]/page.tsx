"use client";

import React, { useCallback, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import {
  AlertCircle,
  ArrowLeft,
  ExternalLink,
  Loader2,
  Play,
  RefreshCw,
} from "lucide-react";
import { AppPageHeader } from "@/components/sections/AppPageHeader";
import { Button } from "@/components/ui/button";
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
import { Icon } from "@/lib/icons";
import { API_BASE } from "@/lib/api-base";
import { mapSource, formatFileSize, sourceTypeLabel } from "@/lib/sources/helpers";
import type { Source } from "@/lib/mock-data/sources";

interface LibraryRow {
  id: string;
  title: string | null;
  stream_type: string | null;
  content_type: string | null;
  file_size_bytes: number | null;
  description: string | null;
  published_at: string | null;
  status: string;
}

type SortKey = "path" | "name" | "type" | "size";

const LIBRARY_PAGE_SIZE = 5000;

function mediaTypeLabel(value: string): string {
  const labels: Record<string, string> = {
    video: "Video",
    pdf: "PDF",
    epub: "EPUB",
    ebook: "Ebook",
    document: "Document",
    audio: "Audio",
    image: "Image",
    folder: "Folder",
    other: "Other",
  };
  return labels[value] || sourceTypeLabel(value);
}

function displayFolderPath(url: string): string {
  if (url.startsWith("file:")) {
    try {
      return decodeURIComponent(url.replace(/^file:\/\//i, "").replace(/^\/([A-Za-z]:)/, "$1"));
    } catch {
      return url;
    }
  }
  return url;
}

function relativePath(item: LibraryRow): string {
  return item.description || item.title || "";
}

function pathCompare(a: string, b: string): number {
  return a.localeCompare(b, undefined, { numeric: true, sensitivity: "base" });
}

export default function LibrarySourceDetailPage() {
  const params = useParams();
  const id = String(params.id ?? "");

  const [source, setSource] = useState<Source | null>(null);
  const [items, setItems] = useState<LibraryRow[]>([]);
  const [total, setTotal] = useState(0);
  const [typeFilter, setTypeFilter] = useState("all");
  const [sortKey, setSortKey] = useState<SortKey>("path");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [scanning, setScanning] = useState(false);
  const [scanMsg, setScanMsg] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!id) return;
    setError(null);
    try {
      const [srcRes, itemsRes] = await Promise.all([
        fetch(`${API_BASE}/api/v1/sources/${id}`),
        fetch(
          `${API_BASE}/api/v1/library?source_id=${id}&page_size=${LIBRARY_PAGE_SIZE}&domain=library`,
        ),
      ]);
      if (!srcRes.ok) throw new Error(`Source not found (${srcRes.status})`);
      setSource(mapSource(await srcRes.json()));
      if (!itemsRes.ok) {
        throw new Error(`Failed to load files (${itemsRes.status})`);
      }
      const data = await itemsRes.json();
      setItems(data.items ?? []);
      setTotal(data.total ?? 0);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load source");
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    setLoading(true);
    setItems([]);
    setTotal(0);
    setError(null);
    void load();
  }, [load]);

  const streamTypes = useMemo(
    () =>
      Array.from(
        new Set(items.map((i) => i.stream_type || i.content_type || "other").filter(Boolean)),
      ).sort(pathCompare),
    [items],
  );

  const rows = useMemo(() => {
    const base =
      typeFilter === "all"
        ? items
        : items.filter((i) => (i.stream_type || i.content_type) === typeFilter);

    return [...base].sort((a, b) => {
      const ra = relativePath(a);
      const rb = relativePath(b);
      if (sortKey === "name") {
        return pathCompare(a.title || ra, b.title || rb);
      }
      if (sortKey === "type") {
        const ta = a.stream_type || a.content_type || "other";
        const tb = b.stream_type || b.content_type || "other";
        return pathCompare(ta, tb) || pathCompare(ra, rb);
      }
      if (sortKey === "size") {
        return (b.file_size_bytes ?? 0) - (a.file_size_bytes ?? 0) || pathCompare(ra, rb);
      }
      return pathCompare(ra, rb);
    });
  }, [items, typeFilter, sortKey]);

  const handleScan = async () => {
    setScanning(true);
    setScanMsg(null);
    try {
      const res = await fetch(`${API_BASE}/api/v1/sources/${id}/discover`, { method: "POST" });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail ?? "Scan failed");
      }
      const data = await res.json();
      const jobId = data.job_id as string | undefined;
      if (jobId) {
        for (let i = 0; i < 120; i++) {
          await new Promise((r) => setTimeout(r, 2000));
          const jr = await fetch(`${API_BASE}/api/v1/jobs/${jobId}`);
          const job = await jr.json().catch(() => ({}));
          if (!jr.ok) continue;
          if (job.status === "completed") {
            const result = job.result || {};
            setScanMsg(
              `Scanned ${result.total_found ?? result.discovered ?? 0} files (${result.new ?? 0} new, ${result.missing ?? 0} missing)`,
            );
            break;
          }
          if (job.status === "failed") {
            throw new Error(job.error_message || "Scan failed");
          }
        }
      }
      await load();
    } catch (err: unknown) {
      setScanMsg(err instanceof Error ? err.message : "Scan failed");
    } finally {
      setScanning(false);
    }
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        <Link href="/library/sources" className="hover:text-foreground inline-flex items-center gap-1">
          <ArrowLeft className="h-4 w-4" />
          Sources
        </Link>
        <span>/</span>
        <span>{source?.name || "…"}</span>
      </div>

      <AppPageHeader
        title={source?.name || "Library source"}
        description={
          source
            ? `${displayFolderPath(source.source_url)} — top-level files and subfolders only`
            : "Local folder"
        }
        icon={<Icon name="library" className="h-5 w-5 text-primary" />}
        actions={
          <div className="flex flex-wrap gap-2">
            <Button
              variant="outline"
              size="sm"
              disabled={scanning}
              onClick={() => void handleScan()}
              className="gap-1.5"
            >
              {scanning ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />}
              Scan folder
            </Button>
            {source?.source_url ? (
              <Button asChild variant="outline" size="sm" className="gap-1.5">
                <a href={source.source_url} title="Open folder URI">
                  <ExternalLink className="h-4 w-4" />
                  Path
                </a>
              </Button>
            ) : null}
          </div>
        }
      />

      {scanMsg ? <p className="text-sm text-muted-foreground">{scanMsg}</p> : null}

      {loading ? (
        <p className="inline-flex items-center gap-2 text-muted-foreground">
          <Loader2 className="h-4 w-4 animate-spin" />
          Loading…
        </p>
      ) : error ? (
        <p className="text-destructive inline-flex items-center gap-2">
          <AlertCircle className="h-4 w-4" />
          {error}
        </p>
      ) : (
        <>
          <div className="flex flex-wrap items-center gap-3">
            <Badge variant="secondary">
              {rows.length === total ? `${total} files` : `${rows.length} of ${total} files`}
            </Badge>
            <Select value={typeFilter} onValueChange={setTypeFilter}>
              <SelectTrigger className="w-[180px]">
                <SelectValue placeholder="All types" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All types</SelectItem>
                {streamTypes.map((t) => (
                  <SelectItem key={t} value={t}>
                    {mediaTypeLabel(t)} ({items.filter((i) => (i.stream_type || i.content_type) === t).length})
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Select value={sortKey} onValueChange={(v) => setSortKey(v as SortKey)}>
              <SelectTrigger className="w-[160px]">
                <SelectValue placeholder="Sort" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="path">Path</SelectItem>
                <SelectItem value="name">Name</SelectItem>
                <SelectItem value="type">Type</SelectItem>
                <SelectItem value="size">Size</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="rounded-2xl border overflow-hidden">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Path</TableHead>
                  <TableHead className="w-[100px]">Type</TableHead>
                  <TableHead className="w-[90px]">Size</TableHead>
                  <TableHead className="w-16 text-center">Open</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {rows.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={4} className="py-10 text-center text-muted-foreground">
                      No files cataloged. Run Scan folder to inventory this directory.
                    </TableCell>
                  </TableRow>
                ) : (
                  rows.map((item) => {
                    const type = item.stream_type || item.content_type || "other";
                    const path = relativePath(item);
                    return (
                      <TableRow key={item.id}>
                        <TableCell className="max-w-[520px] truncate text-sm" title={path}>
                          {path}
                        </TableCell>
                        <TableCell>{mediaTypeLabel(type)}</TableCell>
                        <TableCell>{formatFileSize(item.file_size_bytes)}</TableCell>
                        <TableCell className="text-center">
                          {type === "folder" ? (
                            <span className="text-xs text-muted-foreground">—</span>
                          ) : (
                            <Button asChild variant="outline" size="sm">
                              <Link href={`/library/items/${item.id}`}>
                                <Play className="h-4 w-4" />
                              </Link>
                            </Button>
                          )}
                        </TableCell>
                      </TableRow>
                    );
                  })
                )}
              </TableBody>
            </Table>
          </div>
        </>
      )}
    </div>
  );
}
