"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Card } from "@/components/ui/card";
import { AppPageHeader } from "@/components/sections/AppPageHeader";
import { StatCard } from "@/components/sections/StatCard";
import { Icon } from "@/lib/icons";
import { site } from "@/config/site";
import { chromeNav, intelligenceNav } from "@/config/navigation";
import { DOMAINS } from "@/lib/domains";
import { mapSource } from "@/lib/sources/helpers";
import type { Source } from "@/lib/mock-data/sources";
import { API_BASE } from "@/lib/api-base";

const QUICK_LINKS = [
  chromeNav.domains,
  chromeNav.ask,
  ...DOMAINS.filter((d) => d.enabled).map((d) => ({
    name: d.label,
    href: d.home,
    icon: (d.key === "government"
      ? "building"
      : d.key === "trademarks"
        ? "landmark"
        : d.key === "domain_names"
          ? "globe"
          : d.key === "library"
            ? "library"
            : "radio") as const,
  })),
  ...intelligenceNav,
  chromeNav.settings,
];

export default function DashboardPage() {
  const enabledDomains = DOMAINS.filter((d) => d.enabled);
  const [sources, setSources] = useState<Source[]>([]);
  const [loadingMetrics, setLoadingMetrics] = useState(true);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const res = await fetch(`${API_BASE}/api/v1/sources`);
        if (!res.ok) return;
        const data = await res.json();
        if (!cancelled) setSources((data.items ?? []).map(mapSource));
      } catch {
        /* metrics stay empty */
      } finally {
        if (!cancelled) setLoadingMetrics(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const itemTotal = sources.reduce((sum, s) => sum + Number(s.item_count ?? 0), 0);
  const activeCount = sources.filter((s) => s.status === "active").length;
  const autorunCount = sources.filter((s) => s.autorun).length;
  const checkedCount = sources.filter((s) => Boolean(s.last_checked)).length;
  const errorCount = sources.filter(
    (s) => s.status === "error" || Boolean(s.error_message),
  ).length;
  const transcriptionCount = sources.filter((s) => s.transcription_done).length;

  return (
    <div className="space-y-8 animate-in fade-in duration-500">
      <AppPageHeader
        title="Dashboard"
        description={`Welcome to ${site.name}. Open Domains to pick a control plane.`}
      />

      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
        <StatCard
          label="Sources"
          value={loadingMetrics ? "—" : sources.length}
          sub="monitored channels"
        />
        <StatCard
          label="Items"
          value={loadingMetrics ? "—" : itemTotal}
          sub="catalog total"
        />
        <StatCard
          label="Active"
          value={loadingMetrics ? "—" : activeCount}
          sub="not paused"
        />
        <StatCard
          label="Autorun"
          value={loadingMetrics ? "—" : autorunCount}
          sub="scheduled discover"
        />
        <StatCard
          label="Transcription"
          value={loadingMetrics ? "—" : transcriptionCount}
          sub="channels fully transcribed"
        />
        <StatCard
          label="Errors"
          value={loadingMetrics ? "—" : errorCount}
          sub={checkedCount ? `${checkedCount} checked` : "need attention"}
        />
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
        {QUICK_LINKS.map((item) => (
          <Link key={item.href} href={item.href}>
            <Card className="h-full rounded-2xl border-border/50 p-4 transition-all hover:border-primary/40 hover:shadow-md">
              <div className="flex items-center gap-3">
                <div className="rounded-xl bg-accent/20 p-2">
                  <Icon name={item.icon} className="h-4 w-4 text-primary" />
                </div>
                <div className="min-w-0">
                  <h2 className="font-display text-sm font-semibold tracking-tight">{item.name}</h2>
                  <p className="mt-0.5 truncate text-xs text-muted-foreground">{item.href}</p>
                </div>
              </div>
            </Card>
          </Link>
        ))}
      </div>

      <div className="space-y-3">
        <h2 className="font-display text-sm font-semibold tracking-tight">Active domains</h2>
        <div className="flex flex-wrap gap-2">
          {enabledDomains.map((d) => (
            <Link
              key={d.key}
              href={d.home}
              className="inline-flex items-center gap-2 rounded-lg border border-border/60 bg-card px-3 py-2 text-sm font-normal hover:border-accent hover:bg-accent/15"
            >
              {d.label}
              <Icon name="arrowRight" className="h-3.5 w-3.5 text-muted-foreground" />
            </Link>
          ))}
          <Link
            href={chromeNav.domains.href}
            className="inline-flex items-center gap-2 rounded-lg border border-border/60 px-3 py-2 text-sm font-normal text-muted-foreground hover:text-foreground"
          >
            Domains
            <Icon name="arrowRight" className="h-3.5 w-3.5" />
          </Link>
        </div>
      </div>
    </div>
  );
}
