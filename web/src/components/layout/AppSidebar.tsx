"use client";

import { useEffect, useState, type ReactNode } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { DOMAINS, workspaceDomainForPath } from "@/lib/domains";
import { Icon } from "@/lib/icons";
import { site } from "@/config/site";
import { chromeNav, intelligenceNav } from "@/config/navigation";
import { ThemeToggle } from "@/components/layout/ThemeToggle";

type StackProcess = {
  id: string;
  label: string;
  status: "up" | "down";
  detail?: string;
};

function StackStatus() {
  const [processes, setProcesses] = useState<StackProcess[]>([]);

  useEffect(() => {
    let active = true;
    const load = async () => {
      try {
        const response = await fetch("/api/stack/status", { cache: "no-store" });
        const data = await response.json();
        if (active) setProcesses(data.processes ?? []);
      } catch {
        if (active) setProcesses([]);
      }
    };
    void load();
    const timer = window.setInterval(load, 30_000);
    return () => {
      active = false;
      window.clearInterval(timer);
    };
  }, []);

  return (
    <div className="mb-3 rounded-lg border border-sidebar-border/80 bg-sidebar-accent/50 p-2">
      <p className="mb-1.5 px-0.5 text-[9px] font-bold uppercase tracking-widest text-sidebar-foreground/55">
        Stack
      </p>
      <div className="grid grid-cols-2 gap-x-2 gap-y-1">
        {processes.length > 0 ? (
          processes.map((process) => (
            <div
              key={process.id}
              className="flex min-w-0 items-center gap-1.5"
              title={process.detail}
            >
              <span
                className={cn(
                  "h-1.5 w-1.5 shrink-0 rounded-full",
                  process.status === "up"
                    ? "bg-emerald-500 shadow-[0_0_5px_rgba(16,185,129,.75)]"
                    : "bg-red-500 shadow-[0_0_5px_rgba(239,68,68,.65)]",
                )}
                aria-label={process.status}
              />
              <span className="truncate text-[10px] leading-4 text-sidebar-foreground/70">
                {process.label
                  .replace(" (Celery broker)", "")
                  .replace(" workers", "")
                  .replace(" (Next.js)", "")}
              </span>
            </div>
          ))
        ) : (
          <span className="col-span-2 text-[10px] text-sidebar-foreground/55">
            Checking…
          </span>
        )}
      </div>
    </div>
  );
}

function NavSection({
  label,
  labelId,
  children,
}: {
  label: string;
  labelId: string;
  children: ReactNode;
}) {
  return (
    <div className="flex flex-col gap-2">
      <p
        id={labelId}
        className="eyebrow px-3 pt-1 text-sidebar-foreground/55"
      >
        {label}
      </p>
      <div className="flex flex-col gap-1" role="group" aria-labelledby={labelId}>
        {children}
      </div>
    </div>
  );
}

function workspaceIcon(key: string) {
  if (key === "government" || key === "real_estate") return "building" as const;
  if (key === "finance") return "landmark" as const;
  if (key === "media") return "radio" as const;
  return "dashboard" as const;
}

export function AppSidebar({
  className,
  onNavigate,
}: {
  className?: string;
  /** Called after a nav link is activated (closes mobile sheet). */
  onNavigate?: () => void;
}) {
  const pathname = usePathname();
  const activeWorkspace = workspaceDomainForPath(pathname);
  const linkProps = { onClick: onNavigate };

  return (
    <aside
      className={cn(
        "flex flex-col w-64 h-full border-r border-sidebar-border bg-sidebar text-sidebar-foreground",
        className,
      )}
      aria-label="Application"
    >
      <div className="flex items-center h-16 px-5 border-b border-sidebar-border">
        <Link
          href={chromeNav.dashboard.href}
          className="flex items-center gap-2.5 hover:opacity-80 transition-opacity min-h-11"
          {...linkProps}
        >
          <div className="p-1.5 rounded-lg bg-accent shadow-sm">
            <Icon name="chart" className="w-5 h-5 text-accent-foreground" />
          </div>
          <span className="font-display font-bold text-body-sm tracking-tight text-sidebar-foreground">
            {site.shortName}
          </span>
        </Link>
      </div>

      <div className="flex-1 overflow-y-auto px-3 py-5">
        <nav className="flex flex-col gap-6" aria-label="Primary">
          <div className="flex flex-col gap-1">
            {([chromeNav.dashboard, chromeNav.domains, chromeNav.ask] as const).map((item) => {
              const active =
                pathname === item.href || pathname.startsWith(`${item.href}/`);
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  {...linkProps}
                  className={cn(
                    "flex items-center gap-3 px-3 py-2.5 text-body-sm font-medium rounded-xl transition-all duration-200 min-h-11",
                    active
                      ? "bg-sidebar-accent text-sidebar-accent-foreground"
                      : "text-sidebar-foreground/70 hover:bg-sidebar-accent/70 hover:text-sidebar-accent-foreground",
                  )}
                >
                  <Icon name={item.icon} className="h-5 w-5 shrink-0" />
                  {item.name}
                </Link>
              );
            })}
          </div>

          <NavSection label="Workspace" labelId="workspace-label">
            {DOMAINS.filter((d) => d.enabled).map((d) => {
              const active = activeWorkspace === d.key;
              return (
                <Link
                  key={d.key}
                  href={d.home}
                  {...linkProps}
                  className={cn(
                    "flex items-center gap-2.5 px-3 py-2 rounded-lg text-body-sm font-semibold transition-all min-h-10",
                    active
                      ? "bg-accent text-accent-foreground shadow-sm"
                      : "text-sidebar-foreground/70 hover:bg-sidebar-accent/70 hover:text-sidebar-accent-foreground border border-sidebar-border/60",
                  )}
                  aria-current={active ? "page" : undefined}
                >
                  <Icon name={workspaceIcon(d.key)} className="w-3.5 h-3.5 shrink-0" />
                  {d.label}
                </Link>
              );
            })}
          </NavSection>

          <NavSection label="Intelligence" labelId="intelligence-label">
            {intelligenceNav.map((item) => {
              const isActive =
                pathname === item.href || pathname.startsWith(`${item.href}/`);
              return (
                <Link
                  key={item.name}
                  href={item.href}
                  {...linkProps}
                  aria-current={isActive ? "page" : undefined}
                  className={cn(
                    "flex items-center gap-3 px-3 py-2.5 text-body-sm font-medium rounded-xl transition-all duration-200 min-h-11",
                    isActive
                      ? "bg-accent text-accent-foreground shadow-md shadow-accent/25"
                      : "text-sidebar-foreground/70 hover:bg-sidebar-accent/70 hover:text-sidebar-accent-foreground",
                  )}
                >
                  <Icon
                    name={item.icon}
                    className={cn(
                      "h-5 w-5 shrink-0",
                      isActive ? "text-accent-foreground" : "text-sidebar-foreground/55",
                    )}
                  />
                  {item.name}
                </Link>
              );
            })}
          </NavSection>
        </nav>
      </div>

      <div className="p-4 border-t border-sidebar-border space-y-3">
        <StackStatus />
        <ThemeToggle
          withSettings
          settingsActive={pathname === chromeNav.settings.href}
          onSettingsNavigate={onNavigate}
        />
      </div>
    </aside>
  );
}
