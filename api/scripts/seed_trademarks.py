"""
Load Trademark catalog batches (CSV + XLSX) into sources (header spine).

Reads every Batch*.csv / Batch*.xlsx under docs/Domains/Trademarks/
(TMK-0001 … TMK-0320).

  cd v2/api
  python scripts/seed_trademarks.py
  python scripts/seed_trademarks.py --dry-run

Forces:
  platform = government
  source_type = website   (all rows; Source Type column ignored for now)
"""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import Session

API_ROOT = Path(__file__).resolve().parents[1]
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app.config import get_settings
from app.models.source import Platform, Source, SourcePriority, SourceStatus, SourceType
from app.models.source_stream import SourceStream
from app.services.source_streams import default_streams_for_platform

ROOT = Path(__file__).resolve().parents[2]
CATALOG_DIR = ROOT / "docs" / "Domains" / "Trademarks"

HEADER_ALIASES = {
    "catalog id": "catalog_id",
    "catalog_id": "catalog_id",
    "domain": "domain",
    "name": "name",
    "source url": "source_url",
    "source_url": "source_url",
    "category": "category",
    "description": "description",
    "priority": "priority",
    "platform": "platform",
    "source type": "source_type",
    "source_type": "source_type",
}


def _ensure_enum_values(engine) -> None:
    with engine.begin() as conn:
        conn.execute(text("ALTER TYPE platform ADD VALUE IF NOT EXISTS 'government'"))
        conn.execute(text("ALTER TYPE source_type ADD VALUE IF NOT EXISTS 'website'"))


def _priority(raw: str) -> SourcePriority:
    key = (raw or "normal").strip().lower()
    try:
        return SourcePriority(key)
    except ValueError:
        return SourcePriority.normal


def _normalize_header(value: object) -> str | None:
    if value is None:
        return None
    key = str(value).strip().lower()
    return HEADER_ALIASES.get(key)


def _cell(value: object) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _iter_catalog_files() -> list[Path]:
    if not CATALOG_DIR.is_dir():
        raise SystemExit(f"Catalog dir missing: {CATALOG_DIR}")
    # Prefer *_COMPLETED.xlsx over the plain BatchN file when both exist.
    by_stem: dict[str, Path] = {}
    for path in [
        *CATALOG_DIR.glob("Trademark_Intelligence_Source_Catalog_Batch*.csv"),
        *CATALOG_DIR.glob("Trademark_Intelligence_Source_Catalog_Batch*.xlsx"),
    ]:
        name = path.name
        if name.startswith(".~"):
            continue
        key = name.lower().replace("_completed", "")
        prev = by_stem.get(key)
        if prev is None:
            by_stem[key] = path
            continue
        # Keep COMPLETED when colliding with non-COMPLETED of same batch.
        if "_completed" in name.lower() and "_completed" not in prev.name.lower():
            by_stem[key] = path
    files = sorted(by_stem.values(), key=lambda p: p.name.lower())
    if not files:
        raise SystemExit(f"No trademark batch files in {CATALOG_DIR}")
    return files


def _rows_from_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        out: list[dict[str, str]] = []
        for raw in reader:
            row: dict[str, str] = {}
            for k, v in raw.items():
                nk = _normalize_header(k)
                if nk:
                    row[nk] = _cell(v)
            out.append(row)
        return out


def _rows_from_xlsx(path: Path) -> list[dict[str, str]]:
    import openpyxl

    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    try:
        ws = wb.active
        rows_iter = ws.iter_rows(values_only=True)
        header_raw = next(rows_iter, None)
        if not header_raw:
            return []
        headers = [_normalize_header(h) for h in header_raw]
        out: list[dict[str, str]] = []
        for values in rows_iter:
            if not values or all(v is None or str(v).strip() == "" for v in values):
                continue
            row: dict[str, str] = {}
            for key, value in zip(headers, values):
                if key:
                    row[key] = _cell(value)
            out.append(row)
        return out
    finally:
        wb.close()


def _load_all_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for path in _iter_catalog_files():
        batch = _rows_from_csv(path) if path.suffix.lower() == ".csv" else _rows_from_xlsx(path)
        print(f"  {path.name}: {len(batch)} rows")
        rows.extend(batch)
    return rows


def apply_seed(*, dry_run: bool = False) -> None:
    print(f"Catalog: {CATALOG_DIR}")
    rows = _load_all_rows()
    print(f"Total rows: {len(rows)}")

    engine = create_engine(get_settings().database_url_sync)
    _ensure_enum_values(engine)

    created = updated = skipped = 0
    with Session(engine) as session:
        for row in rows:
            catalog_id = (row.get("catalog_id") or "").strip().upper()
            domain = (row.get("domain") or "trademarks").strip().lower() or "trademarks"
            name = (row.get("name") or "").strip()
            url = (row.get("source_url") or "").strip().rstrip("/")
            if not catalog_id or not name or not url:
                print(f"  skip incomplete row: {catalog_id or name or url}")
                skipped += 1
                continue

            existing = session.scalar(
                select(Source).where(
                    Source.domain == domain,
                    Source.catalog_id == catalog_id,
                )
            )
            url_clash = session.scalar(select(Source).where(Source.source_url == url))
            if url_clash and (not existing or url_clash.id != existing.id):
                print(
                    f"  skip {catalog_id}: URL owned by "
                    f"{url_clash.catalog_id or url_clash.id}"
                )
                skipped += 1
                continue

            category = (row.get("category") or "").strip() or None
            if category:
                category = category[:128]
            description = (row.get("description") or "").strip() or None
            if description and len(description) > 1000:
                description = description[:1000]

            fields = dict(
                domain=domain,
                catalog_id=catalog_id,
                name=name[:512],
                source_url=url[:2048],
                description=description,
                category=category,
                tags=[],
                priority=_priority(row.get("priority") or "normal"),
                platform=Platform.government,
                source_type=SourceType.website,
                status=SourceStatus.active,
                autorun=False,
                auto_transcribe=False,
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
    parser = argparse.ArgumentParser(description="Seed trademark sources (all batches)")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    apply_seed(dry_run=args.dry_run)


if __name__ == "__main__":
    main()
