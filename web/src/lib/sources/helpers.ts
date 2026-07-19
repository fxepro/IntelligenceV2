import type { Platform, Source } from "@/lib/mock-data/sources";
import type { MediaItem } from "@/lib/mock-data/media-items";

/** Map raw discovered items (from discover endpoints) to the UI MediaItem shape. */
export function mapDiscoveredItems(
  raw: any[],
  source: { id: string; platform: Platform; name: string },
): MediaItem[] {
  return raw.map((item) => ({
    id: item.external_id,
    source_id: source.id,
    platform: source.platform,
    external_id: item.external_id,
    canonical_url: item.canonical_url,
    title: item.title,
    thumbnail_url: item.thumbnail_url,
    channel_name: item.channel_name ?? source.name,
    duration_seconds: item.duration_seconds,
    view_count: item.view_count,
    published_at: item.published_at ?? new Date().toISOString(),
    discovered_at: new Date().toISOString(),
    status: "queued" as const,
    content_type: item.content_type as "video" | "short" | undefined,
  }));
}

/** Infer platform + source_type from a pasted URL. */
export function detectPlatform(raw: string): { platform: Platform; source_type: string } | null {
  const u = raw.trim().toLowerCase();
  if (!u) return null;
  if (u.includes("youtube.com") || u.includes("youtu.be"))
    return {
      platform: "youtube",
      source_type: u.includes("/shorts/") ? "youtube_shorts" : "youtube_videos",
    };
  if (u.includes("facebook.com") || u.includes("fb.com") || u.includes("fb.watch"))
    return {
      platform: "facebook",
      source_type: u.includes("/videos") ? "facebook_videos" : "facebook_reels",
    };
  if (u.includes("instagram.com"))
    return { platform: "instagram", source_type: "instagram_reels" };
  if (u.includes("tiktok.com"))
    return { platform: "tiktok", source_type: "tiktok_videos" };
  if (u.includes("x.com") || u.includes("twitter.com"))
    return { platform: "x", source_type: "x_posts" };
  if (
    u.endsWith(".rss") ||
    u.endsWith(".xml") ||
    u.includes("/feed") ||
    u.includes("/rss") ||
    u.includes("podcast")
  )
    return { platform: "podcast", source_type: "rss_feed" };
  if (/^https?:\/\//.test(u)) return { platform: "website", source_type: "sitemap" };
  return null;
}

export function guessNameFromUrl(raw: string): string {
  try {
    const u = new URL(raw.trim());
    const host = u.hostname.replace(/^www\./, "");
    if (host.includes("facebook.com")) {
      const id = u.searchParams.get("id");
      if (id) return `FB ${id}`;
      const parts = u.pathname.split("/").filter(Boolean);
      if (parts[0] === "people" && parts[1]) return decodeURIComponent(parts[1].replace(/-/g, " "));
      if (parts[0] && parts[0] !== "profile.php") return parts[0];
    }
    if (host.includes("youtube.com") || host.includes("youtu.be")) {
      const at = u.pathname.match(/@([^/]+)/);
      if (at) return at[1];
      const ch = u.pathname.match(/\/channel\/([^/]+)/);
      if (ch) return ch[1];
    }
    if (
      host.includes("tiktok.com") ||
      host.includes("instagram.com") ||
      host === "x.com" ||
      host.includes("twitter.com")
    ) {
      const handle = u.pathname.split("/").filter(Boolean)[0];
      if (handle) return handle.replace(/^@/, "");
    }
    return host;
  } catch {
    return "";
  }
}

/** Numeric Facebook page/profile id from a profile.php?id=… URL (or null). */
export function facebookProfileIdFromUrl(url: string | null | undefined): string | null {
  if (!url) return null;
  try {
    const u = new URL(url.trim());
    const id = u.searchParams.get("id");
    if (id && /^\d{8,}$/.test(id)) return id;
  } catch {
    /* ignore */
  }
  const m = String(url).match(/[?&]id=(\d{8,})/i);
  return m?.[1] ?? null;
}

export function mapSource(s: any): Source {
  return {
    id: s.id,
    domain: s.domain ?? "media",
    catalog_id: s.catalog_id ?? null,
    platform: s.platform,
    source_type: s.source_type,
    source_url: s.source_url,
    vanity_url: s.vanity_url ?? null,
    name: s.name ?? s.source_url,
    status: s.status,
    autorun: Boolean(s.autorun),
    auto_transcribe: Boolean(s.auto_transcribe),
    transcription_done: Boolean(s.transcription_done),
    transcription_completed: Number(s.transcription_completed ?? 0),
    category: s.category ?? null,
    tags: Array.isArray(s.tags) ? s.tags.map((tag: unknown) => String(tag)).filter(Boolean) : [],
    priority: (s.priority as Source["priority"]) || "normal",
    last_checked: s.last_checked,
    error_message: s.error_message,
    item_count: s.item_count ?? s.reel_count ?? s.video_count ?? 0,
    streams: (s.streams ?? []).map((stream: any) => ({
      id: stream.id,
      stream_type: stream.stream_type,
      stream_url: stream.stream_url,
      enabled: Boolean(stream.enabled),
      item_count: stream.item_count ?? 0,
      last_checked: stream.last_checked,
      error_message: stream.error_message,
    })),
    subscriber_count: s.subscriber_count,
    video_count: s.video_count,
    total_views: s.total_views,
    joined_at: s.joined_at,
    description: s.description,
    created_at: s.created_at,
  };
}

export const PLATFORM_OPTIONS: { id: Platform; label: string; hint: string }[] = [
  { id: "facebook", label: "Facebook", hint: "Page / profile reels" },
  { id: "youtube", label: "YouTube", hint: "Channel or playlist" },
  { id: "instagram", label: "Instagram", hint: "Public profile" },
  { id: "tiktok", label: "TikTok", hint: "Creator profile" },
  { id: "x", label: "X", hint: "Public profile / posts" },
  { id: "podcast", label: "Podcast", hint: "RSS / feed URL" },
  { id: "rss", label: "RSS", hint: "Any RSS / Atom feed" },
  { id: "website", label: "Website", hint: "Site or sitemap" },
];

export const PLATFORM_GUIDES: Record<
  Platform,
  { title: string; bullets: string[]; examples: string[] }
> = {
  facebook: {
    title: "Facebook page or profile",
    bullets: [
      "Paste the vanity page URL from the address bar (e.g. facebook.com/PageName).",
      "On save we read page source for page_id next to page_id_type and store profile.php?id=….",
      "Both vanity and stable ID URL are kept on the channel.",
    ],
    examples: [
      "https://www.facebook.com/Lockedinangelo",
      "https://www.facebook.com/profile.php?id=61590653349974",
    ],
  },
  youtube: {
    title: "YouTube channel or playlist",
    bullets: [
      "Use a channel URL (@handle, /channel/…, or /c/…) or a playlist link.",
      "Discovery pulls recent uploads; Shorts and long-form both catalog.",
    ],
    examples: [
      "https://www.youtube.com/@SomeChannel",
      "https://www.youtube.com/playlist?list=PLxxxxxxxx",
    ],
  },
  instagram: {
    title: "Instagram profile",
    bullets: ["Public profile URL only. Private accounts can’t be scraped."],
    examples: ["https://www.instagram.com/username"],
  },
  tiktok: {
    title: "TikTok creator",
    bullets: ["Paste the @username profile URL."],
    examples: ["https://www.tiktok.com/@username"],
  },
  x: {
    title: "X profile",
    bullets: [
      "Paste a public X profile URL (x.com/username) or a specific post URL.",
      "X may require authenticated access for complete profile history.",
    ],
    examples: ["https://x.com/username"],
  },
  podcast: {
    title: "Podcast feed",
    bullets: ["Use the show’s RSS feed URL (often ends in .xml or /feed)."],
    examples: ["https://feeds.example.com/show.xml"],
  },
  rss: {
    title: "RSS / Atom feed",
    bullets: ["Any public feed URL. We’ll pull new entries on discover."],
    examples: ["https://example.com/feed"],
  },
  website: {
    title: "Website",
    bullets: ["Homepage or sitemap URL. We’ll probe common feed paths first."],
    examples: ["https://example.com", "https://example.com/sitemap.xml"],
  },
};

export const SOURCE_TYPES_BY_PLATFORM: Record<Platform, { value: string; label: string }[]> = {
  facebook: [
    { value: "facebook_reels", label: "Facebook Reels" },
    { value: "facebook_videos", label: "Facebook Videos" },
  ],
  youtube: [
    { value: "youtube_videos", label: "YouTube Videos" },
    { value: "youtube_shorts", label: "YouTube Shorts" },
  ],
  instagram: [{ value: "instagram_reels", label: "Instagram Reels" }],
  tiktok: [{ value: "tiktok_videos", label: "TikTok Videos" }],
  x: [{ value: "x_posts", label: "X Posts" }],
  podcast: [{ value: "rss_feed", label: "RSS Feed" }],
  rss: [{ value: "rss_feed", label: "RSS Feed" }],
  website: [{ value: "sitemap", label: "Site / Sitemap" }],
};

export function sourceTypeLabel(sourceType: string): string {
  for (const options of Object.values(SOURCE_TYPES_BY_PLATFORM)) {
    const match = options.find((option) => option.value === sourceType);
    if (match) return match.label;
  }
  return sourceType.replaceAll("_", " ");
}

export function formatFileSize(bytes: number | null | undefined): string {
  if (bytes == null || bytes <= 0) return "—";
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  return `${(bytes / (1024 * 1024 * 1024)).toFixed(2)} GB`;
}

export function pipelineStatusLabel(status: string | null | undefined): string {
  if (!status || status === "pending") return "Pending";
  if (status === "running" || status === "queued" || status === "in_progress") return "Queued";
  if (status === "completed") return "Done";
  if (status === "failed") return "Failed";
  return status.replaceAll("_", " ");
}

/** Labels are rank 1–5 (1 = highest priority). */
export const PRIORITY_OPTIONS: {
  value: Source["priority"];
  label: string;
  title: string;
}[] = [
  { value: "urgent", label: "1", title: "1 — highest" },
  { value: "high", label: "2", title: "2" },
  { value: "normal", label: "3", title: "3 — normal" },
  { value: "low", label: "4", title: "4" },
  { value: "lowest", label: "5", title: "5 — lowest" },
];

export function parseTagsInput(raw: string): string[] {
  const seen = new Set<string>();
  const out: string[] = [];
  for (const part of raw.split(/[,;\n]/)) {
    const tag = part.trim().replace(/\s+/g, " ");
    if (!tag) continue;
    const key = tag.toLowerCase();
    if (seen.has(key)) continue;
    seen.add(key);
    out.push(tag.slice(0, 64));
    if (out.length >= 20) break;
  }
  return out;
}

export function formatTagsInput(tags: string[] | undefined | null): string {
  return (tags ?? []).join(", ");
}
