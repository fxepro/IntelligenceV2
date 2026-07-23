"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { ArrowUpRight, Loader2 } from "lucide-react";
import { AppPageHeader } from "@/components/sections/AppPageHeader";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Icon } from "@/lib/icons";
import type { Source } from "@/lib/mock-data/sources";
import { mapSource, PRIORITY_OPTIONS } from "@/lib/sources/helpers";
import { API_BASE } from "@/lib/api-base";

type DetailTab = "overview" | "endpoints" | "criteria" | "results";

interface TrademarkDetail {
  id: string;
  source_id: string;
  catalog_id: string;
  country?: string | null;
  country_code?: string | null;
  jurisdiction?: string | null;
  office?: string | null;
  search_url?: string | null;
  status_lookup_url?: string | null;
  filing_url?: string | null;
  registry_url?: string | null;
  gazette_url?: string | null;
  journal_url?: string | null;
  api_url?: string | null;
  api_docs_url?: string | null;
  bulk_download_url?: string | null;
  has_api_key?: boolean;
  response_format?: string | null;
  pagination?: string | null;
  query_parameters?: string | null;
  access_type?: string | null;
  authentication?: string | null;
  rate_limit?: string | null;
  supports_nice_classes?: boolean | null;
  supports_image_search?: boolean | null;
  update_frequency?: string | null;
  detail_status?: string | null;
  last_verified?: string | null;
  notes?: string | null;
}

const CHANNELS: { key: keyof TrademarkDetail; label: string }[] = [
  { key: "search_url", label: "Search" },
  { key: "status_lookup_url", label: "Status lookup" },
  { key: "filing_url", label: "Filing" },
  { key: "registry_url", label: "Registry" },
  { key: "gazette_url", label: "Gazette" },
  { key: "journal_url", label: "Journal" },
  { key: "api_url", label: "API" },
  { key: "api_docs_url", label: "API docs" },
  { key: "bulk_download_url", label: "Bulk download" },
];

function flagLabel(v: boolean | null | undefined): string {
  if (v === true) return "Yes";
  if (v === false) return "No";
  return "—";
}

function bestPullChannel(detail: TrademarkDetail | null): string | null {
  if (!detail) return null;
  if (detail.api_url) return "api_url";
  if (detail.bulk_download_url) return "bulk_download_url";
  if (detail.search_url) return "search_url";
  if (detail.status_lookup_url) return "status_lookup_url";
  return null;
}

export default function TrademarkSourceDetailPage() {
  const params = useParams();
  const id = String(params?.id || "");
  const [source, setSource] = useState<Source | null>(null);
  const [detail, setDetail] = useState<TrademarkDetail | null>(null);
  const [detailMissing, setDetailMissing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState<DetailTab>("overview");
  const [apiKeyDraft, setApiKeyDraft] = useState("");
  const [savingKey, setSavingKey] = useState(false);
  const [keyMsg, setKeyMsg] = useState<string | null>(null);
  const [keyErr, setKeyErr] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    let cancelled = false;
    (async () => {
      setLoading(true);
      setError(null);
      setDetailMissing(false);
      setKeyMsg(null);
      setKeyErr(null);
      setApiKeyDraft("");
      try {
        const res = await fetch(`${API_BASE}/api/v1/sources/${id}`);
        if (!res.ok) throw new Error(`Failed to load source (${res.status})`);
        const data = await res.json();
        if (cancelled) return;
        setSource(mapSource(data));

        const dres = await fetch(`${API_BASE}/api/v1/trademarks/sources/${id}/details`);
        if (cancelled) return;
        if (dres.status === 404) {
          setDetail(null);
          setDetailMissing(true);
        } else if (!dres.ok) {
          throw new Error(`Failed to load details (${dres.status})`);
        } else {
          setDetail(await dres.json());
        }
      } catch (err: unknown) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Failed to load source");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [id]);

  async function saveApiKey() {
    if (!id) return;
    const key = apiKeyDraft.trim();
    if (!key) {
      setKeyErr("Enter an API key.");
      return;
    }
    setSavingKey(true);
    setKeyMsg(null);
    setKeyErr(null);
    try {
      const res = await fetch(`${API_BASE}/api/v1/trademarks/sources/${id}/details`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ api_key: key }),
      });
      if (!res.ok) throw new Error(`Failed to save API key (${res.status})`);
      setDetail(await res.json());
      setApiKeyDraft("");
      setKeyMsg("API key saved.");
    } catch (err: unknown) {
      setKeyErr(err instanceof Error ? err.message : "Failed to save API key");
    } finally {
      setSavingKey(false);
    }
  }

  async function clearApiKey() {
    if (!id) return;
    setSavingKey(true);
    setKeyMsg(null);
    setKeyErr(null);
    try {
      const res = await fetch(`${API_BASE}/api/v1/trademarks/sources/${id}/details/api-key`, {
        method: "DELETE",
      });
      if (!res.ok) throw new Error(`Failed to clear API key (${res.status})`);
      setDetail(await res.json());
      setApiKeyDraft("");
      setKeyMsg("API key cleared.");
    } catch (err: unknown) {
      setKeyErr(err instanceof Error ? err.message : "Failed to clear API key");
    } finally {
      setSavingKey(false);
    }
  }

  const priorityLabel =
    PRIORITY_OPTIONS.find((o) => o.value === source?.priority)?.title ?? source?.priority;

  const pullChannel = useMemo(() => bestPullChannel(detail), [detail]);
  const primaryUrl =
    detail?.search_url ||
    detail?.status_lookup_url ||
    detail?.api_url ||
    detail?.bulk_download_url ||
    source?.source_url;

  const canPull = Boolean(detail?.api_url || detail?.bulk_download_url);

  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      <AppPageHeader
        title={detail?.office || source?.name || "Trademark source"}
        description={
          [source?.catalog_id, detail?.country, detail?.jurisdiction]
            .filter(Boolean)
            .join(" · ") || "Catalog entry"
        }
        icon={<Icon name="landmark" className="h-5 w-5 text-primary" />}
        actions={
          <div className="flex flex-wrap items-center gap-2">
            <Link
              href="/trademarks/sources"
              className="text-xs font-medium text-muted-foreground hover:text-foreground"
            >
              All sources
            </Link>
            {primaryUrl ? (
              <Button asChild variant="outline" size="sm" className="gap-1.5">
                <a href={primaryUrl} target="_blank" rel="noopener noreferrer">
                  Open primary
                  <ArrowUpRight className="h-3.5 w-3.5" />
                </a>
              </Button>
            ) : null}
            <Button size="sm" disabled title={canPull ? "Coming next" : "No machine endpoint"}>
              Pull
            </Button>
          </div>
        }
      />

      {source || detail ? (
        <div className="flex flex-wrap gap-1.5">
          <Badge className="border-transparent bg-secondary text-secondary-foreground text-fine font-medium normal-case tracking-normal capitalize">
            {detail?.detail_status || source?.status || "—"}
          </Badge>
          {detail?.access_type ? (
            <Badge className="border-transparent bg-secondary text-secondary-foreground text-fine font-medium normal-case tracking-normal">
              {detail.access_type}
            </Badge>
          ) : null}
          <Badge className="border-transparent bg-secondary text-secondary-foreground text-fine font-medium normal-case tracking-normal">
            Nice: {flagLabel(detail?.supports_nice_classes)}
          </Badge>
          <Badge className="border-transparent bg-secondary text-secondary-foreground text-fine font-medium normal-case tracking-normal">
            Image: {flagLabel(detail?.supports_image_search)}
          </Badge>
        </div>
      ) : null}

      {loading ? (
        <p className="inline-flex items-center gap-2 text-sm text-muted-foreground">
          <Loader2 className="h-4 w-4 animate-spin" /> Loading…
        </p>
      ) : null}
      {error ? <p className="text-sm text-red-500">{error}</p> : null}

      {!loading && source ? (
        <div className="space-y-4">
          <Tabs value={tab} onValueChange={(v) => setTab(v as DetailTab)}>
            <TabsList className="h-auto w-full justify-start overflow-x-auto rounded-xl border border-border/60 bg-secondary/40 p-1">
              {(
                [
                  ["overview", "Overview"],
                  ["endpoints", "Endpoints"],
                  ["criteria", "Criteria"],
                  ["results", "Results"],
                ] as const
              ).map(([value, label]) => (
                <TabsTrigger
                  key={value}
                  value={value}
                  className="rounded-lg px-4 py-2 data-[state=active]:bg-accent data-[state=active]:text-accent-foreground data-[state=active]:shadow-sm"
                >
                  {label}
                </TabsTrigger>
              ))}
            </TabsList>
          </Tabs>

          {tab === "overview" ? (
            <Card className="rounded-2xl border-border/50 p-5 space-y-4">
              <dl className="grid gap-4 sm:grid-cols-2">
                <div>
                  <dt className="text-fine font-bold uppercase tracking-wider text-muted-foreground">
                    Catalog ID
                  </dt>
                  <dd className="mt-1 text-sm font-medium tabular-nums">
                    {source.catalog_id ?? "—"}
                  </dd>
                </div>
                <div>
                  <dt className="text-fine font-bold uppercase tracking-wider text-muted-foreground">
                    Status
                  </dt>
                  <dd className="mt-1 text-sm font-medium capitalize">
                    {detail?.detail_status || source.status}
                  </dd>
                </div>
                <div>
                  <dt className="text-fine font-bold uppercase tracking-wider text-muted-foreground">
                    Country
                  </dt>
                  <dd className="mt-1 text-sm font-medium">
                    {detail?.country || "—"}
                    {detail?.country_code ? (
                      <span className="text-muted-foreground"> · {detail.country_code}</span>
                    ) : null}
                  </dd>
                </div>
                <div>
                  <dt className="text-fine font-bold uppercase tracking-wider text-muted-foreground">
                    Jurisdiction
                  </dt>
                  <dd className="mt-1 text-sm font-medium">{detail?.jurisdiction || "—"}</dd>
                </div>
                <div>
                  <dt className="text-fine font-bold uppercase tracking-wider text-muted-foreground">
                    Office
                  </dt>
                  <dd className="mt-1 text-sm font-medium">{detail?.office || source.name || "—"}</dd>
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
                <div>
                  <dt className="text-fine font-bold uppercase tracking-wider text-muted-foreground">
                    Last verified
                  </dt>
                  <dd className="mt-1 text-sm font-medium tabular-nums">
                    {detail?.last_verified || "—"}
                  </dd>
                </div>
                <div className="sm:col-span-2">
                  <dt className="text-fine font-bold uppercase tracking-wider text-muted-foreground">
                    Catalog URL
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
                <div>
                  <p className="text-fine font-bold uppercase tracking-wider text-muted-foreground">
                    Description
                  </p>
                  <p className="mt-1 text-sm text-foreground/90 leading-relaxed">
                    {source.description}
                  </p>
                </div>
              ) : null}

              {detailMissing ? (
                <p className="text-xs text-muted-foreground pt-2 border-t border-border/50">
                  No enriched detail row for this TMK yet (Batch 001 covers TMK-0001–0050).
                </p>
              ) : null}
            </Card>
          ) : null}

          {tab === "endpoints" ? (
            <Card className="rounded-2xl border-border/50 p-5 space-y-5">
              {!detail ? (
                <p className="text-sm text-muted-foreground">
                  Endpoint profile not loaded for this source.
                </p>
              ) : (
                <>
                  <div>
                    <p className="text-fine font-bold uppercase tracking-wider text-muted-foreground mb-3">
                      Channels
                    </p>
                    <ul className="space-y-2.5">
                      {CHANNELS.map(({ key, label }) => {
                        const url = detail[key];
                        const used = pullChannel === key;
                        return (
                          <li key={key} className="space-y-2">
                            <div className="grid gap-1 sm:grid-cols-[140px_1fr_auto] sm:items-center">
                              <span className="text-sm font-medium">
                                {label}
                                {used ? (
                                  <span className="ml-2 text-fine text-muted-foreground font-normal">
                                    Used for Pull
                                  </span>
                                ) : null}
                              </span>
                              {typeof url === "string" && url ? (
                                <a
                                  href={url}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="text-sm text-primary hover:underline break-all"
                                >
                                  {url}
                                </a>
                              ) : (
                                <span className="text-sm text-muted-foreground">—</span>
                              )}
                              {typeof url === "string" && url ? (
                                <a
                                  href={url}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="inline-flex h-8 w-8 items-center justify-center rounded-md border border-border/60 text-muted-foreground hover:text-foreground hover:bg-muted"
                                  title="Open"
                                >
                                  <ArrowUpRight className="h-4 w-4" />
                                </a>
                              ) : (
                                <span />
                              )}
                            </div>

                            {key === "api_url" ? (
                              <div className="sm:ml-[140px] space-y-2 rounded-lg border border-border/50 p-3">
                                <div className="flex flex-wrap items-center gap-2">
                                  <span className="text-sm font-medium">API key</span>
                                  <Badge className="border-transparent bg-secondary text-secondary-foreground text-fine font-medium normal-case tracking-normal">
                                    {detail.has_api_key ? "Saved" : "Not set"}
                                  </Badge>
                                </div>
                                <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
                                  <Input
                                    type="password"
                                    autoComplete="off"
                                    value={apiKeyDraft}
                                    onChange={(e) => setApiKeyDraft(e.target.value)}
                                    placeholder={
                                      detail.has_api_key ? "•••••••• (replace)" : "Paste API key"
                                    }
                                    className="sm:max-w-md"
                                  />
                                  <div className="flex gap-2">
                                    <Button
                                      type="button"
                                      size="sm"
                                      disabled={savingKey || !apiKeyDraft.trim()}
                                      onClick={() => void saveApiKey()}
                                    >
                                      {savingKey ? "Saving…" : detail.has_api_key ? "Update" : "Save"}
                                    </Button>
                                    {detail.has_api_key ? (
                                      <Button
                                        type="button"
                                        size="sm"
                                        variant="outline"
                                        disabled={savingKey}
                                        onClick={() => void clearApiKey()}
                                      >
                                        Clear
                                      </Button>
                                    ) : null}
                                  </div>
                                </div>
                                {keyMsg ? <p className="text-xs text-emerald-600">{keyMsg}</p> : null}
                                {keyErr ? <p className="text-xs text-red-500">{keyErr}</p> : null}
                              </div>
                            ) : null}
                          </li>
                        );
                      })}
                    </ul>
                  </div>

                  <div className="grid gap-4 sm:grid-cols-3 border-t border-border/50 pt-4">
                    <div>
                      <p className="text-fine font-bold uppercase tracking-wider text-muted-foreground">
                        Authentication
                      </p>
                      <p className="mt-1 text-sm">{detail.authentication || "—"}</p>
                    </div>
                    <div>
                      <p className="text-fine font-bold uppercase tracking-wider text-muted-foreground">
                        Rate limit
                      </p>
                      <p className="mt-1 text-sm">{detail.rate_limit || "—"}</p>
                    </div>
                    <div>
                      <p className="text-fine font-bold uppercase tracking-wider text-muted-foreground">
                        Update frequency
                      </p>
                      <p className="mt-1 text-sm">{detail.update_frequency || "—"}</p>
                    </div>
                    <div>
                      <p className="text-fine font-bold uppercase tracking-wider text-muted-foreground">
                        Response format
                      </p>
                      <p className="mt-1 text-sm">{detail.response_format || "—"}</p>
                    </div>
                    <div>
                      <p className="text-fine font-bold uppercase tracking-wider text-muted-foreground">
                        Pagination
                      </p>
                      <p className="mt-1 text-sm">{detail.pagination || "—"}</p>
                    </div>
                    <div>
                      <p className="text-fine font-bold uppercase tracking-wider text-muted-foreground">
                        Query parameters
                      </p>
                      <p className="mt-1 text-sm">{detail.query_parameters || "—"}</p>
                    </div>
                  </div>

                  {detail.notes ? (
                    <div className="border-t border-border/50 pt-4">
                      <p className="text-fine font-bold uppercase tracking-wider text-muted-foreground">
                        Notes
                      </p>
                      <p className="mt-1 text-sm text-foreground/90 leading-relaxed whitespace-pre-wrap">
                        {detail.notes}
                      </p>
                    </div>
                  ) : null}

                  {!canPull ? (
                    <p className="text-xs text-muted-foreground border-t border-border/50 pt-3">
                      No machine endpoint (API/bulk) — Pull stays disabled. Search/filing links are
                      for manual access.
                    </p>
                  ) : null}
                </>
              )}
            </Card>
          ) : null}

          {tab === "criteria" ? (
            <Card className="rounded-2xl border-border/50 p-5">
              <p className="text-sm text-muted-foreground">
                Criteria form comes next — query, Nice classes, date window, and Pull mode.
              </p>
            </Card>
          ) : null}

          {tab === "results" ? (
            <Card className="rounded-2xl border-border/50 p-5">
              <p className="text-sm text-muted-foreground">
                No pulls yet. Results from automated source pulls will list here.
              </p>
            </Card>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}
