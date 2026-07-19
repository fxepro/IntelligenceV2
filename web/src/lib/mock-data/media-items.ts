import { Platform } from "./sources";

export type MediaStatus = "queued" | "downloading" | "transcribing" | "analyzing" | "completed" | "failed";
export type ContentType = "video" | "short";

export interface MediaItem {
  id: string;
  source_id: string;
  platform: Platform;
  external_id: string;
  canonical_url: string;
  title: string;
  thumbnail_url: string;
  channel_name: string;
  duration_seconds: number | null;
  view_count: number | null;
  published_at: string;
  discovered_at: string;
  status: MediaStatus;
  content_type?: ContentType;
}

const now = new Date();
const daysAgo = (n: number) => new Date(now.getTime() - n * 86400000).toISOString();

export const MOCK_MEDIA_ITEMS: MediaItem[] = [
  // ── UnethicalStickman (source_id: "1") ──────────────────────────────────
  {
    id: "m101", source_id: "1", platform: "youtube", external_id: "aBcD1234001",
    canonical_url: "https://www.youtube.com/watch?v=aBcD1234001",
    title: "How I Made $12,000 In One Week Doing This",
    thumbnail_url: "https://picsum.photos/seed/ys1/320/180",
    channel_name: "UnethicalStickman", duration_seconds: 743, view_count: 412000,
    published_at: daysAgo(3), discovered_at: daysAgo(0), status: "queued",
  },
  {
    id: "m102", source_id: "1", platform: "youtube", external_id: "aBcD1234002",
    canonical_url: "https://www.youtube.com/watch?v=aBcD1234002",
    title: "Stop Losing Money On These 5 Mistakes",
    thumbnail_url: "https://picsum.photos/seed/ys2/320/180",
    channel_name: "UnethicalStickman", duration_seconds: 521, view_count: 289000,
    published_at: daysAgo(10), discovered_at: daysAgo(0), status: "queued",
  },
  {
    id: "m103", source_id: "1", platform: "youtube", external_id: "aBcD1234003",
    canonical_url: "https://www.youtube.com/watch?v=aBcD1234003",
    title: "The Secret They Don't Want You To Know About Investing",
    thumbnail_url: "https://picsum.photos/seed/ys3/320/180",
    channel_name: "UnethicalStickman", duration_seconds: 634, view_count: 178000,
    published_at: daysAgo(18), discovered_at: daysAgo(0), status: "queued",
  },
  {
    id: "m104", source_id: "1", platform: "youtube", external_id: "aBcD1234004",
    canonical_url: "https://www.youtube.com/watch?v=aBcD1234004",
    title: "Why 99% Of People Are Broke (And How To Fix It)",
    thumbnail_url: "https://picsum.photos/seed/ys4/320/180",
    channel_name: "UnethicalStickman", duration_seconds: 892, view_count: 534000,
    published_at: daysAgo(25), discovered_at: daysAgo(0), status: "queued",
  },
  {
    id: "m105", source_id: "1", platform: "youtube", external_id: "aBcD1234005",
    canonical_url: "https://www.youtube.com/watch?v=aBcD1234005",
    title: "I Tested 10 Money Hacks So You Don't Have To",
    thumbnail_url: "https://picsum.photos/seed/ys5/320/180",
    channel_name: "UnethicalStickman", duration_seconds: 415, view_count: 91000,
    published_at: daysAgo(32), discovered_at: daysAgo(0), status: "queued",
  },

  // ── DirtyDollarsUg (source_id: "2") ──────────────────────────────────
  {
    id: "m201", source_id: "2", platform: "youtube", external_id: "dDuG2234001",
    canonical_url: "https://www.youtube.com/watch?v=dDuG2234001",
    title: "Passive Income Streams That Actually Work In 2025",
    thumbnail_url: "https://picsum.photos/seed/dd1/320/180",
    channel_name: "DirtyDollarsUg", duration_seconds: 1124, view_count: 67000,
    published_at: daysAgo(5), discovered_at: daysAgo(0), status: "queued",
  },
  {
    id: "m202", source_id: "2", platform: "youtube", external_id: "dDuG2234002",
    canonical_url: "https://www.youtube.com/watch?v=dDuG2234002",
    title: "How Broke People Think vs How Rich People Think",
    thumbnail_url: "https://picsum.photos/seed/dd2/320/180",
    channel_name: "DirtyDollarsUg", duration_seconds: 678, view_count: 142000,
    published_at: daysAgo(12), discovered_at: daysAgo(0), status: "queued",
  },
  {
    id: "m203", source_id: "2", platform: "youtube", external_id: "dDuG2234003",
    canonical_url: "https://www.youtube.com/watch?v=dDuG2234003",
    title: "Crypto Is Dead. Here's What's Next.",
    thumbnail_url: "https://picsum.photos/seed/dd3/320/180",
    channel_name: "DirtyDollarsUg", duration_seconds: 953, view_count: 223000,
    published_at: daysAgo(20), discovered_at: daysAgo(0), status: "queued",
  },
  {
    id: "m204", source_id: "2", platform: "youtube", external_id: "dDuG2234004",
    canonical_url: "https://www.youtube.com/watch?v=dDuG2234004",
    title: "Stock Market Crash Coming? What The Data Says",
    thumbnail_url: "https://picsum.photos/seed/dd4/320/180",
    channel_name: "DirtyDollarsUg", duration_seconds: 812, view_count: 309000,
    published_at: daysAgo(28), discovered_at: daysAgo(0), status: "queued",
  },

  // ── MrProfessorFinance (source_id: "3") ──────────────────────────────────
  {
    id: "m301", source_id: "3", platform: "youtube", external_id: "mPF3334001",
    canonical_url: "https://www.youtube.com/watch?v=mPF3334001",
    title: "Compound Interest Explained For Beginners",
    thumbnail_url: "https://picsum.photos/seed/mp1/320/180",
    channel_name: "MrProfessorFinance", duration_seconds: 1456, view_count: 892000,
    published_at: daysAgo(7), discovered_at: daysAgo(0), status: "queued",
  },
  {
    id: "m302", source_id: "3", platform: "youtube", external_id: "mPF3334002",
    canonical_url: "https://www.youtube.com/watch?v=mPF3334002",
    title: "Index Funds vs ETFs: The Real Difference",
    thumbnail_url: "https://picsum.photos/seed/mp2/320/180",
    channel_name: "MrProfessorFinance", duration_seconds: 1203, view_count: 445000,
    published_at: daysAgo(14), discovered_at: daysAgo(0), status: "queued",
  },
  {
    id: "m303", source_id: "3", platform: "youtube", external_id: "mPF3334003",
    canonical_url: "https://www.youtube.com/watch?v=mPF3334003",
    title: "How To Build A $1M Portfolio On A $50k Salary",
    thumbnail_url: "https://picsum.photos/seed/mp3/320/180",
    channel_name: "MrProfessorFinance", duration_seconds: 1872, view_count: 1240000,
    published_at: daysAgo(21), discovered_at: daysAgo(0), status: "queued",
  },
  {
    id: "m304", source_id: "3", platform: "youtube", external_id: "mPF3334004",
    canonical_url: "https://www.youtube.com/watch?v=mPF3334004",
    title: "The 4% Rule Is Broken. Here's The New Math.",
    thumbnail_url: "https://picsum.photos/seed/mp4/320/180",
    channel_name: "MrProfessorFinance", duration_seconds: 1634, view_count: 678000,
    published_at: daysAgo(30), discovered_at: daysAgo(0), status: "queued",
  },
  {
    id: "m305", source_id: "3", platform: "youtube", external_id: "mPF3334005",
    canonical_url: "https://www.youtube.com/watch?v=mPF3334005",
    title: "Roth IRA vs 401k In 2025: Which Wins?",
    thumbnail_url: "https://picsum.photos/seed/mp5/320/180",
    channel_name: "MrProfessorFinance", duration_seconds: 987, view_count: 334000,
    published_at: daysAgo(38), discovered_at: daysAgo(0), status: "queued",
  },

  // ── DoggieLearns (source_id: "4") ──────────────────────────────────
  {
    id: "m401", source_id: "4", platform: "youtube", external_id: "dL4444001",
    canonical_url: "https://www.youtube.com/watch?v=dL4444001",
    title: "5 Ways To Make Money Online Without Investment",
    thumbnail_url: "https://picsum.photos/seed/dl1/320/180",
    channel_name: "DoggieLearns", duration_seconds: 834, view_count: 56000,
    published_at: daysAgo(4), discovered_at: daysAgo(0), status: "queued",
  },
  {
    id: "m402", source_id: "4", platform: "youtube", external_id: "dL4444002",
    canonical_url: "https://www.youtube.com/watch?v=dL4444002",
    title: "Learning Python In 30 Days — What I Learned",
    thumbnail_url: "https://picsum.photos/seed/dl2/320/180",
    channel_name: "DoggieLearns", duration_seconds: 2134, view_count: 128000,
    published_at: daysAgo(16), discovered_at: daysAgo(0), status: "queued",
  },
  {
    id: "m403", source_id: "4", platform: "youtube", external_id: "dL4444003",
    canonical_url: "https://www.youtube.com/watch?v=dL4444003",
    title: "AI Tools That Will Replace Your Job (And What To Do)",
    thumbnail_url: "https://picsum.photos/seed/dl3/320/180",
    channel_name: "DoggieLearns", duration_seconds: 1245, view_count: 89000,
    published_at: daysAgo(23), discovered_at: daysAgo(0), status: "queued",
  },

  // ── Highfinance_View (source_id: "5") ──────────────────────────────────
  {
    id: "m501", source_id: "5", platform: "youtube", external_id: "hFv5554001",
    canonical_url: "https://www.youtube.com/watch?v=hFv5554001",
    title: "Why The Fed Is Lying About Inflation",
    thumbnail_url: "https://picsum.photos/seed/hf1/320/180",
    channel_name: "Highfinance_View", duration_seconds: 1567, view_count: 234000,
    published_at: daysAgo(6), discovered_at: daysAgo(0), status: "queued",
  },
  {
    id: "m502", source_id: "5", platform: "youtube", external_id: "hFv5554002",
    canonical_url: "https://www.youtube.com/watch?v=hFv5554002",
    title: "BlackRock Buying Everything. Here's Why.",
    thumbnail_url: "https://picsum.photos/seed/hf2/320/180",
    channel_name: "Highfinance_View", duration_seconds: 1823, view_count: 567000,
    published_at: daysAgo(15), discovered_at: daysAgo(0), status: "queued",
  },
  {
    id: "m503", source_id: "5", platform: "youtube", external_id: "hFv5554003",
    canonical_url: "https://www.youtube.com/watch?v=hFv5554003",
    title: "The Dollar Is Collapsing And Nobody's Talking About It",
    thumbnail_url: "https://picsum.photos/seed/hf3/320/180",
    channel_name: "Highfinance_View", duration_seconds: 2201, view_count: 812000,
    published_at: daysAgo(22), discovered_at: daysAgo(0), status: "queued",
  },
  {
    id: "m504", source_id: "5", platform: "youtube", external_id: "hFv5554004",
    canonical_url: "https://www.youtube.com/watch?v=hFv5554004",
    title: "Gold vs Bitcoin: The 2025 Hedge Strategy",
    thumbnail_url: "https://picsum.photos/seed/hf4/320/180",
    channel_name: "Highfinance_View", duration_seconds: 1389, view_count: 345000,
    published_at: daysAgo(29), discovered_at: daysAgo(0), status: "queued",
  },

  // ── BrainLagMemes / Facebook Reels (source_id: "6") ──────────────────
  {
    id: "m601", source_id: "6", platform: "facebook", external_id: "fb_blm_001",
    canonical_url: "https://www.facebook.com/brainlagmemes/videos/1001",
    title: "When You Check Your Bank Account On Monday",
    thumbnail_url: "https://picsum.photos/seed/fb1/320/180",
    channel_name: "BrainLagMemes", duration_seconds: 32, view_count: 1200000,
    published_at: daysAgo(2), discovered_at: daysAgo(0), status: "queued",
  },
  {
    id: "m602", source_id: "6", platform: "facebook", external_id: "fb_blm_002",
    canonical_url: "https://www.facebook.com/brainlagmemes/videos/1002",
    title: "Inflation Hit Different This Month",
    thumbnail_url: "https://picsum.photos/seed/fb2/320/180",
    channel_name: "BrainLagMemes", duration_seconds: 28, view_count: 870000,
    published_at: daysAgo(8), discovered_at: daysAgo(0), status: "queued",
  },
  {
    id: "m603", source_id: "6", platform: "facebook", external_id: "fb_blm_003",
    canonical_url: "https://www.facebook.com/brainlagmemes/videos/1003",
    title: "Investing $100 vs Investing $10,000",
    thumbnail_url: "https://picsum.photos/seed/fb3/320/180",
    channel_name: "BrainLagMemes", duration_seconds: 45, view_count: 430000,
    published_at: daysAgo(15), discovered_at: daysAgo(0), status: "queued",
  },

  // ── RichStickman / Facebook (source_id: "9") ──────────────────────────
  {
    id: "m901", source_id: "9", platform: "facebook", external_id: "fb_rs_001",
    canonical_url: "https://www.facebook.com/RichStickman/videos/2001",
    title: "How I Made My First $100k Online",
    thumbnail_url: "https://picsum.photos/seed/rs1/320/180",
    channel_name: "RichStickman", duration_seconds: 58, view_count: 2300000,
    published_at: daysAgo(1), discovered_at: daysAgo(0), status: "queued",
  },
  {
    id: "m902", source_id: "9", platform: "facebook", external_id: "fb_rs_002",
    canonical_url: "https://www.facebook.com/RichStickman/videos/2002",
    title: "3 Businesses You Can Start With $0",
    thumbnail_url: "https://picsum.photos/seed/rs2/320/180",
    channel_name: "RichStickman", duration_seconds: 52, view_count: 1870000,
    published_at: daysAgo(6), discovered_at: daysAgo(0), status: "queued",
  },
  {
    id: "m903", source_id: "9", platform: "facebook", external_id: "fb_rs_003",
    canonical_url: "https://www.facebook.com/RichStickman/videos/2003",
    title: "The Mindset Shift That Changed Everything",
    thumbnail_url: "https://picsum.photos/seed/rs3/320/180",
    channel_name: "RichStickman", duration_seconds: 44, view_count: 940000,
    published_at: daysAgo(13), discovered_at: daysAgo(0), status: "queued",
  },
  {
    id: "m904", source_id: "9", platform: "facebook", external_id: "fb_rs_004",
    canonical_url: "https://www.facebook.com/RichStickman/videos/2004",
    title: "Why Your 9-5 Is Keeping You Poor",
    thumbnail_url: "https://picsum.photos/seed/rs4/320/180",
    channel_name: "RichStickman", duration_seconds: 61, view_count: 3100000,
    published_at: daysAgo(19), discovered_at: daysAgo(0), status: "queued",
  },

  // ── Silent Profit / Facebook (source_id: "11") ──────────────────────────
  {
    id: "m1101", source_id: "11", platform: "facebook", external_id: "fb_sp_001",
    canonical_url: "https://www.facebook.com/profile.php?id=61584040833501&v=sp001",
    title: "Quiet Ways Rich People Make Money",
    thumbnail_url: "https://picsum.photos/seed/sp1/320/180",
    channel_name: "Silent Profit", duration_seconds: 38, view_count: 540000,
    published_at: daysAgo(4), discovered_at: daysAgo(0), status: "queued",
  },
  {
    id: "m1102", source_id: "11", platform: "facebook", external_id: "fb_sp_002",
    canonical_url: "https://www.facebook.com/profile.php?id=61584040833501&v=sp002",
    title: "The $5 A Day Rule That Built My Wealth",
    thumbnail_url: "https://picsum.photos/seed/sp2/320/180",
    channel_name: "Silent Profit", duration_seconds: 41, view_count: 289000,
    published_at: daysAgo(11), discovered_at: daysAgo(0), status: "queued",
  },
  {
    id: "m1103", source_id: "11", platform: "facebook", external_id: "fb_sp_003",
    canonical_url: "https://www.facebook.com/profile.php?id=61584040833501&v=sp003",
    title: "Nobody Talks About This Income Stream",
    thumbnail_url: "https://picsum.photos/seed/sp3/320/180",
    channel_name: "Silent Profit", duration_seconds: 35, view_count: 712000,
    published_at: daysAgo(18), discovered_at: daysAgo(0), status: "queued",
  },

  // ── TikTok: tips.and.tricks402 (source_id: "13") ─────────────────────
  {
    id: "m1301", source_id: "13", platform: "tiktok", external_id: "tt_tat_001",
    canonical_url: "https://www.tiktok.com/@tips.and.tricks402/video/7001",
    title: "This Credit Card Hack Saves Me $300/Month",
    thumbnail_url: "https://picsum.photos/seed/tt1/320/180",
    channel_name: "tips.and.tricks402", duration_seconds: 22, view_count: 4500000,
    published_at: daysAgo(1), discovered_at: daysAgo(0), status: "queued",
  },
  {
    id: "m1302", source_id: "13", platform: "tiktok", external_id: "tt_tat_002",
    canonical_url: "https://www.tiktok.com/@tips.and.tricks402/video/7002",
    title: "Amazon Hack: Get Free Shipping Every Time",
    thumbnail_url: "https://picsum.photos/seed/tt2/320/180",
    channel_name: "tips.and.tricks402", duration_seconds: 18, view_count: 2800000,
    published_at: daysAgo(5), discovered_at: daysAgo(0), status: "queued",
  },
  {
    id: "m1303", source_id: "13", platform: "tiktok", external_id: "tt_tat_003",
    canonical_url: "https://www.tiktok.com/@tips.and.tricks402/video/7003",
    title: "Budget Grocery Trick That Actually Works",
    thumbnail_url: "https://picsum.photos/seed/tt3/320/180",
    channel_name: "tips.and.tricks402", duration_seconds: 25, view_count: 1600000,
    published_at: daysAgo(9), discovered_at: daysAgo(0), status: "queued",
  },
  {
    id: "m1304", source_id: "13", platform: "tiktok", external_id: "tt_tat_004",
    canonical_url: "https://www.tiktok.com/@tips.and.tricks402/video/7004",
    title: "5 Apps Paying Real Money Right Now",
    thumbnail_url: "https://picsum.photos/seed/tt4/320/180",
    channel_name: "tips.and.tricks402", duration_seconds: 30, view_count: 6200000,
    published_at: daysAgo(14), discovered_at: daysAgo(0), status: "queued",
  },
];

export function getItemsBySource(sourceId: string): MediaItem[] {
  return MOCK_MEDIA_ITEMS.filter((m) => m.source_id === sourceId);
}

export function formatDuration(seconds: number | null): string {
  if (!seconds) return "—";
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${m}:${s.toString().padStart(2, "0")}`;
}

export function formatViews(count: number | null): string {
  if (!count) return "—";
  if (count >= 1000000) return `${(count / 1000000).toFixed(1)}M`;
  if (count >= 1000) return `${(count / 1000).toFixed(0)}K`;
  return count.toString();
}

export function formatRelativeDate(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const days = Math.floor(diff / 86400000);
  if (days === 0) return "Today";
  if (days === 1) return "Yesterday";
  if (days < 7) return `${days}d ago`;
  if (days < 30) return `${Math.floor(days / 7)}w ago`;
  return `${Math.floor(days / 30)}mo ago`;
}

/** Calendar publish date (not relative). */
export function formatPublishedDate(iso: string | null | undefined): string {
  if (!iso) return "—";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "—";
  return d.toLocaleDateString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
    timeZone: "UTC",
  });
}
