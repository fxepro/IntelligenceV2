"""Cascade-delete Enemy.stickman + RichStickman."""
from __future__ import annotations

import os
import urllib.request
from pathlib import Path

from sqlalchemy import create_engine, text

ROOT = Path(__file__).resolve().parents[1]
for line in (ROOT / ".env").read_text(encoding="utf-8").splitlines():
    line = line.strip()
    if not line or line.startswith("#") or "=" not in line:
        continue
    k, v = line.split("=", 1)
    os.environ.setdefault(k.strip(), v.strip())

API = "http://127.0.0.1:8000/api/v1"
NAMES = ["Enemy.stickman", "RichStickman"]


def main() -> None:
    eng = create_engine(os.environ["DATABASE_URL_SYNC"])
    q = text(
        """
        SELECT s.id::text AS id, s.name,
          COUNT(r.id) AS media
        FROM sources s
        LEFT JOIN records r ON r.source_id = s.id AND r.domain = 'media'
        WHERE s.name = ANY(:names)
        GROUP BY s.id, s.name
        ORDER BY s.name
        """
    )
    with eng.connect() as c:
        rows = c.execute(q, {"names": NAMES}).fetchall()
    if not rows:
        print("not found")
        return
    for r in rows:
        print(f"before: {r.media} media | {r.name} | {r.id}")
        req = urllib.request.Request(f"{API}/sources/{r.id}", method="DELETE")
        with urllib.request.urlopen(req, timeout=30) as resp:
            print(f"DELETE {r.name}: {resp.status}")
    with eng.connect() as c:
        left = c.execute(
            text("SELECT name FROM sources WHERE name = ANY(:names)"),
            {"names": NAMES},
        ).fetchall()
        media = c.execute(
            text("SELECT COUNT(*) FROM records WHERE source_id = ANY(CAST(:ids AS uuid[]))"),
            {"ids": [r.id for r in rows]},
        ).scalar()
    print(f"after sources={list(left)} media_on_old_ids={media}")
    if left or media:
        raise SystemExit(1)
    print("PASS")


if __name__ == "__main__":
    main()
