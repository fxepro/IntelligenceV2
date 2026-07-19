"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Card } from "@/components/ui/card";
import { DOMAINS, DomainKey } from "@/lib/domains";
import { AppPageHeader } from "@/components/sections/AppPageHeader";
import { Icon, type IconName } from "@/lib/icons";
import { site } from "@/config/site";

import { API_BASE } from "@/lib/api-base";

const DOMAIN_ICONS: Record<DomainKey, IconName> = {
  media: "radio",
  finance: "landmark",
  software: "sparkles",
  business: "landmark",
  government: "building",
  taxes: "chart",
  healthcare: "plus",
  people: "search",
  geography: "globe",
  politics: "landmark",
  nonprofit: "heart",
  news: "radio",
  real_estate: "building",
  auctions: "gavel",
  torrents: "download",
  trademarks: "landmark",
  patents: "library",
  songs: "music",
  music: "music",
  books: "library",
  movies: "radio",
  fiction: "library",
};

export default function DomainsPage() {
  const [counts, setCounts] = useState<Record<string, number>>({});

  useEffect(() => {
    (async () => {
      try {
        const [media, re] = await Promise.all([
          fetch(`${API_BASE}/api/v1/media?page_size=1`).then((r) => r.json()).catch(() => null),
          fetch(`${API_BASE}/api/v1/records?domain=real_estate&page_size=1`).then((r) => r.json()).catch(() => null),
        ]);
        setCounts({ media: media?.total ?? 0, real_estate: re?.total ?? 0 });
      } catch {
        /* ignore */
      }
    })();
  }, []);

  return (
    <div className="space-y-8 animate-in fade-in duration-500">
      <AppPageHeader
        title="Domains"
        description={`${site.name} is the platform. Pick a domain control plane to work in — each runs the same pipeline over a different kind of data.`}
      />

      <Link
        href="/ask"
        className="block rounded-2xl border border-border/50 bg-card p-4 transition-all hover:border-primary/40 hover:shadow-md"
      >
        <div className="flex items-start gap-3">
          <div className="p-2 rounded-xl bg-primary/10 shrink-0">
            <Icon name="message" className="w-4 h-4 text-primary" />
          </div>
          <div className="min-w-0 flex-1">
            <h2 className="font-display text-sm font-semibold tracking-tight">Ask</h2>
            <p className="text-xs text-muted-foreground mt-1">
              AI chat with platform context — sources, domains, and catalog facts.
            </p>
          </div>
          <Icon name="arrowRight" className="w-4 h-4 text-muted-foreground shrink-0 mt-1" />
        </div>
      </Link>

      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
        {DOMAINS.map((d) => {
          const count = counts[d.key];
          const card = (
            <Card
              className={`relative p-4 rounded-2xl border-border/50 transition-all h-full ${
                d.enabled
                  ? "hover:border-primary/40 hover:shadow-md cursor-pointer"
                  : "opacity-60"
              }`}
            >
              <div className="flex items-start justify-between gap-3">
                <div className="flex items-start gap-3 min-w-0">
                  <div className="p-2 rounded-xl bg-primary/10 shrink-0">
                    <Icon name={DOMAIN_ICONS[d.key]} className="w-4 h-4 text-primary" />
                  </div>
                  <div className="min-w-0">
                    <h2 className="font-display text-sm font-semibold tracking-tight">{d.label}</h2>
                    <p className="text-xs text-muted-foreground mt-1 line-clamp-3">{d.blurb}</p>
                  </div>
                </div>
                <div className="flex flex-col items-end gap-2 shrink-0 text-right">
                  <p className="text-fine tabular-nums text-muted-foreground whitespace-nowrap">
                    {typeof count === "number" ? (
                      <>
                        <span className="font-semibold text-foreground">{count.toLocaleString()}</span>
                        {" "}rec
                      </>
                    ) : (
                      "—"
                    )}
                  </p>
                  {d.enabled ? (
                    <Icon name="arrowRight" className="w-4 h-4 text-muted-foreground" />
                  ) : (
                    <span className="inline-flex items-center gap-1 text-fine font-bold uppercase tracking-widest px-2 py-0.5 rounded-full bg-muted text-muted-foreground border border-border/50">
                      <Icon name="lock" className="w-3 h-3" /> Soon
                    </span>
                  )}
                </div>
              </div>
            </Card>
          );
          return d.enabled ? (
            <Link key={d.key} href={d.home}>
              {card}
            </Link>
          ) : (
            <div key={d.key}>{card}</div>
          );
        })}
      </div>
    </div>
  );
}
