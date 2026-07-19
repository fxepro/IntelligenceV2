import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

URL = "postgresql+asyncpg://postgres:postgres@127.0.0.1:5432/intelligence"


async def main():
    engine = create_async_engine(URL)
    async with engine.begin() as conn:
        row = (
            await conn.execute(
                text(
                    "SELECT current_database(), "
                    "(SELECT count(*) FROM information_schema.tables "
                    "WHERE table_schema = 'public') AS public_tables"
                )
            )
        ).fetchone()
        print(f"database={row[0]} public_tables={row[1]}")
    await engine.dispose()


asyncio.run(main())
