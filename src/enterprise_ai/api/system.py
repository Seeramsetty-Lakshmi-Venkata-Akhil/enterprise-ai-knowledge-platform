from fastapi import APIRouter

router = APIRouter(tags=["System"])


@router.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "healthy"}


@router.get("/ready")
async def readiness_check() -> dict[str, str]:
    return {"status": "ready"}
