"""Backfill missing Tipper FB thumbnails via yt-dlp (owner reel URLs only)."""
from __future__ import annotations

import yt_dlp
from sqlalchemy import create_engine, text

from app.config import get_settings
from app.services.discover_media import _ydl_opts

SID = "d72f32e4-6576-41bd-bbdf-c2180d9d05fd"
LIMIT = 200


def main() -> None:
    e = create_engine(get_settings().database_url_sync)
    with e.connect() as c:
        rows = c.execute(
            text(
                """
                SELECT id, canonical_url
                FROM records
                WHERE source_id = :sid
                  AND domain = 'media'
                  AND COALESCE(fields->>'thumbnail_url', '') = ''
                  AND canonical_url LIKE '%/reel/%'
                ORDER BY created_at DESC
                LIMIT :lim
                """
            ),
            {"sid": SID, "lim": LIMIT},
        ).fetchall()

    print(f"missing={len(rows)}")
    if not rows:
        return

    opts = _ydl_opts(rows[0][1], skip_download=True)
    updated = 0
    failed = 0
    with yt_dlp.YoutubeDL(opts) as ydl, e.begin() as c:
        for rid, url in rows:
            try:
                info = ydl.extract_info(url, download=False) or {}
            except Exception as exc:
                failed += 1
                print("fail", rid, type(exc).__name__)
                continue
            thumb = info.get("thumbnail")
            if not thumb and info.get("thumbnails"):
                thumb = (info.get("thumbnails") or [{}])[-1].get("url")
            if not thumb:
                failed += 1
                print("no_thumb", rid)
                continue
            c.execute(
                text(
                    """
                    UPDATE records
                    SET fields = jsonb_set(
                      COALESCE(fields, '{}'::jsonb),
                      '{thumbnail_url}',
                      to_jsonb(CAST(:thumb AS text)),
                      true
                    )
                    WHERE id = :id
                    """
                ),
                {"id": rid, "thumb": thumb},
            )
            updated += 1
            if updated % 10 == 0:
                print(f"updated={updated}")
    print(f"done updated={updated} failed={failed}")


if __name__ == "__main__":
    main()
