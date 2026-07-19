import {
  CheckCircle2,
  AlertCircle,
  Clock,
  Loader2,
  Circle,
} from "lucide-react";
import { cn } from "@/lib/utils";

const SOURCE_STATUS = {
  active: {
    label: "Active",
    className: "bg-emerald-500/10 text-emerald-500 border-emerald-500/20",
    Icon: CheckCircle2,
  },
  error: {
    label: "Error",
    className: "bg-red-500/10 text-red-400 border-red-500/20",
    Icon: AlertCircle,
  },
  paused: {
    label: "Paused",
    className: "bg-muted text-muted-foreground border-border/50",
    Icon: Clock,
  },
} as const;

export function SourceStatusBadge({
  status,
  className,
}: {
  status: string;
  className?: string;
}) {
  const key = status === "active" || status === "error" ? status : "paused";
  const cfg = SOURCE_STATUS[key];
  const Icon = cfg.Icon;
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 text-fine font-bold uppercase tracking-widest px-2.5 py-1 rounded-full border",
        cfg.className,
        className,
      )}
    >
      <Icon className="w-3 h-3" /> {cfg.label}
    </span>
  );
}

const MEDIA_STATUS: Record<
  string,
  { className: string; label: string; spinning?: boolean; Icon: typeof Circle }
> = {
  queued: {
    className: "bg-slate-500/10 text-slate-400 border-slate-500/20",
    label: "Queued",
    Icon: Circle,
  },
  downloading: {
    className: "bg-blue-500/10 text-blue-400 border-blue-500/20",
    label: "Downloading",
    spinning: true,
    Icon: Loader2,
  },
  transcribing: {
    className: "bg-violet-500/10 text-violet-400 border-violet-500/20",
    label: "Transcribing",
    spinning: true,
    Icon: Loader2,
  },
  analyzing: {
    className: "bg-amber-500/10 text-amber-400 border-amber-500/20",
    label: "Analyzing",
    spinning: true,
    Icon: Loader2,
  },
  completed: {
    className: "bg-emerald-500/10 text-emerald-500 border-emerald-500/20",
    label: "Completed",
    Icon: CheckCircle2,
  },
  failed: {
    className: "bg-red-500/10 text-red-400 border-red-500/20",
    label: "Failed",
    Icon: AlertCircle,
  },
  skipped: {
    className: "bg-muted text-muted-foreground border-border/50",
    label: "Cataloged",
    Icon: Clock,
  },
};

/** Compact pill (raw status text) or rich (icon + human label). */
export function MediaStatusPill({
  status,
  variant = "compact",
  className,
}: {
  status: string;
  variant?: "compact" | "rich";
  className?: string;
}) {
  const cfg = MEDIA_STATUS[status] ?? {
    className: "bg-muted text-muted-foreground border-border/50",
    label: status,
    Icon: Circle,
  };

  if (variant === "compact") {
    return (
      <span
        className={cn(
          "inline-flex text-fine font-bold uppercase tracking-widest px-2 py-0.5 rounded-full border",
          cfg.className,
          className,
        )}
      >
        {status}
      </span>
    );
  }

  const Icon = cfg.Icon;
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 text-fine font-bold uppercase tracking-widest px-2.5 py-1 rounded-full border",
        cfg.className,
        className,
      )}
    >
      <Icon className={cn("w-3 h-3", cfg.spinning && "animate-spin")} /> {cfg.label}
    </span>
  );
}
