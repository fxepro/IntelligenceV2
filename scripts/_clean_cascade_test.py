"""Remove leftover cascade test rows."""
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

eng = create_engine(os.environ["DATABASE_URL_SYNC"])
with eng.begin() as c:
    m = c.execute(
        text("DELETE FROM records WHERE connector = 'test' OR title = 'test reel'")
    ).rowcount
    s = c.execute(text("DELETE FROM sources WHERE name = '__cascade_test__'")).rowcount
print(f"cleaned media={m} sources={s}")
