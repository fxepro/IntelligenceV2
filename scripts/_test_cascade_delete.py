"""Verify source DELETE cascades media."""
from __future__ import annotations

import json
import os
import time
import uuid
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

API = "http://127.0.0.1:8000/api/v1"


def main() -> None:
    # nudge reload
    p = ROOT / "api" / "app" / "api" / "sources.py"
    p.touch()
    time.sleep(3)

    url = f"https://www.facebook.com/cascade.test.{uuid.uuid4().hex[:8]}"
    body = json.dumps(
        {
            "platform": "facebook",
            "source_type": "facebook_reels",
            "source_url": url,
            "name": "__cascade_test__",
            "autorun": False,
        }
    ).encode()
    req = urllib.request.Request(
        f"{API}/sources",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            src = json.loads(resp.read().decode())
    except urllib.error.HTTPError as exc:
        print("CREATE FAIL", exc.code, exc.read()[:400])
        raise SystemExit(1)
    sid = src["id"]
    print("created", sid, src.get("name"))

    eng = create_engine(os.environ["DATABASE_URL_SYNC"])
    rid = str(uuid.uuid4())
    with eng.begin() as c:
        c.execute(
            text(
                """
                INSERT INTO records (
                  id, domain, source_id, connector, external_id, dedup_key,
                  canonical_url, title, fields, status
                ) VALUES (
                  CAST(:id AS uuid), 'media', CAST(:sid AS uuid), 'test', 'x1',
                  :dedup, :curl, 'test reel', '{}'::jsonb, 'needs_review'
                )
                """
            ),
            {
                "id": rid,
                "sid": sid,
                "dedup": f"test-cascade-{rid}",
                "curl": f"https://www.facebook.com/reel/{rid.replace('-','')[:15]}",
            },
        )
    print("inserted media", rid)

    req = urllib.request.Request(f"{API}/sources/{sid}", method="DELETE")
    with urllib.request.urlopen(req, timeout=30) as resp:
        body = resp.read().decode()
        print("DELETE", resp.status, body)

    with eng.connect() as c:
        src_left = c.execute(
            text("SELECT COUNT(*) FROM sources WHERE id=CAST(:sid AS uuid)"),
            {"sid": sid},
        ).scalar()
        media_left = c.execute(
            text("SELECT COUNT(*) FROM records WHERE id=CAST(:id AS uuid)"),
            {"id": rid},
        ).scalar()
        named = c.execute(
            text("SELECT COUNT(*) FROM sources WHERE name='__cascade_test__'")
        ).scalar()
    print(f"source_left={src_left} media_left={media_left} named={named}")
    if src_left == 0 and media_left == 0:
        print("PASS cascade")
    else:
        print("FAIL cascade")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
