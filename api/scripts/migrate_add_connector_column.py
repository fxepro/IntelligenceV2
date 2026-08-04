#!/usr/bin/env python3
"""
Add connector column to sources table.
Run: python scripts/migrate_add_connector_column.py
"""
import asyncio
from sqlalchemy import text
from app.database import engine

async def run_migration():
    async with engine.begin() as conn:
        # Check if column already exists
        result = await conn.execute(
            text("""
            SELECT column_name FROM information_schema.columns
            WHERE table_name='sources' AND column_name='connector'
            """)
        )
        if result.fetchone():
            print("✓ Column 'connector' already exists")
            return

        # Add column
        await conn.execute(
            text("""
            ALTER TABLE sources
            ADD COLUMN connector VARCHAR(64) NULL
            """)
        )
        print("✓ Added 'connector' column to sources table")

if __name__ == "__main__":
    asyncio.run(run_migration())
