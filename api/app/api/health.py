from fastapi import APIRouter

from app.schemas import HealthOut

router = APIRouter()


@router.get("/health", response_model=HealthOut)
async def health():
    return HealthOut(
        status="ok",
        version="2.0.0",
        topology="control-plane",
    )
