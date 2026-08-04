"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { Loader2, RefreshCw, Search, X } from "lucide-react";
import { AppPageHeader } from "@/components/sections/AppPageHeader";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
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

interface PortfolioDomain {
  id: string;
  domain_name: string;
  status?: string | null;
  expiration_date?: string | null;
  purchase_date?: string | null;
  locked: boolean;
  auto_renew: boolean;
  whois_privacy: boolean;
  category?: string | null;
  registrar?: string | null;
  captured_at?: string | null;
}

interface PortfolioResponse {
  items: PortfolioDomain[];
  total: number;
  credentials_configured: boolean;
}

const SUBTABS = [
  { id: "portfolio", label: "My domains", href: "/domain-names/portfolio" },
  { id: "sources", label: "Sources", href: "/domain-names/sources" },
] as const;

const th =
  "h-11 px-2 text-fine font-bold uppercase tracking-wider text-sidebar-foreground text-center";
const td = "px-2 py-2.5 text-center text-sm";

function formatDate(raw?: string | null): string {
  if (!raw) return "—";
  const d = new Date(raw);
  if (Number.isNaN(d.getTime())) return String(raw).slice(0, 10);
  return d.toLocaleDateString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

export default function DomainNamesPortfolioPage() {
  const pathname = usePathname();
  const router = useRouter();
  const [data, setData] = useState<PortfolioResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [flash, setFlash] = useState<string | null>(null);
  const [q, setQ] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");

  const activeTab = pathname.includes("/sources") ? "sources" : "portfolio";

  const fetchPortfolio = useCallback(async (opts?: { silent?: boolean }) => {
    if (!opts?.silent) setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams();
      if (q.trim()) params.set("q", q.trim());
      const res = await fetch(`${API_BASE}/api/v1/domain-names/portfolio?${params}`);
      if (!res.ok) throw new Error(`Failed to load portfolio (${res.status})`);
      setData(await res.json());
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load portfolio");
      if (!opts?.silent) setData(null);
    } finally {
      if (!opts?.silent) setLoading(false);
    }
  }, [q]);

  useEffect(() => {
    const t = setTimeout(() => void fetchPortfolio(), q ? 200 : 0);
    return () => clearTimeout(t);
  }, [fetchPortfolio, q]);

  const sync = async () => {
    if (syncing) return;
    setSyncing(true);
    setError(null);
    setFlash("Syncing NameBright portfolio…");
    try {
      const res = await fetch(`${API_BASE}/api/v1/domain-names/portfolio/sync`, {
        method: "POST",
      });
      const body = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(
          typeof body.detail === "string" ? body.detail : `Sync failed (${res.status})`,
        );
      }
      const jobId = body.id as string | undefined;
      if (!jobId) throw new Error("Sync enqueued but no job id returned");

      let result: Record<string, unknown> | null = null;
      for (let i = 0; i < 60; i++) {
        await new Promise((r) => setTimeout(r, 2000));
        if (i > 0 && i % 3 === 0) await fetchPortfolio({ silent: true });
        const jr = await fetch(`${API_BASE}/api/v1/jobs/${jobId}`);
        const job = await jr.json().catch(() => ({}));
        if (!jr.ok) continue;
        if (job.status === "completed" || job.status === "failed") {
          if (job.status === "failed") {
            throw new Error(job.error_message || "Sync job failed");
          }
          result = (job.result || {}) as Record<string, unknown>;
          break;
        }
      }
      if (!result) {
        setFlash("Sync still running — reload in a minute.");
      } else if (result.note === "acquisition stub") {
        throw new Error(
          "Sync hit the acquire stub — restart the Celery worker, then try again.",
        );
      } else {
        setFlash(
          `Synced ${Number(result.upserted ?? 0)} domains from NameBright `
            + `(fetched ${Number(result.fetched ?? 0)}).`,
        );
      }
      await fetchPortfolio({ silent: true });
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Sync failed");
      setFlash(null);
    } finally {
      setSyncing(false);
    }
  };

  const items = data?.items ?? [];
  const configured = data?.credentials_configured ?? false;

  const statusOptions = useMemo(() => {
    const set = new Set<string>();
    for (const d of items) {
      const s = (d.status || "").trim();
      if (s) set.add(s);
    }
    return Array.from(set).sort((a, b) => a.localeCompare(b));
  }, [items]);

  const rows = useMemo(() => {
    const statusKey = statusFilter.toLowerCase();
    return [...items]
      .filter((d) => {
        if (statusFilter === "all") return true;
        return (d.status || "").trim().toLowerCase() === statusKey;
      })
      .sort((a, b) =>
        a.domain_name.localeCompare(b.domain_name, undefined, { sensitivity: "base" }),
      );
  }, [items, statusFilter]);

  const colSpan = 9;

  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      <AppPageHeader
        title="Domains"
        description="My domains, sources, and later expiring / dropcatch sub-planes."
        icon={<Icon name="globe" className="h-5 w-5 text-primary" />}
        actions={
          <Button
            type="button"
            variant="outline"
            size="sm"
            disabled={syncing || !configured}
            onClick={() => void sync()}
            title={
              configured
                ? "Pull portfolio from NameBright"
                : "Set NAMEBRIGHT_CLIENT_ID / SECRET in v2/.env"
            }
          >
            {syncing ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <RefreshCw className="h-4 w-4" />
            )}
            {syncing ? "Syncing…" : "Sync NameBright"}
          </Button>
        }
      />

      <Tabs value={activeTab}>
        <TabsList className="h-auto w-full justify-start overflow-x-auto rounded-xl border border-border/60 bg-secondary/40 p-1">
          {SUBTABS.map((tab) => (
            <TabsTrigger key={tab.id} value={tab.id} asChild>
              <Link
                href={tab.href}
                className="rounded-lg px-4 py-2 data-[state=active]:bg-accent data-[state=active]:text-accent-foreground"
              >
                {tab.label}
              </Link>
            </TabsTrigger>
          ))}
        </TabsList>
      </Tabs>

      {error ? <p className="text-sm text-red-500">{error}</p> : null}
      {flash ? <p className="text-sm text-muted-foreground">{flash}</p> : null}
      {!configured ? (
        <p className="text-sm text-amber-700 dark:text-amber-400">
          NameBright credentials not loaded. Confirm{" "}
          <code className="text-xs">NAMEBRIGHT_CLIENT_ID</code> /{" "}
          <code className="text-xs">NAMEBRIGHT_CLIENT_SECRET</code> in{" "}
          <code className="text-xs">v2/.env</code> and restart the API.
        </p>
      ) : null}

      <div className="flex flex-col gap-3 sm:flex-row sm:flex-wrap sm:items-center">
        <div className="relative flex-1 min-w-[200px] max-w-md">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="Search domain…"
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

        <Select value={statusFilter} onValueChange={setStatusFilter}>
          <SelectTrigger className="w-full sm:w-[180px]" aria-label="Filter by status">
            <SelectValue placeholder="All statuses" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All statuses</SelectItem>
            {statusOptions.map((s) => (
              <SelectItem key={s} value={s.toLowerCase()}>
                {s}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <Card className="shadow-sm border border-border/50 overflow-hidden rounded-2xl bg-card">
        <CardHeader className="bg-card border-b border-border/50 py-4">
          <CardTitle className="text-sm font-medium flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Icon name="globe" className="w-4 h-4 text-muted-foreground" />
              My domains
            </div>
            <span className="text-fine bg-secondary text-secondary-foreground px-3 py-1 rounded-full font-bold">
              {loading ? "…" : `${rows.length} DOMAIN${rows.length !== 1 ? "S" : ""}`}
            </span>
          </CardTitle>
        </CardHeader>
        <div className="overflow-x-auto">
          <Table className="table-fixed w-full min-w-[960px]">
            <TableHeader>
              <TableRow className="hover:bg-transparent">
                <TableHead className={`${th} w-[5%]`}>#</TableHead>
                <TableHead className={`${th} w-[22%] text-left px-3`}>Domain</TableHead>
                <TableHead className={`${th} w-[12%]`}>Status</TableHead>
                <TableHead className={`${th} w-[12%]`}>Purchase</TableHead>
                <TableHead className={`${th} w-[12%]`}>Expiry</TableHead>
                <TableHead className={`${th} w-[8%]`}>Lock</TableHead>
                <TableHead className={`${th} w-[10%]`}>Auto-renew</TableHead>
                <TableHead className={`${th} w-[9%]`}>Privacy</TableHead>
                <TableHead className={`${th} w-[10%]`}>Category</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {loading && (
                <TableRow>
                  <TableCell colSpan={colSpan} className="h-24 text-center text-muted-foreground">
                    <span className="inline-flex items-center gap-2 text-sm">
                      <Loader2 className="w-4 h-4 animate-spin" /> Loading…
                    </span>
                  </TableCell>
                </TableRow>
              )}
              {!loading && rows.length === 0 && (
                <TableRow>
                  <TableCell colSpan={colSpan} className="h-24 text-center text-sm text-muted-foreground">
                    No portfolio domains match this filter.
                  </TableCell>
                </TableRow>
              )}
              {!loading &&
                rows.map((d, index) => (
                  <TableRow
                    key={d.id}
                    className="h-12 cursor-pointer hover:bg-muted/40"
                    onClick={() => {
                      router.push(`/domain-names/portfolio/${encodeURIComponent(d.domain_name)}`);
                    }}
                  >
                    <TableCell className={`${td} tabular-nums text-xs text-muted-foreground`}>
                      {index + 1}
                    </TableCell>
                    <TableCell className="px-3 py-2.5 text-left">
                      <Link
                        href={`/domain-names/portfolio/${encodeURIComponent(d.domain_name)}`}
                        className="text-sm font-medium text-primary hover:underline truncate block"
                        title={d.domain_name}
                        onClick={(e) => e.stopPropagation()}
                      >
                        {d.domain_name}
                      </Link>
                    </TableCell>
                    <TableCell className={td}>
                      <Badge
                        variant="outline"
                        className="text-fine font-medium normal-case tracking-normal"
                      >
                        {d.status || "—"}
                      </Badge>
                    </TableCell>
                    <TableCell className={`${td} tabular-nums text-muted-foreground`}>
                      {formatDate(d.purchase_date)}
                    </TableCell>
                    <TableCell className={`${td} tabular-nums text-muted-foreground`}>
                      {formatDate(d.expiration_date)}
                    </TableCell>
                    <TableCell className={td}>{d.locked ? "Yes" : "—"}</TableCell>
                    <TableCell className={td}>{d.auto_renew ? "On" : "—"}</TableCell>
                    <TableCell className={td}>{d.whois_privacy ? "On" : "—"}</TableCell>
                    <TableCell
                      className={`${td} text-xs text-muted-foreground truncate`}
                      title={d.category || undefined}
                    >
                      {d.category || "—"}
                    </TableCell>
                  </TableRow>
                ))}
            </TableBody>
          </Table>
        </div>
      </Card>
    </div>
  );
}
