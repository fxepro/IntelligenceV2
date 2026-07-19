"""
Facebook Videos (non-reel) link discovery via Playwright (sync API).

yt-dlp cannot list a page's /videos tab (Unsupported URL). This scraper
opens the Videos tab, scrolls the grid, and collects watch/video IDs —
same approach as facebook_reels.py. Reels (/reel/…) are excluded.
"""
from __future__ import annotations

import re
from urllib.parse import urlparse

from playwright.sync_api import sync_playwright

from app.services.facebook_reels import (
    _dismiss_facebook_overlays,
    _hydrate_durations_from_page,
    _load_facebook_storage_state,
    _safe_playwright_close,
    _scroll_reels_feed,
    clean_reel_title,
    extract_facebook_profile_id,
    normalize_facebook_page_url,
)

_VIDEO_ID_RE = re.compile(
    r"(?:[?&]v=|/videos/(?:[^/]+/)?|/video\.php\?v=)(\d+)",
    re.I,
)


def videos_tab_url(page_url: str) -> str:
    """
    Convert any Facebook page/profile URL into its Videos tab URL.

      profile.php?id=123  →  profile.php?id=123&sk=videos
      /Handle/videos      →  /Handle/videos (kept)
      /Handle             →  /Handle/videos
    """
    raw = (page_url or "").strip()
    if not raw:
        return raw
    low = raw.rstrip("/").lower()
    if low.endswith("/videos") or "sk=videos" in low:
        return raw.rstrip("/")

    profile_id = extract_facebook_profile_id(raw)
    if profile_id:
        return f"https://www.facebook.com/profile.php?id={profile_id}&sk=videos"
    base = normalize_facebook_page_url(raw)
    profile_id = extract_facebook_profile_id(base)
    if profile_id:
        return f"https://www.facebook.com/profile.php?id={profile_id}&sk=videos"
    return f"{base.rstrip('/')}/videos"


def _video_id(href: str) -> str | None:
    if not href or "/reel/" in href.lower():
        return None
    m = _VIDEO_ID_RE.search(href)
    return m.group(1) if m else None


def _canonical_video_url(video_id: str) -> str:
    return f"https://www.facebook.com/watch/?v={video_id}"


def _harvest_video_anchors(page) -> list[dict]:
    """Pull non-reel video tiles currently in the Videos tab DOM."""
    return page.evaluate(
        """() => {
          const out = [];
          const seen = new Set();
          const main = document.querySelector('[role="main"]') || document.body;
          const anchors = Array.from(
            main.querySelectorAll(
              'a[href*="/watch"], a[href*="/videos/"], a[href*="video.php"], a[href*="v="]'
            )
          );
          for (const a of anchors) {
            const href = a.href || '';
            if (!href || /\\/reel\\//i.test(href)) continue;
            let id = null;
            let m = href.match(/[?&]v=(\\d+)/i);
            if (m) id = m[1];
            if (!id) {
              m = href.match(/\\/videos\\/(?:[^/]+\\/)?(\\d+)/i);
              if (m) id = m[1];
            }
            if (!id) continue;
            if (seen.has(id)) continue;
            seen.add(id);

            let title = (a.getAttribute('aria-label') || a.innerText || '').trim();
            title = title.replace(/\\s+/g, ' ').slice(0, 240) || null;
            if (title) {
              const low = title.toLowerCase();
              if (
                low.includes('tile preview')
                || low === 'preview'
                || low === 'video'
                || low === 'videos'
              ) {
                title = null;
              }
            }

            let thumb = null;
            const img = a.querySelector('img');
            if (img) {
              thumb = img.currentSrc || img.src || img.getAttribute('data-src') || null;
              if (thumb && (thumb.startsWith('data:') || thumb.startsWith('blob:'))) thumb = null;
              if ((!title || !title.trim())) {
                const alt = (img.getAttribute('alt') || '').trim();
                if (alt && !/tile preview/i.test(alt) && alt.toLowerCase() !== 'preview') {
                  title = alt.slice(0, 240);
                }
              }
            }
            if (!thumb) {
              const bgEl = a.querySelector('[style*="background-image"]');
              const style = bgEl ? (bgEl.getAttribute('style') || '') : '';
              const bm = style.match(/background-image:\\s*url\\([\"']?([^\"')]+)[\"']?\\)/i);
              if (bm && bm[1] && !bm[1].startsWith('data:')) thumb = bm[1];
            }

            let views = null;
            const labeled = a.querySelector('[aria-label*="view" i]');
            if (labeled) {
              const t = labeled.getAttribute('aria-label') || '';
              const vm = t.match(/([\\d,.]+\\s*[KMB]?)\\s*views?/i);
              if (vm) views = vm[1];
            }

            let duration = null;
            const blob = ((a.getAttribute('aria-label') || '') + ' ' + (a.innerText || '')).trim();
            const dm = blob.match(/\\b(\\d{1,2}):([0-5]\\d)\\b/);
            if (dm) duration = parseInt(dm[1], 10) * 60 + parseInt(dm[2], 10);
            if (!duration) {
              for (const el of a.querySelectorAll('span, div')) {
                const t = (el.textContent || '').trim();
                if (!/^\\d{1,2}:[0-5]\\d$/.test(t)) continue;
                const parts = t.split(':');
                duration = parseInt(parts[0], 10) * 60 + parseInt(parts[1], 10);
                break;
              }
            }
            out.push({ id, href, title, thumb, views, duration });
          }
          return out;
        }"""
    ) or []


def _merge_video_batch(batch: list[dict], collected: dict[str, dict], max_items: int) -> int:
    added = 0
    for row in batch:
        vid = row.get("id") or _video_id(row.get("href") or "")
        if not vid:
            continue
        title = clean_reel_title(row.get("title"))
        thumb = (row.get("thumb") or "").strip() or None
        if vid in collected:
            existing = collected[vid]
            if not clean_reel_title(existing.get("title")) and title:
                existing["title"] = title
            if not existing.get("thumbnail_url") and thumb:
                existing["thumbnail_url"] = thumb
            if not existing.get("view_count_raw") and row.get("views"):
                existing["view_count_raw"] = row.get("views")
            if not existing.get("duration_seconds") and row.get("duration"):
                try:
                    existing["duration_seconds"] = int(row["duration"])
                except (TypeError, ValueError):
                    pass
            continue
        if not thumb:
            continue
        duration = None
        if row.get("duration") is not None:
            try:
                duration = int(row["duration"])
            except (TypeError, ValueError):
                duration = None
        collected[vid] = {
            "id": vid,
            "url": _canonical_video_url(vid),
            "title": title,
            "thumbnail_url": thumb,
            "view_count_raw": row.get("views"),
            "duration_seconds": duration,
        }
        added += 1
        if len(collected) >= max_items:
            break
    return added


def scrape_facebook_videos_sync(
    page_url: str,
    max_items: int = 200,
    max_scrolls: int = 50,
    idle_rounds: int = 6,
) -> tuple[list[dict], str]:
    """
    Collect non-reel video links from a Facebook page Videos tab.

    Returns (items, resolved_videos_tab_url).
    items: id, url, title, thumbnail_url, view_count_raw, duration_seconds.
    """
    import sys
    import asyncio

    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

    start = normalize_facebook_page_url(page_url)
    target = videos_tab_url(page_url)
    collected: dict[str, dict] = {}
    resolved_videos = target
    storage = _load_facebook_storage_state()
    max_scrolls = max(max_scrolls, min(260, max(80, max_items // 2)))
    idle_rounds = max(idle_rounds, 14 if max_items >= 300 else 10)
    if storage:
        max_scrolls = max(max_scrolls, 140)
        idle_rounds = max(idle_rounds, 12)

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-blink-features=AutomationControlled"],
        )
        context_kwargs: dict = {
            "user_agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/131.0.0.0 Safari/537.36"
            ),
            "viewport": {"width": 1400, "height": 1100},
            "locale": "en-US",
        }
        if storage:
            context_kwargs["storage_state"] = storage
        context = browser.new_context(**context_kwargs)
        page = context.new_page()
        try:
            page.goto(target, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(3000)
            _dismiss_facebook_overlays(page)

            for label in ("Allow all cookies", "Accept All", "Decline optional cookies", "Close"):
                try:
                    btn = page.get_by_role("button", name=re.compile(label, re.I))
                    if btn.count():
                        btn.first.click(timeout=1500)
                        page.wait_for_timeout(400)
                except Exception:
                    pass

            def _count_videos() -> int:
                return len(_harvest_video_anchors(page))

            if _count_videos() == 0:
                page.goto(start, wait_until="domcontentloaded", timeout=60000)
                page.wait_for_timeout(2000)
                landed = page.url or start
                resolved_videos = videos_tab_url(
                    landed if extract_facebook_profile_id(landed) else page_url
                )
                page.goto(resolved_videos, wait_until="domcontentloaded", timeout=60000)
                page.wait_for_timeout(3000)

            landed = page.url or target
            path = urlparse(landed).path or ""
            if "sk=videos" in landed or path.rstrip("/").lower().endswith("/videos"):
                resolved_videos = landed
            else:
                resolved_videos = videos_tab_url(landed)
                page.goto(resolved_videos, wait_until="domcontentloaded", timeout=60000)
                page.wait_for_timeout(2500)
                resolved_videos = page.url or resolved_videos

            if _count_videos() == 0:
                for name in (r"^Videos$", r"Videos"):
                    try:
                        link = page.get_by_role("link", name=re.compile(name, re.I))
                        if link.count():
                            link.first.click(timeout=2000)
                            page.wait_for_timeout(2500)
                            break
                    except Exception:
                        pass

            _merge_video_batch(_harvest_video_anchors(page), collected, max_items)
            _hydrate_durations_from_page(page, collected)

            stagnant = 0
            for _ in range(max_scrolls):
                before = len(collected)
                _merge_video_batch(_harvest_video_anchors(page), collected, max_items)
                _hydrate_durations_from_page(page, collected)

                if len(collected) >= max_items:
                    break

                if len(collected) == before:
                    stagnant += 1
                    if stagnant >= idle_rounds:
                        break
                else:
                    stagnant = 0

                _scroll_reels_feed(page)
                page.wait_for_timeout(1800)

            _hydrate_durations_from_page(page, collected)

            # Many modern Pages have no Videos library — /videos still loads, but
            # the nav is Reels/Photos and the feed is reel tiles only.
            if not collected:
                page_kind = page.evaluate(
                    """() => {
                      const hrefs = Array.from(document.querySelectorAll('a[href]')).map(a => a.href || '');
                      const reel = hrefs.filter(h => /\\/reel\\//i.test(h)).length;
                      const video = hrefs.filter(h =>
                        (/\\/videos\\/\\d+/i.test(h) || /\\/watch/i.test(h) || /[?&]v=\\d+/i.test(h))
                        && !/\\/reel\\//i.test(h)
                      ).length;
                      const tabTexts = Array.from(
                        document.querySelectorAll('a[role="tab"], [role="tab"], a[href]')
                      ).map(e => (e.getAttribute('aria-label') || e.innerText || '').trim().toLowerCase());
                      const hasVideosTab = tabTexts.some(t => t === 'videos' || t.startsWith('videos\\n'));
                      return { reel, video, hasVideosTab };
                    }"""
                ) or {}
                reel_n = int(page_kind.get("reel") or 0)
                video_n = int(page_kind.get("video") or 0)
                if reel_n > 0 and video_n == 0 and not page_kind.get("hasVideosTab"):
                    raise RuntimeError(
                        "Facebook page has no Videos catalog "
                        "(Reels-only — /videos does not list separate long-form videos)"
                    )
        finally:
            _safe_playwright_close(context, browser)

    return list(collected.values()), resolved_videos
