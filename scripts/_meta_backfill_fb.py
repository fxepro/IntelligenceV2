"""Backfill missing duration/size on Facebook media via yt-dlp."""
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
    import json

    import yt_dlp

    from app.services.discover_media import _file_size_bytes, _published_at, _ydl_opts

    source_filter = sys.argv[1] if len(sys.argv) > 1 else None  # optional name substring
    print(f"starting backfill filter={source_filter!r}", flush=True)
    eng = create_engine(os.environ["DATABASE_URL_SYNC"])
    list_sql = text(
        """
        SELECT r.id::text, r.canonical_url, s.name, r.fields
        FROM records r
        JOIN sources s ON s.id = r.source_id
        WHERE r.domain = 'media'
          AND s.platform = 'facebook'
          AND (
            NULLIF(r.fields->>'duration_seconds','null') IS NULL
            OR NULLIF(r.fields->>'file_size_bytes','null') IS NULL
          )
          AND (
            CAST(:name AS text) IS NULL
            OR s.name ILIKE '%' || CAST(:name AS text) || '%'
          )
        ORDER BY s.name, r.created_at
        """
    )

    with eng.connect() as c:
        rows = c.execute(list_sql, {"name": source_filter}).fetchall()
    print(f"rows needing duration/size: {len(rows)} (filter={source_filter!r})", flush=True)
    if not rows:
        return

    opts = _ydl_opts(rows[0].canonical_url, skip_download=True)
    # Quiet yt-dlp noise; we print our own progress.
    opts = {**opts, "quiet": True, "no_warnings": True}
    ok = fail = 0
    with yt_dlp.YoutubeDL(opts) as ydl, eng.begin() as c:
        for i, row in enumerate(rows, 1):
            try:
                info = ydl.extract_info(row.canonical_url, download=False)
            except Exception:
                fail += 1
                if i % 10 == 0:
                    print(f"  … {i}/{len(rows)} ok={ok} fail={fail}", flush=True)
                continue
            if not info:
                fail += 1
                continue
            duration = int(float(info["duration"])) if info.get("duration") else None
            fsize = _file_size_bytes(info)
            views = int(info["view_count"]) if info.get("view_count") is not None else None
            published = _published_at(info)
            fields = dict(row.fields or {})
            if duration is not None:
                fields["duration_seconds"] = duration
            if fsize is not None:
                fields["file_size_bytes"] = fsize
            if views is not None:
                fields["view_count"] = views
            if published:
                fields["published_at"] = published
            if duration is None and fsize is None:
                fail += 1
                continue
            c.execute(
                text(
                    """
                    UPDATE records SET fields = CAST(:fields AS jsonb)
                    WHERE id = CAST(:id AS uuid)
                    """
                ),
                {"id": row.id, "fields": json.dumps(fields)},
            )
            ok += 1
            if i % 10 == 0 or i == len(rows):
                print(f"  … {i}/{len(rows)} ok={ok} fail={fail} ({row.name})", flush=True)
    print(f"done ok={ok} fail={fail}", flush=True)


if __name__ == "__main__":
    main()
