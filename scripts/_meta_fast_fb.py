"""
Fast FB duration/size fill — ONE Playwright scroll per channel, not yt-dlp per reel.

Reads playable_duration_in_ms from the reels page JSON for IDs we already have,
then estimates file_size from duration. Minutes, not hours.
"""
from __future__ import annotations

import json
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

os.environ.setdefault(
    "PLAYWRIGHT_BROWSERS_PATH",
    str(ROOT / "infra" / "playwright-browsers"),
)


def _estimate_size(duration: int) -> int:
    return max(1, int(1200.0 * float(duration) * 1000 / 8))


def main() -> None:
    from app.services.facebook_reels import scrape_facebook_reels_sync

    name_filter = sys.argv[1] if len(sys.argv) > 1 else None
    eng = create_engine(os.environ["DATABASE_URL_SYNC"])

    sources_sql = text(
        """
        SELECT s.id::text, s.name, s.source_url,
          COUNT(r.id) FILTER (
            WHERE NULLIF(r.fields->>'duration_seconds','null') IS NULL
          ) AS missing_dur
        FROM sources s
        JOIN records r ON r.source_id = s.id AND r.domain = 'media'
        WHERE s.platform = 'facebook'
          AND (
            CAST(:name AS text) IS NULL
            OR s.name ILIKE '%' || CAST(:name AS text) || '%'
          )
        GROUP BY s.id, s.name, s.source_url
        HAVING COUNT(r.id) FILTER (
          WHERE NULLIF(r.fields->>'duration_seconds','null') IS NULL
        ) > 0
        ORDER BY missing_dur DESC
        """
    )
    ids_sql = text(
        """
        SELECT r.id::text AS rid, r.external_id, r.fields
        FROM records r
        WHERE r.source_id = CAST(:sid AS uuid)
          AND r.domain = 'media'
          AND NULLIF(r.fields->>'duration_seconds','null') IS NULL
        """
    )
    upd_sql = text(
        """
        UPDATE records SET fields = CAST(:fields AS jsonb)
        WHERE id = CAST(:id AS uuid)
        """
    )

    with eng.connect() as c:
        sources = c.execute(sources_sql, {"name": name_filter}).fetchall()
    print(f"channels needing duration: {len(sources)}", flush=True)
    if not sources:
        return

    for src in sources:
        print(f"\n=== {src.name} ({src.missing_dur} missing) ===", flush=True)
        with eng.connect() as c:
            rows = c.execute(ids_sql, {"sid": src.id}).fetchall()
        want = {r.external_id: r for r in rows if r.external_id}
        if not want:
            continue

        # One scrape pass — harvests tiles + hydrates durations from page JSON.
        try:
            items, _ = scrape_facebook_reels_sync(
                src.source_url,
                max_items=max(150, len(want) + 40),
                max_scrolls=min(200, max(60, len(want) // 2)),
                idle_rounds=12,
            )
        except Exception as exc:
            print(f"  scrape failed: {exc}", flush=True)
            continue

        by_id = {it["id"]: it for it in items if it.get("id")}
        filled = 0
        with eng.begin() as c:
            for eid, row in want.items():
                hit = by_id.get(eid) or {}
                dur = hit.get("duration_seconds")
                if not dur:
                    continue
                try:
                    dur_i = int(dur)
                except (TypeError, ValueError):
                    continue
                fields = dict(row.fields or {})
                fields["duration_seconds"] = dur_i
                if not fields.get("file_size_bytes"):
                    fields["file_size_bytes"] = _estimate_size(dur_i)
                c.execute(upd_sql, {"id": row.rid, "fields": json.dumps(fields)})
                filled += 1
        print(f"  filled {filled}/{len(want)} from scrape durations", flush=True)

    print("\ndone", flush=True)


if __name__ == "__main__":
    main()
