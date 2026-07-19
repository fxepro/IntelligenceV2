"use client";

import { useState, type ReactNode } from "react";
import { AppSidebar } from "@/components/layout/AppSidebar";
import { SkipToContent } from "@/components/layout/SkipToContent";
import { Button } from "@/components/ui/button";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";
import { Icon } from "@/lib/icons";
import { site } from "@/config/site";
import { ThemeToggle } from "@/components/layout/ThemeToggle";

/**
 * Dashboard shell — desktop sidebar + mobile drawer, skip link, page-main/body.
 * Route layouts pick this; pages never re-declare viewport min-heights.
 */
export function DashboardShell({ children }: { children: ReactNode }) {
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <div className="flex h-screen overflow-hidden bg-background">
      <SkipToContent />

      <div className="hidden lg:flex h-full shrink-0">
        <AppSidebar />
      </div>

      <div className="flex flex-1 flex-col min-w-0">
        <header className="lg:hidden flex items-center gap-3 h-14 px-4 border-b border-border/60 bg-card/80 backdrop-blur-sm shrink-0">
          <Sheet open={mobileOpen} onOpenChange={setMobileOpen}>
            <SheetTrigger asChild>
              <Button
                variant="outline"
                size="icon"
                className="min-h-11 min-w-11"
                aria-label="Open navigation menu"
              >
                <Icon name="menu" className="h-5 w-5" />
              </Button>
            </SheetTrigger>
            <SheetContent side="left" className="p-0 w-72 sm:max-w-[18rem]">
              <SheetHeader className="sr-only">
                <SheetTitle>{site.shortName} navigation</SheetTitle>
              </SheetHeader>
              <AppSidebar
                className="w-full border-0"
                onNavigate={() => setMobileOpen(false)}
              />
            </SheetContent>
          </Sheet>
          <span className="font-display font-bold text-body-sm tracking-tight truncate">
            {site.shortName}
          </span>
          <ThemeToggle compact className="ml-auto" />
        </header>

        <main
          id="main-content"
          tabIndex={-1}
          className="flex-1 overflow-y-auto relative page-main outline-none bg-background"
        >
          {/* Brand atmosphere on the content canvas (beige + wine + slate) */}
          <div
            className="pointer-events-none absolute inset-0 -z-10 overflow-hidden motion-reduce:hidden"
            aria-hidden
          >
            <div className="absolute -top-24 -right-16 h-[420px] w-[420px] rounded-full bg-accent/10 blur-[110px] dark:bg-accent/15" />
            <div className="absolute top-1/3 -left-24 h-[360px] w-[360px] rounded-full bg-primary/10 blur-[100px] dark:bg-primary/12" />
            <div className="absolute bottom-0 right-1/4 h-[280px] w-[280px] rounded-full bg-accent/15 blur-[90px] dark:bg-accent/20" />
          </div>
          <div className="relative p-4 sm:p-6 lg:p-8 page-body">{children}</div>
        </main>
      </div>
    </div>
  );
}
