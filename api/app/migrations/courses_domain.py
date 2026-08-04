"""Phase 0: rename curriculum vertical domain `library` → `courses`."""
from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.engine import Connection


def migrate_library_to_courses(conn: Connection) -> dict[str, int]:
    """
    Idempotent data migration for sources, jobs, records, and catalog IDs.
    Safe to run on every API startup until no `library` course rows remain.
    """
    counts: dict[str, int] = {}

    row = conn.execute(
        text("SELECT COUNT(*) FROM sources WHERE domain = 'library'")
    ).scalar()
    if row and int(row) > 0:
        conn.execute(
            text(
                """
                UPDATE sources
                SET domain = 'courses'
                WHERE domain = 'library'
                """
            )
        )
        counts["sources_domain"] = int(row)

    row = conn.execute(
        text(
            """
            SELECT COUNT(*) FROM sources
            WHERE domain = 'courses'
              AND source_url LIKE 'mi://library/courses/%'
            """
        )
    ).scalar()
    if row and int(row) > 0:
        conn.execute(
            text(
                """
                UPDATE sources
                SET source_url = 'mi://courses/' || SUBSTRING(source_url FROM 22)
                WHERE domain = 'courses'
                  AND source_url LIKE 'mi://library/courses/%'
                """
            )
        )
        counts["sources_url"] = int(row)

    row = conn.execute(
        text(
            """
            SELECT COUNT(*) FROM sources
            WHERE domain = 'courses'
              AND catalog_id LIKE 'LIB-%'
            """
        )
    ).scalar()
    if row and int(row) > 0:
        conn.execute(
            text(
                """
                UPDATE sources
                SET catalog_id = 'CRS-' || SUBSTRING(catalog_id FROM 5)
                WHERE domain = 'courses'
                  AND catalog_id LIKE 'LIB-%'
                """
            )
        )
        counts["sources_catalog"] = int(row)

    for table in ("jobs", "records"):
        row = conn.execute(
            text(f"SELECT COUNT(*) FROM {table} WHERE domain = 'library'")
        ).scalar()
        if row and int(row) > 0:
            conn.execute(
                text(
                    f"""
                    UPDATE {table}
                    SET domain = 'courses'
                    WHERE domain = 'library'
                    """
                )
            )
            counts[f"{table}_domain"] = int(row)

    return counts
