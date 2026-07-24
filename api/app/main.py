from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api import health, jobs, records, sources, discover, media, research, credentials, system, app_settings, ask, library, trademarks, domain_names
from app.config import get_settings
from app.database import Base, engine
from app.models import (  # noqa: F401 — register metadata
    AppSetting,
    DomainDetail,
    Job,
    Record,
    Source,
    SourceStream,
    PlatformCredential,
    TrademarkSourceDetail,
)


async def _column_exists(conn, table: str, column: str) -> bool:
    row = await conn.execute(
        text(
            """
            SELECT 1
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name = :table
              AND column_name = :column
            """
        ),
        {"table": table, "column": column},
    )
    return row.first() is not None


async def _run_dev_migrations() -> None:
    """
    Idempotent schema patches for local/dev.

    Each statement uses a short lock_timeout so a stuck Celery/API transaction
    cannot freeze uvicorn startup (and leave Sources spinning forever).
    """
    async with engine.connect() as conn:
        await conn.execute(text("SET lock_timeout = '3s'"))
        await conn.run_sync(Base.metadata.create_all)
        await conn.commit()

    patches = [
        "ALTER TYPE platform ADD VALUE IF NOT EXISTS 'x'",
        "ALTER TYPE platform ADD VALUE IF NOT EXISTS 'government'",
        "ALTER TYPE source_type ADD VALUE IF NOT EXISTS 'x_posts'",
        "ALTER TYPE source_type ADD VALUE IF NOT EXISTS 'website'",
        """
        DO $$ BEGIN
            CREATE TYPE source_priority AS ENUM ('low', 'normal', 'high', 'urgent');
        EXCEPTION
            WHEN duplicate_object THEN NULL;
        END $$;
        """,
        "ALTER TYPE source_priority ADD VALUE IF NOT EXISTS 'lowest'",
    ]
    for sql in patches:
        try:
            async with engine.connect() as conn:
                await conn.execute(text("SET lock_timeout = '3s'"))
                await conn.execute(text(sql))
                await conn.commit()
        except Exception as exc:
            # Enum/type patches are best-effort; missing lock should not kill the API.
            print(f"[lifespan] schema patch skipped: {type(exc).__name__}: {exc}")

    column_patches = [
        (
            "tags",
            "ALTER TABLE sources ADD COLUMN IF NOT EXISTS tags JSONB NOT NULL DEFAULT '[]'::jsonb",
        ),
        (
            "priority",
            """
            ALTER TABLE sources
            ADD COLUMN IF NOT EXISTS priority source_priority NOT NULL DEFAULT 'normal'
            """,
        ),
        (
            "auto_transcribe",
            "ALTER TABLE sources ADD COLUMN IF NOT EXISTS auto_transcribe BOOLEAN NOT NULL DEFAULT false",
        ),
        (
            "last_url_check",
            "ALTER TABLE sources ADD COLUMN IF NOT EXISTS last_url_check TIMESTAMPTZ",
        ),
        (
            "vanity_url",
            "ALTER TABLE sources ADD COLUMN IF NOT EXISTS vanity_url VARCHAR(2048)",
        ),
        (
            "catalog_id",
            "ALTER TABLE sources ADD COLUMN IF NOT EXISTS catalog_id VARCHAR(32)",
        ),
        (
            "category",
            "ALTER TABLE sources ADD COLUMN IF NOT EXISTS category VARCHAR(128)",
        ),
    ]
    for column, sql in column_patches:
        try:
            async with engine.connect() as conn:
                await conn.execute(text("SET lock_timeout = '3s'"))
                if await _column_exists(conn, "sources", column):
                    await conn.rollback()
                    continue
                await conn.execute(text(sql))
                await conn.commit()
        except Exception as exc:
            print(f"[lifespan] column patch '{column}' skipped: {type(exc).__name__}: {exc}")

    # Unique (domain, catalog_id) — Postgres allows multiple NULLs.
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SET lock_timeout = '3s'"))
            await conn.execute(
                text(
                    """
                    DO $$ BEGIN
                        ALTER TABLE sources
                        ADD CONSTRAINT uq_sources_domain_catalog_id
                        UNIQUE (domain, catalog_id);
                    EXCEPTION
                        WHEN duplicate_object THEN NULL;
                    END $$;
                    """
                )
            )
            await conn.commit()
    except Exception as exc:
        print(f"[lifespan] catalog_id unique skipped: {type(exc).__name__}: {exc}")

    # platform_credentials.site_url for website Access logins
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SET lock_timeout = '3s'"))
            if not await _column_exists(conn, "platform_credentials", "site_url"):
                await conn.execute(
                    text(
                        "ALTER TABLE platform_credentials "
                        "ADD COLUMN site_url VARCHAR(2048) NOT NULL DEFAULT ''"
                    )
                )
            await conn.execute(
                text(
                    """
                    DO $$ BEGIN
                        ALTER TABLE platform_credentials
                        DROP CONSTRAINT IF EXISTS uq_platform_credentials_platform_username;
                    EXCEPTION
                        WHEN undefined_object THEN NULL;
                    END $$;
                    """
                )
            )
            await conn.execute(
                text(
                    """
                    DO $$ BEGIN
                        ALTER TABLE platform_credentials
                        ADD CONSTRAINT uq_platform_credentials_platform_username_site
                        UNIQUE (platform, username, site_url);
                    EXCEPTION
                        WHEN duplicate_object THEN NULL;
                    END $$;
                    """
                )
            )
            await conn.commit()
    except Exception as exc:
        print(f"[lifespan] platform_credentials.site_url skipped: {type(exc).__name__}: {exc}")

    # trademark_source_details — standard 26-col enrichment + encrypted API key
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SET lock_timeout = '3s'"))
            for col, ddl in (
                ("registry_url", "VARCHAR(2048)"),
                ("journal_url", "VARCHAR(2048)"),
                ("response_format", "TEXT"),
                ("pagination", "TEXT"),
                ("query_parameters", "TEXT"),
                ("api_key_encrypted", "TEXT"),
            ):
                if not await _column_exists(conn, "trademark_source_details", col):
                    await conn.execute(
                        text(f"ALTER TABLE trademark_source_details ADD COLUMN {col} {ddl}")
                    )
            await conn.commit()
    except Exception as exc:
        print(
            f"[lifespan] trademark_source_details columns skipped: "
            f"{type(exc).__name__}: {exc}"
        )

    # Backfill MEDIA-0001… (and any other domain missing ids).
    try:
        from sqlalchemy import create_engine
        from sqlalchemy.orm import Session

        from app.services.catalog_ids import backfill_catalog_ids_sync
        from app.services.category_backfill import (
            backfill_category_from_tags_sync,
            restore_media_tags_from_category_sync,
        )

        sync_engine = create_engine(get_settings().database_url_sync)
        with Session(sync_engine) as session:
            n = backfill_catalog_ids_sync(session)
            if n:
                print(f"[lifespan] catalog_id backfill: assigned {n} source(s)")
            m = restore_media_tags_from_category_sync(session)
            if m:
                print(f"[lifespan] media tags restore: restored {m} source(s) from category")
            c = backfill_category_from_tags_sync(session)
            if c:
                print(f"[lifespan] category backfill: moved {c} source(s) from tags")
        sync_engine.dispose()
    except Exception as exc:
        print(f"[lifespan] catalog/category backfill skipped: {type(exc).__name__}: {exc}")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Dev bootstrap — Alembic later. No in-process workers here (v2 rule).
    await _run_dev_migrations()
    yield
    await engine.dispose()


settings = get_settings()

app = FastAPI(
    title="Media Intelligence API (v2)",
    description="Control plane only — enqueue jobs; workers do long-running work.",
    version="2.0.0",
    lifespan=lifespan,
)

# Dev: localhost + RFC1918 LAN hosts (any port). Tighten for production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_origin_regex=(
        r"http://("
        r"localhost|127\.0\.0\.1|"
        r"192\.168\.\d{1,3}\.\d{1,3}|"
        r"10\.\d{1,3}\.\d{1,3}\.\d{1,3}|"
        r"172\.(1[6-9]|2\d|3[0-1])\.\d{1,3}\.\d{1,3}"
        r")(:\d+)?"
    ),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

prefix = settings.api_v1_prefix
app.include_router(health.router, prefix=prefix, tags=["Health"])
app.include_router(jobs.router, prefix=f"{prefix}/jobs", tags=["Jobs"])
app.include_router(sources.router, prefix=f"{prefix}/sources", tags=["Sources"])
app.include_router(records.router, prefix=f"{prefix}/records", tags=["Records"])
app.include_router(discover.router, prefix=f"{prefix}/discover", tags=["Discover"])
app.include_router(media.router, prefix=f"{prefix}/media", tags=["Media"])
app.include_router(research.router, prefix=f"{prefix}/research", tags=["Research"])
app.include_router(credentials.router, prefix=f"{prefix}/credentials", tags=["Credentials"])
app.include_router(system.router, prefix=f"{prefix}/system", tags=["System"])
app.include_router(app_settings.router, prefix=f"{prefix}/settings", tags=["Settings"])
app.include_router(ask.router, prefix=f"{prefix}/ask", tags=["Ask"])
app.include_router(library.router, prefix=f"{prefix}/library", tags=["Library"])
app.include_router(trademarks.router, prefix=f"{prefix}/trademarks", tags=["Trademarks"])
app.include_router(domain_names.router, prefix=f"{prefix}/domain-names", tags=["Domains"])


@app.get("/")
async def root():
    return {
        "product": "Media Intelligence",
        "version": "2.0.0",
        "role": "control-plane",
        "docs": "/docs",
    }
