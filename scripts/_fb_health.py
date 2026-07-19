"""Quick FB channel health report."""
from __future__ import annotations

import os
import re
from pathlib import Path

from sqlalchemy import create_engine, text

ROOT = Path(__file__).resolve().parents[1]
for line in (ROOT / ".env").read_text(encoding="utf-8").splitlines():
    line = line.strip()
    if not line or line.startswith("#") or "=" not in line:
        continue
    k, v = line.split("=", 1)
    os.environ.setdefault(k.strip(), v.strip())

REEL = re.compile(r"/reel/(\d+)", re.I)


def main() -> None:
    eng = create_engine(os.environ["DATABASE_URL_SYNC"])
    q = text(
        """
        SELECT s.id::text, s.name, s.source_url, s.status::text AS status,
          COUNT(r.id) AS total,
          COUNT(r.id) FILTER (WHERE COALESCE(r.fields->>'thumbnail_url','') <> '') AS thumbs,
          COUNT(r.id) FILTER (WHERE NULLIF(r.fields->>'duration_seconds','null') IS NOT NULL) AS duration,
          COUNT(r.id) FILTER (WHERE NULLIF(r.fields->>'file_size_bytes','null') IS NOT NULL) AS fsize,
          COUNT(r.id) FILTER (WHERE COALESCE(r.title,'') = '' OR r.title ILIKE 'Reel %%') AS weak_title
        FROM sources s
        LEFT JOIN records r ON r.source_id = s.id AND r.domain = 'media'
        WHERE s.platform = 'facebook'
        GROUP BY s.id, s.name, s.source_url, s.status
        ORDER BY s.name
        """
    )
    orphan = text(
        """
        SELECT COUNT(*) FROM records r
        WHERE r.domain = 'media'
          AND r.source_id IS NOT NULL
          AND NOT EXISTS (SELECT 1 FROM sources s WHERE s.id = r.source_id)
        """
    )
    url_bad = text(
        """
        SELECT s.name, r.external_id, r.canonical_url
        FROM records r
        JOIN sources s ON s.id = r.source_id
        WHERE r.domain = 'media' AND s.platform = 'facebook'
        LIMIT 5000
        """
    )
    with eng.connect() as c:
        print("=== Facebook channels ===")
        bad_chans = []
        for r in c.execute(q):
            t = int(r.total or 0)
            th = int(r.thumbs or 0)
            d = int(r.duration or 0)
            fs = int(r.fsize or 0)
            wt = int(r.weak_title or 0)
            thumb_pct = 100.0 * th / t if t else 0
            dur_pct = 100.0 * d / t if t else 0
            flag = ""
            if t == 0:
                flag = " EMPTY"
            elif thumb_pct < 95 or dur_pct < 80:
                flag = " WEAK"
                bad_chans.append(r.name)
            print(
                f"{t:4d} tot | {th:4d} thumb ({thumb_pct:5.1f}%) | "
                f"{d:4d} dur ({dur_pct:5.1f}%) | {fs:4d} size | "
                f"{wt:3d} weak-title | {r.status:8s} | {r.name}{flag}"
            )
        print(f"\norphaned media (source gone): {c.execute(orphan).scalar()}")
        mismatches = 0
        for r in c.execute(url_bad):
            m = REEL.search(r.canonical_url or "")
            if not m or m.group(1) != (r.external_id or ""):
                mismatches += 1
        print(f"url/id mismatches (sample scan): {mismatches}")
        print(f"weak channels: {len(bad_chans)}")
        for n in bad_chans:
            print(f"  - {n}")


if __name__ == "__main__":
    main()
