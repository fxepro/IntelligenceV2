export type Platform =
  | "youtube"
  | "facebook"
  | "x"
  | "instagram"
  | "tiktok"
  | "rss"
  | "podcast"
  | "website"
  | "government";
export type SourceType =
  | "facebook_reels"
  | "facebook_videos"
  | "youtube_videos"
  | "youtube_shorts"
  | "x_posts"
  | "instagram_reels"
  | "tiktok_videos"
  | "rss_feed"
  | "sitemap"
  | "website"
  | "channel"
  | "playlist"
  | "profile";
export type SourceStatus = "active" | "paused" | "error";
/** 1=urgent (highest) … 5=lowest — stored as enum names in the API. */
export type SourcePriority = "urgent" | "high" | "normal" | "low" | "lowest";

export interface SourceStream {
  id: string;
  stream_type: SourceType;
  stream_url?: string | null;
  enabled: boolean;
  item_count: number;
  last_checked?: string | null;
  error_message?: string | null;
}

export interface Source {
  id: string;
  domain?: string;
  /** Stable per-domain id: MEDIA-0001, GOV-0001, … */
  catalog_id?: string | null;
  platform: Platform;
  source_type: SourceType;
  source_url: string;
  /** Facebook vanity URL as entered; source_url holds profile.php?id=… when resolved. */
  vanity_url?: string | null;
  name: string;
  status: SourceStatus;
  autorun?: boolean;
  auto_transcribe?: boolean;
  /** True when every catalog item has transcription_status=completed. */
  transcription_done?: boolean;
  transcription_completed?: number;
  /** Catalog taxonomy (e.g. procurement). */
  category?: string | null;
  tags?: string[];
  priority?: SourcePriority;
  last_checked: string | null;
  item_count?: number;
  streams?: SourceStream[];
  error_message?: string | null;
  created_at: string;
  // Optional channel metadata (populated after discovery or manual lookup)
  subscriber_count?: number | null;
  video_count?: number | null;
  total_views?: number | null;
  joined_at?: string | null;
  description?: string | null;
  /** Trademark machine-channel readiness: api | bulk | api_bulk (only ~17 sources). */
  connect_readiness?: "api" | "bulk" | "api_bulk" | null;
}

export function formatSubscribers(n: number | null | undefined): string {
  if (!n) return "—";
  if (n >= 1000000) return `${(n / 1000000).toFixed(2)}M`;
  if (n >= 1000) return `${(n / 1000).toFixed(2)}K`;
  return n.toLocaleString();
}

export const MOCK_SOURCES: Source[] = [
  {
    id: "1",
    platform: "youtube",
    source_type: "channel",
    source_url: "https://www.youtube.com/@UnethicalStickman-u7p",
    name: "UnethicalStickman",
    status: "active",
    last_checked: null,
    item_count: 0,
    created_at: new Date().toISOString(),
  },
  {
    id: "2",
    platform: "youtube",
    source_type: "channel",
    source_url: "https://www.youtube.com/@DirtyDollarsUg",
    name: "DirtyDollarsUg",
    status: "active",
    last_checked: null,
    item_count: 0,
    created_at: new Date().toISOString(),
  },
  {
    id: "3",
    platform: "youtube",
    source_type: "channel",
    source_url: "https://www.youtube.com/@MrProfessorFinance",
    name: "MrProfessorFinance",
    status: "active",
    last_checked: null,
    item_count: 0,
    created_at: new Date().toISOString(),
  },
  {
    id: "4",
    platform: "youtube",
    source_type: "channel",
    source_url: "https://www.youtube.com/@DoggieLearns",
    name: "DoggieLearns",
    status: "active",
    last_checked: null,
    item_count: 0,
    created_at: new Date().toISOString(),
  },
  {
    id: "5",
    platform: "youtube",
    source_type: "channel",
    source_url: "https://www.youtube.com/@Highfinance_View",
    name: "Highfinance_View",
    status: "active",
    last_checked: null,
    item_count: 23,
    subscriber_count: 8490,
    video_count: 23,
    total_views: 557622,
    joined_at: "2026-04-30",
    created_at: new Date().toISOString(),
  },
  {
    id: "6",
    platform: "facebook",
    source_type: "profile",
    source_url: "https://www.facebook.com/brainlagmemes",
    name: "BrainLagMemes",
    status: "active",
    last_checked: null,
    item_count: 0,
    created_at: new Date().toISOString(),
  },
  {
    id: "7",
    platform: "facebook",
    source_type: "profile",
    source_url: "https://www.facebook.com/profile.php?id=61582200839650&sk=reels_tab",
    name: "Tipper",
    status: "active",
    last_checked: null,
    item_count: 0,
    created_at: new Date().toISOString(),
  },
  {
    id: "8",
    platform: "facebook",
    source_type: "profile",
    source_url: "https://www.facebook.com/profile.php?id=61580056596919",
    name: "MadeInTheUSA",
    status: "active",
    last_checked: null,
    item_count: 0,
    created_at: new Date().toISOString(),
  },
  {
    id: "9",
    platform: "facebook",
    source_type: "profile",
    source_url: "https://www.facebook.com/RichStickman",
    name: "RichStickman",
    status: "active",
    last_checked: null,
    item_count: 0,
    created_at: new Date().toISOString(),
  },
  {
    id: "10",
    platform: "facebook",
    source_type: "profile",
    source_url: "https://www.facebook.com/profile.php?id=61582458930833&sk=reels_tab",
    name: "MrStickmanTKK",
    status: "active",
    last_checked: null,
    item_count: 0,
    created_at: new Date().toISOString(),
  },
  {
    id: "11",
    platform: "facebook",
    source_type: "profile",
    source_url: "https://www.facebook.com/profile.php?id=61584040833501",
    name: "Silent Profit",
    status: "active",
    last_checked: null,
    item_count: 0,
    created_at: new Date().toISOString(),
  },
  {
    id: "12",
    platform: "facebook",
    source_type: "profile",
    source_url: "https://www.facebook.com/profile.php?id=61588697743912",
    name: "Tips and Tricks",
    status: "active",
    last_checked: null,
    item_count: 0,
    created_at: new Date().toISOString(),
  },
  {
    id: "13",
    platform: "tiktok",
    source_type: "profile",
    source_url: "https://www.tiktok.com/@tips.and.tricks402",
    name: "tips.and.tricks402",
    status: "active",
    last_checked: null,
    item_count: 0,
    created_at: new Date().toISOString(),
  },
];

export const PLATFORM_LABELS: Record<Platform, string> = {
  youtube: "YouTube",
  facebook: "Facebook",
  x: "X",
  instagram: "Instagram",
  tiktok: "TikTok",
  rss: "RSS",
  podcast: "Podcast",
  website: "Website",
  government: "Government",
};

export const PLATFORM_COLORS: Record<Platform, string> = {
  youtube: "bg-red-500/10 text-red-400 border-red-500/20",
  facebook: "bg-blue-500/10 text-blue-400 border-blue-500/20",
  x: "bg-zinc-500/10 text-foreground border-zinc-500/30",
  instagram: "bg-pink-500/10 text-pink-400 border-pink-500/20",
  tiktok: "bg-slate-500/10 text-slate-300 border-slate-500/20",
  rss: "bg-orange-500/10 text-orange-400 border-orange-500/20",
  podcast: "bg-purple-500/10 text-purple-400 border-purple-500/20",
  website: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
  government: "bg-amber-500/10 text-amber-700 border-amber-500/25",
};
