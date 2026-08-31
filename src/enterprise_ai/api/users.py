from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from enterprise_ai.api.dependencies import get_current_user
from enterprise_ai.core.security import hash_password
from enterprise_ai.persistence.database import get_db_session
from enterprise_ai.persistence.models.organization import Organization
from enterprise_ai.persistence.models.user import User
from enterprise_ai.schemas.user import UserCreate, UserResponse, UserUpdate

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

    normalized_email = str(payload.email).lower()

    user = User(
        name=payload.name,
        email=normalized_email,
        password_hash=hash_password(payload.password),
        organization_id=payload.organization_id,
    )

    session.add(user)

    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already exists",
        ) from exc

    await session.refresh(user)

    return user


@router.get(
    "",
    response_model=list[UserResponse],
)
async def list_users(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(get_current_user)],
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> list[User]:
    result = await session.execute(
        select(User)
        .where(
            User.organization_id == current_user.organization_id,
        )
        .order_by(User.created_at.desc())
        .limit(limit)
        .offset(offset)
    )

    return list(result.scalars().all())


@router.get(
    "/{user_id}",
    response_model=UserResponse,
)
async def get_user(
    user_id: UUID,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    user = await session.get(User, user_id)

    if user is None or user.organization_id != current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return user


@router.patch(
    "/{user_id}",
    response_model=UserResponse,
)
async def update_user(
    user_id: UUID,
    payload: UserUpdate,
    session: Annotated[
        AsyncSession,
        Depends(get_db_session),
    ],
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
) -> User:
    user = await session.get(User, user_id)

    if user is None or user.organization_id != current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if payload.name is not None:
        user.name = payload.name

    if payload.email is not None:
        user.email = str(payload.email).lower()

    try:
        await session.commit()
        await session.refresh(user)
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already exists",
        ) from exc

    return user


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_user(
    user_id: UUID,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> None:
    user = await session.get(User, user_id)

    if user is None or user.organization_id != current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    await session.delete(user)
    await session.commit()
