"""
Seed trademark_source_details from the standard 26-column workbook or CSV.

  cd v2/api
  python scripts/seed_trademark_details.py
  python scripts/seed_trademark_details.py --dry-run
  python scripts/seed_trademark_details.py --file path/to/batch.xlsx
  python scripts/seed_trademark_details.py --file path/to/batch.csv

Default file:
  docs/Domains/Trademarks/trademark_details_catalog_batch_001_TMK-0001-0050_REPULLED.xlsx
"""
from __future__ import annotations

import argparse
import csv
import sys
from datetime import date, datetime
from pathlib import Path

import openpyxl
from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import Session

API_ROOT = Path(__file__).resolve().parents[1]
ROOT = API_ROOT.parent
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app.config import get_settings
from app.models.source import Source
from app.models.trademark_source_detail import TrademarkSourceDetail

DEFAULT_XLSX = (
    ROOT
    / "docs"
    / "Domains"
    / "Trademarks"
    / "trademark_details_catalog_batch_001_TMK-0001-0050_REPULLED.xlsx"
)

URL_FIELDS = (
    "search_url",
    "status_lookup_url",
    "filing_url",
    "registry_url",
    "gazette_url",
    "journal_url",
    "api_url",
    "api_docs_url",
    "bulk_download_url",
)

TEXT_FIELDS = (
    "response_format",
    "pagination",
    "query_parameters",
)


def _cell(v: object) -> str:
    if v is None:
        return ""
    return str(v).strip()


def _url_or_none(v: object) -> str | None:
    """Only store real http(s) URLs; treat 'No API' / notes as empty."""
    s = _cell(v)
    if not s:
        return None
    low = s.lower()
    if low.startswith("http://") or low.startswith("https://"):
        return s[:2048]
    return None


def _parse_bool(v: object) -> bool | None:
    if v is None or v == "":
        return None
    if isinstance(v, bool):
        return v
    s = str(v).strip().lower()
    if s in {"true", "yes", "y", "1"}:
        return True
    if s in {"false", "no", "n", "0"}:
        return False
    if s in {"unknown", "n/a", "na", "-", "varies"}:
        return None
    return None


def _parse_date(v: object) -> date | None:
    if v is None or v == "":
        return None
    if isinstance(v, datetime):
        return v.date()
    if isinstance(v, date):
        return v
    s = str(v).strip()
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(s[:10], fmt).date()
        except ValueError:
            continue
    return None


def _load_rows(path: Path) -> list[dict]:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        with path.open(encoding="utf-8-sig", newline="") as f:
            return list(csv.DictReader(f))

    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    ws = wb.active
    it = ws.iter_rows(values_only=True)
    header = [str(h).strip() if h is not None else "" for h in next(it)]
    rows = []
    for values in it:
        if not values or all(v is None or str(v).strip() == "" for v in values):
            continue
        row = {}
        for i, key in enumerate(header):
            if key:
                row[key] = values[i] if i < len(values) else None
        rows.append(row)
    wb.close()
    return rows


def _ensure_columns(engine) -> None:
    """Add/widen standard enrichment columns if missing (local/dev)."""
    alters = [
        "ALTER TABLE trademark_source_details ADD COLUMN IF NOT EXISTS registry_url VARCHAR(2048)",
        "ALTER TABLE trademark_source_details ADD COLUMN IF NOT EXISTS journal_url VARCHAR(2048)",
        "ALTER TABLE trademark_source_details ADD COLUMN IF NOT EXISTS response_format TEXT",
        "ALTER TABLE trademark_source_details ADD COLUMN IF NOT EXISTS pagination TEXT",
        "ALTER TABLE trademark_source_details ADD COLUMN IF NOT EXISTS query_parameters TEXT",
        "ALTER TABLE trademark_source_details ADD COLUMN IF NOT EXISTS api_key_encrypted TEXT",
        "ALTER TABLE trademark_source_details ALTER COLUMN jurisdiction TYPE VARCHAR(256)",
        "ALTER TABLE trademark_source_details ALTER COLUMN update_frequency TYPE TEXT",
        "ALTER TABLE trademark_source_details ALTER COLUMN rate_limit TYPE TEXT",
    ]
    with engine.begin() as conn:
        for stmt in alters:
            conn.execute(text(stmt))


def apply_seed(*, path: Path, dry_run: bool = False) -> None:
    if not path.is_file():
        raise SystemExit(f"File not found: {path}")

    rows = _load_rows(path)
    print(f"File: {path.name} ({len(rows)} rows)")

    engine = create_engine(get_settings().database_url_sync)
    from app.database import Base

    Base.metadata.create_all(engine, tables=[TrademarkSourceDetail.__table__])
    _ensure_columns(engine)

    created = updated = skipped = 0
    with Session(engine) as session:
        for raw in rows:
            catalog_id = _cell(raw.get("catalog_id")).upper()
            if not catalog_id:
                skipped += 1
                continue

            source = session.scalar(
                select(Source).where(
                    Source.domain == "trademarks",
                    Source.catalog_id == catalog_id,
                )
            )
            if not source:
                print(f"  skip {catalog_id}: no trademarks source row")
                skipped += 1
                continue

            fields = dict(
                source_id=source.id,
                catalog_id=catalog_id,
                country=_cell(raw.get("country")) or None,
                country_code=_cell(raw.get("country_code")) or None,
                jurisdiction=_cell(raw.get("jurisdiction")) or None,
                office=_cell(raw.get("office")) or None,
                access_type=_cell(raw.get("access_type")) or None,
                authentication=_cell(raw.get("authentication")) or None,
                rate_limit=_cell(raw.get("rate_limit")) or None,
                supports_nice_classes=_parse_bool(raw.get("supports_nice_classes")),
                supports_image_search=_parse_bool(raw.get("supports_image_search")),
                update_frequency=_cell(raw.get("update_frequency")) or None,
                detail_status=_cell(raw.get("status")) or None,
                last_verified=_parse_date(raw.get("last_verified")),
                notes=_cell(raw.get("notes")) or None,
            )
            for key in URL_FIELDS:
                fields[key] = _url_or_none(raw.get(key))
            for key in TEXT_FIELDS:
                val = _cell(raw.get(key))
                fields[key] = val or None

            existing = session.scalar(
                select(TrademarkSourceDetail).where(
                    TrademarkSourceDetail.catalog_id == catalog_id
                )
            )
            if existing:
                for k, v in fields.items():
                    setattr(existing, k, v)
                updated += 1
            else:
                session.add(TrademarkSourceDetail(**fields))
                created += 1

        if dry_run:
            session.rollback()
            print(f"DRY RUN — would create {created}, update {updated}, skip {skipped}")
        else:
            session.commit()
            print(f"Applied — created {created}, updated {updated}, skipped {skipped}")

    engine.dispose()


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed trademark_source_details")
    parser.add_argument("--file", type=Path, default=DEFAULT_XLSX)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    apply_seed(path=args.file, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
