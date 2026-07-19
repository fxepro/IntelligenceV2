"""Clear false URL-check errors that painted live sources red."""
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
    with eng.begin() as c:
        rows = c.execute(
            text(
                """
                SELECT id::text, name, error_message, status::text
                FROM sources
                WHERE error_message LIKE 'URL check:%'
                ORDER BY name
                """
            )
        ).fetchall()
        print(f"URL-check errors: {len(rows)}")
        for r in rows:
            msg = (r.error_message or "").encode("ascii", "replace").decode("ascii")
            print(f"  {r.status:8s} | {r.name} | {msg}")
        # Clear URL-check stamps; restore active when status was only from that.
        n = c.execute(
            text(
                """
                UPDATE sources
                SET error_message = NULL,
                    status = CASE
                      WHEN status = 'error' THEN 'active'::source_status
                      ELSE status
                    END
                WHERE error_message LIKE 'URL check:%'
                """
            )
        ).rowcount
        print(f"cleared: {n}")


if __name__ == "__main__":
    main()
