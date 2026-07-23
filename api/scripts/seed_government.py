"""
Load government_sources.seed.json into Postgres (idempotent upsert by catalog_id).

  cd v2/api
  python scripts/build_government_seed.py   # refresh seed from CSV
  python scripts/seed_government.py         # apply to DB
  python scripts/seed_government.py --dry-run
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

# Allow `python scripts/seed_government.py` from v2/api
API_ROOT = Path(__file__).resolve().parents[1]
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app.config import get_settings
from app.models.source import Platform, Source, SourcePriority, SourceStatus, SourceType
from app.models.source_stream import SourceStream
from app.services.source_streams import default_streams_for_platform

ROOT = Path(__file__).resolve().parents[2]
SEED_PATH = ROOT / "docs" / "Domains" / "government_sources.seed.json"


def _enum(cls, value: str):
    return cls(value)


def apply_seed(*, dry_run: bool = False) -> None:
    if not SEED_PATH.is_file():
        raise SystemExit(
            f"Seed file missing: {SEED_PATH}\n"
            "Run: python scripts/build_government_seed.py"
        )
    payload = json.loads(SEED_PATH.read_text(encoding="utf-8"))
    items = payload.get("items") or []
    print(f"Seed: {SEED_PATH.name} ({len(items)} items)")

    engine = create_engine(get_settings().database_url_sync)
    created = updated = skipped = 0

    with Session(engine) as session:
        for item in items:
            catalog_id = item["catalog_id"]
            domain = item.get("domain") or "government"
            existing = session.scalar(
                select(Source).where(
                    Source.domain == domain,
                    Source.catalog_id == catalog_id,
                )
            )
            url = item["source_url"]
            url_clash = session.scalar(select(Source).where(Source.source_url == url))
            if url_clash and (not existing or url_clash.id != existing.id):
                print(f"  skip {catalog_id}: URL owned by {url_clash.catalog_id or url_clash.id}")
                skipped += 1
                continue

            category = (item.get("category") or "").strip() or None
            if category:
                category = category[:128]
            fields = dict(
                domain=domain,
                catalog_id=catalog_id,
                name=item.get("name"),
                source_url=url,
                description=item.get("description"),
                category=category,
                tags=list(item.get("tags") or []),
                priority=_enum(SourcePriority, item.get("priority") or "normal"),
                platform=_enum(Platform, item.get("platform") or "website"),
                source_type=_enum(SourceType, item.get("source_type") or "sitemap"),
                status=_enum(SourceStatus, item.get("status") or "active"),
                autorun=bool(item.get("autorun", False)),
                auto_transcribe=bool(item.get("auto_transcribe", False)),
            )

            if existing:
                for k, v in fields.items():
                    setattr(existing, k, v)
                updated += 1
                source = existing
            else:
                source = Source(**fields)
                session.add(source)
                session.flush()
                created += 1

            # Ensure at least one stream row for the platform default.
            streams = (
                session.execute(
                    select(SourceStream).where(SourceStream.source_id == source.id)
                )
                .scalars()
                .all()
            )
            if not streams:
                for stream_type, enabled, stream_url in default_streams_for_platform(
                    source.platform,
                    source.source_type,
                    source_url=source.source_url,
                ):
                    session.add(
                        SourceStream(
                            source_id=source.id,
                            stream_type=stream_type,
                            stream_url=stream_url or source.source_url,
                            enabled=enabled,
                        )
                    )

        if dry_run:
            session.rollback()
            print(f"DRY RUN — would create {created}, update {updated}, skip {skipped}")
        else:
            session.commit()
            print(f"Applied — created {created}, updated {updated}, skipped {skipped}")

    engine.dispose()


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed government sources")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    apply_seed(dry_run=args.dry_run)


if __name__ == "__main__":
    main()
