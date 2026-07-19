r"""Create source_streams table and backfill from sources + records.

Usage from v2/:
    .\.venv\Scripts\python.exe infra\scripts\migrate_source_streams.py
"""

from __future__ import annotations

import json
import uuid

import psycopg

DATABASE_URL = "postgresql://postgres:postgres@127.0.0.1:5432/intelligence"


def main() -> None:
    with psycopg.connect(DATABASE_URL, autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS source_streams (
                    id UUID PRIMARY KEY,
                    source_id UUID NOT NULL REFERENCES sources(id) ON DELETE CASCADE,
                    stream_type source_type NOT NULL,
                    stream_url VARCHAR(2048),
                    enabled BOOLEAN NOT NULL DEFAULT TRUE,
                    last_checked TIMESTAMPTZ,
                    error_message VARCHAR(1024),
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    CONSTRAINT uq_source_streams_source_type UNIQUE (source_id, stream_type)
                )
                """
            )
            cur.execute(
                "CREATE INDEX IF NOT EXISTS ix_source_streams_source_id ON source_streams(source_id)"
            )
            cur.execute(
                "ALTER TABLE source_streams ADD COLUMN IF NOT EXISTS stream_url VARCHAR(2048)"
            )

            cur.execute(
                """
                SELECT id, platform::text, source_type::text, last_checked, error_message
                FROM sources
                ORDER BY created_at
                """
            )
            sources = cur.fetchall()
            streams_created = 0

            for source_id, platform, source_type, last_checked, error_message in sources:
                types: list[tuple[str, bool]] = [(source_type, True)]
                if platform == "youtube" and source_type == "youtube_videos":
                    types.append(("youtube_shorts", True))
                elif platform == "facebook" and source_type == "facebook_reels":
                    types.append(("facebook_videos", False))

                for stream_type, enabled in types:
                    cur.execute(
                        """
                        INSERT INTO source_streams (
                            id, source_id, stream_type, enabled, last_checked, error_message
                        ) VALUES (%s, %s, %s, %s, %s, %s)
                        ON CONFLICT (source_id, stream_type) DO NOTHING
                        """,
                        (uuid.uuid4(), source_id, stream_type, enabled, last_checked, error_message),
                    )
                    streams_created += cur.rowcount

            # Backfill record stream + pipeline fields
            cur.execute(
                """
                SELECT r.id, r.fields, s.platform::text, s.source_type::text
                FROM records r
                LEFT JOIN sources s ON s.id = r.source_id
                WHERE r.domain = 'media'
                """
            )
            updated_records = 0
            for record_id, fields, platform, source_type in cur.fetchall():
                fields = dict(fields or {})
                changed = False
                if not fields.get("stream_type"):
                    ct = (fields.get("content_type") or "video").lower()
                    if platform == "youtube":
                        st = "youtube_shorts" if ct == "short" else "youtube_videos"
                    elif platform == "facebook":
                        st = "facebook_reels" if ct == "short" else "facebook_videos"
                    elif platform == "instagram":
                        st = "instagram_reels"
                    elif platform == "tiktok":
                        st = "tiktok_videos"
                    else:
                        st = source_type or "profile"
                    fields["stream_type"] = st
                    changed = True
                if not fields.get("download_status"):
                    fields["download_status"] = "pending"
                    changed = True
                if not fields.get("transcription_status"):
                    fields["transcription_status"] = "pending"
                    changed = True
                if changed:
                    cur.execute(
                        "UPDATE records SET fields = %s::jsonb WHERE id = %s",
                        (json.dumps(fields), record_id),
                    )
                    updated_records += 1

            # YouTube stream URLs are deterministic. Facebook stream URLs are
            # not, so existing rows use the known page URL until edited.
            cur.execute(
                """
                UPDATE source_streams ss
                SET stream_url =
                    regexp_replace(s.source_url, '/(videos|shorts)/?$', '') || '/videos',
                    enabled = TRUE
                FROM sources s
                WHERE ss.source_id = s.id
                  AND ss.stream_type = 'youtube_videos'
                """
            )
            # Merge duplicate YouTube rows such as /@channel and
            # /@channel/shorts into one channel source.
            cur.execute(
                """
                SELECT id, source_url, created_at
                FROM sources
                WHERE platform = 'youtube'
                ORDER BY created_at, id
                """
            )
            youtube_groups: dict[str, list[tuple]] = {}
            for source_id, source_url, created_at in cur.fetchall():
                base = source_url.rstrip("/")
                for suffix in ("/videos", "/shorts"):
                    if base.lower().endswith(suffix):
                        base = base[: -len(suffix)]
                        break
                youtube_groups.setdefault(base, []).append(
                    (source_id, source_url, created_at)
                )

            merged_sources = 0
            for base, rows in youtube_groups.items():
                keeper = next((row for row in rows if row[1].rstrip("/") == base), rows[0])
                keeper_id = keeper[0]
                for duplicate_id, _duplicate_url, _created_at in rows:
                    if duplicate_id == keeper_id:
                        continue
                    cur.execute(
                        "UPDATE records SET source_id = %s WHERE source_id = %s",
                        (keeper_id, duplicate_id),
                    )
                    cur.execute(
                        "UPDATE jobs SET source_id = %s WHERE source_id = %s",
                        (keeper_id, duplicate_id),
                    )
                    cur.execute(
                        """
                        INSERT INTO source_streams (
                            id, source_id, stream_type, stream_url, enabled,
                            last_checked, error_message
                        )
                        SELECT gen_random_uuid(), %s, stream_type, stream_url,
                               enabled, last_checked, error_message
                        FROM source_streams
                        WHERE source_id = %s
                        ON CONFLICT (source_id, stream_type) DO UPDATE SET
                            stream_url = COALESCE(
                                source_streams.stream_url,
                                EXCLUDED.stream_url
                            ),
                            enabled = source_streams.enabled OR EXCLUDED.enabled
                        """,
                        (keeper_id, duplicate_id),
                    )
                    cur.execute("DELETE FROM sources WHERE id = %s", (duplicate_id,))
                    merged_sources += 1
                cur.execute(
                    "UPDATE sources SET source_url = %s WHERE id = %s",
                    (base, keeper_id),
                )
            cur.execute(
                """
                UPDATE source_streams ss
                SET stream_url =
                    regexp_replace(s.source_url, '/(videos|shorts)/?$', '') || '/shorts',
                    enabled = TRUE
                FROM sources s
                WHERE ss.source_id = s.id
                  AND ss.stream_type = 'youtube_shorts'
                """
            )
            cur.execute("SELECT COUNT(*) FROM source_streams")
            total_streams = cur.fetchone()[0]
            cur.execute(
                """
                UPDATE source_streams ss
                SET stream_url = COALESCE(ss.stream_url, s.source_url),
                    enabled = TRUE
                FROM sources s
                WHERE ss.source_id = s.id
                  AND ss.stream_type IN ('facebook_reels', 'facebook_videos')
                """
            )
            cur.execute(
                """
                UPDATE source_streams ss
                SET stream_url = COALESCE(ss.stream_url, s.source_url)
                FROM sources s
                WHERE ss.source_id = s.id
                  AND ss.stream_url IS NULL
                """
            )

    print(
        f"source_streams: inserted={streams_created} total={total_streams} "
        f"records_backfilled={updated_records} sources_merged={merged_sources}"
    )


if __name__ == "__main__":
    main()
