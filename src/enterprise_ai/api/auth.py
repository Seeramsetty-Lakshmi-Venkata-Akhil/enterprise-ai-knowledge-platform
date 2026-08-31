from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from enterprise_ai.api.dependencies import get_current_user
from enterprise_ai.core.security import create_access_token, verify_password
from enterprise_ai.persistence.database import get_db_session
from enterprise_ai.persistence.models.user import User
from enterprise_ai.schemas.auth import LoginRequest, LoginResponse
from enterprise_ai.schemas.user import UserResponse

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


@router.post(
    "/login",
    response_model=LoginResponse,
)
async def login(
    payload: LoginRequest,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> LoginResponse:
    normalized_email = str(payload.email).lower()

    result = await session.execute(select(User).where(User.email == normalized_email))
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not verify_password(
        payload.password,
        user.password_hash,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    access_token = create_access_token(
        user_id=user.id,
        organization_id=user.organization_id,
    )

    return LoginResponse(
        access_token=access_token,
    )


@router.get(
    "/me",
    response_model=UserResponse,
)
async def get_me(
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
) -> User:
    return current_user
