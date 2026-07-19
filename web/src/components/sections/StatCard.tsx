import { cn } from "@/lib/utils";

export function StatCard({
  label,
  value,
  sub,
  className,
}: {
  label: string;
  value: string | number;
  sub?: string;
  className?: string;
}) {
  return (
    <div
      className={cn(
        "flex flex-col gap-1 p-4 rounded-2xl bg-card border border-border/50 shadow-sm",
        className,
      )}
    >
      <span className="label-caps">{label}</span>
      <span className="font-display text-h5 tracking-tight">{value}</span>
      {sub ? <span className="text-fine text-muted-foreground">{sub}</span> : null}
    </div>
  );
}
