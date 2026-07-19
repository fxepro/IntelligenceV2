"""One-shot: audit + backfill missing media thumbnails (targeted)."""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

from sqlalchemy import create_engine, text

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "api"))
sys.path.insert(0, str(ROOT / "workers"))

for line in (ROOT / ".env").read_text(encoding="utf-8").splitlines():
    line = line.strip()
    if not line or line.startswith("#") or "=" not in line:
        continue
    k, v = line.split("=", 1)
    os.environ.setdefault(k.strip(), v.strip())


def yt_thumb_from_url(url: str, external_id: str | None) -> str | None:
    vid = (external_id or "").strip()
    if not re.fullmatch(r"[\w-]{6,}", vid or ""):
        m = re.search(r"(?:v=|/shorts/|/embed/)([\w-]{6,})", url or "")
        vid = m.group(1) if m else ""
    if vid:
        return f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg"
    return None


def main() -> None:
    eng = create_engine(os.environ["DATABASE_URL_SYNC"])
    audit = text(
        """
        SELECT s.id::text, s.name, s.platform,
          COUNT(*) FILTER (WHERE COALESCE(r.fields->>'thumbnail_url','') = '') AS missing,
          COUNT(*) FILTER (WHERE COALESCE(r.fields->>'thumbnail_url','') <> '') AS have,
          COUNT(*) AS total
        FROM sources s
        JOIN records r ON r.source_id = s.id AND r.domain = 'media'
        GROUP BY s.id, s.name, s.platform
        HAVING COUNT(*) FILTER (WHERE COALESCE(r.fields->>'thumbnail_url','') = '') > 0
        ORDER BY missing DESC
        """
    )
    with eng.connect() as c:
        rows = c.execute(audit).fetchall()
    print("=== channels with missing thumbs ===")
    for r in rows:
        pct = 100.0 * int(r.have) / int(r.total) if r.total else 0
        print(f"{r.missing:4d} miss | {r.have:4d} ok | {pct:5.1f}% | {r.platform:8s} | {r.name} | {r.id}")

    # YouTube: instant deterministic backfill
    yt_sql = text(
        """
        SELECT r.id::text, r.canonical_url, r.external_id, r.fields
        FROM records r
        JOIN sources s ON s.id = r.source_id
        WHERE r.domain = 'media'
          AND s.platform = 'youtube'
          AND COALESCE(r.fields->>'thumbnail_url','') = ''
        """
    )
    yt_upd = text(
        """
        UPDATE records
        SET fields = jsonb_set(COALESCE(fields, '{}'::jsonb), '{thumbnail_url}', to_jsonb(CAST(:thumb AS text)), true)
        WHERE id = CAST(:id AS uuid)
        """
    )
    fb_rows_sql = text(
        """
        SELECT r.id::text, r.canonical_url
        FROM records r
        JOIN sources s ON s.id = r.source_id
        WHERE r.domain = 'media'
          AND s.platform = 'facebook'
          AND COALESCE(r.fields->>'thumbnail_url','') = ''
        ORDER BY r.created_at DESC
        LIMIT :lim
        """
    )

    with eng.begin() as c:
        yt_rows = c.execute(yt_sql).fetchall()
        yt_fixed = 0
        for row in yt_rows:
            thumb = yt_thumb_from_url(row.canonical_url or "", row.external_id)
            if not thumb:
                continue
            c.execute(yt_upd, {"id": row.id, "thumb": thumb})
            yt_fixed += 1
        print(f"\nYouTube thumbs set: {yt_fixed}/{len(yt_rows)}")

    # Facebook: yt-dlp enrich (slower) — batch
    import yt_dlp

    from app.services.discover_media import _ydl_opts  # type: ignore

    lim = int(sys.argv[1]) if len(sys.argv) > 1 else 250
    with eng.connect() as c:
        fb_rows = c.execute(fb_rows_sql, {"lim": lim}).fetchall()
    print(f"Facebook missing to try: {len(fb_rows)} (limit={lim})")

    fixed_fb = 0
    failed = 0
    if fb_rows:
        sample = fb_rows[0].canonical_url
        opts = _ydl_opts(sample, skip_download=True)
        with yt_dlp.YoutubeDL(opts) as ydl, eng.begin() as c:
            for i, row in enumerate(fb_rows, 1):
                try:
                    info = ydl.extract_info(row.canonical_url, download=False)
                except Exception:
                    failed += 1
                    continue
                thumb = (info or {}).get("thumbnail") if info else None
                if not thumb:
                    failed += 1
                    continue
                c.execute(yt_upd, {"id": row.id, "thumb": thumb})
                fixed_fb += 1
                if i % 25 == 0:
                    print(f"  … {i}/{len(fb_rows)} (ok={fixed_fb} fail={failed})")
    print(f"Facebook thumbs set: {fixed_fb} (fail={failed})")

    with eng.connect() as c:
        rows = c.execute(audit).fetchall()
    print("\n=== after ===")
    for r in rows:
        pct = 100.0 * int(r.have) / int(r.total) if r.total else 0
        print(f"{r.missing:4d} miss | {r.have:4d} ok | {pct:5.1f}% | {r.platform:8s} | {r.name}")
    if not rows:
        print("(none — all channels complete)")


if __name__ == "__main__":
    main()
