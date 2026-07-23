"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { ArrowUpRight, Loader2 } from "lucide-react";
import { AppPageHeader } from "@/components/sections/AppPageHeader";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { Icon } from "@/lib/icons";
import type { Source } from "@/lib/mock-data/sources";
import { mapSource, PRIORITY_OPTIONS } from "@/lib/sources/helpers";
import { API_BASE } from "@/lib/api-base";

export default function DomainNamesSourceDetailPage() {
  const params = useParams();
  const id = String(params?.id || "");
  const [source, setSource] = useState<Source | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!id) return;
    let cancelled = false;
    (async () => {
      try {
        const res = await fetch(`${API_BASE}/api/v1/sources/${id}`);
        if (!res.ok) throw new Error(`Failed to load source (${res.status})`);
        const data = await res.json();
        if (!cancelled) setSource(mapSource(data));
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

  const priorityLabel =
    PRIORITY_OPTIONS.find((o) => o.value === source?.priority)?.title ?? source?.priority;

  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      <AppPageHeader
        title={source?.name || "Domain source"}
        description={source?.catalog_id || "Catalog entry"}
        icon={<Icon name="globe" className="h-5 w-5 text-primary" />}
        actions={
          <Link
            href="/domain-names/sources"
            className="text-xs font-medium text-muted-foreground hover:text-foreground"
          >
            All sources
          </Link>
        }
      />

      {loading ? (
        <p className="inline-flex items-center gap-2 text-sm text-muted-foreground">
          <Loader2 className="h-4 w-4 animate-spin" /> Loading…
        </p>
      ) : null}
      {error ? <p className="text-sm text-red-500">{error}</p> : null}

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
            <div>
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
            <div>
              <p className="text-fine font-bold uppercase tracking-wider text-muted-foreground">
                Description
              </p>
              <p className="mt-1 text-sm text-foreground/90 leading-relaxed">{source.description}</p>
            </div>
          ) : null}

          {(source.tags?.length ?? 0) > 0 ? (
            <div>
              <p className="text-fine font-bold uppercase tracking-wider text-muted-foreground mb-2">
                Tags
              </p>
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
            </div>
          ) : null}

          <p className="text-xs text-muted-foreground pt-2 border-t border-border/50">
            Connectors and discovery for domain sources are not wired yet. This entry is catalog
            inventory.
          </p>
        </Card>
      ) : null}
    </div>
  );
}
