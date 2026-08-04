import type { DomainKey } from "@/lib/domains";
import type { IconName } from "@/lib/icons";

export type NavItem = {
  name: string;
  href: string;
  icon: IconName;
};

/**
 * Per-domain secondary nav (usually empty — Sources is the domain home).
 * Domain homes are reached via Domains.
 */
export const domainNav: Record<DomainKey, NavItem[]> = {
  media: [],
  finance: [
    { name: "Records", href: "/finance", icon: "landmark" },
  ],
  software: [],
  business: [],
  government: [],
  taxes: [],
  healthcare: [],
  people: [],
  geography: [],
  politics: [],
  nonprofit: [],
  news: [],
  real_estate: [
    { name: "Records", href: "/real-estate", icon: "building" },
  ],
  auctions: [],
  torrents: [],
  trademarks: [],
  domain_names: [],
  courses: [],
  library: [],
  patents: [],
  songs: [],
  music: [],
  books: [],
  movies: [],
  fiction: [],
};

/** Platform Intelligence section (header in sidebar — not a page). */
export const intelligenceNav: NavItem[] = [
  { name: "Research", href: "/research", icon: "telescope" },
  { name: "Opportunities", href: "/opportunities", icon: "target" },
];

/** Always-visible chrome links (above / below domain lists). */
export const chromeNav = {
  dashboard: { name: "Dashboard", href: "/dashboard", icon: "dashboard" as IconName },
  domains: { name: "Domains", href: "/domains", icon: "home" as IconName },
  /** Platform-scoped AI chat grounded in catalog context (not per-domain Research). */
  ask: { name: "Ask", href: "/ask", icon: "message" as IconName },
  settings: { name: "Settings", href: "/settings", icon: "settings" as IconName },
};

/** Public marketing header links (landing). */
export const marketingNav: { label: string; href: string }[] = [
  { label: "Features", href: "#features" },
  { label: "How it Works", href: "#how-it-works" },
];
