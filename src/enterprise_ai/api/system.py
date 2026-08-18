from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from enterprise_ai.persistence.database import get_db_session

router = APIRouter(tags=["System"])


@router.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "healthy"}


@router.get("/ready")
async def readiness_check(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict[str, str]:
    try:
        await session.execute(text("SELECT 1"))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database unavailable",
        ) from exc

    return {"status": "ready"}
