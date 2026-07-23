"""
Download Drata SOC 2 Learn collection (public text articles).

Starts from the 6 featured hub lessons, then follows in-article
links under /learn/soc-2/ (BFS) so linked texts are included too.

  cd v2/api
  python scripts/download_drata_soc2.py
"""
from __future__ import annotations

import json
import re
import sys
import time
from collections import deque
from pathlib import Path
from urllib.parse import urlparse, urlunparse

API_ROOT = Path(__file__).resolve().parents[1]
ROOT = API_ROOT.parent
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

SITE = "https://drata.com"
HUB = f"{SITE}/learn/soc-2"
OUT_DIR = ROOT / "data" / "drata-soc2"

# Featured collection cards on the hub (user minimum).
FEATURED: list[tuple[str, str, str]] = [
    ("Getting Started", "What is SOC 2 Compliance? A Beginner's Guide", f"{HUB}/beginners-guide"),
    ("Getting Started", "SOC 2 Compliance Checklist: Your Complete Guide to Audit Success", f"{HUB}/checklist"),
    ("Best Practices", "How to Choose the Right SOC 2 Audit Firm", f"{HUB}/pick-right-audit-firm"),
    ("Best Practices", "SOC 2 Guide: Pro Tips to Streamline Your SOC 2", f"{HUB}/how-to-streamline"),
    ("Reporting and Documentation", "Trust Services Criteria for SOC 2: What You Need to Know", f"{HUB}/trust-services-criteria"),
    ("Additional Resources", "What Is a SOC 2 Bridge Letter?", f"{HUB}/bridge-letter"),
]


def _norm_url(url: str) -> str:
    raw = (url or "").split("#")[0].split("?")[0].rstrip("/")
    if not raw:
        return ""
    parsed = urlparse(raw)
    if parsed.netloc and "drata.com" not in parsed.netloc.lower():
        return ""
    path = parsed.path or ""
    if not path.startswith("/learn/soc-2"):
        return ""
    # Skip the hub itself as a lesson page.
    if path.rstrip("/") == "/learn/soc-2":
        return ""
    return urlunparse(("https", "drata.com", path.rstrip("/"), "", "", ""))


def _slug_from_url(url: str) -> str:
    path = urlparse(url).path.rstrip("/")
    name = path.split("/")[-1] or "item"
    name = re.sub(r"[^\w\-]+", "-", name).strip("-").lower()
    return name[:120] or "item"


def _title_from_slug(url: str) -> str:
    slug = _slug_from_url(url).replace("-", " ").strip()
    return slug[:1].upper() + slug[1:] if slug else "Untitled"


def _clean_article_body(text: str, title: str = "") -> str:
    text = re.sub(r"\n{3,}", "\n\n", (text or "").strip())
    # Drop AI summarize chrome / share widgets
    for noise in (
        "Summarize with Claude",
        "Summarize with ChatGPT",
        "Summarize with Gemini",
        "Summarize with Perplexity",
        "Copy prompt",
    ):
        text = text.replace(noise, "")
    lines = [ln.rstrip() for ln in text.splitlines()]
    # Drop leading breadcrumb/nav lines
    while lines:
        s = lines[0].strip()
        low = s.lower()
        if s in ("/", "learn", "soc 2", "LEARN", "SOC 2") or low in ("learn", "soc 2"):
            lines.pop(0)
            continue
        if title and s.lower() == title.lower():
            lines.pop(0)
            continue
        if s.startswith("# ") and title and s[2:].strip().lower() == title.lower():
            lines.pop(0)
            continue
        break
    cut_markers = (
        "ready to automate",
        "see drata in action",
        "request a demo",
        "get a demo",
        "start free",
        "book a demo",
    )
    cut = len(lines)
    for i, ln in enumerate(lines):
        if any(m in ln.lower() for m in cut_markers):
            cut = i
            break
    text = "\n".join(lines[:cut]).strip()
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text


def _extract_article(page) -> tuple[str, str, list[dict]]:
    data = page.evaluate(
        """() => {
          const h1 = document.querySelector('h1');
          const title = ((h1 && h1.innerText) || document.title || '').trim();
          const picks = ['article', '[class*="prose"]', 'main', '#content', 'body'];
          let root = document.body;
          for (const sel of picks) {
            const el = document.querySelector(sel);
            if (el && (el.innerText || '').trim().length > 400) {
              root = el;
              break;
            }
          }

          const skipTags = new Set(['script','style','nav','header','footer','aside','noscript','svg','button','form']);
          const parts = [];

          function pushBlank() {
            if (parts.length && parts[parts.length - 1] !== '') parts.push('');
          }

          function walk(node) {
            if (!node) return;
            if (node.nodeType === 3) return;
            if (node.nodeType !== 1) return;
            const tag = node.tagName.toLowerCase();
            if (skipTags.has(tag)) return;
            // Skip known chrome widgets
            const cls = (node.className && typeof node.className === 'string') ? node.className.toLowerCase() : '';
            const txQuick = (node.innerText || '').trim();
            if (/summarize with|copy prompt/i.test(txQuick) && txQuick.length < 120) return;

            if (/^h[1-6]$/.test(tag)) {
              const level = Number(tag[1]);
              const tx = (node.innerText || '').trim().replace(/\\s+/g, ' ');
              if (tx) {
                pushBlank();
                parts.push('#'.repeat(Math.min(level, 4)) + ' ' + tx);
                parts.push('');
              }
              return;
            }
            if (tag === 'p') {
              const tx = (node.innerText || '').trim();
              if (tx) {
                parts.push(tx);
                parts.push('');
              }
              return;
            }
            if (tag === 'ul' || tag === 'ol') {
              const items = Array.from(node.querySelectorAll(':scope > li'))
                .map(li => (li.innerText || '').trim().replace(/\\s+/g, ' '))
                .filter(Boolean);
              if (items.length) {
                for (const item of items) parts.push('- ' + item);
                parts.push('');
              }
              return;
            }
            if (tag === 'blockquote') {
              const tx = (node.innerText || '').trim();
              if (tx) {
                parts.push('> ' + tx.replace(/\\n+/g, ' '));
                parts.push('');
              }
              return;
            }
            if (tag === 'pre' || tag === 'code') {
              const tx = (node.innerText || '').trim();
              if (tx) {
                parts.push('```');
                parts.push(tx);
                parts.push('```');
                parts.push('');
              }
              return;
            }
            // Descend into containers
            for (const child of node.childNodes) walk(child);
          }

          walk(root);
          const markdown = parts.join('\\n').replace(/\\n{3,}/g, '\\n\\n').trim();
          const links = Array.from(root.querySelectorAll('a')).map(a => ({
            text: (a.innerText || '').trim().replace(/\\s+/g, ' ').slice(0, 160),
            href: (a.href || '').split('#')[0]
          }));
          return { title, markdown, links };
        }"""
    )
    title = (data.get("title") or "").strip()
    if " | " in title:
        title = title.split(" | ", 1)[0].strip()
    body = _clean_article_body(data.get("markdown") or "", title=title)
    links = data.get("links") or []
    return title, body, links


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "pages").mkdir(exist_ok=True)

    from playwright.sync_api import sync_playwright

    # seed: featured first (preserve category), then BFS linked /learn/soc-2/*
    queue: deque[tuple[str, str, str]] = deque()  # category, label, url
    meta_by_url: dict[str, dict] = {}
    for cat, label, url in FEATURED:
        nu = _norm_url(url)
        if not nu:
            continue
        queue.append((cat, label, nu))
        meta_by_url[nu] = {"category": cat, "label": label, "featured": True}

    seen: set[str] = set()
    ordered: list[str] = []
    manifest: list[dict] = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
            )
        )
        page = context.new_page()

        while queue:
            category, label, url = queue.popleft()
            if url in seen:
                continue
            seen.add(url)
            ordered.append(url)
            idx = len(ordered)
            slug = f"{idx:03d}-{_slug_from_url(url)}"
            out_path = OUT_DIR / "pages" / f"{slug}.md"
            print(f"[{idx}] {label[:70]}")
            print(f"     {url}")
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=60000)
                page.wait_for_timeout(1800)
                title, body, links = _extract_article(page)
                if len(body) < 200:
                    page.wait_for_timeout(2500)
                    title, body, links = _extract_article(page)
                title = title or label or _title_from_slug(url)
                # Enqueue in-article SOC 2 learn links
                for link in links:
                    nu = _norm_url(link.get("href") or "")
                    if not nu or nu in seen or nu in meta_by_url:
                        continue
                    link_label = (link.get("text") or "").strip()
                    if len(link_label) < 3 or link_label.startswith("."):
                        link_label = _title_from_slug(nu)
                    meta_by_url[nu] = {
                        "category": "Linked articles",
                        "label": link_label[:200],
                        "featured": False,
                        "from": url,
                    }
                    queue.append(("Linked articles", link_label[:200], nu))

                md = (
                    f"# {title}\n\n"
                    f"- kind: text\n"
                    f"- title: {title}\n"
                    f"- label: {label}\n"
                    f"- category: {category}\n"
                    f"- course: Drata SOC 2\n"
                    f"- url: {url}\n"
                    f"- featured: {str(bool(meta_by_url.get(url, {}).get('featured'))).lower()}\n"
                    f"- fetched_at: {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}\n\n"
                    f"---\n\n{body}\n"
                )
                out_path.write_text(md, encoding="utf-8")
                manifest.append(
                    {
                        "index": idx,
                        "kind": "text",
                        "label": label,
                        "title": title,
                        "category": category,
                        "url": url,
                        "file": str(out_path.relative_to(ROOT)).replace("\\", "/"),
                        "chars": len(body),
                        "featured": bool(meta_by_url.get(url, {}).get("featured")),
                        "ok": True,
                    }
                )
            except Exception as exc:
                print(f"  FAIL {type(exc).__name__}: {exc}")
                manifest.append(
                    {
                        "index": idx,
                        "kind": "text",
                        "label": label,
                        "category": category,
                        "url": url,
                        "ok": False,
                        "error": f"{type(exc).__name__}: {exc}",
                    }
                )
            time.sleep(0.35)

        browser.close()

    (OUT_DIR / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    ok = sum(1 for m in manifest if m.get("ok"))
    featured = sum(1 for m in manifest if m.get("featured") and m.get("ok"))
    print(f"done — {ok}/{len(manifest)} saved ({featured} featured) -> {OUT_DIR}")


if __name__ == "__main__":
    main()
