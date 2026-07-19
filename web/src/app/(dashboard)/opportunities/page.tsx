"use client";

import { AppPageHeader } from "@/components/sections/AppPageHeader";
import { Icon } from "@/lib/icons";

export default function OpportunitiesPage() {
  return (
    <div className="space-y-8 animate-in fade-in duration-500">
      <AppPageHeader
        title="Opportunities"
        icon={
          <div className="rounded-lg bg-primary/10 p-1.5">
            <Icon name="target" className="h-5 w-5 text-primary" />
          </div>
        }
        description="Surface actionable opportunities from researched sources and intelligence."
      />
      <p className="text-sm text-muted-foreground">
        Opportunity workflows will land here. For now, continue from Research, Sources, and Intelligence.
      </p>
    </div>
  );
}
