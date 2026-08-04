"""Generic article body acquire — read manifest.json, fetch each URL, update pages in place."""
from __future__ import annotations

import json
import re
import time
from pathlib import Path
from urllib.parse import urlparse

from app.services.library_lesson_metadata import normalize_lesson_title_category

V2_ROOT = Path(__file__).resolve().parents[2]
DATA_ROOT = V2_ROOT / "data"

EXTRACT_ARTICLE_JS = """() => {
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

  function cellText(node) {
    return (node.innerText || node.textContent || '').replace(/\\s+/g, ' ').trim();
  }

  function absUrl(src) {
    if (!src) return '';
    try { return new URL(src, location.href).href; } catch (e) { return src; }
  }

  function pushImage(img) {
    let src = img.getAttribute('src') || img.getAttribute('data-src') || '';
    if (!src) {
      const srcset = img.getAttribute('srcset') || '';
      if (srcset) src = srcset.split(',')[0].trim().split(/\\s+/)[0] || '';
    }
    src = absUrl(src);
    if (!src || /^data:image\\/svg/i.test(src)) return;
    const alt = (img.getAttribute('alt') || '').replace(/[\\[\\]]/g, '').trim();
    pushBlank();
    parts.push('![' + alt + '](' + src + ')');
    parts.push('');
  }

  function tableToMd(table) {
    const rows = [];
    for (const tr of table.querySelectorAll('tr')) {
      const cells = Array.from(tr.querySelectorAll('th,td')).map((td) =>
        cellText(td).replace(/\\|/g, '\\\\|')
      );
      if (!cells.length) continue;
      rows.push('| ' + cells.join(' | ') + ' |');
    }
    if (!rows.length) return;
    const colCount = Math.max(...rows.map((r) => (r.match(/\\|/g) || []).length - 1), 1);
    const sep = '| ' + Array.from({ length: colCount }, () => '---').join(' | ') + ' |';
    pushBlank();
    parts.push(rows[0]);
    parts.push(sep);
    for (const row of rows.slice(1)) parts.push(row);
    parts.push('');
  }

  function walk(node) {
    if (!node) return;
    if (node.nodeType === 3) return;
    if (node.nodeType !== 1) return;
    const tag = node.tagName.toLowerCase();
    if (skipTags.has(tag)) return;
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
      for (const img of node.querySelectorAll('img')) pushImage(img);
      const clone = node.cloneNode(true);
      clone.querySelectorAll('img').forEach((n) => n.remove());
      const tx = (clone.innerText || '').trim();
      if (tx) {
        parts.push(tx);
        parts.push('');
      }
      return;
    }
    if (tag === 'figure') {
      const img = node.querySelector('img');
      if (img) pushImage(img);
      const cap = node.querySelector('figcaption');
      if (cap) {
        const tx = cellText(cap);
        if (tx) {
          parts.push('*' + tx + '*');
          parts.push('');
        }
      }
      return;
    }
    if (tag === 'img') {
      if (node.closest('p, figure, table, li')) return;
      pushImage(node);
      return;
    }
    if (tag === 'table') {
      tableToMd(node);
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


def _slug_from_url(url: str) -> str:
    path = urlparse(url).path.rstrip("/")
    name = path.split("/")[-1] or "item"
    return re.sub(r"[^\w\-]+", "-", name).strip("-").lower()[:120] or "item"


def _title_from_slug(url: str) -> str:
    slug = _slug_from_url(url).replace("-", " ").strip()
    return slug[:1].upper() + slug[1:] if slug else "Untitled"


def clean_article_body(text: str, title: str = "") -> str:
    text = re.sub(r"\n{3,}", "\n\n", (text or "").strip())
    for noise in (
        "Summarize with Claude",
        "Summarize with ChatGPT",
        "Summarize with Gemini",
        "Summarize with Perplexity",
        "Copy prompt",
    ):
        text = text.replace(noise, "")
    lines = [ln.rstrip() for ln in text.splitlines()]
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
    return re.sub(r"\n{3,}", "\n\n", text)


def extract_article_from_page(page) -> tuple[str, str, list[dict]]:
    data = page.evaluate(EXTRACT_ARTICLE_JS)
    title = (data.get("title") or "").strip()
    if " | " in title:
        title = title.split(" | ", 1)[0].strip()
    body = clean_article_body(data.get("markdown") or "", title=title)
    return title, body, data.get("links") or []


def _localize_body_images(page, body: str, slug: str, *, target: Path, files_prefix: str) -> str:
    from app.services.library_media import localize_markdown_images

    def request_get(url: str):
        return page.context.request.get(url, timeout=60000)

    return localize_markdown_images(
        body,
        disk_dir=target / "assets" / slug,
        files_prefix=files_prefix,
        request_get=request_get,
    )


def run_acquire_bodies(out_dir: Path | None = None, *, course_name: str | None = None) -> dict:
    """
    Fetch full article bodies for manifest rows (any article_hub destination).
    Updates existing page files in place.
    """
    from playwright.sync_api import sync_playwright

    target = Path(out_dir) if out_dir else DATA_ROOT
    manifest_path = target / "manifest.json"
    if not manifest_path.is_file():
        raise FileNotFoundError(f"No manifest at {manifest_path}")

    manifest: list[dict] = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(manifest, list):
        raise ValueError("manifest.json must be a list")

    course_slug = target.name
    display_name = (course_name or course_slug.replace("-", " ").title()).strip()
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    ok = 0
    failed = 0

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
            )
        )
        page = context.new_page()

        for row in manifest:
            if not row.get("ok") or not row.get("url"):
                continue
            url = str(row["url"])
            idx = int(row.get("index") or 0)
            file_rel = str(row.get("file") or "").replace("\\", "/")
            if file_rel.startswith("data/"):
                out_path = V2_ROOT / file_rel
            elif file_rel:
                out_path = target / "pages" / Path(file_rel).name
            else:
                out_path = target / "pages" / f"{idx:03d}-{_slug_from_url(url)}.md"
            label = str(row.get("label") or row.get("title") or "")
            slug = out_path.stem or f"{idx:03d}-{_slug_from_url(url)}"
            asset_prefix = f"data/{course_slug}/assets/{slug}"

            try:
                page.goto(url, wait_until="domcontentloaded", timeout=60000)
                page.wait_for_timeout(1800)
                fetched_title, body, _links = extract_article_from_page(page)
                if len(body) < 200:
                    page.wait_for_timeout(2500)
                    fetched_title, body, _links = extract_article_from_page(page)
                if body:
                    body = _localize_body_images(
                        page,
                        body,
                        slug,
                        target=target,
                        files_prefix=asset_prefix,
                    )

                norm_row = {
                    **row,
                    "title": fetched_title or row.get("title") or label,
                    "label": label,
                    "url": url,
                }
                title, category = normalize_lesson_title_category(row=norm_row, file_rel=file_rel)
                if not title:
                    title = fetched_title or label or _title_from_slug(url)

                frontmatter = [
                    "- kind: text",
                    f"- title: {title}",
                    f"- label: {label}",
                    f"- category: {category}",
                    f"- course: {display_name}",
                    f"- course_id: {course_slug}",
                    f"- order: {idx}",
                    f"- url: {url}",
                    f"- fetched_at: {now}",
                ]
                if row.get("lesson_id"):
                    frontmatter.append(f"- lesson_id: {row['lesson_id']}")

                out_path.parent.mkdir(parents=True, exist_ok=True)
                out_path.write_text(
                    f"# {title}\n\n" + "\n".join(frontmatter) + "\n\n---\n\n" + body + "\n",
                    encoding="utf-8",
                )

                rel = file_rel or str(out_path.relative_to(V2_ROOT)).replace("\\", "/")
                row["title"] = title
                row["category"] = category
                row["file"] = rel
                row["chars"] = len(body)
                row["ok"] = True
                row.pop("error", None)
                ok += 1
            except Exception as exc:
                row["ok"] = False
                row["error"] = f"{type(exc).__name__}: {exc}"
                failed += 1
            time.sleep(0.35)

        browser.close()

    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return {
        "course_id": course_slug,
        "ok": ok,
        "locked": 0,
        "failed": failed,
        "total": len(manifest),
        "out_dir": str(target),
        "mode": "acquire_bodies",
    }
