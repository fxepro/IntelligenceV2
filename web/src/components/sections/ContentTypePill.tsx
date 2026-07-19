import { cn } from "@/lib/utils";

/** Short vs long-form content type chip — one variant API, no page forks. */
export function ContentTypePill({
  contentType,
  className,
}: {
  contentType?: string | null;
  className?: string;
}) {
  const isShort = (contentType || "").toLowerCase() === "short";
  return (
    <span
      className={cn(
        "text-fine font-bold uppercase tracking-widest px-1.5 py-0.5 rounded border",
        isShort
          ? "bg-pink-500/10 text-pink-400 border-pink-500/20"
          : "bg-sky-500/10 text-sky-400 border-sky-500/20",
        className,
      )}
    >
      {isShort ? "Short" : contentType || "Video"}
    </span>
  );
}
