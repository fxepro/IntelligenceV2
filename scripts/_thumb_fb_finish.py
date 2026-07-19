"""Finish FB thumb backfill; delete rows that remain incomplete."""
from __future__ import annotations

import os
import sys
from pathlib import Path

from sqlalchemy import create_engine, text

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "api"))

for line in (ROOT / ".env").read_text(encoding="utf-8").splitlines():
    line = line.strip()
    if not line or line.startswith("#") or "=" not in line:
        continue
    k, v = line.split("=", 1)
    os.environ.setdefault(k.strip(), v.strip())


def main() -> None:
    import yt_dlp

    from app.services.discover_media import _ydl_opts

    eng = create_engine(os.environ["DATABASE_URL_SYNC"])
    list_sql = text(
        """
        SELECT r.id::text, r.canonical_url, s.name
        FROM records r
        JOIN sources s ON s.id = r.source_id
        WHERE r.domain = 'media'
          AND s.platform = 'facebook'
          AND COALESCE(r.fields->>'thumbnail_url','') = ''
        ORDER BY s.name, r.created_at
        """
    )
    upd = text(
        """
        UPDATE records
        SET fields = jsonb_set(COALESCE(fields, '{}'::jsonb), '{thumbnail_url}', to_jsonb(CAST(:thumb AS text)), true)
        WHERE id = CAST(:id AS uuid)
        """
    )
    delete_sql = text(
        """
        DELETE FROM records
        WHERE domain = 'media'
          AND COALESCE(fields->>'thumbnail_url','') = ''
          AND source_id IN (
            SELECT id FROM sources WHERE platform = 'facebook'
          )
        """
    )
    audit = text(
        """
        SELECT s.name, s.platform,
          COUNT(*) FILTER (WHERE COALESCE(r.fields->>'thumbnail_url','') = '') AS missing,
          COUNT(*) FILTER (WHERE COALESCE(r.fields->>'thumbnail_url','') <> '') AS have,
          COUNT(*) AS total
        FROM sources s
        JOIN records r ON r.source_id = s.id AND r.domain = 'media'
        GROUP BY s.name, s.platform
        HAVING COUNT(*) FILTER (WHERE COALESCE(r.fields->>'thumbnail_url','') = '') > 0
        ORDER BY missing DESC
        """
    )

    with eng.connect() as c:
        rows = c.execute(list_sql).fetchall()
    print(f"Remaining FB without thumb: {len(rows)}")
    if not rows:
        print("Nothing to do")
        return

    opts = _ydl_opts(rows[0].canonical_url, skip_download=True)
    fixed = failed = 0
    with yt_dlp.YoutubeDL(opts) as ydl, eng.begin() as c:
        for i, row in enumerate(rows, 1):
            try:
                info = ydl.extract_info(row.canonical_url, download=False)
            except Exception:
                failed += 1
                continue
            thumb = (info or {}).get("thumbnail") if info else None
            if not thumb:
                failed += 1
                continue
            c.execute(upd, {"id": row.id, "thumb": thumb})
            fixed += 1
            if i % 40 == 0:
                print(f"  … {i}/{len(rows)} ok={fixed} fail={failed}")
    print(f"Backfill ok={fixed} fail={failed}")

    # Incomplete FB rows are not playable in-grid — drop so rediscover can refill.
    with eng.begin() as c:
        result = c.execute(delete_sql)
        print(f"Deleted incomplete FB media rows: {result.rowcount}")

    with eng.connect() as c:
        left = c.execute(audit).fetchall()
    print("=== channels still missing thumbs ===")
    if not left:
        print("(none)")
    for r in left:
        print(f"{r.missing:4d} miss | {r.have:4d} ok | {r.platform:8s} | {r.name}")


if __name__ == "__main__":
    main()
