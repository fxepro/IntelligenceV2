import { NextResponse } from "next/server";
import net from "net";
import { execFile } from "child_process";
import { promisify } from "util";
import path from "path";
import { BACKEND_URL } from "@/lib/api-base";

const execFileAsync = promisify(execFile);

const API_BASE = BACKEND_URL;
const V2_ROOT = path.resolve(process.cwd(), "..");

function tcpOk(port: number, host = "127.0.0.1", timeoutMs = 800): Promise<boolean> {
  return new Promise((resolve) => {
    const socket = net.connect({ port, host }, () => {
      socket.end();
      resolve(true);
    });
    socket.on("error", () => resolve(false));
    socket.setTimeout(timeoutMs, () => {
      socket.destroy();
      resolve(false);
    });
  });
}

async function httpOk(url: string): Promise<boolean> {
  try {
    const res = await fetch(url, { signal: AbortSignal.timeout(1500) });
    return res.ok;
  } catch {
    return false;
  }
}

async function countCeleryProcesses(kind: "worker" | "beat"): Promise<{ ok: boolean; detail: string }> {
  const redisUp = await tcpOk(6379);
  if (!redisUp) {
    return {
      ok: false,
      detail: kind === "beat" ? "redis down — cannot probe beat" : "redis down — cannot probe workers",
    };
  }
  const match =
    kind === "beat"
      ? "$_.CommandLine -match 'celery' -and $_.CommandLine -match 'beat'"
      : "$_.CommandLine -match 'celery' -and $_.CommandLine -match 'worker' -and $_.CommandLine -notmatch 'beat'";
  try {
    const { stdout } = await execFileAsync(
      "powershell",
      [
        "-NoProfile",
        "-Command",
        `Get-CimInstance Win32_Process -Filter "Name = 'python.exe'" | Where-Object { $_.CommandLine -and (${match}) } | Measure-Object | Select-Object -ExpandProperty Count`,
      ],
      { timeout: 5000, windowsHide: true },
    );
    const n = parseInt(String(stdout).trim(), 10) || 0;
    if (n > 0) {
      return {
        ok: true,
        detail: kind === "beat" ? `${n} beat process(es)` : `${n} worker process(es)`,
      };
    }
    return {
      ok: false,
      detail: kind === "beat" ? "no celery beat process" : "no celery worker process",
    };
  } catch (e: any) {
    return { ok: false, detail: e?.message ?? `${kind} probe failed` };
  }
}

export async function GET() {
  const [apiTcp, apiHealth, postgres, redis, web, celery, beat] = await Promise.all([
    tcpOk(8000),
    httpOk(`${API_BASE.replace(/\/$/, "")}/api/v1/health`),
    tcpOk(5432),
    tcpOk(6379),
    tcpOk(3000),
    countCeleryProcesses("worker"),
    countCeleryProcesses("beat"),
  ]);

  const apiDocs = `${API_BASE.replace(/\/$/, "")}/docs`;

  // Shells match v2/.startup (plus Postgres as external dependency).
  const processes = [
    {
      id: "api",
      label: "API",
      status: apiHealth || apiTcp ? "up" : "down",
      detail: apiHealth ? "health ok" : apiTcp ? "port 8000 open" : "not on :8000",
      docs_url: apiDocs,
      can_start: true,
      can_stop: true,
    },
    {
      id: "postgres",
      label: "PostgreSQL",
      status: postgres ? "up" : "down",
      detail: postgres ? "port 5432" : "not listening",
      can_start: false,
      can_stop: false,
    },
    {
      id: "redis",
      label: "Redis (Celery broker)",
      status: redis ? "up" : "down",
      detail: redis ? "port 6379" : "not listening",
      can_start: true,
      can_stop: true,
    },
    {
      id: "celery",
      label: "Celery workers",
      status: celery.ok ? "up" : "down",
      detail: celery.detail,
      can_start: true,
      can_stop: true,
    },
    {
      id: "celery_beat",
      label: "Celery Beat",
      status: beat.ok ? "up" : "down",
      detail: beat.detail,
      can_start: true,
      can_stop: true,
    },
    {
      id: "web",
      label: "Web (Next.js)",
      status: web ? "up" : "down",
      detail: web ? "port 3000" : "not listening",
      can_start: true,
      can_stop: true,
    },
  ];

  // Domain control planes — alphabetical by label (matches docs/domains)
  const control_planes = [
    {
      id: "media",
      label: "Media",
      status: "active",
      blurb: "Social posts, videos, websites, podcasts, newsletters and channels",
      home: "/media/sources",
      docs_url: apiDocs,
    },
    {
      id: "finance",
      label: "Finance",
      status: "planned",
      blurb: "Markets, filings, companies, securities and financial signals",
      home: "/finance",
      docs_url: null,
    },
    {
      id: "software",
      label: "Software",
      status: "planned",
      blurb: "Products, vendors, licenses, codebases and digital platforms",
      home: "/software",
      docs_url: null,
    },
    {
      id: "business",
      label: "Business",
      status: "planned",
      blurb: "Companies, ownership, operations, filings and commercial signals",
      home: "/business",
      docs_url: null,
    },
    {
      id: "government",
      label: "Government",
      status: "active",
      blurb: "Agencies, regulations, procurement, public records and policy",
      home: "/government/sources",
      docs_url: null,
    },
    {
      id: "taxes",
      label: "Taxes",
      status: "planned",
      blurb: "Rules, filings, jurisdictions, incentives and compliance signals",
      home: "/taxes",
      docs_url: null,
    },
    {
      id: "healthcare",
      label: "Healthcare/Medical",
      status: "planned",
      blurb: "Providers, facilities, claims, treatments, pharma and clinical signals",
      home: "/healthcare",
      docs_url: null,
    },
    {
      id: "people",
      label: "People",
      status: "planned",
      blurb: "Individuals, roles, relationships, affiliations and influence signals",
      home: "/people",
      docs_url: null,
    },
    {
      id: "geography",
      label: "Geography",
      status: "planned",
      blurb: "Places, regions, borders, corridors and spatial economic signals",
      home: "/geography",
      docs_url: null,
    },
    {
      id: "politics",
      label: "Politics",
      status: "planned",
      blurb: "Campaigns, officials, legislation, elections and civic power signals",
      home: "/politics",
      docs_url: null,
    },
    {
      id: "nonprofit",
      label: "Non-profit",
      status: "planned",
      blurb: "Orgs, missions, funding, grants, programs and civic initiatives",
      home: "/nonprofit",
      docs_url: null,
    },
    {
      id: "news",
      label: "News",
      status: "planned",
      blurb: "Published events, claims, organizations, people and developing stories",
      home: null,
      docs_url: null,
    },
    {
      id: "real_estate",
      label: "Real Estate",
      status: "planned",
      blurb: "Parcels, buildings, owners, liens, zoning, permits and transactions",
      home: "/real-estate",
      docs_url: null,
    },
    {
      id: "auctions",
      label: "Auctions",
      status: "planned",
      blurb: "HOA, tax, foreclosure and public auctions — lots, dates, bidders and jurisdictions",
      home: "/auctions",
      docs_url: null,
    },
    {
      id: "torrents",
      label: "Torrents",
      status: "planned",
      blurb: "Torrent indexes, releases, magnets, swarm activity and distribution signals",
      home: "/torrents",
      docs_url: null,
    },
    {
      id: "trademarks",
      label: "Trademarks",
      status: "active",
      blurb: "Marks, owners, classes, status, prosecution history and related brands",
      home: "/trademarks/sources",
      docs_url: null,
    },
    {
      id: "domain_names",
      label: "Domains",
      status: "active",
      blurb: "www, .net and other TLDs — registries, WHOIS, DNS, availability and ownership",
      home: "/domain-names/portfolio",
      docs_url: null,
    },
    {
      id: "library",
      label: "Courses",
      status: "active",
      blurb: "Lessons from courses, books, and videos — text, PDF, and video by topic",
      home: "/library/sources",
      docs_url: null,
    },
    {
      id: "patents",
      label: "Patents",
      status: "planned",
      blurb: "Applications, grants, claims, inventors, assignees, citations and legal status",
      home: null,
      docs_url: null,
    },
    {
      id: "songs",
      label: "Songs",
      status: "planned",
      blurb: "Musical compositions and associated writers, publishers and rights",
      home: null,
      docs_url: null,
    },
    {
      id: "music",
      label: "Music",
      status: "planned",
      blurb: "Sound recordings, releases, artists, labels and catalogs",
      home: null,
      docs_url: null,
    },
    {
      id: "books",
      label: "Books",
      status: "planned",
      blurb: "Published works, editions, authors, publishers, rights and sales signals",
      home: null,
      docs_url: null,
    },
    {
      id: "movies",
      label: "Movies",
      status: "planned",
      blurb: "Films, television, video works, production entities and distribution rights",
      home: null,
      docs_url: null,
    },
    {
      id: "fiction",
      label: "Fiction",
      status: "planned",
      blurb: "Unpublished or independently created stories, characters, settings and story worlds",
      home: null,
      docs_url: null,
    },
  ].sort((a, b) => a.label.localeCompare(b.label));

  return NextResponse.json({
    processes,
    control_planes,
    v2_root: V2_ROOT,
  });
}
