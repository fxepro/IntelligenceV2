"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { ArrowLeft, ArrowUpRight, Loader2, RefreshCw } from "lucide-react";
import { AppPageHeader } from "@/components/sections/AppPageHeader";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
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
  purchase_date?: string | null;
  expiration_date?: string | null;
  locked: boolean;
  auto_renew: boolean;
  whois_privacy: boolean;
  upgraded_domain: boolean;
  category?: string | null;
  registrar?: string | null;
  provider?: string;
  nameservers: string[];
  dns_a: Record<string, unknown>[];
  dns_aaaa: Record<string, unknown>[];
  dns_cname: Record<string, unknown>[];
  dns_mx: Record<string, unknown>[];
  dns_txt: Record<string, unknown>[];
  dns_srv: Record<string, unknown>[];
  synced_at?: string | null;
  dns_synced_at?: string | null;
}

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

function formatWhen(raw?: string | null): string {
  if (!raw) return "Never";
  const d = new Date(raw);
  if (Number.isNaN(d.getTime())) return String(raw);
  return d.toLocaleString();
}

function cell(v: unknown): string {
  if (v == null || v === "") return "—";
  return String(v);
}

function pick(row: Record<string, unknown>, key: string): unknown {
  if (key in row) return row[key];
  const found = Object.keys(row).find((k) => k.toLowerCase() === key.toLowerCase());
  return found ? row[found] : null;
}

function DnsTable({
  title,
  rows,
  columns,
}: {
  title: string;
  rows: Record<string, unknown>[];
  columns: { key: string; label: string }[];
}) {
  return (
    <Card className="shadow-sm border border-border/50 overflow-hidden rounded-2xl bg-card">
      <CardHeader className="bg-card border-b border-border/50 py-3">
        <CardTitle className="text-sm font-medium flex items-center justify-between">
          <span>{title}</span>
          <span className="text-fine bg-secondary text-secondary-foreground px-2.5 py-0.5 rounded-full font-bold">
            {rows.length}
          </span>
        </CardTitle>
      </CardHeader>
      <CardContent className="p-0">
        {rows.length === 0 ? (
          <p className="px-4 py-6 text-sm text-muted-foreground">No {title} records.</p>
        ) : (
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow className="hover:bg-transparent">
                  {columns.map((c) => (
                    <TableHead
                      key={c.key}
                      className="h-10 px-3 text-fine font-bold uppercase tracking-wider text-sidebar-foreground"
                    >
                      {c.label}
                    </TableHead>
                  ))}
                </TableRow>
              </TableHeader>
              <TableBody>
                {rows.map((row, i) => (
                  <TableRow key={i}>
                    {columns.map((c) => (
                      <TableCell key={c.key} className="px-3 py-2 text-sm tabular-nums break-all">
                        {cell(pick(row, c.key))}
                      </TableCell>
                    ))}
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

async function waitForJob(jobId: string, maxPolls = 45): Promise<Record<string, unknown>> {
  for (let i = 0; i < maxPolls; i++) {
    await new Promise((r) => setTimeout(r, 1500));
    const jr = await fetch(`${API_BASE}/api/v1/jobs/${jobId}`);
    const job = await jr.json().catch(() => ({}));
    if (!jr.ok) continue;
    if (job.status === "completed") return (job.result || {}) as Record<string, unknown>;
    if (job.status === "failed") {
      throw new Error(job.error_message || "DNS sync job failed");
    }
  }
  throw new Error("DNS sync still running — refresh in a minute.");
}

export default function PortfolioDomainDetailPage() {
  const params = useParams();
  const rawParam = String(params?.domain || "");
  const domain = decodeURIComponent(rawParam).trim().toLowerCase();

  const [data, setData] = useState<PortfolioDomain | null>(null);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [flash, setFlash] = useState<string | null>(null);

  const load = useCallback(async (opts?: { silent?: boolean }) => {
    if (!domain) return;
    if (!opts?.silent) setLoading(true);
    setError(null);
    try {
      const res = await fetch(
        `${API_BASE}/api/v1/domain-names/portfolio/${encodeURIComponent(domain)}`,
      );
      if (res.status === 404) throw new Error("Domain not found in portfolio");
      if (!res.ok) throw new Error(`Failed to load domain (${res.status})`);
      setData(await res.json());
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load domain");
      if (!opts?.silent) setData(null);
    } finally {
      if (!opts?.silent) setLoading(false);
    }
  }, [domain]);

  useEffect(() => {
    void load();
  }, [load]);

  const refreshDns = async () => {
    if (!domain || syncing) return;
    setSyncing(true);
    setError(null);
    setFlash("Pulling nameservers + DNS from NameBright…");
    try {
      const res = await fetch(
        `${API_BASE}/api/v1/domain-names/portfolio/${encodeURIComponent(domain)}/sync-dns`,
        { method: "POST" },
      );
      const body = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(
          typeof body.detail === "string" ? body.detail : `DNS sync failed (${res.status})`,
        );
      }
      const jobId = body.id as string | undefined;
      if (!jobId) throw new Error("DNS sync enqueued but no job id returned");
      const result = await waitForJob(jobId);
      if (result.note === "acquisition stub") {
        throw new Error("Hit acquire stub — restart Celery Worker, then try again.");
      }
      setFlash(
        `DNS updated — NS ${Number(result.nameservers ?? 0)}, `
          + `A ${Number(result.dns_a ?? 0)}, CNAME ${Number(result.dns_cname ?? 0)}, `
          + `MX ${Number(result.dns_mx ?? 0)}, TXT ${Number(result.dns_txt ?? 0)}.`,
      );
      await load({ silent: true });
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "DNS sync failed");
      setFlash(null);
    } finally {
      setSyncing(false);
    }
  };

  const ns = data?.nameservers ?? [];
  const hasDns =
    Boolean(data?.dns_synced_at)
    || ns.length > 0
    || (data?.dns_a?.length ?? 0) > 0
    || (data?.dns_cname?.length ?? 0) > 0
    || (data?.dns_mx?.length ?? 0) > 0
    || (data?.dns_txt?.length ?? 0) > 0
    || (data?.dns_aaaa?.length ?? 0) > 0
    || (data?.dns_srv?.length ?? 0) > 0;

  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      <AppPageHeader
        title={data?.domain_name || domain || "Domain"}
        description="Registrar settings, nameservers, and DNS host records."
        icon={<Icon name="globe" className="h-5 w-5 text-primary" />}
        actions={
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" asChild>
              <Link href="/domain-names/portfolio">
                <ArrowLeft className="h-4 w-4" />
                My domains
              </Link>
            </Button>
            <Button
              type="button"
              variant="outline"
              size="sm"
              disabled={syncing || loading || !data}
              onClick={() => void refreshDns()}
            >
              {syncing ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <RefreshCw className="h-4 w-4" />
              )}
              {syncing ? "Refreshing…" : "Refresh DNS"}
            </Button>
            {data ? (
              <Button variant="outline" size="sm" asChild>
                <a
                  href={`https://${data.domain_name}`}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  Open
                  <ArrowUpRight className="h-4 w-4" />
                </a>
              </Button>
            ) : null}
          </div>
        }
      />

      {error ? <p className="text-sm text-red-500">{error}</p> : null}
      {flash ? <p className="text-sm text-muted-foreground">{flash}</p> : null}

      {loading ? (
        <p className="inline-flex items-center gap-2 text-sm text-muted-foreground">
          <Loader2 className="h-4 w-4 animate-spin" /> Loading…
        </p>
      ) : null}

      {data ? (
        <>
          <Card className="rounded-2xl border-border/50 p-5">
            <dl className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              <div>
                <dt className="text-fine font-bold uppercase tracking-wider text-muted-foreground">
                  Status
                </dt>
                <dd className="mt-1">
                  <Badge variant="outline" className="normal-case tracking-normal font-medium">
                    {data.status || "—"}
                  </Badge>
                </dd>
              </div>
              <div>
                <dt className="text-fine font-bold uppercase tracking-wider text-muted-foreground">
                  Purchase
                </dt>
                <dd className="mt-1 text-sm tabular-nums">{formatDate(data.purchase_date)}</dd>
              </div>
              <div>
                <dt className="text-fine font-bold uppercase tracking-wider text-muted-foreground">
                  Expiry
                </dt>
                <dd className="mt-1 text-sm tabular-nums">{formatDate(data.expiration_date)}</dd>
              </div>
              <div>
                <dt className="text-fine font-bold uppercase tracking-wider text-muted-foreground">
                  Lock
                </dt>
                <dd className="mt-1 text-sm">{data.locked ? "Yes" : "—"}</dd>
              </div>
              <div>
                <dt className="text-fine font-bold uppercase tracking-wider text-muted-foreground">
                  Auto-renew
                </dt>
                <dd className="mt-1 text-sm">{data.auto_renew ? "On" : "—"}</dd>
              </div>
              <div>
                <dt className="text-fine font-bold uppercase tracking-wider text-muted-foreground">
                  Privacy
                </dt>
                <dd className="mt-1 text-sm">{data.whois_privacy ? "On" : "—"}</dd>
              </div>
              <div>
                <dt className="text-fine font-bold uppercase tracking-wider text-muted-foreground">
                  Category
                </dt>
                <dd className="mt-1 text-sm">{data.category || "—"}</dd>
              </div>
              <div>
                <dt className="text-fine font-bold uppercase tracking-wider text-muted-foreground">
                  Registrar
                </dt>
                <dd className="mt-1 text-sm">{data.registrar || "—"}</dd>
              </div>
              <div>
                <dt className="text-fine font-bold uppercase tracking-wider text-muted-foreground">
                  Portfolio synced
                </dt>
                <dd className="mt-1 text-sm text-muted-foreground">{formatWhen(data.synced_at)}</dd>
              </div>
            </dl>
          </Card>

          <Card className="rounded-2xl border-border/50 p-5 space-y-3">
            <div className="flex items-center justify-between gap-3">
              <h2 className="text-sm font-medium">Nameservers</h2>
              <span className="text-xs text-muted-foreground">
                DNS synced {formatWhen(data.dns_synced_at)}
              </span>
            </div>
            {!hasDns ? (
              <p className="text-sm text-muted-foreground">
                No DNS pulled yet. Use <strong>Refresh DNS</strong> to load nameservers and host
                records from NameBright (requires Celery Worker).
              </p>
            ) : ns.length === 0 ? (
              <p className="text-sm text-muted-foreground">
                No nameservers returned (zone may live elsewhere).
              </p>
            ) : (
              <ul className="space-y-1.5">
                {ns.map((n) => (
                  <li key={n} className="text-sm font-medium tabular-nums">
                    {n}
                  </li>
                ))}
              </ul>
            )}
          </Card>

          <div className="grid gap-4 lg:grid-cols-2">
            <DnsTable
              title="A"
              rows={data.dns_a || []}
              columns={[
                { key: "Subdomain", label: "Host" },
                { key: "IPV4Address", label: "IPv4" },
                { key: "RecordId", label: "Id" },
              ]}
            />
            <DnsTable
              title="AAAA"
              rows={data.dns_aaaa || []}
              columns={[
                { key: "Subdomain", label: "Host" },
                { key: "IPV6Address", label: "IPv6" },
                { key: "RecordId", label: "Id" },
              ]}
            />
            <DnsTable
              title="CNAME"
              rows={data.dns_cname || []}
              columns={[
                { key: "Subdomain", label: "Host" },
                { key: "RedirectDomain", label: "Target" },
                { key: "RecordId", label: "Id" },
              ]}
            />
            <DnsTable
              title="MX"
              rows={data.dns_mx || []}
              columns={[
                { key: "Subdomain", label: "Host" },
                { key: "MailServer", label: "Mail server" },
                { key: "Priority", label: "Priority" },
                { key: "RecordId", label: "Id" },
              ]}
            />
            <DnsTable
              title="TXT"
              rows={data.dns_txt || []}
              columns={[
                { key: "Subdomain", label: "Host" },
                { key: "TextRecord", label: "Value" },
                { key: "RecordId", label: "Id" },
              ]}
            />
            <DnsTable
              title="SRV"
              rows={data.dns_srv || []}
              columns={[
                { key: "Service", label: "Service" },
                { key: "Protocol", label: "Protocol" },
                { key: "Priority", label: "Priority" },
                { key: "Weight", label: "Weight" },
                { key: "Port", label: "Port" },
                { key: "Target", label: "Target" },
                { key: "RecordId", label: "Id" },
              ]}
            />
          </div>
        </>
      ) : null}
    </div>
  );
}
