/** How a source URL is structured — not which vendor hosts it. */

export const CURRICULUM_TYPES = [
  {
    value: "manual",
    label: "Manual only",
    hint: "Paste YouTube links yourself — no auto-discover",
  },
  {
    value: "youtube_curriculum",
    label: "Video curriculum",
    hint: "Index page with sections and YouTube lesson links",
  },
  {
    value: "youtube_playlist",
    label: "YouTube playlist",
    hint: "Full playlist — all videos via yt-dlp in one discover",
  },
  {
    value: "article_hub",
    label: "Article hub",
    hint: "Hub page linking to individual article lessons",
  },
  {
    value: "coursera_catalog",
    label: "Coursera catalog",
    hint: "Public syllabus / JSON-LD (login may block full content)",
  },
  {
    value: "udemy_catalog",
    label: "Udemy catalog",
    hint: "Public curriculum outline (login for videos)",
  },
  {
    value: "website",
    label: "Generic website",
    hint: "Try video + article parsers automatically",
  },
] as const;

export type CurriculumType =
  | (typeof CURRICULUM_TYPES)[number]["value"]
  | "coursera_catalog"
  | "udemy_catalog";

/** Map legacy vendor-based connector values stored in DB. */
export function normalizeCurriculumType(value: string | null | undefined): string {
  const v = (value || "manual").trim().toLowerCase();
  if (v === "strongdm") return "youtube_curriculum";
  if (v === "drata") return "article_hub";
  if (v === "youtube") return "youtube_curriculum";
  if (v === "coursera") return "coursera_catalog";
  if (v === "udemy") return "udemy_catalog";
  if (CURRICULUM_TYPES.some((t) => t.value === v)) return v;
  return "manual";
}

/** Guess curriculum shape from URL — mirrors backend infer_connector(). */
export function inferCurriculumTypeFromUrl(url: string): string {
  const u = (url || "").trim().toLowerCase();
  if (!u.startsWith("http")) return "manual";
  if (u.includes("youtube.com/playlist") || (u.includes("youtube.com") && u.includes("list="))) {
    return "youtube_playlist";
  }
  if (u.includes("youtu.be") || u.includes("youtube.com")) return "youtube_curriculum";
  if (u.includes("coursera.org")) return "coursera_catalog";
  if (u.includes("udemy.com")) return "udemy_catalog";
  if (u.includes("/learn/") || u.includes("/articles") || u.includes("/blog/")) return "article_hub";
  if (u.includes("curriculum") || u.includes("/course/") || u.includes("/soc2/") || u.includes("/soc-2/")) {
    return "youtube_curriculum";
  }
  return "website";
}

export function curriculumTypeLabel(value: string | null | undefined): string {
  const key = normalizeCurriculumType(value);
  return CURRICULUM_TYPES.find((t) => t.value === key)?.label ?? key;
}
