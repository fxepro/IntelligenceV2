import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.job import Job
from app.schemas import JobOut

router = APIRouter()


@router.get("/{job_id}", response_model=JobOut)
async def get_job(job_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    job = await db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.get("", response_model=list[JobOut])
async def list_jobs(
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    rows = (
        await db.scalars(select(Job).order_by(Job.created_at.desc()).limit(min(limit, 200)))
    ).all()
    return rows
