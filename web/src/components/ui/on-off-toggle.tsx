"use client";

import * as React from "react";
import { cn } from "@/lib/utils";

export function OnOffToggle({
  checked,
  onCheckedChange,
  disabled = false,
  size = "default",
  title,
  className,
}: {
  checked: boolean;
  onCheckedChange: (checked: boolean) => void;
  disabled?: boolean;
  size?: "default" | "sm";
  title?: string;
  className?: string;
}) {
  const sm = size === "sm";

  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      aria-label={checked ? "On" : "Off"}
      title={title}
      disabled={disabled}
      onClick={() => onCheckedChange(!checked)}
      className={cn(
        "relative inline-flex shrink-0 cursor-pointer select-none items-center rounded-full transition-colors",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background",
        "disabled:cursor-not-allowed disabled:opacity-50",
        sm ? "h-7 w-[3.25rem]" : "h-10 w-[5.5rem]",
        checked
          ? "bg-emerald-500 border-2 border-emerald-500"
          : "bg-muted/40 border-2 border-foreground/25 dark:border-white/70",
        className,
      )}
    >
      <span
        className={cn(
          "absolute font-bold uppercase tracking-wide transition-opacity",
          sm ? "text-[9px]" : "text-xs",
          checked
            ? cn("left-2 text-emerald-950/90", sm && "left-1.5")
            : cn("right-1.5 text-muted-foreground dark:text-white/90", sm && "right-1 text-[8px]"),
        )}
      >
        {checked ? "ON" : "OFF"}
      </span>
      <span
        aria-hidden
        className={cn(
          "absolute rounded-full bg-white shadow-md transition-all duration-200 ease-out",
          sm ? "h-5 w-5" : "h-8 w-8",
          checked ? (sm ? "right-0.5" : "right-1") : (sm ? "left-0.5" : "left-1"),
        )}
      />
    </button>
  );
}
