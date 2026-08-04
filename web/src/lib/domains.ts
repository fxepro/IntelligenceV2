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
  | "courses"
  | "library"
  | "patents"
  | "songs"
  | "music"
  | "books"
  | "movies"
  | "fiction";

export type DomainDef = {
  key: DomainKey;
  label: string;
  blurb: string;
  home: string;
  enabled: boolean;
};

export const DOMAINS: DomainDef[] = [
  {
    key: "media" as DomainKey,
    label: "Media",
    blurb: "Social posts, videos, websites, podcasts, newsletters and channels",
    home: "/media/sources",
    enabled: true,
  },
  {
    key: "finance" as DomainKey,
    label: "Finance",
    blurb: "Markets, filings, companies, securities and financial signals",
    home: "/finance",
    enabled: false,
  },
  {
    key: "software" as DomainKey,
    label: "Software",
    blurb: "Products, vendors, licenses, codebases and digital platforms",
    home: "/software",
    enabled: false,
  },
  {
    key: "business" as DomainKey,
    label: "Business",
    blurb: "Companies, ownership, operations, filings and commercial signals",
    home: "/business",
    enabled: false,
  },
  {
    key: "government" as DomainKey,
    label: "Government",
    blurb: "Agencies, regulations, procurement, public records and policy",
    home: "/government/sources",
    enabled: true,
  },
  {
    key: "taxes" as DomainKey,
    label: "Taxes",
    blurb: "Rules, filings, jurisdictions, incentives and compliance signals",
    home: "/taxes",
    enabled: false,
  },
  {
    key: "healthcare" as DomainKey,
    label: "Healthcare/Medical",
    blurb: "Providers, facilities, claims, treatments, pharma and clinical signals",
    home: "/healthcare",
    enabled: false,
  },
  {
    key: "people" as DomainKey,
    label: "People",
    blurb: "Individuals, roles, relationships, affiliations and influence signals",
    home: "/people",
    enabled: false,
  },
  {
    key: "geography" as DomainKey,
    label: "Geography",
    blurb: "Places, regions, borders, corridors and spatial economic signals",
    home: "/geography",
    enabled: false,
  },
  {
    key: "politics" as DomainKey,
    label: "Politics",
    blurb: "Campaigns, officials, legislation, elections and civic power signals",
    home: "/politics",
    enabled: false,
  },
  {
    key: "nonprofit" as DomainKey,
    label: "Non-profit",
    blurb: "Orgs, missions, funding, grants, programs and civic initiatives",
    home: "/nonprofit",
    enabled: false,
  },
  {
    key: "news" as DomainKey,
    label: "News",
    blurb: "Published events, claims, organizations, people and developing stories",
    home: "#",
    enabled: false,
  },
  {
    key: "real_estate" as DomainKey,
    label: "Real Estate",
    blurb: "Parcels, buildings, owners, liens, zoning, permits and transactions",
    home: "/real-estate",
    enabled: false,
  },
  {
    key: "auctions" as DomainKey,
    label: "Auctions",
    blurb: "HOA, tax, foreclosure and public auctions — lots, dates, bidders and jurisdictions",
    home: "/auctions",
    enabled: false,
  },
  {
    key: "torrents" as DomainKey,
    label: "Torrents",
    blurb: "Torrent indexes, releases, magnets, swarm activity and distribution signals",
    home: "/torrents",
    enabled: false,
  },
  {
    key: "trademarks" as DomainKey,
    label: "Trademarks",
    blurb: "Marks, owners, classes, status, prosecution history and related brands",
    home: "/trademarks/sources",
    enabled: true,
  },
  {
    key: "domain_names" as DomainKey,
    label: "Domains",
    blurb: "www, .net and other TLDs — registries, WHOIS, DNS, availability and ownership",
    home: "/domain-names/portfolio",
    enabled: true,
  },
  {
    key: "courses" as DomainKey,
    label: "Courses",
    blurb: "Online curricula — YouTube, article hubs, and LMS-style discover and acquire",
    home: "/courses/sources",
    enabled: true,
  },
  {
    key: "library" as DomainKey,
    label: "Library",
    blurb: "Local folders — top-level files and subfolders; view or play assets inside",
    home: "/library/sources",
    enabled: true,
  },
  {
    key: "patents" as DomainKey,
    label: "Patents",
    blurb: "Applications, grants, claims, inventors, assignees, citations and legal status",
    home: "#",
    enabled: false,
  },
  {
    key: "songs" as DomainKey,
    label: "Songs",
    blurb: "Musical compositions and associated writers, publishers and rights",
    home: "#",
    enabled: false,
  },
  {
    key: "music" as DomainKey,
    label: "Music",
    blurb: "Sound recordings, releases, artists, labels and catalogs",
    home: "#",
    enabled: false,
  },
  {
    key: "books" as DomainKey,
    label: "Books",
    blurb: "Published works, editions, authors, publishers, rights and sales signals",
    home: "#",
    enabled: false,
  },
  {
    key: "movies" as DomainKey,
    label: "Movies",
    blurb: "Films, television, video works, production entities and distribution rights",
    home: "#",
    enabled: false,
  },
  {
    key: "fiction" as DomainKey,
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
  if (pathname.startsWith("/courses")) return "courses";
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
  if (pathname.startsWith("/courses")) return "courses";
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
