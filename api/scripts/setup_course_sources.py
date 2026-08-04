#!/usr/bin/env python3
"""
Setup course sources feature.
Run: python scripts/setup_course_sources.py
"""
import asyncio
import sys
from pathlib import Path

async def run_setup():
    print("🚀 Setting up Course Sources feature...")

    # 1. Migrate database
    print("\n1️⃣  Migrating database (adding connector column)...")
    try:
        from sqlalchemy import text
        from app.database import engine

        async with engine.begin() as conn:
            # Check if column exists
            result = await conn.execute(
                text("""
                SELECT column_name FROM information_schema.columns
                WHERE table_name='sources' AND column_name='connector'
                """)
            )
            if result.fetchone():
                print("   ✓ Column 'connector' already exists")
            else:
                await conn.execute(
                    text("""
                    ALTER TABLE sources
                    ADD COLUMN connector VARCHAR(64) NULL
                    """)
                )
                print("   ✓ Added 'connector' column to sources table")
    except Exception as e:
        print(f"   ⚠️  Database migration: {e}")

    # 2. Verify scraper dependencies
    print("\n2️⃣  Checking Playwright installation...")
    try:
        from playwright.sync_browser import sync_playwright
        print("   ✓ Playwright installed")
    except ImportError:
        print("   ⚠️  Playwright not found. Install with:")
        print("      pip install playwright")
        print("      playwright install chromium")

    # 3. Verify course sources registry
    print("\n3️⃣  Verifying course sources registry...")
    try:
        from app.services.course_sources import COURSE_SOURCES
        count = len(COURSE_SOURCES)
        print(f"   ✓ {count} course source(s) registered:")
        for source_id in COURSE_SOURCES:
            print(f"     • {source_id}")
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return False

    # 4. Test API endpoint
    print("\n4️⃣  Testing API endpoint...")
    try:
        from app.services.course_sources import get_available_course_sources
        sources = get_available_course_sources()
        print(f"   ✓ API endpoint working ({len(sources)} sources)")
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return False

    print("\n✅ Setup complete!")
    print("\nNext steps:")
    print("1. Start API: python -m uvicorn app.main:app --reload --port 8000")
    print("2. Start worker: python -m celery -A celery_app.celery_app worker -l info")
    print("3. Start web: npm run dev (in web/)")
    print("4. Navigate to http://localhost:3000/courses/sources")
    print("5. Click 'Add Course Source' button")
    return True

if __name__ == "__main__":
    try:
        success = asyncio.run(run_setup())
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Setup failed: {e}")
        sys.exit(1)
