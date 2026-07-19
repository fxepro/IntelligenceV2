"use client";

import { AppPageHeader } from "@/components/sections/AppPageHeader";
import { Icon } from "@/lib/icons";
import { BACKEND_URL } from "@/lib/api-base";

/** Dev ops view — jobs / control plane status. */
export default function ControlPlanePage() {
  return (
    <div className="space-y-8 animate-in fade-in duration-500">
      <AppPageHeader
        title="Control plane"
        icon={
          <div className="p-1.5 bg-primary/10 rounded-lg">
            <Icon name="chart" className="w-5 h-5 text-primary" />
          </div>
        }
        description="Jobs and worker status. Primary workflows live under Research, Sources, and Intelligence."
      />
      <p className="text-sm text-muted-foreground">
        API docs:{" "}
        <a className="text-primary underline" href={`${BACKEND_URL}/docs`} target="_blank" rel="noreferrer">
          /docs
        </a>
      </p>
    </div>
  );
}
