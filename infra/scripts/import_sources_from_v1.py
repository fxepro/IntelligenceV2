"""Import v1 sources (socialmedia) → v2 sources (intelligence).

Preserves source IDs. Sets domain='media'. Skips v1-only columns
(access_mode, subscriber_count, video_count, total_views, joined_at).

Usage (from v2/, with venv):
  python infra/scripts/import_sources_from_v1.py
"""

from __future__ import annotations

import argparse
import sys

import psycopg

SRC = "postgresql://postgres:postgres@127.0.0.1:5432/socialmedia"
DST = "postgresql://postgres:postgres@127.0.0.1:5432/intelligence"

COLS = (
    "id",
    "platform",
    "source_type",
    "source_url",
    "name",
    "description",
    "autorun",
    "status",
    "error_message",
    "last_checked",
    "created_at",
    "updated_at",
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Import sources from v1 DB into v2")
    parser.add_argument("--src", default=SRC, help="v1 DATABASE URL (socialmedia)")
    parser.add_argument("--dst", default=DST, help="v2 DATABASE URL (intelligence)")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Count and preview only; do not write",
    )
    args = parser.parse_args()

    with psycopg.connect(args.src) as src_conn, psycopg.connect(args.dst) as dst_conn:
        with src_conn.cursor() as scur, dst_conn.cursor() as dcur:
            scur.execute(
                f"""
                SELECT {", ".join(COLS)}
                FROM sources
                ORDER BY created_at NULLS LAST, id
                """
            )
            rows = scur.fetchall()
            print(f"v1 sources: {len(rows)}")

            dcur.execute("SELECT COUNT(*) FROM sources")
            before = dcur.fetchone()[0]
            print(f"v2 sources before: {before}")

            if args.dry_run:
                for row in rows[:10]:
                    print(" ", row[0], row[1], row[3][:70], row[4])
                if len(rows) > 10:
                    print(f"  ... +{len(rows) - 10} more")
                print("dry-run: no writes")
                return 0

            insert_sql = f"""
                INSERT INTO sources (
                    {", ".join(COLS)}, domain
                ) VALUES (
                    {", ".join(["%s"] * len(COLS))}, 'media'
                )
                ON CONFLICT (id) DO UPDATE SET
                    platform = EXCLUDED.platform,
                    source_type = EXCLUDED.source_type,
                    source_url = EXCLUDED.source_url,
                    name = EXCLUDED.name,
                    description = EXCLUDED.description,
                    autorun = EXCLUDED.autorun,
                    status = EXCLUDED.status,
                    error_message = EXCLUDED.error_message,
                    last_checked = EXCLUDED.last_checked,
                    updated_at = EXCLUDED.updated_at,
                    domain = 'media'
                """

            # source_url is also UNIQUE — if a different id owns the URL, skip & report
            inserted = 0
            updated = 0
            skipped = 0
            for row in rows:
                source_id, source_url = row[0], row[3]
                dcur.execute("SELECT id FROM sources WHERE id = %s", (source_id,))
                exists_id = dcur.fetchone()
                dcur.execute(
                    "SELECT id FROM sources WHERE source_url = %s AND id <> %s",
                    (source_url, source_id),
                )
                url_clash = dcur.fetchone()
                if url_clash:
                    print(f"SKIP url clash: {source_url!r} owned by {url_clash[0]} (wanted {source_id})")
                    skipped += 1
                    continue
                dcur.execute(insert_sql, row)
                if exists_id:
                    updated += 1
                else:
                    inserted += 1

            dst_conn.commit()
            dcur.execute("SELECT COUNT(*) FROM sources")
            after = dcur.fetchone()[0]
            print(f"inserted={inserted} updated={updated} skipped={skipped}")
            print(f"v2 sources after: {after}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
