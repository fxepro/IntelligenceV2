import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.job import JobType
from app.models.record import Record
from app.schemas import EnqueueResponse, RecordList, RecordOut
from app.services.jobs import enqueue_job

router = APIRouter()


@router.get("", response_model=RecordList)
async def list_records(
    domain: str = Query("media"),
    source_id: uuid.UUID | None = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    q = select(Record).where(Record.domain == domain)
    if source_id:
        q = q.where(Record.source_id == source_id)
    q = q.order_by(Record.created_at.desc()).limit(min(limit, 200))
    items = (await db.scalars(q)).all()
    count_q = select(func.count()).select_from(Record).where(Record.domain == domain)
    if source_id:
        count_q = count_q.where(Record.source_id == source_id)
    total = await db.scalar(count_q)
    return RecordList(items=items, total=total or 0)


@router.get("/{record_id}", response_model=RecordOut)
async def get_record(record_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    record = await db.get(Record, record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    return record


@router.post("/{record_id}/process", response_model=EnqueueResponse)
async def process_record(record_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Enqueue transcription / extraction — never process inside this request."""
    record = await db.get(Record, record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    job = await enqueue_job(
        db,
        job_type=JobType.transcribe,
        domain=record.domain,
        source_id=record.source_id,
        record_id=record.id,
        payload={"dedup_key": record.dedup_key},
    )
    return EnqueueResponse(job_id=job.id, status=job.status)
