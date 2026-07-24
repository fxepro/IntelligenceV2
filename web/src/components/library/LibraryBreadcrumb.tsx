"use client";

import Link from "next/link";
import { ChevronRight } from "lucide-react";
import { cn } from "@/lib/utils";

export type LibraryCrumb = {
  label: string;
  href?: string;
};

/** Shared Courses trail: Courses → Course → Lesson */
export function LibraryBreadcrumb({
  items,
  className,
}: {
  items: LibraryCrumb[];
  className?: string;
}) {
  return (
    <nav
      aria-label="Courses"
      className={cn("flex flex-wrap items-center gap-1 text-sm text-muted-foreground", className)}
    >
      {items.map((item, i) => {
        const last = i === items.length - 1;
        return (
          <span key={`${item.label}-${i}`} className="inline-flex items-center gap-1 min-w-0">
            {i > 0 ? <ChevronRight className="h-3.5 w-3.5 shrink-0 opacity-60" aria-hidden /> : null}
            {item.href && !last ? (
              <Link
                href={item.href}
                className="truncate hover:text-foreground font-medium max-w-[14rem] sm:max-w-[20rem]"
              >
                {item.label}
              </Link>
            ) : (
              <span
                className={cn(
                  "truncate max-w-[16rem] sm:max-w-[28rem]",
                  last ? "text-foreground font-medium" : "",
                )}
              >
                {item.label}
              </span>
            )}
          </span>
        );
      })}
    </nav>
  );
}
