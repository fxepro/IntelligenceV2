"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { cn } from "@/lib/utils";
import { Icon } from "@/lib/icons";
import { chromeNav } from "@/config/navigation";

const STORAGE_KEY = "media-intelligence-theme";
const THEME_EVENT = "media-intelligence-theme-change";

export function ThemeToggle({
  compact = false,
  /** Split control: theme icon | Settings icon (sidebar footer). */
  withSettings = false,
  className,
  settingsActive = false,
  onSettingsNavigate,
}: {
  compact?: boolean;
  withSettings?: boolean;
  className?: string;
  settingsActive?: boolean;
  onSettingsNavigate?: () => void;
}) {
  const [dark, setDark] = useState(false);

  useEffect(() => {
    const sync = () => setDark(document.documentElement.classList.contains("dark"));
    sync();
    window.addEventListener(THEME_EVENT, sync);
    return () => window.removeEventListener(THEME_EVENT, sync);
  }, []);

  const setTheme = (nextDark: boolean) => {
    document.documentElement.classList.toggle("dark", nextDark);
    localStorage.setItem(STORAGE_KEY, nextDark ? "dark" : "light");
    setDark(nextDark);
    window.dispatchEvent(new Event(THEME_EVENT));
  };

  const toggleTheme = () => setTheme(!dark);

  if (withSettings) {
    return (
      <div
        role="group"
        aria-label="Theme and settings"
        className={cn(
          "grid w-full grid-cols-2 rounded-xl border border-sidebar-border bg-sidebar-accent/40 p-0.5",
          className,
        )}
      >
        <button
          type="button"
          onClick={toggleTheme}
          aria-label={dark ? "Switch to light mode" : "Switch to dark mode"}
          aria-pressed={dark}
          title={dark ? "Light mode" : "Dark mode"}
          className={cn(
            "inline-flex h-10 items-center justify-center rounded-lg transition-colors",
            "text-sidebar-foreground/70 hover:bg-sidebar-accent hover:text-sidebar-accent-foreground",
          )}
        >
          <Icon name={dark ? "sun" : "moon"} className="h-4 w-4" />
        </button>
        <Link
          href={chromeNav.settings.href}
          onClick={onSettingsNavigate}
          aria-label="Settings"
          aria-current={settingsActive ? "page" : undefined}
          title="Settings"
          className={cn(
            "inline-flex h-10 items-center justify-center rounded-lg transition-colors",
            settingsActive
              ? "bg-sidebar-accent text-sidebar-accent-foreground shadow-sm"
              : "text-sidebar-foreground/70 hover:bg-sidebar-accent hover:text-sidebar-accent-foreground",
          )}
        >
          <Icon name="settings" className="h-4 w-4" />
        </Link>
      </div>
    );
  }

  if (compact) {
    return (
      <button
        type="button"
        onClick={toggleTheme}
        aria-label={dark ? "Switch to light mode" : "Switch to dark mode"}
        aria-pressed={dark}
        title={dark ? "Light mode" : "Dark mode"}
        className={cn(
          "inline-flex h-10 w-10 items-center justify-center rounded-xl border border-border/60 bg-card text-foreground transition-colors hover:bg-muted",
          className,
        )}
      >
        <Icon name={dark ? "sun" : "moon"} className="h-4 w-4" />
      </button>
    );
  }

  return (
    <div
      role="group"
      aria-label="Theme"
      className={cn(
        "grid w-full grid-cols-2 rounded-xl border border-sidebar-border bg-sidebar-accent/40 p-0.5",
        className,
      )}
    >
      <button
        type="button"
        onClick={() => setTheme(false)}
        aria-pressed={!dark}
        className={cn(
          "rounded-lg px-2 py-1.5 text-xs font-medium transition-colors",
          !dark
            ? "bg-sidebar-accent text-sidebar-accent-foreground shadow-sm"
            : "text-sidebar-foreground/55 hover:text-sidebar-foreground/80",
        )}
      >
        Light
      </button>
      <button
        type="button"
        onClick={() => setTheme(true)}
        aria-pressed={dark}
        className={cn(
          "rounded-lg px-2 py-1.5 text-xs font-medium transition-colors",
          dark
            ? "bg-sidebar-accent text-sidebar-accent-foreground shadow-sm"
            : "text-sidebar-foreground/55 hover:text-sidebar-foreground/80",
        )}
      >
        Dark
      </button>
    </div>
  );
}
