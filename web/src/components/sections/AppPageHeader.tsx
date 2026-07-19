import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

/**
 * Compact dashboard page header (standard §10 AppPageHeader).
 * Title (header) + description (subheader) use a fixed vertical rhythm.
 */
export function AppPageHeader({
  title,
  description,
  icon,
  actions,
  className,
}: {
  title: ReactNode;
  description?: ReactNode;
  icon?: ReactNode;
  actions?: ReactNode;
  className?: string;
}) {
  return (
    <div className={cn("flex items-start justify-between gap-4", className)}>
      <div className="flex flex-col gap-2 min-w-0">
        <div className="flex items-center gap-2.5 min-w-0">
          {icon}
          <h1 className="page-title truncate">{title}</h1>
        </div>
        <div
          className="h-0.5 w-12 rounded-full bg-accent"
          aria-hidden
        />
        {description ? (
          <p className="text-muted-foreground text-body-sm max-w-2xl leading-relaxed">
            {description}
          </p>
        ) : null}
      </div>
      {actions ? (
        <div className="flex items-center gap-2 shrink-0 pt-1">{actions}</div>
      ) : null}
    </div>
  );
}
