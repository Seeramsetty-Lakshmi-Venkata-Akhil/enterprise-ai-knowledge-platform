from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from enterprise_ai.persistence.database import get_db_session
from enterprise_ai.persistence.models.organization import Organization
from enterprise_ai.persistence.models.user import User
from enterprise_ai.schemas.user import UserCreate, UserResponse

router = APIRouter(
    prefix="/users",
    tags=["Users"],
)


@router.post(
    "",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_user(
    payload: UserCreate,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> User:
    organization = await session.get(
        Organization,
        payload.organization_id,
    )

    if organization is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found",
        )

    user = User(
        name=payload.name,
        email=payload.email,
        organization_id=payload.organization_id,
    )

    session.add(user)

    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User already exists",
        ) from exc

    await session.refresh(user)

    return user


@router.get(
    "/{user_id}",
    response_model=UserResponse,
)
async def get_user(
    user_id: UUID,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> User:
    user = await session.get(User, user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return user
