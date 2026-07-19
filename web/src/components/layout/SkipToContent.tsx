import Link from "next/link";

/** Skip to main content — first focusable control for keyboard users (§17). */
export function SkipToContent({
  href = "#main-content",
  label = "Skip to main content",
}: {
  href?: string;
  label?: string;
}) {
  return (
    <Link
      href={href}
      className="sr-only focus:not-sr-only focus:fixed focus:left-4 focus:top-4 focus:z-[100] focus:rounded-lg focus:bg-primary focus:px-4 focus:py-2 focus:text-primary-foreground focus:shadow-lg focus:outline-none focus:ring-2 focus:ring-ring"
    >
      {label}
    </Link>
  );
}
