"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import {
  ArrowUpRight,
  ChevronLeft,
  ChevronRight,
  ExternalLink,
  Loader2,
  RefreshCw,
} from "lucide-react";
import { AppPageHeader } from "@/components/sections/AppPageHeader";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Icon } from "@/lib/icons";
import type { Source } from "@/lib/mock-data/sources";
import { mapSource, PRIORITY_OPTIONS } from "@/lib/sources/helpers";
import { API_BASE } from "@/lib/api-base";

const GOV_OPPORTUNITIES = "GOV-0001";
const PAGE_SIZE = 25;

interface OppRow {
  id: string;
  title: string | null;
  description: string | null;
  content_type: string | null;
  canonical_url: string | null;
  published_at: string | null;
}

export default function GovernmentSourceDetailPage() {
  const params = useParams();
  const id = String(params?.id || "");
  const [source, setSource] = useState<Source | null>(null);
  const [items, setItems] = useState<OppRow[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [itemsLoading, setItemsLoading] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [syncMsg, setSyncMsg] = useState<string | null>(null);

  const isOpportunities = source?.catalog_id?.toUpperCase() === GOV_OPPORTUNITIES;
  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));
  const pageStart = total === 0 ? 0 : (page - 1) * PAGE_SIZE + 1;
  const pageEnd = Math.min(page * PAGE_SIZE, total);

  const loadSource = useCallback(async () => {
    if (!id) return null;
    const srcRes = await fetch(`${API_BASE}/api/v1/sources/${id}`);
    if (!srcRes.ok) throw new Error(`Failed to load source (${srcRes.status})`);
    const src = mapSource(await srcRes.json());
    setSource(src);
    return src;
  }, [id]);

  const loadOpportunities = useCallback(
    async (pageNum: number) => {
      if (!id) return;
      setItemsLoading(true);
      try {
        const itemsRes = await fetch(
          `${API_BASE}/api/v1/government/opportunities?source_id=${id}&page=${pageNum}&page_size=${PAGE_SIZE}`,
        );
        if (!itemsRes.ok) throw new Error(`Failed to load opportunities (${itemsRes.status})`);
        const data = await itemsRes.json();
        setItems(data.items ?? []);
        setTotal(data.total ?? 0);
      } finally {
        setItemsLoading(false);
      }
    },
    [id],
  );

  const load = useCallback(async () => {
    if (!id) return;
    setError(null);
    setLoading(true);
    try {
      const src = await loadSource();
      if (src?.catalog_id?.toUpperCase() !== GOV_OPPORTUNITIES) {
        setItems([]);
        setTotal(0);
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load source");
    } finally {
      setLoading(false);
    }
  }, [id, loadSource]);

  useEffect(() => {
    void load();
  }, [load]);

  useEffect(() => {
    if (!isOpportunities || loading) return;
    void loadOpportunities(page);
  }, [isOpportunities, loading, loadOpportunities, page]);

  const sync = async () => {
    if (!isOpportunities || syncing) return;
    setSyncing(true);
    setSyncMsg("Syncing from SAM.gov…");
    setError(null);
    try {
      const res = await fetch(
        `${API_BASE}/api/v1/government/sources/${id}/sync-opportunities`,
        { method: "POST", headers: { "Content-Type": "application/json" }, body: "{}" },
      );
      const body = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(typeof body.detail === "string" ? body.detail : `Sync failed (${res.status})`);
      }
      const jobId = body.id as string | undefined;
      if (!jobId) throw new Error("No job id returned");

      for (let i = 0; i < 45; i++) {
        await new Promise((r) => setTimeout(r, 2000));
        const jr = await fetch(`${API_BASE}/api/v1/jobs/${jobId}`);
        const job = await jr.json().catch(() => ({}));
        if (!jr.ok) continue;
        if (job.status === "failed") {
          throw new Error(job.error_message || "Sync failed");
        }
        if (job.status === "completed") {
          const r = (job.result || {}) as Record<string, unknown>;
          if (r.note === "acquisition stub") {
            throw new Error(
              "Sync hit the worker stub — restart Celery Worker (Settings → Stack), then Sync again.",
            );
          }
          setSyncMsg(
            `Synced ${Number(r.fetched ?? 0)} notices (${Number(r.new ?? 0)} new, ${Number(r.updated ?? 0)} updated).`,
          );
          setPage(1);
          await loadSource();
          await loadOpportunities(1);
          return;
        }
      }
      setSyncMsg("Still running — refresh in a minute.");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Sync failed");
      setSyncMsg(null);
    } finally {
      setSyncing(false);
    }
  };

  const priorityLabel =
    PRIORITY_OPTIONS.find((o) => o.value === source?.priority)?.title ?? source?.priority;

  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      <AppPageHeader
        title={source?.name || "Government source"}
        description={source?.catalog_id || "Catalog entry"}
        icon={<Icon name="building" className="h-5 w-5 text-primary" />}
        actions={
          <div className="flex items-center gap-2">
            {isOpportunities ? (
              <Button size="sm" variant="outline" disabled={syncing} onClick={() => void sync()}>
                {syncing ? (
                  <Loader2 className="h-4 w-4 animate-spin mr-1" />
                ) : (
                  <RefreshCw className="h-4 w-4 mr-1" />
                )}
                Sync
              </Button>
            ) : null}
            <Link
              href="/government/sources"
              className="text-xs font-medium text-muted-foreground hover:text-foreground"
            >
              All sources
            </Link>
          </div>
        }
      />

      {loading ? (
        <p className="inline-flex items-center gap-2 text-sm text-muted-foreground">
          <Loader2 className="h-4 w-4 animate-spin" /> Loading…
        </p>
      ) : null}
      {error ? <p className="text-sm text-red-500">{error}</p> : null}
      {syncMsg ? <p className="text-sm text-muted-foreground">{syncMsg}</p> : null}

      {source ? (
        <Card className="rounded-2xl border-border/50 p-5 space-y-4">
          <dl className="grid gap-4 sm:grid-cols-2">
            <div>
              <dt className="text-fine font-bold uppercase tracking-wider text-muted-foreground">
                Catalog ID
              </dt>
              <dd className="mt-1 text-sm font-medium tabular-nums">{source.catalog_id ?? "—"}</dd>
            </div>
            <div>
              <dt className="text-fine font-bold uppercase tracking-wider text-muted-foreground">
                Status
              </dt>
              <dd className="mt-1 text-sm font-medium capitalize">{source.status}</dd>
            </div>
            <div>
              <dt className="text-fine font-bold uppercase tracking-wider text-muted-foreground">
                Category
              </dt>
              <dd className="mt-1 text-sm font-medium">{source.category || "—"}</dd>
            </div>
            <div>
              <dt className="text-fine font-bold uppercase tracking-wider text-muted-foreground">
                Priority
              </dt>
              <dd className="mt-1 text-sm font-medium">{priorityLabel}</dd>
            </div>
            <div className="sm:col-span-2">
              <dt className="text-fine font-bold uppercase tracking-wider text-muted-foreground">
                Access
              </dt>
              <dd className="mt-1">
                <a
                  href={source.source_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1 text-sm text-primary hover:underline break-all"
                >
                  {source.source_url}
                  <ArrowUpRight className="h-3.5 w-3.5 shrink-0" />
                </a>
              </dd>
            </div>
          </dl>

          {source.description ? (
            <p className="text-sm text-foreground/90 leading-relaxed border-t border-border/50 pt-4">
              {source.description}
            </p>
          ) : null}

          {(source.tags?.length ?? 0) > 0 ? (
            <div className="flex flex-wrap gap-1.5">
              {source.tags!.map((tag) => (
                <Badge
                  key={tag}
                  className="border-transparent bg-secondary text-secondary-foreground text-fine font-medium normal-case tracking-normal"
                >
                  {tag}
                </Badge>
              ))}
            </div>
          ) : null}

          {!isOpportunities ? (
            <p className="text-xs text-muted-foreground pt-2 border-t border-border/50">
              Connector not wired for this catalog entry yet.
            </p>
          ) : null}
        </Card>
      ) : null}

      {isOpportunities ? (
        <div className="space-y-3">
          <div className="flex items-center justify-between gap-3 flex-wrap">
            <h2 className="text-sm font-semibold tracking-tight">
              Opportunities
              <span className="ml-2 text-muted-foreground font-normal">({total})</span>
            </h2>
            {total > 0 ? (
              <p className="text-xs text-muted-foreground tabular-nums">
                {pageStart}–{pageEnd} of {total}
              </p>
            ) : null}
          </div>

          {itemsLoading && items.length === 0 ? (
            <p className="text-sm text-muted-foreground flex items-center gap-2">
              <Loader2 className="h-4 w-4 animate-spin" /> Loading opportunities…
            </p>
          ) : total === 0 ? (
            <p className="text-sm text-muted-foreground">
              No records yet. Turn source on and click Sync (last 7 days, 1 API call).
            </p>
          ) : (
            <>
              <div className="rounded-xl border border-border/50 overflow-hidden">
                <Table>
                  <TableHeader>
                    <TableRow className="hover:bg-transparent">
                      <TableHead className="h-11 px-3 text-fine font-bold uppercase tracking-wider w-[52px] text-right">
                        #
                      </TableHead>
                      <TableHead className="h-11 px-4 text-fine font-bold uppercase tracking-wider">
                        Title
                      </TableHead>
                      <TableHead className="h-11 px-4 text-fine font-bold uppercase tracking-wider w-[200px]">
                        Type
                      </TableHead>
                      <TableHead className="h-11 px-4 text-fine font-bold uppercase tracking-wider min-w-[200px]">
                        Agency
                      </TableHead>
                      <TableHead className="h-11 px-4 text-fine font-bold uppercase tracking-wider w-[110px]">
                        Posted
                      </TableHead>
                      <TableHead className="h-11 px-4 text-fine font-bold uppercase tracking-wider w-[72px] text-right">
                        Open
                      </TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {items.map((row, index) => (
                      <TableRow key={row.id} className="h-14">
                        <TableCell className="px-3 py-3 text-right text-xs tabular-nums text-muted-foreground">
                          {(page - 1) * PAGE_SIZE + index + 1}
                        </TableCell>
                        <TableCell className="px-4 py-3">
                          <p className="text-sm font-medium leading-snug line-clamp-2">
                            {row.title || "—"}
                          </p>
                        </TableCell>
                        <TableCell className="px-4 py-3 text-sm text-muted-foreground">
                          {row.content_type || "—"}
                        </TableCell>
                        <TableCell className="px-4 py-3 text-sm text-muted-foreground">
                          <span className="line-clamp-2">{row.description || "—"}</span>
                        </TableCell>
                        <TableCell className="px-4 py-3 text-sm tabular-nums text-muted-foreground">
                          {row.published_at ? row.published_at.slice(0, 10) : "—"}
                        </TableCell>
                        <TableCell className="px-4 py-3 text-right">
                          {row.canonical_url ? (
                            <a
                              href={row.canonical_url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="inline-flex items-center justify-center text-primary hover:text-primary/80"
                              title="Open on SAM.gov"
                            >
                              <ExternalLink className="h-4 w-4" />
                            </a>
                          ) : (
                            "—"
                          )}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>

              <div className="flex items-center justify-between gap-3 pt-1">
                <p className="text-xs text-muted-foreground tabular-nums">
                  Page {page} of {totalPages}
                </p>
                <div className="flex items-center gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={page <= 1 || itemsLoading}
                    onClick={() => setPage((p) => Math.max(1, p - 1))}
                    className="gap-1.5"
                  >
                    <ChevronLeft className="h-4 w-4" /> Previous
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={page >= totalPages || itemsLoading}
                    onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                    className="gap-1.5"
                  >
                    Next <ChevronRight className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            </>
          )}
        </div>
      ) : null}
    </div>
  );
}
