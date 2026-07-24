// Domain registry — source of truth for product copy: docs/domains
// Drives domain cards, sidebar switcher, and workspace nav.
// Order is alphabetical by label (see sort on DOMAINS).
//
// Intelligence is the platform name. These keys are control planes.

export type DomainKey =
  | "media"
  | "finance"
  | "software"
  | "business"
  | "government"
  | "taxes"
  | "healthcare"
  | "people"
  | "geography"
  | "politics"
  | "nonprofit"
  | "news"
  | "real_estate"
  | "auctions"
  | "torrents"
  | "trademarks"
  | "domain_names"
  | "library"
  | "patents"
  | "songs"
  | "music"
  | "books"
  | "movies"
  | "fiction";

export interface DomainDef {
  key: DomainKey;
  label: string;
  blurb: string;
  home: string; // entry route for the workspace
  enabled: boolean;
}

export const DOMAINS: DomainDef[] = [
  {
    key: "media",
    label: "Media",
    blurb: "Social posts, videos, websites, podcasts, newsletters and channels",
    home: "/media/sources",
    enabled: true,
  },
  {
    key: "finance",
    label: "Finance",
    blurb: "Markets, filings, companies, securities and financial signals",
    home: "/finance",
    enabled: false,
  },
  {
    key: "software",
    label: "Software",
    blurb: "Products, vendors, licenses, codebases and digital platforms",
    home: "/software",
    enabled: false,
  },
  {
    key: "business",
    label: "Business",
    blurb: "Companies, ownership, operations, filings and commercial signals",
    home: "/business",
    enabled: false,
  },
  {
    key: "government",
    label: "Government",
    blurb: "Agencies, regulations, procurement, public records and policy",
    home: "/government/sources",
    enabled: true,
  },
  {
    key: "taxes",
    label: "Taxes",
    blurb: "Rules, filings, jurisdictions, incentives and compliance signals",
    home: "/taxes",
    enabled: false,
  },
  {
    key: "healthcare",
    label: "Healthcare/Medical",
    blurb: "Providers, facilities, claims, treatments, pharma and clinical signals",
    home: "/healthcare",
    enabled: false,
  },
  {
    key: "people",
    label: "People",
    blurb: "Individuals, roles, relationships, affiliations and influence signals",
    home: "/people",
    enabled: false,
  },
  {
    key: "geography",
    label: "Geography",
    blurb: "Places, regions, borders, corridors and spatial economic signals",
    home: "/geography",
    enabled: false,
  },
  {
    key: "politics",
    label: "Politics",
    blurb: "Campaigns, officials, legislation, elections and civic power signals",
    home: "/politics",
    enabled: false,
  },
  {
    key: "nonprofit",
    label: "Non-profit",
    blurb: "Orgs, missions, funding, grants, programs and civic initiatives",
    home: "/nonprofit",
    enabled: false,
  },
  {
    key: "news",
    label: "News",
    blurb: "Published events, claims, organizations, people and developing stories",
    home: "#",
    enabled: false,
  },
  {
    key: "real_estate",
    label: "Real Estate",
    blurb: "Parcels, buildings, owners, liens, zoning, permits and transactions",
    home: "/real-estate",
    enabled: false,
  },
  {
    key: "auctions",
    label: "Auctions",
    blurb: "HOA, tax, foreclosure and public auctions — lots, dates, bidders and jurisdictions",
    home: "/auctions",
    enabled: false,
  },
  {
    key: "torrents",
    label: "Torrents",
    blurb: "Torrent indexes, releases, magnets, swarm activity and distribution signals",
    home: "/torrents",
    enabled: false,
  },
  {
    key: "trademarks",
    label: "Trademarks",
    blurb: "Marks, owners, classes, status, prosecution history and related brands",
    home: "/trademarks/sources",
    enabled: true,
  },
  {
    key: "domain_names",
    label: "Domains",
    blurb: "www, .net and other TLDs — registries, WHOIS, DNS, availability and ownership",
    home: "/domain-names/portfolio",
    enabled: true,
  },
  {
    key: "library",
    label: "Courses",
    blurb: "Lessons from courses, books, and videos — text, PDF, and video by topic",
    home: "/library/sources",
    enabled: true,
  },
  {
    key: "patents",
    label: "Patents",
    blurb: "Applications, grants, claims, inventors, assignees, citations and legal status",
    home: "#",
    enabled: false,
  },
  {
    key: "songs",
    label: "Songs",
    blurb: "Musical compositions and associated writers, publishers and rights",
    home: "#",
    enabled: false,
  },
  {
    key: "music",
    label: "Music",
    blurb: "Sound recordings, releases, artists, labels and catalogs",
    home: "#",
    enabled: false,
  },
  {
    key: "books",
    label: "Books",
    blurb: "Published works, editions, authors, publishers, rights and sales signals",
    home: "#",
    enabled: false,
  },
  {
    key: "movies",
    label: "Movies",
    blurb: "Films, television, video works, production entities and distribution rights",
    home: "#",
    enabled: false,
  },
  {
    key: "fiction",
    label: "Fiction",
    blurb: "Unpublished or independently created stories, characters, settings and story worlds",
    home: "#",
    enabled: false,
  },
].sort((a, b) => a.label.localeCompare(b.label));

// Which domain a pathname belongs to (for the sidebar).
export function domainForPath(pathname: string): DomainKey {
  if (pathname.startsWith("/media") || pathname.startsWith("/sources")) return "media";
  if (pathname.startsWith("/finance")) return "finance";
  if (pathname.startsWith("/software")) return "software";
  if (pathname.startsWith("/business")) return "business";
  if (pathname.startsWith("/government")) return "government";
  if (pathname.startsWith("/trademarks")) return "trademarks";
  if (pathname.startsWith("/domain-names")) return "domain_names";
  if (pathname.startsWith("/library")) return "library";
  if (pathname.startsWith("/taxes")) return "taxes";
  if (pathname.startsWith("/healthcare")) return "healthcare";
  if (pathname.startsWith("/people")) return "people";
  if (pathname.startsWith("/geography")) return "geography";
  if (pathname.startsWith("/politics")) return "politics";
  if (pathname.startsWith("/nonprofit")) return "nonprofit";
  if (pathname.startsWith("/real-estate")) return "real_estate";
  if (pathname.startsWith("/auctions")) return "auctions";
  if (pathname.startsWith("/torrents")) return "torrents";
  return "media";
}

/** True when path is inside a domain workspace (Sources), not Research/Ask/etc. */
export function workspaceDomainForPath(pathname: string): DomainKey | null {
  if (pathname.startsWith("/media") || pathname.startsWith("/sources")) return "media";
  if (pathname.startsWith("/government")) return "government";
  if (pathname.startsWith("/trademarks")) return "trademarks";
  if (pathname.startsWith("/domain-names")) return "domain_names";
  if (pathname.startsWith("/library")) return "library";
  if (pathname.startsWith("/finance")) return "finance";
  if (pathname.startsWith("/real-estate")) return "real_estate";
  return null;
}

// Field-config for the real_estate records table (column key → header + accessor).
export const REAL_ESTATE_COLUMNS: { key: string; label: string; get: (f: any) => string }[] = [
  { key: "parcel", label: "Parcel", get: (f) => f.parcel_display ?? f.strap ?? "—" },
  { key: "owner", label: "Owner", get: (f) => (f.owners && f.owners[0]) || "—" },
  { key: "situs", label: "Situs Address", get: (f) => f.situs_address ?? "—" },
  { key: "use", label: "Use", get: (f) => f.land_use ?? "—" },
  { key: "acreage", label: "Acreage", get: (f) => (f.acreage != null ? String(f.acreage) : "—") },
  {
    key: "land_value",
    label: "Land Value",
    get: (f) => (f.land_value != null ? `$${Number(f.land_value).toLocaleString()}` : "—"),
  },
];
