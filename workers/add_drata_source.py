import os
os.environ["PYTHONPATH"] = r"C:\AIProjects\intelligence\v2\api"

from db import session_scope
from app.models.source import Source, Platform, SourceType, SourceStatus, SourcePriority
from app.models.job import JobType
from app.services.catalog_ids import allocate_catalog_id
from app.services.jobs import enqueue_job
from sqlalchemy import select
import asyncio

def add_drata_source_sync():
    """Add Drata source directly to database and trigger discovery."""
    
    with session_scope() as db:
        # Check if Drata source already exists
        existing = db.scalar(
            select(Source).where(
                Source.domain == "courses",
                Source.source_url == "https://drata.com/learn/soc-2"
            )
        )
        
        if existing:
            print(f"Source already exists: {existing.id}")
            source = existing
        else:
            # Allocate catalog ID - need async wrapper
            import asyncio
            from app.services.catalog_ids import allocate_catalog_id as alloc_async
            
            # Create Drata source
            source = Source(
                domain="courses",
                catalog_id=None,  # Will set after allocation
                platform=Platform.website,
                source_type=SourceType.sitemap,
                source_url="https://drata.com/learn/soc-2",
                name="Drata SOC 2 Learn",
                description="Drata's SOC 2 compliance learning center (41 articles)",
                category="Course",
                tags=[],
                priority=SourcePriority.normal,
                autorun=False,
                auto_transcribe=False,
                status=SourceStatus.active,
                connector="drata",
            )
            db.add(source)
            db.flush()
            db.refresh(source)
            print(f"Created Drata source: {source.id}")
        
        # Enqueue discovery job
        from app.services.jobs import enqueue_job as enqueue_async
        
        # For now, manually create the job since enqueue_job is async
        from app.models.job import Job, JobStatus
        from datetime import datetime, timezone
        import uuid
        
        job = Job(
            job_type=JobType.discover,
            status=JobStatus.queued,
            domain="courses",
            source_id=source.id,
            payload={"source_id": str(source.id)},
            progress=0.0,
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        
        print(f"Enqueued discovery job: {job.id} (status: {job.status})")
        
        return str(source.id), str(job.id)

if __name__ == "__main__":
    source_id, job_id = add_drata_source_sync()
    print(f"\nSUCCESS!")
    print(f"Source ID: {source_id}")
    print(f"Job ID: {job_id}")
    print(f"Monitor discovery in worker terminal...")
