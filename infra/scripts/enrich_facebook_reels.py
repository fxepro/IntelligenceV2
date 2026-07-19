r"""Enrich Facebook reel metadata via yt-dlp (title/duration/published/views).

Usage from v2/:
  .\.venv\Scripts\python.exe infra\scripts\enrich_facebook_reels.py [source_id] [limit]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import psycopg
import yt_dlp

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "api"))

from app.services.discover_media import (  # noqa: E402
    _clean_facebook_info_title,
    _file_size_bytes,
    _published_at,
)

DATABASE_URL = "postgresql://postgres:postgres@127.0.0.1:5432/intelligence"
DEFAULT_SOURCE = "d72f32e4-6576-41bd-bbdf-c2180d9d05fd"  # Tipper FB


def main() -> None:
    source_id = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_SOURCE
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else 20

    conn = psycopg.connect(DATABASE_URL, autocommit=True)
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id, canonical_url, title, fields
        FROM records
        WHERE source_id = %s::uuid
          AND domain = 'media'
            AND (
            title ILIKE 'Reel %%'
            OR title ILIKE '%%tile preview%%'
            OR fields->>'duration_seconds' IS NULL
            OR fields->>'published_at' IS NULL
            OR fields->>'file_size_bytes' IS NULL
          )
        ORDER BY created_at DESC
        LIMIT %s
        """,
        (source_id, limit),
    )
    rows = cur.fetchall()
    print(f"enriching {len(rows)} rows")

    opts = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "ignoreerrors": True,
    }
    updated = 0
    with yt_dlp.YoutubeDL(opts) as ydl:
        for record_id, url, old_title, fields in rows:
            fields = dict(fields or {})
            try:
                info = ydl.extract_info(url, download=False)
            except Exception as exc:
                print("fail", url, type(exc).__name__)
                continue
            if not info:
                print("empty", url)
                continue

            title = _clean_facebook_info_title(info) or (info.get("title") or "").strip() or old_title
            if info.get("duration") is not None:
                fields["duration_seconds"] = int(float(info["duration"]))
            published = _published_at(info)
            if published:
                fields["published_at"] = published
            size = _file_size_bytes(info)
            if size is not None:
                fields["file_size_bytes"] = size
            if info.get("view_count") is not None:
                fields["view_count"] = int(info["view_count"])
            if info.get("thumbnail"):
                fields["thumbnail_url"] = info["thumbnail"]
            if info.get("description"):
                fields["description"] = str(info["description"])[:4000]
            if info.get("uploader"):
                fields["channel_name"] = info["uploader"]

            cur.execute(
                """
                UPDATE records
                SET title = %s,
                    fields = %s::jsonb,
                    updated_at = NOW()
                WHERE id = %s::uuid
                """,
                (title, json.dumps(fields), str(record_id)),
            )
            updated += 1
            safe = (title or "").encode("ascii", "replace").decode("ascii")[:60]
            print("ok", str(record_id)[:8], safe)

    print("updated", updated)
    cur.close()
    conn.close()


if __name__ == "__main__":
    main()
