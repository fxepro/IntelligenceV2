"use client";

import React, { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import {
  AlertCircle,
  ArrowRight,
  CheckCircle2,
  FolderOpen,
  Loader2,
  Plus,
  RefreshCw,
  Search,
  Trash2,
  X,
} from "lucide-react";
import { AppPageHeader } from "@/components/sections/AppPageHeader";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Card, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
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
import { mapSource } from "@/lib/sources/helpers";
import { formatRelativeDate } from "@/lib/mock-data/media-items";
import type { Source } from "@/lib/mock-data/sources";

function displayFolderPath(url: string): string {
  if (url.startsWith("file:")) {
    try {
      const decoded = decodeURIComponent(url.replace(/^file:\/\//i, "").replace(/^\/([A-Za-z]:)/, "$1"));
      return decoded;
    } catch {
      return url;
    }
  }
  return url;
}

export default function LibrarySourcesPage() {
  const [sources, setSources] = useState<Source[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [showAdd, setShowAdd] = useState(false);
  const [folderPath, setFolderPath] = useState("");
  const [sourceName, setSourceName] = useState("");
  const [adding, setAdding] = useState(false);
  const [addError, setAddError] = useState<string | null>(null);
  const [scanning, setScanning] = useState<Set<string>>(new Set());
  const [scanMsg, setScanMsg] = useState<Record<string, string>>({});

  const fetchSources = useCallback(async () => {
    setLoadError(null);
    try {
      const res = await fetch(`${API_BASE}/api/v1/sources?domain=library`);
      if (!res.ok) throw new Error(`Failed to load sources (${res.status})`);
      const data = await res.json();
      setSources((data.items ?? []).map(mapSource));
    } catch (err: unknown) {
      setLoadError(err instanceof Error ? err.message : "Failed to load sources");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void fetchSources();
  }, [fetchSources]);

  const filtered = sources.filter((source) => {
    const q = searchQuery.trim().toLowerCase();
    if (!q) return true;
    return [source.name, source.source_url, ...(source.tags ?? [])]
      .filter(Boolean)
      .some((v) => String(v).toLowerCase().includes(q));
  });

  const handleAdd = async () => {
    const path = folderPath.trim();
    if (!path) {
      setAddError("Folder path is required");
      return;
    }
    setAdding(true);
    setAddError(null);
    try {
      const res = await fetch(`${API_BASE}/api/v1/sources`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          domain: "library",
          platform: "local",
          source_type: "local_folder",
          source_url: path,
          name: sourceName.trim() || undefined,
        }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail ?? `Create failed (${res.status})`);
      }
      setShowAdd(false);
      setFolderPath("");
      setSourceName("");
      await fetchSources();
    } catch (err: unknown) {
      setAddError(err instanceof Error ? err.message : "Failed to add source");
    } finally {
      setAdding(false);
    }
  };

  const handleScan = async (id: string) => {
    setScanning((prev) => new Set(prev).add(id));
    setScanMsg((prev) => {
      const next = { ...prev };
      delete next[id];
      return next;
    });
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
            setScanMsg((prev) => ({
              ...prev,
              [id]: `${result.total_found ?? result.discovered ?? 0} files (${result.new ?? 0} new)`,
            }));
            break;
          }
          if (job.status === "failed") {
            throw new Error(job.error_message || "Scan job failed");
          }
        }
      }
      await fetchSources();
    } catch (err: unknown) {
      setScanMsg((prev) => ({
        ...prev,
        [id]: err instanceof Error ? err.message : "Scan failed",
      }));
    } finally {
      setScanning((prev) => {
        const next = new Set(prev);
        next.delete(id);
        return next;
      });
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Delete this library source and all cataloged files?")) return;
    await fetch(`${API_BASE}/api/v1/sources/${id}`, { method: "DELETE" });
    await fetchSources();
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      <AppPageHeader
        title="Library Sources"
        description="Local folders on your drives — scan to catalog files, then view or play them in the browser."
        icon={<Icon name="library" className="h-5 w-5 text-primary" />}
        actions={
          <Button onClick={() => setShowAdd(true)} className="gap-1.5">
            <Plus className="h-4 w-4" />
            Add folder
          </Button>
        }
      />

      <div className="flex flex-wrap items-center gap-3">
        <div className="relative flex-1 min-w-[200px] max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search sources…"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-9"
          />
          {searchQuery ? (
            <button
              type="button"
              className="absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground"
              onClick={() => setSearchQuery("")}
            >
              <X className="h-4 w-4" />
            </button>
          ) : null}
        </div>
        <Button variant="outline" size="sm" onClick={() => void fetchSources()} className="gap-1.5">
          <RefreshCw className="h-4 w-4" />
          Refresh
        </Button>
      </div>

      {loadError ? (
        <p className="text-sm text-destructive inline-flex items-center gap-2">
          <AlertCircle className="h-4 w-4" />
          {loadError}
        </p>
      ) : null}

      <Card className="shadow-sm border border-border/50 overflow-hidden rounded-2xl">
        <CardHeader className="border-b py-4">
          <CardTitle className="text-sm font-medium flex items-center gap-2">
            <FolderOpen className="h-4 w-4 text-muted-foreground" />
            Folder sources
            <Badge variant="secondary" className="ml-auto">
              {filtered.length}
            </Badge>
          </CardTitle>
        </CardHeader>
        <div className="overflow-x-auto">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-12 text-center">#</TableHead>
                <TableHead>Name</TableHead>
                <TableHead>Folder path</TableHead>
                <TableHead className="text-center">Items</TableHead>
                <TableHead className="text-center">Last scan</TableHead>
                <TableHead className="text-center w-40">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {loading ? (
                <TableRow>
                  <TableCell colSpan={6} className="py-10 text-center text-muted-foreground">
                    <Loader2 className="h-5 w-5 animate-spin inline mr-2" />
                    Loading…
                  </TableCell>
                </TableRow>
              ) : filtered.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={6} className="py-10 text-center text-muted-foreground">
                    No library sources yet. Add a folder path to get started.
                  </TableCell>
                </TableRow>
              ) : (
                filtered.map((source, idx) => (
                  <TableRow key={source.id}>
                    <TableCell className="text-center text-muted-foreground">{idx + 1}</TableCell>
                    <TableCell>
                      <div className="font-medium">{source.name || "—"}</div>
                      {source.catalog_id ? (
                        <div className="text-xs text-muted-foreground">{source.catalog_id}</div>
                      ) : null}
                    </TableCell>
                    <TableCell className="max-w-[360px] truncate text-sm text-muted-foreground" title={displayFolderPath(source.source_url)}>
                      {displayFolderPath(source.source_url)}
                    </TableCell>
                    <TableCell className="text-center">{source.item_count ?? 0}</TableCell>
                    <TableCell className="text-center text-sm text-muted-foreground">
                      {source.last_checked ? formatRelativeDate(source.last_checked) : "—"}
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center justify-center gap-1">
                        <Button
                          variant="outline"
                          size="sm"
                          disabled={scanning.has(source.id)}
                          onClick={() => void handleScan(source.id)}
                          title="Scan folder"
                        >
                          {scanning.has(source.id) ? (
                            <Loader2 className="h-4 w-4 animate-spin" />
                          ) : (
                            <RefreshCw className="h-4 w-4" />
                          )}
                        </Button>
                        <Button asChild variant="outline" size="sm">
                          <Link href={`/library/sources/${source.id}`}>
                            <ArrowRight className="h-4 w-4" />
                          </Link>
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          className="text-destructive"
                          onClick={() => void handleDelete(source.id)}
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                      {scanMsg[source.id] ? (
                        <p className="text-xs text-muted-foreground mt-1 text-center">{scanMsg[source.id]}</p>
                      ) : null}
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </div>
      </Card>

      <Dialog open={showAdd} onOpenChange={setShowAdd}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Add library folder</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-2">
            <div className="space-y-2">
              <label className="text-sm font-medium">Folder path</label>
              <Input
                placeholder="D:\AI Projects Learning\Ethical_robot"
                value={folderPath}
                onChange={(e) => setFolderPath(e.target.value)}
              />
              <p className="text-xs text-muted-foreground">
                Paste the full path to an unzipped folder on this machine.
              </p>
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">Display name (optional)</label>
              <Input
                placeholder="Defaults to folder name"
                value={sourceName}
                onChange={(e) => setSourceName(e.target.value)}
              />
            </div>
            {addError ? (
              <p className="text-sm text-destructive inline-flex items-center gap-1">
                <AlertCircle className="h-4 w-4" />
                {addError}
              </p>
            ) : null}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowAdd(false)}>
              Cancel
            </Button>
            <Button onClick={() => void handleAdd()} disabled={adding} className="gap-1.5">
              {adding ? <Loader2 className="h-4 w-4 animate-spin" /> : <CheckCircle2 className="h-4 w-4" />}
              Add source
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
