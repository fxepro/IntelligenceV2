"""Seed Courses domain sources from file-backed courses (sync).

  cd v2/api
  python scripts/seed_library_sources.py
"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

API_ROOT = Path(__file__).resolve().parents[1]
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app.database import SessionLocal
from app.services.library_sources import ensure_library_sources


async def main() -> None:
    async with SessionLocal() as db:
        rows = await ensure_library_sources(db)
        await db.commit()
        print(f"Ensured {len(rows)} library source(s):")
        for row in rows:
            print(f"  {row.catalog_id}  {row.name}  ({row.status.value})")


if __name__ == "__main__":
    asyncio.run(main())
