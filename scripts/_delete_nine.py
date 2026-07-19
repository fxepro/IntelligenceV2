"""Delete named sources via API (cascade) and verify media is gone."""
from __future__ import annotations

import json
import os
import sys
import urllib.error
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

NAMES = [
    "EverydaySailing",
    "Stickmans Story",
    "Psych Aero",
    "CrypticCash",
    "Mrstickmantkk - Facebook",
    "Unethical.stickmansjr",
    "Highfinance_View",
    "DoggieLearns",
    "Tipper FB",
]


def main() -> None:
    eng = create_engine(os.environ["DATABASE_URL_SYNC"])
    find = text(
        """
        SELECT id::text, name, platform::text,
          (SELECT COUNT(*) FROM records r WHERE r.source_id = s.id) AS media
        FROM sources s
        WHERE s.name = ANY(:names)
        ORDER BY s.name
        """
    )
    with eng.connect() as c:
        rows = c.execute(find, {"names": NAMES}).fetchall()
    print("=== before ===")
    found = {r.name for r in rows}
    for r in rows:
        print(f"  {r.media:4d} media | {r.platform:8s} | {r.name} | {r.id}")
    missing = [n for n in NAMES if n not in found]
    if missing:
        print(f"  (not found): {missing}")

    for r in rows:
        req = urllib.request.Request(
            f"{API}/sources/{r.id}",
            method="DELETE",
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                print(f"DELETE {r.name}: {resp.status}")
        except urllib.error.HTTPError as exc:
            print(f"DELETE FAIL {r.name}: {exc.code} {exc.read()[:200]!r}")
            sys.exit(1)

    with eng.connect() as c:
        left_src = c.execute(find, {"names": NAMES}).fetchall()
        orphan = c.execute(
            text(
                """
                SELECT COUNT(*) FROM records r
                WHERE r.domain = 'media'
                  AND r.source_id IS NOT NULL
                  AND NOT EXISTS (SELECT 1 FROM sources s WHERE s.id = r.source_id)
                """
            )
        ).scalar()
        # Any media still keyed by deleted ids?
        leftover_media = c.execute(
            text(
                """
                SELECT COUNT(*) FROM records
                WHERE source_id = ANY(CAST(:ids AS uuid[]))
                """
            ),
            {"ids": [r.id for r in rows]},
        ).scalar()

    print("=== after ===")
    print(f"sources still matching names: {len(left_src)}")
    print(f"media still on deleted ids: {leftover_media}")
    print(f"orphaned media (any): {orphan}")
    if left_src or leftover_media:
        print("FAIL")
        sys.exit(1)
    print("PASS — clean delete")


if __name__ == "__main__":
    main()
