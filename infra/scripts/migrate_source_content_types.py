r"""Add platform-specific source content types and migrate existing media sources.

Usage from v2/:
    .\.venv\Scripts\python.exe infra\scripts\migrate_source_content_types.py
"""

from __future__ import annotations

import psycopg


DATABASE_URL = "postgresql://postgres:postgres@127.0.0.1:5432/intelligence"

NEW_TYPES = (
    "facebook_reels",
    "facebook_videos",
    "youtube_videos",
    "youtube_shorts",
    "instagram_reels",
    "tiktok_videos",
)


def main() -> None:
    # PostgreSQL requires newly-added enum values to be committed before use.
    with psycopg.connect(DATABASE_URL, autocommit=True) as conn:
        with conn.cursor() as cur:
            for source_type in NEW_TYPES:
                cur.execute(f"ALTER TYPE source_type ADD VALUE IF NOT EXISTS '{source_type}'")

            cur.execute(
                """
                UPDATE sources
                SET source_type = 'facebook_reels'
                WHERE platform = 'facebook'
                  AND source_type IN ('profile', 'video')
                """
            )
            facebook = cur.rowcount

            cur.execute(
                """
                UPDATE sources
                SET source_type = 'youtube_videos'
                WHERE platform = 'youtube'
                  AND source_type IN ('channel', 'playlist', 'video')
                """
            )
            youtube = cur.rowcount

            cur.execute(
                """
                UPDATE sources
                SET source_type = 'instagram_reels'
                WHERE platform = 'instagram'
                  AND source_type IN ('profile', 'video')
                """
            )
            instagram = cur.rowcount

            cur.execute(
                """
                UPDATE sources
                SET source_type = 'tiktok_videos'
                WHERE platform = 'tiktok'
                  AND source_type IN ('profile', 'video')
                """
            )
            tiktok = cur.rowcount

    print(
        "Migrated source types: "
        f"facebook={facebook}, youtube={youtube}, "
        f"instagram={instagram}, tiktok={tiktok}"
    )


if __name__ == "__main__":
    main()
