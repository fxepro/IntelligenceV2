"""Clean incomplete/polluted FB media, enqueue rediscover, audit URL integrity."""
from __future__ import annotations

import json
import os
import re
import sys
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

API = os.environ.get("API_BASE", "http://127.0.0.1:8000/api/v1")
REEL_ID_IN_URL = re.compile(r"/reel/(\d+)", re.I)
YT_ID_IN_URL = re.compile(r"(?:v=|/shorts/|/embed/)([\w-]{6,11})")


def main() -> None:
    eng = create_engine(os.environ["DATABASE_URL_SYNC"])

    dirty_sql = text(
        """
        SELECT s.id::text AS id, s.name, s.platform::text AS platform, s.source_url,
          COUNT(*) AS total,
          COUNT(*) FILTER (WHERE COALESCE(r.fields->>'thumbnail_url','') = '') AS missing
        FROM sources s
        JOIN records r ON r.source_id = s.id AND r.domain = 'media'
        WHERE s.platform = 'facebook'
        GROUP BY s.id, s.name, s.platform, s.source_url
        HAVING COUNT(*) FILTER (WHERE COALESCE(r.fields->>'thumbnail_url','') = '') > 0
        ORDER BY missing DESC
        """
    )

    # Full wipe media for dirty FB sources (incomplete = pollution signal).
    wipe_sql = text(
        """
        DELETE FROM records
        WHERE domain = 'media'
          AND source_id = CAST(:sid AS uuid)
        """
    )
    # Also drop incomplete FB rows on otherwise-clean sources (belt+suspenders).
    wipe_incomplete = text(
        """
        DELETE FROM records
        WHERE domain = 'media'
          AND COALESCE(fields->>'thumbnail_url','') = ''
          AND source_id IN (SELECT id FROM sources WHERE platform = 'facebook')
        """
    )

    url_audit = text(
        """
        SELECT s.name, s.platform::text AS platform, r.external_id, r.canonical_url,
               COALESCE(r.fields->>'thumbnail_url','') AS thumb
        FROM records r
        JOIN sources s ON s.id = r.source_id
        WHERE r.domain = 'media'
          AND s.platform IN ('facebook', 'youtube')
        """
    )

    with eng.begin() as c:
        dirty = c.execute(dirty_sql).fetchall()
        print("=== dirty FB sources (will full wipe + rediscover) ===")
        for d in dirty:
            print(f"  {d.missing:4d} miss / {d.total:4d} | {d.name} | {d.id}")

        wiped = 0
        for d in dirty:
            res = c.execute(wipe_sql, {"sid": d.id})
            wiped += res.rowcount or 0
            print(f"  wiped {res.rowcount} media from {d.name}")

        leftover = c.execute(wipe_incomplete)
        print(f"leftover incomplete FB deleted: {leftover.rowcount}")
        print(f"total media wiped: {wiped + (leftover.rowcount or 0)}")

    # Enqueue discover for each dirty source
    print("\n=== enqueue rediscover ===")
    jobs = []
    for d in dirty:
        req = urllib.request.Request(
            f"{API}/sources/{d.id}/discover",
            data=json.dumps({"max_items": 400}).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                body = json.loads(resp.read().decode())
                jobs.append((d.name, body.get("job_id"), body.get("status")))
                print(f"  {d.name}: job={body.get('job_id')} status={body.get('status')}")
        except Exception as exc:
            print(f"  FAIL {d.name}: {exc}")
            jobs.append((d.name, None, str(exc)))

    # Structural link audit on remaining (non-wiped) media
    bad = []
    no_thumb = []
    with eng.connect() as c:
        rows = c.execute(url_audit).fetchall()
    for r in rows:
        if not (r.thumb or "").strip():
            no_thumb.append((r.name, r.platform, r.external_id, r.canonical_url))
        url = r.canonical_url or ""
        eid = (r.external_id or "").strip()
        if r.platform == "facebook":
            m = REEL_ID_IN_URL.search(url)
            if not m or m.group(1) != eid or "facebook.com/reel/" not in url.lower():
                bad.append(("fb_url", r.name, eid, url))
        elif r.platform == "youtube":
            if "youtube.com" not in url.lower() and "youtu.be" not in url.lower():
                bad.append(("yt_host", r.name, eid, url))
            m = YT_ID_IN_URL.search(url)
            if eid and m and m.group(1) != eid:
                bad.append(("yt_id", r.name, eid, url))
            if eid and not (r.thumb or "").strip():
                # should have been filled; flag
                pass

    print(f"\n=== structural audit (remaining media) ===")
    print(f"rows checked: {len(rows)}")
    print(f"url/id mismatches: {len(bad)}")
    for b in bad[:20]:
        print(f"  BAD {b}")
    print(f"still missing thumb (should be ~0 after rediscover): {len(no_thumb)}")

    print("\n=== jobs queued ===")
    for name, jid, st in jobs:
        print(f"  {name}: {jid} ({st})")


if __name__ == "__main__":
    main()
