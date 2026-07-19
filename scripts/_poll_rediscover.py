"""Poll discover job status for clean+rediscover batch."""
from __future__ import annotations

import os
import time
from pathlib import Path

from sqlalchemy import create_engine, text

ROOT = Path(__file__).resolve().parents[1]
for line in (ROOT / ".env").read_text(encoding="utf-8").splitlines():
    line = line.strip()
    if not line or line.startswith("#") or "=" not in line:
        continue
    k, v = line.split("=", 1)
    os.environ.setdefault(k.strip(), v.strip())

JOBS = [
    "8a3989fc-9ae3-4bf8-ad09-c98d72d19a74",
    "b54db6cd-1c87-4109-9aa0-2012c3133405",
    "5462ffd3-d3dc-4dca-ae6a-9a61595e84ea",
    "ed932904-4ead-4718-8ed1-1a9dea885ab2",
    "159d48b3-e3b3-4c87-aae1-5f8bc20817f9",
    "77d499cd-23b6-483f-84c2-e1f0275276e8",
    "4c985aa6-1971-43b9-a250-7c7c05b9ddce",
]


def main() -> None:
    eng = create_engine(os.environ["DATABASE_URL_SYNC"])
    q = text(
        """
        SELECT j.id::text, j.status::text, j.error_message, s.name,
               j.result, j.updated_at
        FROM jobs j
        LEFT JOIN sources s ON s.id = j.source_id
        WHERE j.id = ANY(CAST(:ids AS uuid[]))
        ORDER BY s.name
        """
    )
    audit = text(
        """
        SELECT s.name,
          COUNT(r.id) AS total,
          COUNT(r.id) FILTER (WHERE COALESCE(r.fields->>'thumbnail_url','') <> '') AS have,
          COUNT(r.id) FILTER (WHERE COALESCE(r.fields->>'thumbnail_url','') = '') AS missing
        FROM sources s
        LEFT JOIN records r ON r.source_id = s.id AND r.domain = 'media'
        WHERE s.id IN (
          '7ed8247b-d095-44d8-9f2c-9af08832c180',
          'd6905730-f606-4917-b2f1-f563ef5805ef',
          'cb7341d5-66df-4b2b-8b48-f6975fe31658',
          'd209829a-bdc6-4745-9a83-fa985246ede5',
          'beb7d43a-fc2d-476a-aa10-0d2e637380db',
          'd72f32e4-6576-41bd-bbdf-c2180d9d05fd',
          '3828ef5f-46b6-4c67-ba6c-0ebbd7aa5838'
        )
        GROUP BY s.name
        ORDER BY s.name
        """
    )
    with eng.connect() as c:
        rows = c.execute(q, {"ids": JOBS}).fetchall()
        print("=== jobs ===")
        done = 0
        for r in rows:
            print(f"  {r.status:10s} | {r.name} | err={r.error_message!r}")
            if r.status in ("succeeded", "completed", "failed", "cancelled"):
                done += 1
            if r.result:
                print(f"         result={r.result}")
        print(f"finished {done}/{len(rows)}")
        print("=== catalog ===")
        for r in c.execute(audit):
            total = int(r.total or 0)
            have = int(r.have or 0)
            missing = int(r.missing or 0)
            pct = 100.0 * have / total if total else 0
            print(f"  {total:4d} total | {have:4d} thumb | {missing:4d} miss | {pct:5.1f}% | {r.name}")


if __name__ == "__main__":
    main()
