r"""Create persisted application settings for local transcription.

Usage from v2/:
    .\.venv\Scripts\python.exe infra\scripts\migrate_transcription_settings.py
"""
import psycopg

DATABASE_URL = "postgresql://postgres:postgres@127.0.0.1:5432/intelligence"


def main() -> None:
    with psycopg.connect(DATABASE_URL, autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS app_settings (
                    key VARCHAR(128) PRIMARY KEY,
                    value JSONB NOT NULL DEFAULT '{}'::jsonb,
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
                """
            )
            cur.execute(
                """
                INSERT INTO app_settings (key, value)
                VALUES (
                    'transcription',
                    '{"engine":"whisper_cpp","model":"medium","language":"auto","keep_audio":false}'::jsonb
                )
                ON CONFLICT (key) DO NOTHING
                """
            )
    print("Transcription settings migration complete.")


if __name__ == "__main__":
    main()
