"""Structural URL / thumb integrity check."""
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
YT = re.compile(r"(?:v=|/shorts/|/embed/|youtu\.be/)([\w-]{6,})")


def main() -> None:
    eng = create_engine(os.environ["DATABASE_URL_SYNC"])
    q = text(
        """
        SELECT s.name, s.platform::text AS platform, r.external_id, r.canonical_url,
               COALESCE(r.fields->>'thumbnail_url','') AS thumb
        FROM records r
        JOIN sources s ON s.id = r.source_id
        WHERE r.domain = 'media' AND s.platform IN ('facebook', 'youtube')
        """
    )
    no_thumb = url_bad = 0
    samples = []
    with eng.connect() as c:
        rows = c.execute(q).fetchall()
    for r in rows:
        thumb = (r.thumb or "").strip()
        eid = (r.external_id or "").strip()
        url = r.canonical_url or ""
        if not thumb:
            no_thumb += 1
            if len(samples) < 8:
                samples.append(("no_thumb", r.platform, r.name, eid, url[:80]))
            continue
        if r.platform == "facebook":
            m = REEL.search(url)
            if not m or m.group(1) != eid:
                url_bad += 1
                if len(samples) < 8:
                    samples.append(("fb_mismatch", r.name, eid, url[:100]))
        elif r.platform == "youtube":
            if "youtube" not in url.lower() and "youtu.be" not in url.lower():
                url_bad += 1
            else:
                m = YT.search(url)
                if eid and m and m.group(1) != eid:
                    url_bad += 1
                    if len(samples) < 8:
                        samples.append(("yt_mismatch", r.name, eid, url[:100]))
    print(f"checked={len(rows)} no_thumb={no_thumb} url_mismatch={url_bad}")
    for s in samples:
        print(" ", s)


if __name__ == "__main__":
    main()
