"""Audit FB media metadata coverage."""
from __future__ import annotations

import os
from pathlib import Path

from sqlalchemy import create_engine, text

ROOT = Path(__file__).resolve().parents[1]
for line in (ROOT / ".env").read_text(encoding="utf-8").splitlines():
    line = line.strip()
    if not line or line.startswith("#") or "=" not in line:
        continue
    k, v = line.split("=", 1)
    os.environ.setdefault(k.strip(), v.strip())


def main() -> None:
    eng = create_engine(os.environ["DATABASE_URL_SYNC"])
    q = text(
        """
        SELECT s.name,
          COUNT(r.id) AS total,
          COUNT(r.id) FILTER (
            WHERE COALESCE(r.fields->>'thumbnail_url','') <> ''
          ) AS thumbs,
          COUNT(r.id) FILTER (
            WHERE NULLIF(r.fields->>'duration_seconds','null') IS NOT NULL
          ) AS duration,
          COUNT(r.id) FILTER (
            WHERE NULLIF(r.fields->>'file_size_bytes','null') IS NOT NULL
          ) AS fsize,
          COUNT(r.id) FILTER (
            WHERE NULLIF(r.fields->>'view_count','null') IS NOT NULL
          ) AS views
        FROM sources s
        JOIN records r ON r.source_id = s.id AND r.domain = 'media'
        WHERE s.platform = 'facebook'
        GROUP BY s.name
        ORDER BY s.name
        """
    )
    with eng.connect() as c:
        for r in c.execute(q):
            t = int(r.total)
            print(
                f"{t:4d} tot | {int(r.thumbs):4d} thumb | {int(r.duration):4d} dur "
                f"| {int(r.fsize):4d} size | {int(r.views):4d} views | {r.name}"
            )


if __name__ == "__main__":
    main()
