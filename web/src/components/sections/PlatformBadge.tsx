import { cn } from "@/lib/utils";
import { PLATFORM_COLORS, PLATFORM_LABELS, type Platform } from "@/lib/mock-data/sources";

/** Brand marks for platform columns — icon only; label via title/aria. */
function BrandSvg({
  platform,
  className,
}: {
  platform: string;
  className?: string;
}) {
  const p = platform.toLowerCase();
  const cls = cn("shrink-0", className);

  if (p === "youtube") {
    return (
      <svg viewBox="0 0 24 24" className={cls} aria-hidden fill="currentColor">
        <path d="M23.5 6.2a3 3 0 0 0-2.1-2.1C19.5 3.5 12 3.5 12 3.5s-7.5 0-9.4.6A3 3 0 0 0 .5 6.2 31.5 31.5 0 0 0 0 12a31.5 31.5 0 0 0 .5 5.8 3 3 0 0 0 2.1 2.1c1.9.6 9.4.6 9.4.6s7.5 0 9.4-.6a3 3 0 0 0 2.1-2.1A31.5 31.5 0 0 0 24 12a31.5 31.5 0 0 0-.5-5.8zM9.75 15.5v-7l6.5 3.5-6.5 3.5z" />
      </svg>
    );
  }
  if (p === "facebook") {
    return (
      <svg viewBox="0 0 24 24" className={cls} aria-hidden fill="currentColor">
        <path d="M24 12.07C24 5.41 18.63 0 12 0S0 5.41 0 12.07C0 18.1 4.39 23.1 10.13 24v-8.44H7.08v-3.49h3.05V9.41c0-3.02 1.79-4.7 4.53-4.7 1.31 0 2.68.24 2.68.24v2.95h-1.51c-1.49 0-1.95.93-1.95 1.89v2.26h3.32l-.53 3.49h-2.79V24C19.61 23.1 24 18.1 24 12.07z" />
      </svg>
    );
  }
  if (p === "x" || p === "twitter") {
    return (
      <svg viewBox="0 0 24 24" className={cls} aria-hidden fill="currentColor">
        <path d="M18.24 2H21.8l-7.78 8.89L23.18 22H16l-5.62-7.35L3.95 22H.38l8.33-9.52L-.08 2H7.28l5.08 6.72L18.24 2zm-1.25 18h1.97L6.21 3.9H4.1L16.99 20z" />
      </svg>
    );
  }
  if (p === "instagram") {
    return (
      <svg viewBox="0 0 24 24" className={cls} aria-hidden fill="currentColor">
        <path d="M12 2.2c3.2 0 3.6 0 4.9.1 3.3.1 4.8 1.7 4.9 4.9.1 1.3.1 1.7.1 4.9s0 3.6-.1 4.9c-.1 3.2-1.7 4.8-4.9 4.9-1.3.1-1.7.1-4.9.1s-3.6 0-4.9-.1c-3.3-.1-4.8-1.7-4.9-4.9-.1-1.3-.1-1.7-.1-4.9s0-3.6.1-4.9C2.3 4 3.9 2.4 7.1 2.3 8.4 2.2 8.8 2.2 12 2.2zm0 1.8c-3.2 0-3.5 0-4.8.1-2.3.1-3.3 1.1-3.4 3.4-.1 1.2-.1 1.6-.1 4.8s0 3.5.1 4.8c.1 2.2 1.1 3.3 3.4 3.4 1.2.1 1.6.1 4.8.1s3.5 0 4.8-.1c2.3-.1 3.3-1.2 3.4-3.4.1-1.2.1-1.6.1-4.8s0-3.5-.1-4.8c-.1-2.3-1.1-3.3-3.4-3.4-1.3-.1-1.6-.1-4.8-.1zm0 3.2a4.8 4.8 0 1 1 0 9.6 4.8 4.8 0 0 1 0-9.6zm0 7.9a3.1 3.1 0 1 0 0-6.2 3.1 3.1 0 0 0 0 6.2zm6.1-8.1a1.1 1.1 0 1 1-2.3 0 1.1 1.1 0 0 1 2.3 0z" />
      </svg>
    );
  }
  if (p === "tiktok") {
    return (
      <svg viewBox="0 0 24 24" className={cls} aria-hidden fill="currentColor">
        <path d="M19.6 7.1a5.6 5.6 0 0 1-3.2-1V15a5.6 5.6 0 1 1-5.6-5.6c.2 0 .5 0 .7.1v2.8a2.8 2.8 0 1 0 2 2.7V2.2h2.7a5.6 5.6 0 0 0 3.4 4.9z" />
      </svg>
    );
  }
  if (p === "podcast" || p === "rss") {
    return (
      <svg viewBox="0 0 24 24" className={cls} aria-hidden fill="currentColor">
        <path d="M6.2 15.8a1.4 1.4 0 1 1-2 2 1.4 1.4 0 0 1 2-2zM12 14.5a3.5 3.5 0 0 0-3.5 3.5h2a1.5 1.5 0 0 1 3 0h2A3.5 3.5 0 0 0 12 14.5zm0-4.5a8 8 0 0 0-8 8h2a6 6 0 0 1 12 0h2a8 8 0 0 0-8-8zm0-4.5C6.2 5.5 1.5 10.2 1.5 16h2c0-4.7 3.8-8.5 8.5-8.5S20.5 11.3 20.5 16h2c0-5.8-4.7-10.5-10.5-10.5z" />
      </svg>
    );
  }
  // website / fallback
  return (
    <svg viewBox="0 0 24 24" className={cls} aria-hidden fill="none" stroke="currentColor" strokeWidth="2">
      <circle cx="12" cy="12" r="9" />
      <path d="M3 12h18M12 3a14 14 0 0 1 0 18M12 3a14 14 0 0 0 0 18" />
    </svg>
  );
}

export function PlatformIcon({
  platform,
  className = "w-3.5 h-3.5",
}: {
  platform: string;
  className?: string;
}) {
  return <BrandSvg platform={platform} className={className} />;
}

export function PlatformBadge({
  platform,
  className,
  showIcon = true,
  /** `logo` = icon only (table columns); `badge` = icon + label */
  variant = "badge",
}: {
  platform: string;
  className?: string;
  showIcon?: boolean;
  variant?: "badge" | "logo";
}) {
  const colors =
    PLATFORM_COLORS[platform as Platform] ??
    "bg-muted text-muted-foreground border-border/50";
  const label = PLATFORM_LABELS[platform as Platform] ?? platform;

  if (variant === "logo") {
    return (
      <span
        title={label}
        aria-label={label}
        className={cn(
          "inline-flex items-center justify-center w-8 h-8 rounded-lg border",
          colors,
          className,
        )}
      >
        <BrandSvg platform={platform} className="w-4 h-4" />
      </span>
    );
  }

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 text-fine font-bold uppercase tracking-widest px-2 py-1 rounded-md border whitespace-nowrap",
        colors,
        className,
      )}
    >
      {showIcon ? <BrandSvg platform={platform} className="w-3.5 h-3.5" /> : null}
      {label}
    </span>
  );
}
